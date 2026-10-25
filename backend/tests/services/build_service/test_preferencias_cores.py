from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

import pytest

from services.build_service.preferencias_cores_service import PreferenciasCoresService as Cores
from services.build_service.amostrar_catalogo_service import AmostrarCatalogoService
from services.build_service.planejar_perifericos_service import PlanejarPerifericosService
from services.build_service.criar_build_service import CriarBuildService


@pytest.mark.parametrize("cor,esperadas", [("Preto", {"preto"}), ("BRANCA", {"branco"}),
    ("black & white", {"preto", "branco"}), ("Preto e branco", {"preto", "branco"}), ("Azul", {"outra"})])
def test_cor_cadastrada_tem_prioridade_sobre_nome(cor, esperadas):
    cores, origem = Cores.identificar({"cor": cor, "modelo": "Modelo Branco Preto"})
    assert cores == esperadas and origem == "cor_cadastrada"


@pytest.mark.parametrize("peca", [
    {"modelo": "RGB"}, {"modelo": "Teclado Switch White"}, {"modelo": "Teclado Switch Gateron Black"},
    {"modelo": "Iluminação Branca"}, {"modelo": "LED branco"}, {"modelo": "RGB Branco"},
    {"modelo": "WD_BLACK SN850X"}, {"modelo": "Fonte 80 Plus White"},
    {"modelo": "Black Edition", "categoria": "processador"},
    {"modelo": "Ryzen Black", "categoria": "processador"},
    {"modelo": "Modelo", "link": "https://loja.invalid/produto-branco", "part_number": "WHITE"},
    {"modelo": "WhiteboardPro"}, {"cor": [], "modelo": "Branco"}, {"cor": True}, {},
])
def test_nao_inventa_cor_por_rgb_switch_certificacao_url_codigo_ou_texto_ambiguo(peca):
    assert Cores.identificar(peca) == (frozenset(), None)
    assert Cores.metadados(peca) == {}
    assert Cores.prioridade(peca, "branco") == 3


def test_nome_e_apenas_indicacao_e_nao_sobrescreve_cor_ou_ficha():
    peca = {"modelo": "Teclado Switch Red, Branco", "preco": 100, "id": 1}
    antes = deepcopy(peca)
    assert Cores.metadados(peca) == {"cor_referencia": ["branco"], "fonte_cor_referencia": "nome_cadastrado"}
    assert Cores.prioridade(peca, "branco") > Cores.prioridade({"cor": "branco"}, "branco")
    assert peca == antes and "cor" not in peca
    assert Cores.metadados({"cor": "  ", "modelo": "Gabinete Branco"}) == {"cor_referencia": ["branco"], "fonte_cor_referencia": "nome_cadastrado"}
    assert Cores.metadados({"modelo": "Fonte 80+ White"}) == {}
    for cor in ("preto", "branco", "Preto e branco"):
        assert Cores.prioridade({"cor": cor}, "misto") == 0
    assert Cores.prioridade({"cor": "preto"}, "sem-preferencia") == 0
    assert Cores.prioridade({"cor": "preto"}, "branco") > Cores.prioridade({}, "branco")


@pytest.mark.parametrize("categoria", ["placa_mae", "placa_video", "memoria_ram", "ssd", "hd", "fonte", "gabinete",
    "fan", "air_cooler", "water_cooler", "monitor", "teclado", "mouse", "fone", "cabo_rede", "adaptador_wifi"])
def test_amostra_preserva_cor_em_todas_as_categorias_sem_remover_alternativa_economica(categoria):
    dados = [{"id": i, "preco": 100+i, "cor": "preto"} for i in range(1, 45)]
    dados[23] = {**dados[23], "cor": "branco"}
    antes = deepcopy(dados)
    amostra = AmostrarCatalogoService().executar(categoria, dados, cor="branco")
    assert {1, 24, 44} <= {p["id"] for p in amostra}
    assert len(amostra) == len({p["id"] for p in amostra}) == 12
    assert dados == antes


def test_prefere_cores_sem_perder_soquetes_e_padroes_de_memoria():
    dados = [{"id": i, "preco": 100+i, "ddr": "DDR4", "cor": "preto"} for i in range(1, 50)]
    dados += [{"id": 50, "preco": 300, "ddr": "DDR5", "cor": "branco"},
              {"id": 51, "preco": 200, "ddr": "DDR4", "cor": "branco"}]
    amostra = AmostrarCatalogoService().executar("memoria_ram", dados, cor="branco")
    assert {1, 50, 51} <= {p["id"] for p in amostra}
    assert {p["ddr"] for p in amostra} == {"DDR4", "DDR5"}
    sem_cor = [{"id": i, "preco": i+1} for i in range(30)]
    servico = AmostrarCatalogoService()
    assert servico.executar("fan", sem_cor, cor="branco") == servico.executar("fan", sem_cor)


def test_planejamento_mantem_cor_e_mistura_viaveis_sem_aumentar_reserva():
    catalogo = {tipo: [{"id": i, "preco": i+40, "cor": "branco" if i == 6 else "preto"} for i in range(1, 11)]
                for tipo in PlanejarPerifericosService.TIPOS}
    antes = deepcopy(catalogo)
    plano = PlanejarPerifericosService().executar(catalogo, 200, cor="branco")
    assert plano["viavel"] and len(plano["combinacoes"]) <= 12
    assert any(all(p["id"] == 6 for p in c["componentes"]) for c in plano["combinacoes"])
    for c in plano["combinacoes"]:
        soma = sum(Decimal(str(next(p["preco"] for p in catalogo[i["tipo"]] if p["id"] == i["id"]))) for i in c["componentes"])
        assert soma == Decimal(str(c["total"])) and soma <= 200
    economico = PlanejarPerifericosService().executar(catalogo, 164, cor="branco")
    assert economico["viavel"] and all(all(p["id"] == 1 for p in c["componentes"]) for c in economico["combinacoes"])
    assert catalogo == antes
    mistos = {tipo: [{"id": 1, "preco": 50, "cor": "preto"}, {"id": 2, "preco": 50, "cor": "branco"},
                    {"id": 3, "preco": 50, "cor": "azul"}] for tipo in PlanejarPerifericosService.TIPOS}
    combinacoes = PlanejarPerifericosService().executar(mistos, 200, cor="misto")["combinacoes"]
    assert all({i["id"] for i in c["componentes"]} == {1, 2} for c in combinacoes[:3])


def test_cor_nao_recompra_periferico_proprio_nem_torna_catalogo_sem_cor_inviavel():
    dados = {tipo: [{"id": 1, "preco": 50}] for tipo in PlanejarPerifericosService.TIPOS}
    plano = PlanejarPerifericosService().executar(dados, 150, {"monitor": "Meu monitor preto"}, cor="branco")
    assert plano["viavel"]
    assert all({i["tipo"] for i in c["componentes"]} == {"teclado", "mouse", "fone"} for c in plano["combinacoes"])


def test_cor_e_origem_da_referencia_chegam_ao_prompt_sem_mudar_cor_cadastrada():
    peca = SimpleNamespace(id=4, to_catalogo=lambda: {"id": "teclado:4", "categoria": "teclado", "modelo": "Teclado Branco", "preco": 100})
    campos = CriarBuildService._campos_pecas(peca)
    assert campos["cor_referencia"] == ["branco"] and campos["fonte_cor_referencia"] == "nome_cadastrado"
    assert "cor" not in campos
    prompt = CriarBuildService._criar_prompt({"nome": "PC", "descricao": "Teste", "utilidade": "Jogos", "aparencia": {"cor": "branco"}}, 5000, 800, {"teclado": [campos]})
    for termo in ("TODOS os itens novos", "ventoinhas", "monitor, teclado, mouse, fone", "não cor confirmada",
                  "Nunca substitua peças próprias", "sacrifique orçamento, segurança", "Copie nome, descricao"):
        assert termo in prompt


def test_cor_propagada_para_complemento_de_fans_sem_chamar_llm_real(mocker):
    mocker.patch("services.build_service.criar_build_service.LLMService.executar", return_value={"componentes": []})
    completar = mocker.patch("services.build_service.criar_build_service.CompletarVentilacaoService.executar", return_value={"componentes": []})
    mocker.patch.object(CriarBuildService, "_validar_build", return_value={"componentes": []})
    CriarBuildService()._gerar_validada(1, "Prompt", "teste", {}, 1000, 0, {}, {}, {}, tentativas_correcao=0, cor="branco")
    assert completar.call_args.kwargs == {"cor": "branco"}
