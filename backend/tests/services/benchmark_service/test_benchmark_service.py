from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock

import pytest
import requests

from services.benchmark_service.fpshq_service import FpshqService, ErroBenchmark
from services.benchmark_service.consultar_benchmark_service import ConsultarBenchmarkService
from services.benchmark_service.buscar_jogos_benchmark_service import BuscarJogosBenchmarkService


CONSULTA = {"game": "valorant", "cpu": "ryzen-5-5600", "gpu": "rtx-3060", "res": "1080p", "preset": "high"}


def resposta(**alteracoes):
    dados = {"ok": True, "game": {"slug": "valorant", "name": "Valorant"},
             "cpu": {"slug": "ryzen-5-5600"}, "gpu": {"slug": "rtx-3060"},
             "res": "1080p", "preset": "high", "fps": 288, "low1": 261,
             "source": "measured", "basis": "measured", "matrix": {"1080p": {"high": 288}}}
    dados.update(alteracoes)
    return Mock(status_code=200, headers={}, json=Mock(return_value=dados))


def cliente(buscar=None, **opcoes):
    return FpshqService(buscar=buscar or Mock(return_value=resposta()), **opcoes)


def test_redirecionamento_externo_nao_e_seguido_e_ativa_intervalo():
    buscar=Mock(return_value=Mock(status_code=302, headers={"Location":"https://externo.invalid/noactive/"}))
    api=cliente(buscar)
    for _ in range(2):
        with pytest.raises(ErroBenchmark) as erro:
            api.executar("games",{"q":"valorant"},1)
        assert erro.value.status == 503
        assert erro.value.codigo == "redirecionamento"
        assert erro.value.espera == 60
    assert buscar.call_count == 1
    assert buscar.call_args.kwargs["allow_redirects"] is False


def test_redirecionamento_preserva_resposta_validada_com_aviso_de_desatualizada():
    tempo=[0]
    api=cliente(Mock(return_value=Mock(status_code=302, headers={})),relogio=lambda:tempo[0])
    api.salvar("games",{"q":"valorant"},{"jogos":[{"nome":"Valorant"}]})
    tempo[0]=3601
    resultado=api.executar("games",{"q":"valorant"},1)
    assert resultado["cache"] and resultado["desatualizado"]


@pytest.mark.parametrize("campo,valor", [("cpu", None), ("gpu", "../gpu"), ("game", "http://externo.test"), ("res", "8k"), ("preset", "extreme")])
def test_valida_antes_da_rede(campo, valor):
    api = cliente()
    with pytest.raises(ValueError):
        ConsultarBenchmarkService(api).executar({**CONSULTA, campo: valor}, 1)
    api.buscar.assert_not_called()


def test_normaliza_e_preserva_ausencias_sem_aprovar_requisitos():
    api = cliente(Mock(return_value=resposta(low1=None, fps_range=None, basis="aggregate")))
    resultado = ConsultarBenchmarkService(api).executar(CONSULTA, 1)
    assert resultado["fps"] == 288
    assert resultado["low1"] is None
    assert resultado["intervalo"] is None
    assert resultado["matriz"]["4K"]["high"] is None
    assert resultado["base"] == "aggregate"
    assert resultado["requisitosVerificados"] is False
    assert resultado["ramAvaliada"] is False
    assert "verdict" not in resultado
    assert api.buscar.call_args.kwargs["allow_redirects"] is False
    assert api.buscar.call_args.kwargs["timeout"] == (4, 10)


@pytest.mark.parametrize("alteracao", [{"cpu": {"slug": "outra"}}, {"cpu": None}, {"gpu": None}, {"game": {"slug": "outro"}}, {"res": "4K"}, {"preset": "low"}])
def test_rejeita_resposta_que_nao_confirma_a_combinacao(alteracao):
    api = cliente(Mock(return_value=resposta(**alteracao)))
    with pytest.raises(ErroBenchmark, match="confirmou|ajustes"):
        ConsultarBenchmarkService(api).executar(CONSULTA, 1)
    assert not api.cache


@pytest.mark.parametrize("fps", [None, "288", True, float("nan"), float("inf"), -1])
def test_nao_inventa_fps_quando_nao_ha_dados(fps):
    api = cliente(Mock(return_value=resposta(fps=fps)))
    with pytest.raises(ErroBenchmark) as erro:
        ConsultarBenchmarkService(api).executar(CONSULTA, 1)
    assert erro.value.status == 422
    assert not api.cache


def test_zero_e_intervalos_validos_sao_preservados():
    resultado = ConsultarBenchmarkService(cliente(Mock(return_value=resposta(fps=0, fps_range=[0, 15])))).executar(CONSULTA, 1)
    assert resultado["fps"] == 0
    assert resultado["intervalo"] == [0, 15]


def test_matriz_aceita_rotulo_4k_sem_inventar_presets_ausentes():
    resultado = ConsultarBenchmarkService(cliente(Mock(return_value=resposta(matrix={"4k": {"high": 42}})))).executar(CONSULTA, 1)
    assert resultado["matriz"]["4K"]["high"] == 42
    assert resultado["matriz"]["4K"]["ultra"] is None


def test_cache_compartilhado_ttl_e_copia_defensiva():
    tempo = [0]
    api = cliente(relogio=lambda: tempo[0])
    service = ConsultarBenchmarkService(api)
    primeiro = service.executar(CONSULTA, 1)
    segundo = service.executar(CONSULTA, 2)
    assert primeiro["cache"] is False and segundo["cache"] is True
    segundo["matriz"]["1080p"]["high"] = 999
    assert service.executar(CONSULTA, 3)["matriz"]["1080p"]["high"] == 288
    assert api.buscar.call_count == 1
    tempo[0] = 3601
    assert service.executar(CONSULTA, 1)["cache"] is False
    assert api.buscar.call_count == 2


def test_consultas_simultaneas_identicas_usam_uma_so_chamada():
    api = cliente()
    with ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(lambda usuario: ConsultarBenchmarkService(api).executar(CONSULTA, usuario), range(4)))
    assert len(resultados) == 4
    assert api.buscar.call_count == 1


def test_consultas_diferentes_nao_ficam_presas_na_mesma_requisicao():
    encontro = Barrier(2, timeout=3)

    def buscar(_url, *, params, **_opcoes):
        encontro.wait()
        return resposta(game={"slug": params["game"], "name": params["game"]})

    api = cliente(Mock(side_effect=buscar))
    jogos = ["valorant", "cs2"]
    while api.travar("fps", {**CONSULTA, "game": jogos[0]}) is api.travar("fps", {**CONSULTA, "game": jogos[1]}):
        jogos[1] += "-x"
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(lambda jogo: ConsultarBenchmarkService(api).executar({**CONSULTA, "game": jogo}, 1), jogos))
    assert [item["consulta"]["game"] for item in resultados] == jogos


def test_timeout_usa_ultima_consulta_valida_por_ate_24_horas():
    tempo = [0]
    api = cliente(relogio=lambda: tempo[0])
    service = ConsultarBenchmarkService(api)
    original = service.executar(CONSULTA, 1)
    tempo[0] = 3601
    api.buscar.side_effect = requests.Timeout()
    reserva = service.executar(CONSULTA, 1)
    assert reserva["fps"] == original["fps"]
    assert reserva["consultadoEm"] == original["consultadoEm"]
    assert reserva["cache"] is True
    assert reserva["desatualizado"] is True
    tempo[0] = 86401
    with pytest.raises(ErroBenchmark) as erro:
        service.executar(CONSULTA, 1)
    assert erro.value.status == 504


def test_limite_provedor_respeita_espera_e_permite_ler_cache():
    tempo = [0]
    api = cliente(relogio=lambda: tempo[0])
    service = ConsultarBenchmarkService(api)
    service.executar(CONSULTA, 1)
    api.buscar.return_value = Mock(status_code=429, headers={"Retry-After": "120"})
    with pytest.raises(ErroBenchmark) as erro:
        service.executar({**CONSULTA, "game": "cs2"}, 1)
    assert erro.value.espera == 120
    assert service.executar(CONSULTA, 2)["cache"] is True
    tempo[0] = 20
    with pytest.raises(ErroBenchmark) as erro:
        service.executar({**CONSULTA, "game": "cs2"}, 2)
    assert erro.value.espera == 100
    assert api.buscar.call_count == 2


def test_cache_de_reserva_funciona_durante_pausa_por_falha_http():
    tempo = [0]
    api = cliente(relogio=lambda: tempo[0])
    service = ConsultarBenchmarkService(api)
    original = service.executar(CONSULTA, 1)
    tempo[0] = 3601
    api.buscar.return_value = Mock(status_code=503, headers={"Retry-After": "60"})
    primeira = service.executar(CONSULTA, 1)
    assert primeira["desatualizado"] and primeira["consultadoEm"] == original["consultadoEm"]
    primeira["matriz"]["1080p"]["high"] = 999
    tempo[0] = 3602
    segunda = service.executar(CONSULTA, 2)
    assert segunda["desatualizado"] and segunda["matriz"]["1080p"]["high"] == 288
    assert api.buscar.call_count == 2
    with pytest.raises(ErroBenchmark) as erro:
        service.executar({**CONSULTA, "game": "fortnite"}, 2)
    assert erro.value.codigo == "provedor" and erro.value.espera == 59
    assert api.buscar.call_count == 2


def test_limites_por_usuario_globais_e_cache_limitado():
    api = cliente()
    api.buscar.return_value = Mock(status_code=200, headers={}, json=Mock(return_value={"ok": True, "results": []}))
    for n in range(api.LIMITE_USUARIO):
        BuscarJogosBenchmarkService(api).executar({"q": "jogo " + str(n)}, 1)
    with pytest.raises(ErroBenchmark) as erro:
        BuscarJogosBenchmarkService(api).executar({"q": "outro"}, 1)
    assert erro.value.status == 429
    for n in range(api.MAX_CACHE + 10):
        api.salvar("games", {"q": str(n)}, {"jogos": [], "cache": False})
    assert len(api.cache) == api.MAX_CACHE
    api.LIMITE_MINUTO = 10
    with pytest.raises(ErroBenchmark):
        BuscarJogosBenchmarkService(api).executar({"q": "novo"}, 2)


@pytest.mark.parametrize("status,esperado", [(404, 404), (503, 503), (302, 503)])
def test_erros_http_sem_cache(status, esperado):
    api = cliente(Mock(return_value=Mock(status_code=status, headers={})))
    with pytest.raises(ErroBenchmark) as erro:
        ConsultarBenchmarkService(api).executar(CONSULTA, 1)
    assert erro.value.status == esperado
    assert not api.cache


@pytest.mark.parametrize("falha,status", [(requests.Timeout(), 504), (requests.ConnectionError(), 503)])
def test_timeout_rede_e_json_invalido(falha, status):
    api = cliente(Mock(side_effect=falha))
    with pytest.raises(ErroBenchmark) as erro:
        ConsultarBenchmarkService(api).executar(CONSULTA, 1)
    assert erro.value.status == status
    api = cliente(Mock(return_value=Mock(status_code=200, headers={}, json=Mock(side_effect=ValueError()))))
    with pytest.raises(ErroBenchmark, match="inválida"):
        ConsultarBenchmarkService(api).executar(CONSULTA, 1)


@pytest.mark.parametrize("falha,codigo,status", [
    (requests.exceptions.SSLError(), "tls", 503),
    (requests.ConnectionError(), "rede", 503),
    (requests.Timeout(), "timeout", 504),
])
def test_falha_temporaria_pausa_rede_sem_bloquear_cache(falha, codigo, status):
    tempo = [0]
    api = cliente(relogio=lambda: tempo[0])
    service = ConsultarBenchmarkService(api)
    service.executar(CONSULTA, 1)
    api.buscar.side_effect = falha
    with pytest.raises(ErroBenchmark) as erro:
        service.executar({**CONSULTA, "game": "cs2"}, 1)
    assert (erro.value.codigo, erro.value.status) == (codigo, status)
    assert erro.value.espera > 0
    espera = erro.value.espera
    assert service.executar(CONSULTA, 2)["cache"] is True
    with pytest.raises(ErroBenchmark):
        service.executar({**CONSULTA, "game": "fortnite"}, 2)
    assert api.buscar.call_count == 2
    tempo[0] = espera + 1
    api.buscar.side_effect = None
    assert service.executar(CONSULTA, 1)["fps"] == 288


def test_busca_valida_filtra_e_limita_resultados():
    api = cliente(Mock(return_value=Mock(status_code=200, headers={}, json=Mock(return_value={"ok": True, "results": [{"slug": "../errado", "name": "X"}, None] + [{"slug": "game-" + str(i), "name": "Jogo"} for i in range(20)]}))))
    service = BuscarJogosBenchmarkService(api)
    for q in ("", "a", "a" * 61, 5):
        with pytest.raises(ValueError):
            service.executar({"q": q}, 1)
    assert len(service.executar({"q": " jogo "}, 1)["jogos"]) == 10
    assert api.buscar.call_args.kwargs["params"]["q"] == "jogo"
