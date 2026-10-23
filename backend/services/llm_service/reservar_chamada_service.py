from datetime import datetime, timedelta
from threading import Lock
from zoneinfo import ZoneInfo

from flask import current_app, has_app_context
from redis import Redis, RedisError


_controle = Lock()
_dia_local = None
_chamadas_locais = 0


class CotaGlobalIAError(RuntimeError):
  def __init__(self, espera):
    super().__init__("O limite diário de gerações foi atingido. Tente novamente amanhã.")
    self.espera = espera


class ControleIAIndisponivelError(RuntimeError):
  pass


class ReservarChamadaService:
  LIMITE_DIARIO = 100
  FUSO = ZoneInfo("America/Sao_Paulo")

  def executar(self):
    global _dia_local, _chamadas_locais
    agora = datetime.now(self.FUSO)
    amanha = (agora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    espera = max(1, int((amanha - agora).total_seconds()))
    armazenamento = current_app.config.get("RATELIMIT_STORAGE_URI", "memory://") if has_app_context() else "memory://"

    if armazenamento.startswith(("redis://", "rediss://")):
      try:
        cliente = Redis.from_url(armazenamento, socket_connect_timeout=3, socket_timeout=3)
        chamadas = cliente.eval(
          "local n=redis.call('INCR',KEYS[1]); "
          "if n==1 then redis.call('EXPIREAT',KEYS[1],ARGV[1]) end; return n",
          1, f"boostio:ia:chamadas:{agora.date().isoformat()}", int(amanha.timestamp()),
        )
      except RedisError as erro:
        raise ControleIAIndisponivelError("Controle de geração indisponível") from erro
    else:
      with _controle:
        if _dia_local != agora.date():
          _dia_local, _chamadas_locais = agora.date(), 0
        _chamadas_locais += 1
        chamadas = _chamadas_locais

    if chamadas > self.LIMITE_DIARIO:
      raise CotaGlobalIAError(espera)
