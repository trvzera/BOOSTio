import os

import requests

class LLMService:
  def executar(self, prompt: str):
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
      raise RuntimeError("GEMINI_API_KEY não configurada")

    resposta = requests.post(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
      headers={"x-goog-api-key": chave},
      json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
      },
      timeout=90,
    )
    resposta.raise_for_status()
    return resposta.json()["candidates"][0]["content"]["parts"][0]["text"]
