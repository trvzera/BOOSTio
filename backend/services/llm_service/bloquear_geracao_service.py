from contextlib import contextmanager
from threading import Lock

from flask import current_app
from redis import Redis, RedisError
from redis.exceptions import LockError

from .reservar_chamada_service import ControleIAIndisponivelError


_controle = Lock()
_usuarios_ativos = set()


class GeracaoEmAndamentoError(RuntimeError):
  pass


class BloquearGeracaoService:
  @contextmanager
  def executar(self, usuario_id):
    armazenamento = current_app.config.get("RATELIMIT_STORAGE_URI", "memory://")
    if armazenamento.startswith(("redis://", "rediss://")):
      try:
        cliente = Redis.from_url(armazenamento, socket_connect_timeout=3, socket_timeout=3)
        trava = cliente.lock(f"boostio:ia:usuario:{usuario_id}", timeout=600)
        adquirida = trava.acquire(blocking=False)
      except RedisError as erro:
        raise ControleIAIndisponivelError("Controle de geração indisponível") from erro
      if not adquirida:
        raise GeracaoEmAndamentoError("Você já tem uma build sendo gerada. Aguarde a conclusão.")
      try:
        yield
      finally:
        try:
          trava.release()
        except (LockError, RedisError):
          current_app.logger.error("Não foi possível liberar a trava de geração do usuário %s", usuario_id)
      return

    with _controle:
      if usuario_id in _usuarios_ativos:
        raise GeracaoEmAndamentoError("Você já tem uma build sendo gerada. Aguarde a conclusão.")
      _usuarios_ativos.add(usuario_id)
    try:
      yield
    finally:
      with _controle:
        _usuarios_ativos.discard(usuario_id)
