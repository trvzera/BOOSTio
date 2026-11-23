import pytest
from services.llm_service.llm_service import LLMService, RespostaLLMInvalida


def resposta(mocker, monkeypatch, dados):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-ficticia-somente-testes")
    retorno = mocker.Mock()
    retorno.json.return_value = dados
    mocker.patch("services.llm_service.llm_service.requests.post", return_value=retorno)


@pytest.mark.parametrize("dados", [None, [], {}, {"candidates": []}, {"candidates": [None]},
    {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "parcial"}]}}]},
    {"candidates": [{"finishReason": "SAFETY"}]}, {"candidates": [{"finishReason": "STOP"}]},
    {"candidates": [{"finishReason": "STOP", "content": None}]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": None}}]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "   "}]}}]}])
def test_retorno_incompleto_nao_vira_keyerror_ou_build(mocker, monkeypatch, dados):
    resposta(mocker, monkeypatch, dados)
    with pytest.raises(RespostaLLMInvalida):
        LLMService().executar("Pedido de teste")


def test_texto_completo_e_concatenado_sem_partes_de_pensamento(mocker, monkeypatch):
    resposta(mocker, monkeypatch, {"candidates": [{"finishReason": "STOP", "content": {"parts": [
        {"text": "não deve ser usado", "thought": True}, {"text": '{"nome":'}, {"text": '"PC"}'},
    ]}}]})
    assert LLMService().executar("Pedido de teste") == '{"nome":"PC"}'


def erro_http(status):
    from requests import Response
    from requests.exceptions import HTTPError
    resposta_http = Response()
    resposta_http.status_code = status
    return HTTPError(response=resposta_http)


def sucesso(mocker, texto='{"nome":"PC"}'):
    retorno = mocker.Mock()
    retorno.json.return_value = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": texto}]}}]}
    return retorno


def test_erro_temporario_do_provedor_tenta_de_novo_uma_vez(mocker, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-ficticia-somente-testes")
    mocker.patch("services.llm_service.llm_service.time.sleep")
    falha = mocker.Mock()
    falha.raise_for_status.side_effect = erro_http(503)
    post = mocker.patch("services.llm_service.llm_service.requests.post", side_effect=[falha, sucesso(mocker)])
    assert LLMService().executar("Pedido de teste") == '{"nome":"PC"}'
    assert post.call_count == 2


def test_nunca_chama_o_modelo_mais_de_duas_vezes(mocker, monkeypatch):
    from requests.exceptions import HTTPError
    monkeypatch.setenv("GEMINI_API_KEY", "chave-ficticia-somente-testes")
    mocker.patch("services.llm_service.llm_service.time.sleep")
    falha = mocker.Mock()
    falha.raise_for_status.side_effect = erro_http(503)
    post = mocker.patch("services.llm_service.llm_service.requests.post", return_value=falha)
    with pytest.raises(HTTPError):
        LLMService().executar("Pedido de teste")
    assert post.call_count == 2


@pytest.mark.parametrize("status", [400, 401, 404, 429])
def test_erro_que_nao_passa_sozinho_nao_tenta_de_novo(mocker, monkeypatch, status):
    from requests.exceptions import HTTPError
    monkeypatch.setenv("GEMINI_API_KEY", "chave-ficticia-somente-testes")
    falha = mocker.Mock()
    falha.raise_for_status.side_effect = erro_http(status)
    post = mocker.patch("services.llm_service.llm_service.requests.post", return_value=falha)
    with pytest.raises(HTTPError):
        LLMService().executar("Pedido de teste")
    assert post.call_count == 1
