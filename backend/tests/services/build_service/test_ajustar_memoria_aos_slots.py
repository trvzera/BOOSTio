from services.build_service.ajustar_memoria_aos_slots_service import AjustarMemoriaAosSlotsService

CATALOGO = {
    "placa_mae": [{"id": 1, "quantidade_slots_ram": 2}, {"id": 2, "quantidade_slots_ram": 4}],
    "memoria_ram": [{"id": 10, "quantidade_pentes": 1}, {"id": 11, "quantidade_pentes": 2}],
}


def build(placa, ram, quantidade):
    return {"componentes": [{"tipo": "placa_mae", "id": placa, "quantidade": 1},
                            {"tipo": "memoria_ram", "id": ram, "quantidade": quantidade}]}


def quantidade_ram(resultado):
    return next(i["quantidade"] for i in resultado["componentes"] if i["tipo"] == "memoria_ram")


def test_reduz_quatro_pentes_para_os_dois_slots_da_placa():
    assert quantidade_ram(AjustarMemoriaAosSlotsService().executar(build(1, 10, 4), CATALOGO)) == 2


def test_conta_pentes_por_kit():
    assert quantidade_ram(AjustarMemoriaAosSlotsService().executar(build(1, 11, 2), CATALOGO)) == 1
    assert quantidade_ram(AjustarMemoriaAosSlotsService().executar(build(2, 11, 3), CATALOGO)) == 2


def test_nao_mexe_quando_cabe():
    original = build(2, 10, 4)
    assert AjustarMemoriaAosSlotsService().executar(original, CATALOGO) is original


def test_nao_mexe_sem_dados_de_slots():
    original = build(3, 10, 4)
    assert AjustarMemoriaAosSlotsService().executar(original, CATALOGO) is original


def test_nao_mexe_em_ram_propria():
    original = build(1, 10, 4)
    assert AjustarMemoriaAosSlotsService().executar(original, CATALOGO, {"memoria_ram": "X"}) is original


def test_usa_slots_da_placa_propria():
    detalhes = {"placa_mae": {"especificacoes_confirmadas": {"quantidade_slots_ram": 2}}}
    original = {"componentes": [{"tipo": "memoria_ram", "id": 10, "quantidade": 4}]}
    resultado = AjustarMemoriaAosSlotsService().executar(original, CATALOGO, {"placa_mae": "X"}, detalhes)
    assert quantidade_ram(resultado) == 2
    assert original["componentes"][0]["quantidade"] == 4
