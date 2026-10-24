from decimal import Decimal

import pytest

from services.build_service.planejar_perifericos_service import PlanejarPerifericosService


def catalogo():
    return {tipo: [{"id": i + 1, "preco": preco, "esgotado": False} for i, preco in enumerate(precos)]
            for tipo, precos in {"monitor": [323.99, 499.99, 599.99], "teclado": [20.03, 100, 200],
                                 "mouse": [19.12, 100, 200], "fone": [36.71, 100, 200]}.items()}


def test_todos_os_conjuntos_respeitam_os_600_reais_reservados():
    dados = catalogo()
    plano = PlanejarPerifericosService().executar(dados, Decimal("600"))
    assert plano["viavel"]
    assert plano["minimo_catalogado"] == 399.85
    assert 1 <= len(plano["combinacoes"]) <= 12
    for conjunto in plano["combinacoes"]:
        assert {item["tipo"] for item in conjunto["componentes"]} == set(dados)
        real = sum(Decimal(str(next(p for p in dados[item["tipo"]] if p["id"] == item["id"])["preco"])) for item in conjunto["componentes"])
        assert real <= 600 and real == Decimal(str(conjunto["total"]))


def test_reserva_insuficiente_e_detectada_antes_de_pedir_uma_solucao_inexistente():
    plano = PlanejarPerifericosService().executar(catalogo(), Decimal("399.84"))
    assert not plano["viavel"] and plano["combinacoes"] == []
    assert plano["minimo_catalogado"] == 399.85


def test_proprios_nao_sao_comprados_e_sobra_nao_precisa_ser_gasta():
    plano = PlanejarPerifericosService().executar(catalogo(), 100, {"monitor": "Meu monitor"})
    assert plano["viavel"] and plano["minimo_catalogado"] == 75.86
    assert all({i["tipo"] for i in c["componentes"]} == {"teclado", "mouse", "fone"} for c in plano["combinacoes"])
    todos = PlanejarPerifericosService().executar({}, 600, dict.fromkeys(PlanejarPerifericosService.TIPOS, "Próprio"))
    assert todos["combinacoes"] == [{"total": 0.0, "componentes": []}]


@pytest.mark.parametrize("preco", [None, True, False, 0, -1, float("nan"), float("inf"), "100"])
def test_preco_invalido_nao_cria_conjunto_ficticio(preco):
    dados = catalogo()
    dados["monitor"] = [{"id": 1, "preco": preco}]
    assert not PlanejarPerifericosService().executar(dados, 600)["viavel"]


def test_estoque_e_categorias_ausentes_nao_sao_ignorados():
    dados = catalogo()
    dados["monitor"] = [{"id": 1, "preco": 10, "esgotado": True}]
    plano = PlanejarPerifericosService().executar(dados, 600)
    assert not plano["viavel"] and plano["categoria_ausente"] == "monitor"


def test_centavos_e_amostragem_limitada_nao_mudam_o_catalogo():
    dados = catalogo()
    dados["mouse"] = [{"id": i, "preco": i + 1} for i in range(100)]
    plano = PlanejarPerifericosService().executar(dados, Decimal("399.85"))
    assert plano["viavel"]
    assert len(dados["mouse"]) == 100
    assert len(plano["combinacoes"]) <= 12
