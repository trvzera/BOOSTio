import os

import requests

class RespostaLLMInvalida(ValueError):
  """O provedor respondeu, mas não entregou uma saída completa para validar."""

class LLMService:
  def executar(self, prompt: str, modelo: str = "gemini-3.5-flash-lite"):
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
      raise RuntimeError("GEMINI_API_KEY não configurada")

    resposta = requests.post(
      f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
      headers={"x-goog-api-key": chave},
      json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
      },
      timeout=90,
    )
    resposta.raise_for_status()
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
