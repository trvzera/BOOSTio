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
