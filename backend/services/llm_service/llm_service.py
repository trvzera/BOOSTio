import os

import requests

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
    return resposta.json()["candidates"][0]["content"]["parts"][0]["text"]
