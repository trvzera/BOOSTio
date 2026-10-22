import pytest
from flask import Flask
from sqlalchemy.orm.attributes import flag_modified

from models import db, lm, Usuario, BuildSalva, MemoriaRAM
from controllers.benchmark_controller import benchmark_bp


@pytest.fixture
def app_requisitos(tmp_path):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="somente-testes", SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'requisitos.db'}")
    db.init_app(app)
    lm.init_app(app)
    app.register_blueprint(benchmark_bp)
    with app.app_context():
        db.create_all()
        db.session.add_all([Usuario(nome="A", email="a@example.test"), Usuario(nome="B", email="b@example.test")])
        db.session.add_all([
            MemoriaRAM(fabricante="Teste", modelo="8 GB", preco=100, consumo_energia=3, capacidade_gb=8, ddr="DDR4", frequencia_mhz=3200, quantidade_pentes=1),
            MemoriaRAM(fabricante="Teste", modelo="Kit 16 GB", preco=200, consumo_energia=6, capacidade_gb=16, ddr="DDR4", frequencia_mhz=3200, quantidade_pentes=2),
        ])
        db.session.flush()
        db.session.add_all([
            BuildSalva(usuario_id=1, estado={"titulo": "Minha", "componentes": {"memoria_ram": [{"id": 1, "quantidade": 1}]}}),
            BuildSalva(usuario_id=2, estado={"titulo": "Outra conta", "componentes": {"memoria_ram": [{"id": 2, "quantidade": 2}]}}),
        ])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def cliente(app):
    navegador = app.test_client()
    with navegador.session_transaction() as sessao:
        sessao["_user_id"] = "1:1"
        sessao["_fresh"] = True
    return navegador


def selecionar(app, itens):
    with app.app_context():
        salva = db.session.get(BuildSalva, 1)
        salva.estado = {"titulo": "Minha", "componentes": {"memoria_ram": itens} if itens is not None else {}}
        flag_modified(salva, "estado")
        db.session.commit()


@pytest.mark.parametrize("itens,gb,pentes", [
    ([{"id": 1, "quantidade": 2}], 16, 2),
    ([{"id": 2, "quantidade": 1}], 16, 2),
    ([{"id": 2, "quantidade": 2}], 32, 4),
    ([{"id": 1, "quantidade": 1}, {"id": 2, "quantidade": 1}], 24, 3),
])
def test_soma_capacidade_por_item_sem_multiplicar_pelos_pentes(app_requisitos, mocker, itens, gb, pentes):
    fps = mocker.patch("services.benchmark_service.fpshq_service.FpshqService.executar", side_effect=AssertionError("Não deve consultar FPSHQ"))
    selecionar(app_requisitos, itens)
    resposta = cliente(app_requisitos).get("/benchmark/requisitos-build?game=fortnite&build_id=s-1")
    assert resposta.status_code == 200
    dados = resposta.json["resultado"]
    assert dados["ram"]["informadaGb"] == gb
    assert dados["ram"]["pentesIdentificados"] == pentes
    assert dados["ram"]["fonte"] == "build_salva"
    assert dados["ram"]["completa"] is True
    assert dados["ram"]["status"] == "recomendado"
    assert dados["requisitosVerificados"] is False and dados["fpsValidado"] is False
    assert resposta.headers["Cache-Control"] == "no-store"
    fps.assert_not_called()


def test_abaixo_do_minimo_e_alteracao_da_build_sao_reavaliados(app_requisitos):
    navegador = cliente(app_requisitos)
    caminho = "/benchmark/requisitos-build?game=cyberpunk-2077&build_id=s-1"
    assert navegador.get(caminho).json["resultado"]["ram"]["atendeMinimo"] is False
    selecionar(app_requisitos, [{"id": 1, "quantidade": 2}])
    assert navegador.get(caminho).json["resultado"]["ram"]["status"] == "recomendado"


@pytest.mark.parametrize("itens,conhecida", [
    (None, 0), ([], 0), ([{"proprio": "RAM sem identificação", "quantidade": 1}], 0),
    ([{"id": 999, "quantidade": 1}], 0),
    ([{"id": 1, "quantidade": 1}, {"proprio": "Outra RAM", "quantidade": 1}], 8),
    ([{"id": 1, "quantidade": True}], 0), ([{"id": 1, "quantidade": 0}], 0),
])
def test_ram_desconhecida_nao_vira_zero_confirmado_ou_aprovacao(app_requisitos, itens, conhecida):
    selecionar(app_requisitos, itens)
    dados = cliente(app_requisitos).get("/benchmark/requisitos-build?game=fortnite&build_id=s-1").json["resultado"]
    assert dados["ram"]["informadaGb"] is None
    assert dados["ram"]["conhecidaGb"] == conhecida
    assert dados["ram"]["completa"] is False
    assert dados["ram"]["status"] == "nao_informada"
    assert dados["ram"]["atendeMinimo"] is None
    assert dados["ram"]["pendencias"]


def test_sessao_propriedade_e_parametros_nao_podem_ser_contornados(app_requisitos):
    caminho = "/benchmark/requisitos-build?game=fortnite&build_id="
    assert app_requisitos.test_client().get(caminho + "s-1").status_code == 401
    navegador = cliente(app_requisitos)
    outra = navegador.get(caminho + "s-2")
    ausente = navegador.get(caminho + "s-999")
    assert outra.status_code == ausente.status_code == 404
    assert outra.json == ausente.json
    assert outra.json["codigo"] == "build-nao-encontrada"
    for sufixo in ["s-1&ram_gb=128", "s-1&usuario_id=2", "s-1&build_id=s-2", "../build", "s-0"]:
        assert navegador.get(caminho + sufixo).status_code == 400
    assert navegador.get("/benchmark/requisitos-build?game=sem-ficha&build_id=s-1").json["codigo"] == "sem-requisitos"


def test_vram_e_disco_usam_modelos_persistidos_e_nao_somam_capacidade_de_unidades(app_requisitos):
    from models import PlacaVideo, SSD, HD
    with app_requisitos.app_context():
        db.session.add_all([
            PlacaVideo(id=1, fabricante="Teste", modelo="4GB", memoria_gb=4, consumo_energia=50, preco=100),
            SSD(id=1, fabricante="Teste", modelo="40GB", capacidade_gb=40, tipo="SSD", interface="SATA", consumo_energia=3, preco=100),
            HD(id=1, fabricante="Teste", modelo="1TB", capacidade_gb=1000, interface="SATA", consumo_energia=3, preco=100),
        ])
        salva = db.session.get(BuildSalva, 1)
        salva.estado = {"titulo": "QA", "componentes": {"memoria_ram": [{"id": 2}], "placa_video": {"id": "placa_video:1"},
                       "ssd": [{"id": "ssd:1", "quantidade": 2}], "hd": [{"id": "hd:1"}]}}
        db.session.commit()
    resposta = cliente(app_requisitos).get("/benchmark/requisitos-build?game=cyberpunk-2077&build_id=s-1")
    assert resposta.status_code == 200
    dados = resposta.json["resultado"]
    assert dados["ram"]["atendeMinimo"] is True
    assert dados["vram"] == {"dedicadaGb": 4, "minimaGb": 6, "atendeCapacidadeMinima": False}
    assert dados["armazenamento"]["maiorUnidadeElegivelGb"] == 40
    assert dados["armazenamento"]["atendeCapacidadeMinima"] is False  # 2x40 não é um volume de 80
    assert dados["armazenamento"]["espacoLivreVerificado"] is False
    assert len(dados["impedimentosMinimos"]) == 2
    cs2 = cliente(app_requisitos).get("/benchmark/requisitos-build?game=cs2&build_id=s-1").json["resultado"]
    assert cs2["vram"]["atendeCapacidadeMinima"] is True
    assert cs2["armazenamento"]["maiorUnidadeElegivelGb"] == 1000
    assert cs2["armazenamento"]["atendeCapacidadeMinima"] is True
    assert cs2["impedimentosMinimos"] == [] and cs2["requisitosVerificados"] is False


def test_video_integrado_e_armazenamento_proprio_continuam_desconhecidos(app_requisitos):
    with app_requisitos.app_context():
        salva = db.session.get(BuildSalva, 1)
        salva.estado = {"titulo": "QA", "componentes": {"memoria_ram": [{"id": 2}], "ssd": [{"proprio": "Meu SSD"}]}}
        db.session.commit()
    dados = cliente(app_requisitos).get("/benchmark/requisitos-build?game=cyberpunk-2077&build_id=s-1").json["resultado"]
    assert dados["vram"]["dedicadaGb"] is None and dados["vram"]["atendeCapacidadeMinima"] is None
    assert dados["armazenamento"]["completo"] is False and dados["armazenamento"]["atendeCapacidadeMinima"] is None
    assert dados["impedimentosMinimos"] == []
