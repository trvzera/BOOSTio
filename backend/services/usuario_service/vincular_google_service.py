from sqlalchemy.exc import IntegrityError
from models import db, Usuario
from .entrar_google_usuario_service import EntrarGoogleService


class VincularGoogleService:
  def executar(self, usuario, identidade):
    if usuario is None:
      raise ValueError("Usuário não encontrado")
    EntrarGoogleService()._validar_identidade(identidade)
    sub = identidade["sub"]
    existente = Usuario.buscar_por_google_sub(sub)
    if existente is not None and existente.id != usuario.id:
      raise ValueError("Esta conta Google já está vinculada a outra conta BOOSTio")
    return self._vincular(usuario, sub)

  @staticmethod
  def _vincular(usuario, sub):
    try:
      atualizados = Usuario.query.filter_by(id=usuario.id, ativo=True, google_sub=None,
                                            versao_sessao=usuario.versao_sessao).update({
        Usuario.google_sub: sub, Usuario.login_google: True,
        Usuario.versao_sessao: Usuario.versao_sessao + 1,
      }, synchronize_session=False)
      if atualizados != 1:
        raise ValueError("Sua conta mudou. Atualize a página antes de vincular o Google")
      db.session.commit()
      db.session.refresh(usuario)
      return usuario
    except (IntegrityError, ValueError) as erro:
      db.session.rollback()
      raise ValueError("Não foi possível vincular esta conta Google. Ela pode já estar em uso.") from erro
