import time

from flask import has_request_context, session
from werkzeug.security import check_password_hash


class ConfirmarIdentidadeService:
  def executar(self, usuario, dados=None):
    if usuario.senha:
      senha = dados.get("senha_atual") if isinstance(dados, dict) else None
      if not isinstance(senha, str) or not senha or not check_password_hash(usuario.senha, senha):
        raise ValueError("Digite a senha atual correta para confirmar esta ação")
      return
    confirmacao = session.get("confirmacao_google", {}) if has_request_context() else {}
    instante = confirmacao.get("instante", 0)
    if (not usuario.google_sub or confirmacao.get("sessao") != usuario.get_id()
        or confirmacao.get("sub") != usuario.google_sub
        or not isinstance(instante, (int, float)) or not 0 <= time.time() - instante <= 300):
      raise ValueError("Confirme sua identidade pelo Google antes de realizar esta ação")
