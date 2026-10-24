from contextlib import nullcontext

import pytest
from requests import Response
from requests.exceptions import HTTPError, Timeout, ConnectionError

from services.build_service.gerar_build_service import GerarBuildService
from services.build_service.criar_build_service import ErroGeracaoBuild


def preparar(mocker, respostas):
    trava = mocker.patch("services.build_service.gerar_build_service.BloquearGeracaoService.executar", return_value=nullcontext())
    criar = mocker.patch("services.build_service.criar_build_service.CriarBuildService.executar", side_effect=respostas)
    return trava, criar


def test_sucesso_usa_uma_chamada_e_a_trava_do_usuario(mocker):
    trava, criar = preparar(mocker, [{"id":"s-1"}])
    assert GerarBuildService().executar(7, {"nome":"Teste"}) == {"id":"s-1"}
    trava.assert_called_once_with(7)
    criar.assert_called_once_with(7, {"nome":"Teste"})


@pytest.mark.parametrize("status", [429,500,502,503,504])
def test_fallback_permitido_preserva_tentativa_unica_e_sem_novo_ciclo_de_correcao(mocker,status):
    resposta=Response();resposta.status_code=status
    trava, criar = preparar(mocker, [HTTPError(response=resposta), {"id":"s-2"}])
    assert GerarBuildService().executar(7, {}) == {"id":"s-2"}
    assert criar.call_count == 2
    assert criar.call_args.kwargs == {"modelo":"gemini-3.8-flash","tentativas_correcao":0}
    trava.assert_called_once_with(7)


@pytest.mark.parametrize("erro", [Timeout(),ConnectionError(),ErroGeracaoBuild("inválida")])
def test_erro_no_fallback_nao_inicia_loop(mocker,erro):
    _, criar = preparar(mocker, [Timeout(), erro])
    with pytest.raises(type(erro)):
        GerarBuildService().executar(7,{})
    assert criar.call_count == 2


@pytest.mark.parametrize("status", [400,401,403,404])
def test_http_nao_transitorio_nao_gasta_fallback(mocker,status):
    resposta=Response();resposta.status_code=status
    erro=HTTPError(response=resposta)
    _, criar = preparar(mocker, [erro])
    with pytest.raises(HTTPError) as capturada:
        GerarBuildService().executar(7,{})
    assert capturada.value is erro
    assert criar.call_count == 1


def test_resposta_invalida_nao_e_tratada_como_falha_de_transporte(mocker):
    _, criar = preparar(mocker, [ErroGeracaoBuild("incompleta")])
    with pytest.raises(ErroGeracaoBuild):
        GerarBuildService().executar(7,{})
    assert criar.call_count == 1
