from flask import current_app
from redis import Redis
from repositories.saude_repository import SaudeRepository


class VerificarSaudeService:
  def executar(self):
    SaudeRepository().verificar_conexao()
    armazenamento = current_app.config.get("RATELIMIT_STORAGE_URI") or ""
    if armazenamento.startswith(("redis://", "rediss://")):
      Redis.from_url(armazenamento, socket_connect_timeout=2, socket_timeout=2).ping()
