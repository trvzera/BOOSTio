from services.build_service.prompt_build_service import criar_prompt
import json
from copy import deepcopy

import pytest

from services.build_service.amostrar_catalogo_service import AmostrarCatalogoService
from services.build_service.preferencias_processador_service import PreferenciasProcessadorService as CPUs
from services.build_service.criar_build_service import CriarBuildService
from services.validacoes_service.validar_pedido_build_service import validar_preferencia_processador
from models import Usuario


CATALOGO = {
    "processador": [
        {"id": 1, "fabricante": "Intel", "modelo": "Core i5", "soquete": "LGA1700", "preco": 600},
        {"id": 2, "fabricante": "AMD", "modelo": "Ryzen 5 5600", "soquete": "AM4", "preco": 700},
        {"id": 3, "fabricante": "AMD", "modelo": "Ryzen 5 7600", "soquete": "AM5", "preco": 1200},
    ],
    "placa_mae": [{"id": 10, "socket": "AM4"}, {"id": 11, "socket": "LGA1700"}],
}


def test_jogos_priorizam_ryzen_apenas_com_socket_disponivel():
    assert CPUs.ids_prioritarios(CATALOGO, "Jogos") == [2]
    assert CPUs.ids_prioritarios(CATALOGO, "Estudos") == []
    assert CPUs.ids_prioritarios(CATALOGO, "Trabalho pesado") == []
    assert CPUs.ids_prioritarios({**CATALOGO, "placa_mae": []}, "Jogos") == []


@pytest.mark.parametrize("proprias,esperadas", [
    ({"processador": {"modelo_informado": "Meu Intel"}}, []),
    ({"placa_mae": {"especificacoes_confirmadas": {"socket": "LGA 1700"}}}, []),
    ({"placa_mae": {"especificacoes_confirmadas": {"socket": "AM5"}}}, [3]),
    ({"placa_mae": {"especificacoes_confirmadas": {}}}, []),
])
def test_pecas_proprias_vem_antes_da_preferencia_de_marca(proprias, esperadas):
    assert CPUs.ids_prioritarios(CATALOGO, "Jogos", proprias) == esperadas


def test_amd_sem_ser_ryzen_ou_ryzen_cadastrado_em_outra_marca_nao_e_priorizado():
    for peca in [{"fabricante": "AMD", "modelo": "Athlon"},
                 {"fabricante": "Intel", "modelo": "Ryzen"}, {"modelo": "Ryzen"}, {}]:
        assert not CPUs.ryzen(peca)


def test_amostra_mantem_ryzen_em_faixas_distintas_sem_excluir_intel():
    intel = [{"id": i, "fabricante": "Intel", "modelo": "Core " + str(i),
              "soquete": "LGA1700", "preco": 100+i*50} for i in range(1, 40)]
    ryzen = [{"id": 40, "fabricante": "AMD", "modelo": "Ryzen 5 5600", "soquete": "AM4", "preco": 700},
             {"id": 41, "fabricante": "AMD", "modelo": "Ryzen 5 7600", "soquete": "AM5", "preco": 1200},
             {"id": 42, "fabricante": "AMD", "modelo": "Ryzen 7 9700", "soquete": "AM5", "preco": 1800}]
    pecas = intel + ryzen
    antes = deepcopy(pecas)
    amostra = AmostrarCatalogoService().executar("processador", pecas, utilidade="Jogos")
    assert {1, 39, 40, 41, 42} <= {p["id"] for p in amostra}
    assert len(amostra) == len({p["id"] for p in amostra}) == 12
    assert pecas == antes


def test_prompt_informa_prioridade_e_excecoes_sem_afirmar_superioridade_universal():
    dados = {"nome": "PC", "descricao": "Teste", "utilidade": "Jogos"}
    prompt = criar_prompt(dados, 8000, 2000, CATALOGO)
    restricoes = json.loads(prompt.split("# RESTRIÇÕES CALCULADAS PELO SERVIDOR\n")[1].split("\n")[0])
    assert restricoes["processadores_ryzen_prioritarios"] == [2]
    regra = prompt.split("# PREFERÊNCIA DE PROCESSADOR\n")[1].split("\n\n")[0]
    assert "dê preferência a AMD Ryzen" in regra
    assert "não reduza a capacidade gráfica" in regra
    assert "não recompre cpu própria" in regra.casefold()
    assert "nem prova de que todo Ryzen supera todo Intel" in regra
    dados["utilidade"] = "Estudos"
    prompt = criar_prompt(dados, 8000, 2000, CATALOGO)
    assert '"processadores_ryzen_prioritarios": []' in prompt


@pytest.mark.parametrize("marca,ids", [("intel", [1]), ("amd", [2]), ("sem-preferencia", [])])
def test_preferencia_explicita_substitui_regra_de_jogos_e_chega_ao_prompt(marca, ids):
    dados = dict(nome="PC", descricao="Teste", utilidade="Jogos", preferencia_processador=marca)
    prompt = criar_prompt(dados, 8000, 2000, CATALOGO, preferencia_neutra=True)
    pedido = json.loads(prompt.split("# PEDIDO\n")[1].split("\n")[0])
    restricoes = json.loads(prompt.split("# RESTRIÇÕES CALCULADAS PELO SERVIDOR\n")[1].split("\n")[0])
    assert pedido["preferencia_processador"] == marca
    assert restricoes["processadores_marca_preferida"] == ids
    assert restricoes["processadores_ryzen_prioritarios"] == []
    if marca != "sem-preferencia":
        assert "não se aplica à placa de vídeo" in prompt
        assert "A marca escolhida é obrigatória" in prompt


@pytest.mark.parametrize("marca", [None, "", "Intel", "nvidia", [], {}, True, 1])
def test_marca_invalida_rejeitada_antes_de_acessar_usuario(marca, mocker):
    buscar = mocker.patch.object(Usuario, "buscar_por_id")
    with pytest.raises(ValueError, match="preferência de processador"):
        CriarBuildService().executar(1, dict(nome="PC", descricao="Teste", utilidade="Jogos",
                                           orcamento=8000, preferencia_processador=marca))
    buscar.assert_not_called()


def test_preferencia_nao_recompra_cpu_nem_forca_socket_em_placa_propria():
    assert validar_preferencia_processador({}) == "sem-preferencia"
    propria = {"placa_mae": {"especificacoes_confirmadas": {"socket": "AM4"}}}
    assert CPUs.ids_prioritarios(CATALOGO, "Jogos", propria, preferencia="intel") == []
    assert CPUs.ids_prioritarios(CATALOGO, "Estudos", propria, preferencia="amd") == [2]
    assert CPUs.ids_prioritarios(CATALOGO, "Estudos", {"processador": {}}, preferencia="intel") == []


@pytest.mark.parametrize("marca", ["intel", "amd"])
def test_amostra_preserva_opcoes_da_marca_em_faixas_de_preco_sem_excluir_fallback(marca):
    outras = [{"id": i, "fabricante": "Outra", "modelo": str(i), "soquete": "AM4", "preco": 100+i*50} for i in range(1, 40)]
    preferidas = [{"id": 40+i, "fabricante": marca.upper(), "modelo": str(i), "soquete": "LGA1700" if marca == "intel" else "AM4", "preco": preco} for i, preco in enumerate([700, 1200, 1800])]
    amostra = AmostrarCatalogoService().executar("processador", outras + preferidas, utilidade="Estudos", preferencia_processador=marca)
    assert {40, 41, 42} <= {p["id"] for p in amostra}
    assert any(p["fabricante"] == "Outra" for p in amostra)
    assert len(amostra) == 12
