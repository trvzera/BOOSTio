from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
import requests

from services.benchmark_service.blender_service import BlenderService
from services.benchmark_service.fpshq_service import ErroBenchmark

CPU = "AMD Ryzen 5 5600 6-Core Processor"
GPU = "NVIDIA GeForce RTX 3060"
CONSULTA = {"dispositivo": CPU, "tipo": "cpu"}


def resposta(linhas=None):
    return Mock(status_code=200, headers={}, json=Mock(return_value={
        "columns": [{"display_name": nome} for nome in BlenderService.COLUNAS],
        "rows": linhas if linhas is not None else [[CPU, "CPU", "4.5.0", 150.5, 20]],
    }))


def test_normaliza_mediana_sem_converter_em_fps_e_cache_defensivo():
    buscar = Mock(return_value=resposta())
    service = BlenderService(buscar=buscar, data_atual=lambda: 10)
    primeiro = service.executar(CONSULTA, 1)
    assert primeiro["score"] == 150.5 and primeiro["quantidade"] == 20
    assert primeiro["unidade"] == "amostras/min" and "fps" not in primeiro
    assert primeiro["consultadoEm"] == 10000 and not primeiro["cache"]
    primeiro["score"] = 0
    assert service.executar(CONSULTA, 2)["score"] == 150.5
    assert buscar.call_count == 1
    assert buscar.call_args.kwargs["timeout"] == (4, 10)
    assert buscar.call_args.kwargs["allow_redirects"] is False


def test_isola_gpu_exata_versao_e_metodo_sem_misturar_laptop_ou_ti():
    service = BlenderService(buscar=Mock(return_value=resposta([
        [GPU + " Ti", "OPTIX", "9.0.0", 9999, 500],
        [GPU + " Laptop GPU", "OPTIX", "9.0.0", 9999, 500],
        [GPU, "OPTIX", "4.5.0", 2000, 20],
        [GPU, "OPTIX", "5.2.0", 1800, 10],
        [GPU, "CUDA", "5.2.0", 1000, 2],
        [GPU, "CPU", "9.0.0", 9999, 500],
    ])))
    resultado = service.executar({"dispositivo": GPU, "tipo": "gpu"}, 1)
    assert resultado["versao"] == "5.2.0" and resultado["metodo"] == "OPTIX"
    assert resultado["score"] == 1800 and resultado["quantidade"] == 10


@pytest.mark.parametrize("entrada", [{}, {**CONSULTA, "tipo": "url"}, {**CONSULTA, "dispositivo": "https://interno/"},
                                    {**CONSULTA, "dispositivo": "x" * 161}])
def test_valida_antes_de_acessar_rede(entrada):
    buscar = Mock()
    with pytest.raises(ValueError):
        BlenderService(buscar=buscar).executar(entrada, 1)
    buscar.assert_not_called()


@pytest.mark.parametrize("score", [True, "150", -1, float("nan"), float("inf"), None])
def test_nao_inventa_resultados_invalidos(score):
    service = BlenderService(buscar=Mock(return_value=resposta([[CPU, "CPU", "4.5.0", score, 10]])))
    with pytest.raises(ErroBenchmark) as erro:
        service.executar(CONSULTA, 1)
    assert erro.value.status == 422 and not service.cache


def test_contrato_desconhecido_e_resposta_vazia_nao_entram_no_cache():
    for bruto in ({}, {"columns": [{"display_name": []}], "rows": []}):
        service = BlenderService(buscar=Mock(return_value=Mock(status_code=200, json=Mock(return_value=bruto))))
        with pytest.raises(ErroBenchmark, match="formato|mudou"):
            service.executar(CONSULTA, 1)
        assert not service.cache
    with pytest.raises(ErroBenchmark, match="Não há resultados"):
        BlenderService(buscar=Mock(return_value=resposta([]))).executar(CONSULTA, 1)


@pytest.mark.parametrize("erro,status", [(requests.Timeout(), 504), (requests.ConnectionError(), 503)])
def test_falhas_externas_nao_viram_pontuacoes(erro, status):
    with pytest.raises(ErroBenchmark) as falha:
        BlenderService(buscar=Mock(side_effect=erro)).executar(CONSULTA, 1)
    assert falha.value.status == status


def test_pausa_429_preserva_cache_e_evita_nova_chamada():
    tempo = [0]
    buscar = Mock(return_value=resposta())
    service = BlenderService(buscar=buscar, relogio=lambda: tempo[0])
    service.executar(CONSULTA, 1)
    buscar.return_value = Mock(status_code=429, headers={"Retry-After": "90"})
    with pytest.raises(ErroBenchmark) as erro:
        service.executar({"dispositivo": GPU, "tipo": "gpu"}, 1)
    assert erro.value.espera == 90
    assert service.executar(CONSULTA, 2)["cache"]
    with pytest.raises(ErroBenchmark):
        service.executar({"dispositivo": GPU, "tipo": "gpu"}, 2)
    assert buscar.call_count == 2


def test_consultas_simultaneas_usam_uma_chamada_e_cache_expira():
    tempo = [0]
    buscar = Mock(return_value=resposta())
    service = BlenderService(buscar=buscar, relogio=lambda: tempo[0])
    with ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(lambda usuario: service.executar(CONSULTA, usuario), range(4)))
    assert len(resultados) == 4 and buscar.call_count == 1
    tempo[0] = service.TTL + 1
    assert not service.executar(CONSULTA, 1)["cache"]
    assert buscar.call_count == 2


def test_intel_aceita_prefixo_de_geracao_sem_trocar_sufixo_f():
    nome = "Intel Core i3-12100F"
    service = BlenderService(buscar=Mock(return_value=resposta([[nome,"CPU","4.5.0",105.5,12]])))
    resultado = service.executar({"dispositivo":"12th Gen Intel Core i3-12100F","tipo":"cpu"},1)
    assert resultado["dispositivo"] == nome and resultado["score"] == 105.5
    assert ("device_name",nome) in service.buscar.call_args.kwargs["params"]
    with pytest.raises(ErroBenchmark):
        service.executar({"dispositivo":"Intel Core i3-12100","tipo":"cpu"},1)


@pytest.mark.parametrize("http,codigo", [(403, "acesso-provedor"), (401, "acesso-provedor"), (302, "redirecionamento"), (503, "provedor")])
def test_diagnostico_distingue_http_da_fonte_sem_expor_conteudo(http, codigo, caplog):
    buscar = Mock(return_value=Mock(status_code=http, headers={"Content-Type": "text/html", "Set-Cookie": "segredo"}, text="conteudo-privado"))
    service = BlenderService(buscar=buscar)
    with pytest.raises(ErroBenchmark) as erro:
        service.executar(CONSULTA, 1)
    assert erro.value.status == 503 and erro.value.codigo == codigo
    assert erro.value.diagnostico == {"httpProvedor": http, "tipoResposta": "html", "redirecionamento": http == 302}
    assert "segredo" not in caplog.text and "conteudo-privado" not in caplog.text
    assert f"http_provedor={http}" in caplog.text
    assert not service.cache


def test_tls_tem_mensagem_do_servidor_e_nao_do_wifi_do_usuario():
    with pytest.raises(ErroBenchmark) as erro:
        BlenderService(buscar=Mock(side_effect=requests.exceptions.SSLError("detalhe-interno"))).executar(CONSULTA, 1)
    assert erro.value.codigo == "tls" and erro.value.status == 503
    assert "servidor da BOOSTio" in str(erro.value) and "detalhe-interno" not in str(erro.value)


def test_html_com_http_200_nao_vira_score_ou_cache():
    bruto = Mock(status_code=200, headers={"Content-Type": "text/html"}, json=Mock(side_effect=ValueError()))
    service = BlenderService(buscar=Mock(return_value=bruto))
    with pytest.raises(ErroBenchmark) as erro:
        service.executar(CONSULTA, 1)
    assert erro.value.status == 502 and erro.value.codigo == "resposta"
    assert erro.value.diagnostico["httpProvedor"] == 200
    assert erro.value.diagnostico["tipoResposta"] == "html"
    assert not service.cache
