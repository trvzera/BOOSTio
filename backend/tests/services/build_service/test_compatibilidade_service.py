from copy import deepcopy

import pytest

from services.build_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService, numero


def avaliar(pecas, componentes=None):
    if componentes is None:
        componentes = {p["categoria"]: {"id": p["id"], "quantidade": 1} for p in pecas}
    return AvaliarCompatibilidadeService().executar({"componentes": componentes}, catalogo=pecas)


def regra(resultado, codigo):
    return next(r for r in resultado["verificacoes"] if r["codigo"] == codigo)


@pytest.mark.parametrize("valor", [None, "", True, False, float("nan"), float("inf"), -1, "desconhecido"])
def test_ausencia_nao_vira_zero(valor):
    assert numero(valor) is None


def test_socket_confirma_somente_dados_conhecidos_sem_aprovar_bios():
    pecas = [{"id": 1, "categoria": "processador", "soquete": "AM4"},
             {"id": 2, "categoria": "placa_mae", "socket": " am4 "}]
    resultado = avaliar(pecas)
    assert regra(resultado, "socket")["status"] == "sem_conflitos"
    assert regra(resultado, "suporte-cpu-bios")["status"] == "nao_verificado"
    assert resultado["status"] == "nao_verificado" and resultado["pecasPendentes"]
    pecas[1]["socket"] = "AM5"
    assert avaliar(pecas)["status"] == "incompativel"
    pecas[1]["socket"] = None
    assert regra(avaliar(pecas), "socket")["status"] == "nao_verificado"


def test_peca_propria_e_build_vazia_nao_sao_aprovadas():
    for componentes in ({}, {"processador": {"proprio": "Meu Ryzen", "quantidade": 1}}):
        resultado = avaliar([], componentes)
        assert resultado["status"] == "nao_verificado"
        assert not resultado["erros"]
    assert avaliar([], {"processador": {"proprio": "Meu Ryzen"}})["naoVerificado"]


def test_ram_conta_kits_e_nao_presume_slots_ou_capacidade():
    pecas = [{"id": 1, "categoria": "placa_mae", "tipo_memoria": "DDR4", "quantidade_slots_ram": 4, "memoria_maxima_gb": 64},
             {"id": 2, "categoria": "memoria_ram", "ddr": "DDR4", "quantidade_pentes": 2, "capacidade_gb": 32}]
    componentes = {"placa_mae": {"id": 1}, "memoria_ram": [{"id": 2, "quantidade": 2}]}
    resultado = avaliar(pecas, componentes)
    assert regra(resultado, "ram-slots")["status"] == "sem_conflitos"
    assert regra(resultado, "ram-capacidade")["status"] == "sem_conflitos"
    componentes["memoria_ram"][0]["quantidade"] = 3
    assert regra(avaliar(pecas, componentes), "ram-slots")["status"] == "incompativel"
    pecas[0]["quantidade_slots_ram"] = None
    assert regra(avaliar(pecas, componentes), "ram-slots")["status"] == "nao_verificado"
    pecas[1]["ddr"] = "DDR5"
    assert regra(avaliar(pecas, componentes), "ram-ddr")["status"] == "incompativel"


def test_medida_ausente_ou_ambigua_nao_confirma_encaixe():
    pecas = [{"id": 1, "categoria": "gabinete", "tamanho_max_gpu_mm": 300, "tamanho_max_cooler_mm": 160},
             {"id": 2, "categoria": "placa_video", "modelo": "GPU 280 mm"},
             {"id": 3, "categoria": "air_cooler", "dimensoes": 150}]
    resultado = avaliar(pecas)
    assert regra(resultado, "placa_video-medida")["status"] == "nao_verificado"
    assert regra(resultado, "air_cooler-medida")["status"] == "nao_verificado"
    pecas[1]["comprimento_mm"] = 300
    assert regra(avaliar(pecas), "placa_video-medida")["status"] == "sem_conflitos"
    pecas[1]["comprimento_mm"] = 301
    assert regra(avaliar(pecas), "placa_video-medida")["status"] == "incompativel"
    pecas[1]["comprimento_mm"] = 0
    assert regra(avaliar(pecas), "placa_video-medida")["status"] == "nao_verificado"


def test_radiador_precisa_de_tamanhos_e_posicao_nao_e_aprovada_por_tamanho():
    pecas = [{"id": 1, "categoria": "gabinete", "suporte_water_cooler": True},
             {"id": 2, "categoria": "water_cooler", "tamanho_radiador_mm": 360}]
    assert regra(avaliar(pecas), "radiador")["status"] == "nao_verificado"
    pecas[0]["radiadores_suportados_mm"] = [120, 240]
    assert regra(avaliar(pecas), "radiador")["status"] == "incompativel"
    pecas[0]["radiadores_suportados_mm"].append(360)
    resultado = avaliar(pecas)
    assert regra(resultado, "radiador")["status"] == "sem_conflitos"
    assert regra(resultado, "radiador-posicao")["status"] == "nao_verificado"


def test_sata_desconhecido_nao_equivale_a_portas_ilimitadas():
    pecas = [{"id": 1, "categoria": "placa_mae", "quantidade_slots_m2": 1},
             {"id": 2, "categoria": "ssd", "interface": "NVMe", "formato": "M.2"},
             {"id": 3, "categoria": "hd", "interface": "SATA"}]
    componentes = {"placa_mae": {"id": 1}, "ssd": [{"id": 2, "quantidade": 2}], "hd": [{"id": 3}]}
    resultado = avaliar(pecas, componentes)
    assert regra(resultado, "discos-m2")["status"] == "incompativel"
    assert regra(resultado, "discos-sata")["status"] == "nao_verificado"
    pecas[0]["quantidade_portas_sata"] = 0
    assert regra(avaliar(pecas, componentes), "discos-sata")["status"] == "incompativel"


def test_fonte_usa_quantidades_e_falta_de_consumo_permanece_desconhecida():
    pecas = [{"id": 1, "categoria": "fonte", "potencia_w": 500},
             {"id": 2, "categoria": "processador", "consumo_energia": 100},
             {"id": 3, "categoria": "memoria_ram", "consumo_energia": 100}]
    componentes = {"fonte": {"id": 1}, "processador": {"id": 2}, "memoria_ram": [{"id": 3, "quantidade": 5}]}
    assert regra(avaliar(pecas, componentes), "fonte-potencia")["status"] == "incompativel"
    componentes["memoria_ram"][0]["quantidade"] = 4
    assert regra(avaliar(pecas, componentes), "fonte-potencia")["status"] == "nao_verificado"
    pecas[2]["consumo_energia"] = None
    assert regra(avaliar(pecas, componentes), "fonte-potencia")["status"] == "nao_verificado"


def test_avaliacao_nao_muda_o_estado_recebido():
    estado = {"componentes": {"ssd": [{"proprio": "Meu SSD", "quantidade": 2}]}}
    original = deepcopy(estado)
    AvaliarCompatibilidadeService().executar(estado, catalogo=[])
    assert estado == original


def test_consumo_desconhecido_nao_esconde_fonte_ja_insuficiente():
    pecas = [{"id": 1, "categoria": "fonte", "potencia_w": 500},
             {"id": 2, "categoria": "processador", "consumo_energia": 600}]
    componentes = {"fonte": {"id": 1}, "processador": {"id": 2},
                   "memoria_ram": [{"proprio": "Minha RAM", "quantidade": 1}]}
    assert regra(avaliar(pecas, componentes), "fonte-potencia")["status"] == "incompativel"
    pecas[1]["consumo_energia"] = 100
    assert regra(avaliar(pecas, componentes), "fonte-potencia")["status"] == "nao_verificado"
