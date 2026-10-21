from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from decimal import Decimal

import pytest
from flask import Flask

from models import db, lm, Usuario, Build, BuildSalva
from models.build_salva import LimiteBuildsError
from models.build_salva import MODELOS
from controllers.build_controller import build_bp
from services.build_service.criar_build_manual_service import CriarBuildManualService
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.duplicar_build_service import DuplicarBuildService


ESTADO = {"titulo": "PC de teste", "descricao": "", "componentes": {}}
PEDIDO = {"nome": "PC", "descricao": "Teste", "utilidade": "Jogos", "orcamento": 5000}


@pytest.fixture
def app_build(tmp_path):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="somente-testes", SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'builds.db'}")
    db.init_app(app)
    lm.init_app(app)
    app.register_blueprint(build_bp)
    with app.app_context():
        db.create_all()
        db.session.add_all([Usuario(nome="A", email="a@example.test",verificado=True), Usuario(nome="B", email="b@example.test",verificado=True)])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def autenticar(cliente):
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = "1"
        sessao["_fresh"] = True


def cadastrar_pecas(tipos):
    for tipo in tipos:
        modelo = MODELOS[tipo]
        dados = {"fabricante": "Teste", "modelo": tipo, "preco": 100, "consumo_energia": 1}
        for coluna in modelo.__table__.columns:
            if coluna.name not in dados and not coluna.nullable and not coluna.primary_key and not coluna.default and not coluna.server_default:
                dados[coluna.name] = "Teste" if coluna.type.python_type is str else 1
        if tipo == "processador":
            dados.update(videointegrado=True, cooler=True)
        if tipo == "fonte":
            dados["potencia_w"] = 500
        db.session.add(modelo(**dados))
    db.session.commit()


def test_limite_em_manual_importacao_duplicacao_e_llm(app_build, mocker):
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar")
    cliente = app_build.test_client()
    autenticar(cliente)
    for _ in range(3):
        resposta = cliente.post("/build/manual", json=ESTADO)
        assert resposta.status_code == 201
    identificador = resposta.json["build"]["id"]
    for rota, dados in [("/build/manual", ESTADO), (f"/build/{identificador}/duplicar", None), ("/build/", PEDIDO)]:
        resposta = cliente.post(rota, json=dados)
        assert resposta.status_code == 409
        assert resposta.json["codigo"] == "limite-builds"
    llm.assert_not_called()
    assert cliente.get("/build/").json["limite"] == 3
    # Edição continua disponível; liberar uma vaga permite criar novamente.
    assert cliente.put(f"/build/{identificador}", json={**ESTADO, "titulo": "Editada"}).status_code == 200
    assert cliente.delete(f"/build/{identificador}").status_code == 204
    assert cliente.post("/build/manual", json=ESTADO).status_code == 201
    with app_build.app_context():
        assert BuildSalva.query.filter_by(usuario_id=1).count() == 3
        assert CriarBuildManualService().executar(2, ESTADO)["usuario_id"] == 2


def test_duas_criacoes_simultaneas_na_ultima_vaga(app_build):
    with app_build.app_context():
        for _ in range(2):
            CriarBuildManualService().executar(1, ESTADO)
    def criar(_):
        with app_build.app_context():
            try:
                CriarBuildManualService().executar(1, ESTADO)
                return "criada"
            except LimiteBuildsError:
                return "limite"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(criar, range(2))) == ["criada", "limite"]
    with app_build.app_context():
        assert BuildSalva.query.filter_by(usuario_id=1).count() == 3


def test_reverifica_limite_depois_da_llm_e_rollback_sem_orfa(app_build):
    with app_build.app_context():
        BuildSalva.verificar_espaco(1)
        for _ in range(3):
            CriarBuildManualService().executar(1, ESTADO)
        with pytest.raises(LimiteBuildsError):
            BuildSalva.criar_limitada(1, ESTADO, gerada={"nome": "Resultado atrasado"})
        assert Build.query.count() == 0


@pytest.mark.parametrize("percentual", [-1, 100, 20.5, True, "20", None])
def test_rejeita_percentual_invalido_antes_da_llm(app_build, mocker, percentual):
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar")
    with app_build.app_context(), pytest.raises(ValueError, match="porcentagem"):
        CriarBuildService().executar(1, {**PEDIDO, "percentual_perifericos": percentual})
    llm.assert_not_called()


def test_reserva_preservada_ao_salvar_duplicar(app_build):
    with app_build.app_context():
        dados = CriarBuildManualService().executar(1, {**ESTADO, "orcamento": 5000, "incluirPerifericos": True, "percentualPerifericos": 20})
        salva = BuildSalva.buscar(1, dados["id"])
        salva.salvar_estado({**salva.estado, "titulo": "Renomeada"})
        assert salva.estado["percentualPerifericos"] == 20
        copia = DuplicarBuildService().executar(1, dados["id"])
        assert copia["estado"]["percentualPerifericos"] == 20


def test_divisao_exata_do_orcamento_e_prompt():
    assert CriarBuildService._dividir_orcamento(1234.56, 20) == (Decimal("987.65"), Decimal("246.91"))
    prompt = CriarBuildService._criar_prompt(PEDIDO, 5000, 800, {}, 20)
    assert "R$ 4000.00" in prompt and "R$ 1000.00 (20%)" in prompt
    assert "Teto para periféricos" in prompt
    assert "saldo de periféricos NÃO aumenta o teto do PC" in prompt
    assert "meta flexível" not in prompt


@pytest.mark.parametrize("permitido,valor,esperado", [(True, "4321.75", 4321.75), (False, "4321.75", None), (True, "0", None)])
def test_manual_usa_budget_autorizado_da_propria_conta(app_build, permitido, valor, esperado):
    with app_build.app_context():
        usuario = db.session.get(Usuario, 1)
        usuario.budget, usuario.usar_budget = Decimal(valor), permitido
        db.session.commit()
        resultado = CriarBuildManualService().executar(1, ESTADO)
        assert resultado["estado"]["orcamento"] == esperado
        assert resultado["compatibilidade"]["status"] == "nao_verificado"
        assert CriarBuildManualService().executar(2, ESTADO)["estado"]["orcamento"] is None


def test_manual_respeita_teto_explicito_e_nao_reescreve_edicao_ou_copia(app_build):
    with app_build.app_context():
        usuario = db.session.get(Usuario, 1)
        usuario.budget, usuario.usar_budget = Decimal("5000"), True
        db.session.commit()
        resultado = CriarBuildManualService().executar(1, {**ESTADO, "orcamento": None})
        assert resultado["estado"]["orcamento"] is None
        original = BuildSalva.buscar(1, resultado["id"])
        usuario.budget = Decimal("9000")
        db.session.commit()
        assert DuplicarBuildService().executar(1, original.to_dict()["id"])["estado"]["orcamento"] is None
        assert CriarBuildManualService().executar(1, {**ESTADO, "orcamento": 1234.56})["estado"]["orcamento"] == 1234.56


def test_rotas_recalculam_diagnostico_por_id_sem_confiar_no_front_e_preservam_rascunho(app_build):
    with app_build.app_context():
        cadastrar_pecas(["processador", "placa_mae"])
        cpu = MODELOS["processador"].buscar_por_id(1)
        placa = MODELOS["placa_mae"].buscar_por_id(1)
        cpu.soquete, placa.socket = "AM4", "AM5"
        db.session.commit()
    cliente = app_build.test_client()
    autenticar(cliente)
    estado = {**ESTADO, "visibilidade": "publico", "componentes": {"processador": {"id": 1}, "placa_mae": {"id": 1}},
              "compatibilidade": {"status": "sem_conflitos"}}
    resposta = cliente.post("/build/manual", json=estado)
    assert resposta.status_code == 201  # Rascunho com conflito continua podendo ser salvo.
    identificador = resposta.json["build"]["id"]
    for build in (resposta.json["build"], cliente.get(f"/build/{identificador}").json["build"],
                  cliente.get("/build/").json["builds"][0], cliente.get(f"/build/{identificador}/publica").json["build"]):
        assert build["compatibilidade"]["status"] == "incompativel"
        assert "compatibilidade" not in build["estado"]
    with app_build.app_context():
        MODELOS["placa_mae"].buscar_por_id(1).socket = "AM4"
        db.session.commit()
    resposta = cliente.put(f"/build/{identificador}", json=estado)
    assert resposta.status_code == 200
    assert resposta.json["build"]["compatibilidade"]["status"] == "nao_verificado"  # BIOS/encaixes ainda pendentes.


def resposta_com_perifericos():
    itens = [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in
             ("processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd", "monitor", "teclado", "mouse", "fone")]
    catalogo = {item["tipo"]: [{"id": 1, "fabricante": "Teste", "modelo": item["tipo"],
                "preco": 800 if item["tipo"] == "processador" else 50 if item["tipo"] in CriarBuildService.PERIFERICOS else 20}] for item in itens}
    return {**PEDIDO, "componentes": itens}, catalogo


def test_tetos_independentes_permitem_gastar_menos_sem_transferir_a_sobra():
    build, catalogo = resposta_com_perifericos()
    assert CriarBuildService._validar_build(deepcopy(build), catalogo, 1500, 20)["preco_total"] == 1100
    catalogo["processador"][0]["preco"] = 1100
    assert CriarBuildService._validar_build(deepcopy(build), catalogo, 1500, 20)["preco_total"] == 1400
    catalogo["processador"][0]["preco"] = 1100.01
    with pytest.raises(ValueError, match="limite destinado ao PC"):
        CriarBuildService._validar_build(deepcopy(build), catalogo, 1500, 20)
    catalogo["processador"][0]["preco"] = 800
    catalogo["monitor"][0]["preco"] = 150
    assert CriarBuildService._validar_build(deepcopy(build), catalogo, 1500, 20)["preco_total"] == 1200
    catalogo["monitor"][0]["preco"] = 150.01
    with pytest.raises(ValueError, match="limite reservado para periféricos"):
        CriarBuildService._validar_build(deepcopy(build), catalogo, 1500, 20)
    catalogo["processador"][0]["preco"] = 1500
    with pytest.raises(ValueError, match="Não foi possível gerar uma configuração dentro do orçamento"):
        CriarBuildService._validar_build(deepcopy(build), catalogo, 1500, 20)


def test_teto_percentual_preserva_centavos_sem_arredondar_para_cima():
    build, catalogo = resposta_com_perifericos()
    catalogo["monitor"][0]["preco"] = 96.91
    assert CriarBuildService._validar_build(deepcopy(build), catalogo, 1234.56, 20)["preco_total"] == 1146.91
    catalogo["monitor"][0]["preco"] = 96.92
    with pytest.raises(ValueError, match="limite reservado para periféricos"):
        CriarBuildService._validar_build(deepcopy(build), catalogo, 1234.56, 20)


def test_catalogo_respeita_os_dois_tetos_antes_de_chamar_a_llm(app_build, mocker):
    gerar_catalogo = mocker.patch("services.build_service.criar_build_service.CriarBuildService._gerar_catalogo", return_value={})
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar")
    with app_build.app_context(), pytest.raises(ValueError, match="Não há peças suficientes"):
        CriarBuildService().executar(1, {**PEDIDO, "percentual_perifericos": 90})
    assert gerar_catalogo.call_args.args[:2] == (Decimal("500.00"), Decimal("4500.00"))
    llm.assert_not_called()


@pytest.mark.parametrize("excesso", ["pc", "perifericos"])
def test_geracao_rejeita_transferencia_de_sobra_antes_de_salvar(app_build, mocker, excesso):
    tipos = ["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd", "monitor", "teclado", "mouse", "fone"]
    with app_build.app_context():
        cadastrar_pecas(tipos)
        if excesso == "perifericos":
            MODELOS["monitor"].buscar_por_id(1).preco = 750
        else:
            # Cada peça cabe no filtro individual, mas o subtotal do PC excede R$ 4.000.
            MODELOS["processador"].buscar_por_id(1).preco = 3000
            MODELOS["placa_mae"].buscar_por_id(1).preco = 700
        db.session.commit()
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", return_value={
        **PEDIDO, "componentes": [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in tipos],
    })
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json={**PEDIDO, "percentual_perifericos": 20})
    assert resposta.status_code == 502
    assert resposta.json["codigo"] == "geracao-invalida"
    assert ("limite destinado ao PC" if excesso == "pc" else "limite reservado para periféricos") in llm.call_args.args[0]
    assert llm.call_count == 2
    with app_build.app_context():
        assert Build.query.count() == BuildSalva.query.count() == 0


def test_faltam_perifericos_na_resposta():
    build, catalogo = resposta_com_perifericos()
    build["componentes"].pop()
    with pytest.raises(ValueError, match="não incluiu"):
        CriarBuildService._validar_build(build, catalogo, 1500, 20)


def test_geracao_persiste_original_e_estado_em_uma_transacao(app_build, mocker):
    tipos = ["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd", "monitor", "teclado", "mouse", "fone"]
    with app_build.app_context():
        cadastrar_pecas(tipos)
        llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", return_value={
            "nome": "PC gerado", "descricao": "Com periféricos", "utilidade": "Jogos",
            "componentes": [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in tipos],
        })
        resposta = CriarBuildService().executar(1, {**PEDIDO, "percentual_perifericos": 20})
        assert resposta["estado"]["percentualPerifericos"] == 20
        assert resposta["estado"]["orcamento"] == 5000
        assert resposta["preco_total"] == 1000
        assert len(resposta["componentes"]) == 10
        assert Build.query.count() == BuildSalva.query.count() == 1
        assert "Teto para periféricos: R$ 1000.00" in llm.call_args.args[0]
        assert len(BuildSalva.listar_por_usuario(1)) == 1


def test_geracao_rejeita_conflito_antes_de_gravar_build(app_build, mocker):
    tipos = ["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd"]
    with app_build.app_context():
        cadastrar_pecas(tipos)
        MODELOS["processador"].buscar_por_id(1).soquete = "AM4"
        MODELOS["placa_mae"].buscar_por_id(1).socket = "AM5"
        db.session.commit()
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", return_value={
        **PEDIDO, "componentes": [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in tipos],
    })
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json=PEDIDO)
    assert resposta.status_code == 502
    assert resposta.json["codigo"] == "geracao-invalida"
    assert "incompatibilidades" in llm.call_args.args[0]
    assert llm.call_count == 2
    with app_build.app_context():
        assert Build.query.count() == BuildSalva.query.count() == 0


def test_contas_que_ja_excederam_limite_nao_perdem_builds(app_build):
    with app_build.app_context():
        for _ in range(4):
            db.session.add(BuildSalva(usuario_id=1, estado=deepcopy(ESTADO)))
        db.session.commit()
        with pytest.raises(LimiteBuildsError):
            CriarBuildManualService().executar(1, ESTADO)
        assert len(BuildSalva.listar_por_usuario(1)) == 4


def test_geracao_de_rede_preserva_opcao_sem_perifericos_e_criacao_limitada(app_build, mocker):
    tipos = ["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd", "cabo_rede"]
    rede = {"tipo": "cabo", "possuiAcessorio": False, "comprimentoMetros": 2}
    with app_build.app_context():
        cadastrar_pecas(tipos)
        llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", return_value={
            **PEDIDO, "componentes": [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in tipos],
        })
        resposta = CriarBuildService().executar(1, {**PEDIDO, "rede": rede})
        assert resposta["estado"]["rede"] == rede
        assert resposta["estado"]["incluirRede"]
        assert not resposta["estado"]["incluirPerifericos"]
        assert resposta["estado"]["percentualPerifericos"] == 0
        assert resposta["estado"]["componentes"]["cabo_rede"]["id"] == 1
        assert Build.query.count() == BuildSalva.query.count() == 1
        assert "# REDE" in llm.call_args.args[0]


def test_orcamento_nao_aceita_fracao_de_centavo(app_build, mocker):
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar")
    with app_build.app_context(), pytest.raises(ValueError, match="casas decimais"):
        CriarBuildService().executar(1, {**PEDIDO, "orcamento": 5000.001})
    llm.assert_not_called()


@pytest.mark.parametrize("percentual", [0, 20])
def test_geracao_com_pecas_proprias_preserva_reserva_rede_e_extras(app_build, mocker, percentual):
    base = ["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd"]
    perifericos = ["monitor", "teclado", "mouse", "fone"]
    proprias = {"processador": "Teste processador", "monitor": "Meu monitor", "webcam": "Minha webcam"}
    novas = base[1:] + (perifericos[1:] if percentual else [])
    rede = {"tipo": "cabo", "possuiAcessorio": True}
    with app_build.app_context():
        cadastrar_pecas(base + perifericos)
        llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", return_value={
            **PEDIDO, "componentes": [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in novas],
        })
        resultado = CriarBuildService().executar(1, {**PEDIDO, "pecas_proprias": proprias, "rede": rede,
                                                  "percentual_perifericos": percentual})
        estado = resultado["estado"]
        assert estado["percentualPerifericos"] == percentual
        assert estado["rede"] == rede and estado["incluirRede"]
        assert estado["pecasExtras"] == {"webcam": "Minha webcam"}
        assert estado["componentes"]["processador"] == {"proprio": "Teste processador", "quantidade": 1}
        assert estado["componentes"]["monitor"] == {"proprio": "Meu monitor", "quantidade": 1}
        assert resultado["preco_total"] == 100 * len(novas)
        assert Build.query.count() == 0 and BuildSalva.query.count() == 1
        assert "PEÇAS QUE O USUÁRIO JÁ POSSUI" in llm.call_args.args[0]
        if not percentual:
            assert "Não inclua periféricos novos" in llm.call_args.args[0]
            assert not set(perifericos[1:]) & set(estado["componentes"])
        salva = BuildSalva.buscar(1, resultado["id"])
        salva.salvar_estado({**estado, "titulo": "Renomeada"})
        copia = DuplicarBuildService().executar(1, resultado["id"])
        assert copia["estado"]["pecasExtras"] == estado["pecasExtras"]
        assert copia["estado"]["percentualPerifericos"] == percentual


def test_pecas_proprias_reverificam_quota_apos_llm(app_build, mocker):
    tipos = ["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd"]
    with app_build.app_context():
        cadastrar_pecas(tipos)
        for _ in range(2):
            CriarBuildManualService().executar(1, ESTADO)

        def ocupar_ultima_vaga(*_args):
            CriarBuildManualService().executar(1, ESTADO)
            return {**PEDIDO, "componentes": [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in tipos[1:]]}

        llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", side_effect=ocupar_ultima_vaga)
        with pytest.raises(LimiteBuildsError):
            CriarBuildService().executar(1, {**PEDIDO, "pecas_proprias": {"processador": "Minha CPU"}})
        llm.assert_called_once()
        assert BuildSalva.query.count() == 3 and Build.query.count() == 0


def test_email_nao_verificado_bloqueia_todas_as_criacoes_sem_chamar_llm(app_build, mocker):
    cliente = app_build.test_client()
    autenticar(cliente)
    existente = cliente.post("/build/manual", json=ESTADO).json["build"]["id"]
    with app_build.app_context():
        db.session.get(Usuario,1).verificado = False
        db.session.commit()
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar")
    for rota,dados in [("/build/manual",ESTADO),("/build/",PEDIDO),(f"/build/{existente}/duplicar",None)]:
        resposta = cliente.post(rota,json=dados)
        assert resposta.status_code == 403
        assert resposta.json["codigo"] == "email-nao-verificado"
    llm.assert_not_called()
    with app_build.app_context():
        assert BuildSalva.query.count() == 1


@pytest.mark.parametrize("falha", ["gpu", "json", "id", "quantidade", "texto", "duplicada", "orcamento", "rede"])
def test_ia_corrige_saida_invalida_antes_de_persistir(app_build, mocker, falha):
    tipos = ["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd", "placa_video"]
    with app_build.app_context():
        cadastrar_pecas(tipos)
        MODELOS["processador"].buscar_por_id(1).videointegrado = False
        db.session.commit()
    correta = {**PEDIDO, "componentes": [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in tipos]}
    invalida = deepcopy(correta)
    if falha == "gpu":
        invalida["componentes"].pop()
    elif falha == "json":
        invalida = '{"componentes":'
    elif falha == "id":
        invalida["componentes"][0]["id"] = 999
    elif falha == "quantidade":
        invalida["componentes"][0]["quantidade"] = 0
    elif falha == "texto":
        invalida["nome"] = []
    elif falha == "duplicada":
        invalida["componentes"].append(deepcopy(invalida["componentes"][0]))
    elif falha == "orcamento":
        invalida["componentes"][5]["quantidade"] = 60
    else:
        invalida["componentes"].append({"tipo": "cabo_rede", "id": 1})
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", side_effect=[invalida, correta])
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json=PEDIDO)
    assert resposta.status_code == 201, resposta.json
    assert llm.call_count == 2
    assert "REVISÃO OBRIGATÓRIA" in llm.call_args.args[0]
    assert "NOVO JSON COMPLETO" in llm.call_args.args[0]
    assert resposta.json["build"]["estado"]["componentes"]["placa_video"]["id"] == 1
    with app_build.app_context():
        assert Build.query.count() == BuildSalva.query.count() == 1


def test_ia_invalida_duas_vezes_nao_persiste_nem_repete_sem_limite(app_build, mocker):
    with app_build.app_context():
        cadastrar_pecas(["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd"])
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", return_value="JSON inválido")
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json=PEDIDO)
    assert resposta.status_code == 502 and resposta.json["codigo"] == "geracao-invalida"
    assert "Nenhuma build foi salva" in resposta.json["erro"]
    assert llm.call_count == 2
    with app_build.app_context():
        assert Build.query.count() == BuildSalva.query.count() == 0


def test_revisao_reverifica_vaga_antes_de_gastar_outra_consulta(app_build, mocker):
    with app_build.app_context():
        cadastrar_pecas(["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd"])
        for _ in range(2):
            CriarBuildManualService().executar(1, ESTADO)
    def ocupar(*_args):
        CriarBuildManualService().executar(1, ESTADO)
        return "JSON inválido"
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", side_effect=ocupar)
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json=PEDIDO)
    assert resposta.status_code == 409
    llm.assert_called_once()
    with app_build.app_context():
        assert BuildSalva.query.count() == 3 and Build.query.count() == 0


def test_fallback_de_transporte_nao_inicia_outro_ciclo_de_correcao(app_build, mocker):
    from requests.exceptions import Timeout
    with app_build.app_context():
        cadastrar_pecas(["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd"])
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", side_effect=["JSON inválido", Timeout(), "JSON inválido"])
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json=PEDIDO)
    assert resposta.status_code == 502 and resposta.json["codigo"] == "geracao-invalida"
    assert llm.call_count == 3
    with app_build.app_context():
        assert BuildSalva.query.count() == Build.query.count() == 0


@pytest.mark.parametrize("falha,status,codigo", [("timeout",504,"ia-timeout"),("conexao",503,"ia-indisponivel"),("limite",503,"ia-limite"),("http",502,"ia-provedor")])
def test_falha_do_provedor_nao_e_tratada_como_erro_do_usuario(app_build, mocker, falha, status, codigo):
    from requests import Response
    from requests.exceptions import Timeout, ConnectionError, HTTPError
    with app_build.app_context():
        cadastrar_pecas(["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd"])
    resposta_provedor = Response()
    resposta_provedor.status_code = 429 if falha == "limite" else 503
    resposta_provedor.headers["Retry-After"] = "45"
    erro = Timeout() if falha == "timeout" else ConnectionError() if falha == "conexao" else HTTPError(response=resposta_provedor)
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar", side_effect=erro)
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json=PEDIDO)
    assert resposta.status_code == status and resposta.json["codigo"] == codigo
    assert llm.call_count == 2
    if falha == "limite":
        assert resposta.headers["Retry-After"] == "45"
    with app_build.app_context():
        assert BuildSalva.query.count() == Build.query.count() == 0


@pytest.mark.parametrize("valor", [{"valor": 5000}, [], "sem valor", 10**400])
def test_orcamento_malformado_nao_gasta_consulta(app_build, mocker, valor):
    llm = mocker.patch("services.build_service.criar_build_service.LLMService.executar")
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json={**PEDIDO,"orcamento":valor})
    assert resposta.status_code == 400
    llm.assert_not_called()


def test_menu_tranca_visibilidade_edicao_copia_e_exclusao_na_conta(app_build):
    cliente = app_build.test_client()
    autenticar(cliente)
    criada = cliente.post("/build/manual",json=ESTADO).json["build"]
    rota = "/build/" + criada["id"]
    assert cliente.get(rota + "/publica").status_code == 404
    estado = {**criada["estado"],"titulo":"PC editado","visibilidade":"publico"}
    assert cliente.put(rota,json=estado).status_code == 200
    assert cliente.get(rota + "/publica").json["build"]["nome"] == "PC editado"
    estado["travada"] = True
    assert cliente.put(rota,json=estado).status_code == 200
    for alteracao in [{**estado,"titulo":"Não salvar"},{**estado,"visibilidade":"privado"}]:
        assert cliente.put(rota,json=alteracao).status_code == 400
    assert cliente.delete(rota).status_code == 400
    assert cliente.get(rota).json["build"]["nome"] == "PC editado"
    copia = cliente.post(rota + "/duplicar").json["build"]
    assert copia["id"] != criada["id"]
    assert copia["estado"]["visibilidade"] == "privado" and not copia["estado"]["travada"]
    assert cliente.put(rota,json={"travada":False}).status_code == 200
    assert cliente.delete(rota).status_code == 204
    assert cliente.get(rota).status_code == 404
    assert cliente.get("/build/" + copia["id"]).status_code == 200


def test_menu_setup_atual_alterna_e_operacoes_respeitam_proprietario(app_build):
    cliente = app_build.test_client()
    autenticar(cliente)
    primeira = cliente.post("/build/manual",json=ESTADO).json["build"]
    segunda = cliente.post("/build/manual",json={**ESTADO,"titulo":"Segunda"}).json["build"]
    assert cliente.post("/build/" + primeira["id"] + "/setup-atual").status_code == 200
    assert cliente.post("/build/" + segunda["id"] + "/setup-atual").status_code == 200
    salvas = cliente.get("/build/").json["builds"]
    assert [b["id"] for b in salvas if b["estado"].get("setupAtual")] == [segunda["id"]]
    cliente.post("/build/" + segunda["id"] + "/setup-atual")
    assert not any(b["estado"].get("setupAtual") for b in cliente.get("/build/").json["builds"])
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = "2"
    rota = "/build/" + primeira["id"]
    assert cliente.get(rota).status_code == 404
    assert cliente.put(rota,json=ESTADO).status_code == 400
    assert cliente.delete(rota).status_code == 400
    assert cliente.post(rota + "/setup-atual").status_code == 404
    assert cliente.post(rota + "/duplicar").status_code == 400
    with app_build.app_context():
        assert BuildSalva.query.count() == 2
