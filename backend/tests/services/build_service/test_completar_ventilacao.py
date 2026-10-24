from copy import deepcopy

import pytest

from services.build_service.completar_ventilacao_service import CompletarVentilacaoService


def cenario():
    catalogo = {
        "gabinete": [{"id": 1, "preco": 100, "fans_inclusos": 1, "quantidade_max_fans": 5,
                      "tamanhos_fan_suportados_mm": [120]}],
        "fan": [{"id": 1, "preco": 10, "quantidade": 1, "tamanho_mm": 120},
                {"id": 2, "preco": 15, "quantidade": 2, "tamanho_mm": 120}],
        "water_cooler": [{"id": 1, "preco": 100, "quantidade_fans": 2, "tamanho_fan_mm": 120, "tamanho_radiador_mm": 240}],
        "monitor": [{"id": 1, "preco": 500}],
    }
    build = {"nome": "PC", "componentes": [{"tipo": "gabinete", "id": 1, "quantidade": 1}]}
    return build, catalogo


def test_completa_quatro_fans_sem_comprar_a_que_veio_no_gabinete():
    build, catalogo = cenario()
    antes = deepcopy(build)
    resultado = CompletarVentilacaoService().executar(build, catalogo, 130)
    assert resultado["componentes"][-1] == {"tipo": "fan", "id": 2, "quantidade": 2}
    assert build == antes


def test_desconta_duas_fans_do_aio_e_nao_transfere_verba_dos_perifericos():
    build, catalogo = cenario()
    build["componentes"].extend([{"tipo": "water_cooler", "id": 1}, {"tipo": "monitor", "id": 1}])
    resultado = CompletarVentilacaoService().executar(build, catalogo, 215)
    assert resultado["componentes"][-1] == {"tipo": "fan", "id": 2, "quantidade": 1}
    assert CompletarVentilacaoService().executar(build, catalogo, 214.99) is build


def test_completa_quantidade_do_modelo_ja_escolhido_sem_trocar():
    build, catalogo = cenario()
    build["componentes"].append({"tipo": "fan", "id": 1, "quantidade": 1})
    resultado = CompletarVentilacaoService().executar(build, catalogo, 150)
    assert resultado["componentes"][-1] == {"tipo": "fan", "id": 1, "quantidade": 4}


@pytest.mark.parametrize("alteracao", [{"quantidade_max_fans": None}, {"fans_inclusos": None},
    {"tamanhos_fan_suportados_mm": None}, {"tamanhos_fan_suportados_mm": [140]}, {"fans_inclusos": 5}])
def test_nao_inventa_limites_tamanhos_ou_compras_desnecessarias(alteracao):
    build, catalogo = cenario()
    catalogo["gabinete"][0].update(alteracao)
    assert CompletarVentilacaoService().executar(build, catalogo, 500) is build


def test_fans_proprias_e_aio_proprio_desconhecido_sao_preservados():
    build, catalogo = cenario()
    assert CompletarVentilacaoService().executar(build, catalogo, 500, {"fan": "Minhas fans"}) is build
    assert CompletarVentilacaoService().executar(build, catalogo, 500, {"water_cooler": "Meu AIO"}) is build


def test_nao_divide_kit_nem_usa_estoque_indisponivel():
    build, catalogo = cenario()
    catalogo["fan"] = [{"id": 1, "preco": 10, "quantidade": 3, "tamanho_mm": 120},
                       {"id": 2, "preco": 10, "quantidade": 1, "tamanho_mm": 120, "esgotado": True}]
    assert CompletarVentilacaoService().executar(build, catalogo, 500) is build


def test_arranjo_fisico_conflitante_nao_e_aprovado_pela_soma_total():
    build, catalogo = cenario()
    catalogo["gabinete"][0]["posicoes_fans"] = [{"nome": "Frente", "opcoes": [{"quantidade": 5, "tamanho_mm": 140}],
                                             "fans_inclusas": [{"quantidade": 1, "tamanho_mm": 140}], "radiadores_mm": []}]
    assert CompletarVentilacaoService().executar(build, catalogo, 500) is build


@pytest.mark.parametrize("invalida", [None, {"erro": "impossível", "componentes": []}, {"componentes": [None]},
    {"componentes": [{"tipo": "gabinete", "id": True}]}, {"componentes": [{"tipo": "gabinete", "id": 1, "quantidade": False}]}])
def test_saida_invalida_continua_para_validacao_sem_ser_disfarcada(invalida):
    assert CompletarVentilacaoService().executar(invalida, cenario()[1], 500) is invalida
