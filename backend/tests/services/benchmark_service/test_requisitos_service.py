import pytest

from services.benchmark_service.consultar_requisitos_service import ConsultarRequisitosService
from services.benchmark_service.fpshq_service import ErroBenchmark


@pytest.mark.parametrize("jogo,minimo,recomendado", [
    ("valorant", 4, 4), ("cs2", 8, None), ("fortnite", 8, 16),
    ("cyberpunk-2077", 12, 16), ("red-dead-redemption-2", 8, 12),
])
def test_cinco_jogos_com_fontes_e_sem_aprovacao_do_pc(jogo, minimo, recomendado):
    dados = ConsultarRequisitosService().executar({"game": jogo}, 1)
    assert dados["ram"]["minimaGb"] == minimo
    assert dados["ram"]["recomendadaGb"] == recomendado
    assert dados["ram"]["atendeMinimo"] is None
    assert dados["ram"]["status"] == "nao_informada"
    assert dados["escopo"] == "parcial"
    assert dados["requisitosVerificados"] is False and dados["fpsValidado"] is False
    assert dados["fonte"]["url"].startswith("https://")
    assert dados["fonte"]["verificadoEm"] == "2026-10-21"
    assert dados["naoVerificado"]
    if jogo == "cs2":
        assert dados["recomendados"] is None


@pytest.mark.parametrize("ram,status,minimo,recomendado", [
    (7, "abaixo_minimo", False, False), (8, "abaixo_recomendado", True, False),
    (12, "abaixo_recomendado", True, False), (16, "recomendado", True, True),
    (32, "recomendado", True, True),
])
def test_ram_abaixo_no_limite_e_acima_sem_inventar_fps(ram, status, minimo, recomendado):
    dados = ConsultarRequisitosService().executar({"game": "fortnite", "ram_gb": str(ram)}, 1)
    assert dados["ram"]["status"] == status
    assert dados["ram"]["atendeMinimo"] is minimo
    assert dados["ram"]["atendeRecomendado"] is recomendado
    assert dados["fpsValidado"] is False
    assert "fps" not in dados


def test_cs2_nao_inventa_recomendacao_e_nao_modifica_ficha_em_cache():
    service = ConsultarRequisitosService()
    dados = service.executar({"game": "cs2", "ram_gb": "8"}, 1)
    assert dados["ram"]["status"] == "minimo_sem_recomendacao"
    assert dados["ram"]["atendeRecomendado"] is None
    dados["minimos"]["ramGb"] = 0
    assert service.executar({"game": "cs2"}, 1)["minimos"]["ramGb"] == 8


@pytest.mark.parametrize("ram", [True, 0, -1, "NaN", "Infinity", "1e2", "1.5", "", "4097", "9" * 5000])
def test_rejeita_ram_invalida(ram):
    with pytest.raises(ValueError, match="RAM"):
        ConsultarRequisitosService().executar({"game": "valorant", "ram_gb": ram}, 1)


def test_modelo_ou_jogo_sem_dados_nao_e_reprovado_como_incompativel():
    with pytest.raises(ErroBenchmark) as erro:
        ConsultarRequisitosService().executar({"game": "sem-ficha"}, 1)
    assert erro.value.status == 404 and erro.value.codigo == "sem-requisitos"
    with pytest.raises(ValueError):
        ConsultarRequisitosService().executar({"game": "../../arquivo"}, 1)
