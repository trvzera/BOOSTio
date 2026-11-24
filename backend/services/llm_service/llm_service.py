import logging
import os
import random
import time

import requests
from requests.exceptions import ConnectionError, HTTPError

from .reservar_chamada_service import ReservarChamadaService

logger = logging.getLogger(__name__)

TENTATIVAS = 2                          # no máximo duas chamadas ao mesmo modelo
STATUS_TEMPORARIOS = (500, 502, 503, 504)   # falhas do provedor que costumam passar sozinhas
ESPERA_SEGUNDOS = 2

class RespostaLLMInvalida(ValueError):
  pass

class LLMService:
  def executar(self, prompt: str, modelo: str = "gemini-3.5-flash-lite", *, reservar_cota: bool = True):
    if not isinstance(prompt, str) or not prompt.strip():
      raise ValueError("Informe o prompt para gerar a resposta")
    if not isinstance(modelo, str) or not modelo.strip():
      raise ValueError("Informe o modelo de IA")

    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
      raise RuntimeError("GEMINI_API_KEY não configurada")

    if reservar_cota:
      ReservarChamadaService().executar()

    for tentativa in range(1, TENTATIVAS + 1):
      try:
        resposta = requests.post(
          f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
          headers={"x-goog-api-key": chave},
          json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 8192},
          },
          timeout=90,
        )
        resposta.raise_for_status()
        break
      except (HTTPError, ConnectionError) as erro:
        status = erro.response.status_code if isinstance(erro, HTTPError) and erro.response is not None else None
        logger.warning("IA: modelo=%s tentativa=%d status=%s", modelo, tentativa, status or type(erro).__name__)
        if tentativa == TENTATIVAS or not (isinstance(erro, ConnectionError) or status in STATUS_TEMPORARIOS):
          raise
        time.sleep(ESPERA_SEGUNDOS + random.random())
    return self._ler_resposta(resposta)

  @staticmethod
  def _ler_resposta(resposta):
    try:
      dados = resposta.json()
      candidatos = dados.get("candidates") if isinstance(dados, dict) else None
      candidato = candidatos[0] if isinstance(candidatos, list) and candidatos else None
      if not isinstance(candidato, dict) or candidato.get("finishReason") != "STOP":
        raise RespostaLLMInvalida("A IA não concluiu a resposta. Gere novamente o JSON completo da build.")
      partes = candidato.get("content", {}).get("parts", [])
      texto = "".join(parte["text"] for parte in partes if isinstance(parte, dict)
                      and parte.get("thought") is not True and isinstance(parte.get("text"), str))
      if not texto.strip():
        raise RespostaLLMInvalida("A IA retornou uma resposta vazia. Gere um JSON completo da build.")
      return texto
    except (TypeError, AttributeError, ValueError) as erro:
      if isinstance(erro, RespostaLLMInvalida):
        raise
      raise RespostaLLMInvalida("A IA retornou uma resposta malformada. Gere um JSON válido da build.") from erro
