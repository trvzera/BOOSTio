from . import db
from .base import ModeloBase
from datetime import datetime, timedelta, timezone
import hashlib

class TokenRecuperacao(ModeloBase):
  __tablename__ = "token_recuperacao"

  usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"),nullable = False)
  token_hash = db.Column(db.String(255),nullable = False, index=True)
  email_destino = db.Column(db.String(150), nullable=True)
  versao_sessao = db.Column(db.Integer, nullable=True)
  data_expiracao = db.Column(
      db.DateTime(timezone=True),
      default=lambda: datetime.now(timezone.utc) + timedelta(minutes=30)
  )
  usado = db.Column(db.Boolean, default=False ,nullable = False)

  usuario = db.relationship('Usuario', backref='tokens_recuperacao')

  def marcar_como_usado(self):
    self.usado = True
    db.session.commit()

  def esta_expirado(self):
    expiracao = self.data_expiracao
    if expiracao.tzinfo is None:
      expiracao = expiracao.replace(tzinfo=timezone.utc)
    return expiracao <= datetime.now(timezone.utc)

  @staticmethod
  def buscar_por_token(token:str):
    if not isinstance(token, str) or not token or len(token) > 512:
      return None
    return TokenRecuperacao.query.filter(
      TokenRecuperacao.token_hash == TokenRecuperacao._hash_token(token),
      TokenRecuperacao.usado.is_(False),
      TokenRecuperacao.data_expiracao > datetime.now(timezone.utc),
    ).first()

  @staticmethod
  def _hash_token(token):
    # O token aleatório tem 256 bits; o hash permite busca indexada sem armazená-lo em claro.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

  @staticmethod
  def emitir(usuario, token):
    from .usuario import Usuario
    try:
      atualizados = Usuario.query.filter_by(
        id=usuario.id, ativo=True, email=usuario.email, versao_sessao=usuario.versao_sessao,
      ).update({Usuario.versao_sessao: Usuario.versao_sessao}, synchronize_session=False)
      if atualizados != 1:
        raise ValueError("Conta indisponível para recuperação")
      TokenRecuperacao.query.filter_by(usuario_id=usuario.id, usado=False).update(
        {TokenRecuperacao.usado: True}, synchronize_session=False,
      )
      registro = TokenRecuperacao(
        usuario_id=usuario.id, token_hash=TokenRecuperacao._hash_token(token),
        email_destino=usuario.email, versao_sessao=usuario.versao_sessao,
      )
      db.session.add(registro)
      db.session.commit()
      return registro
    except Exception:
      db.session.rollback()
      raise

  def redefinir_senha(self, senha_hash):
    from .usuario import Usuario
    try:
      # Bloqueia a linha do usuário antes do token, na mesma ordem usada na emissão.
      atualizados = Usuario.query.filter_by(
        id=self.usuario_id, ativo=True, email=self.email_destino, versao_sessao=self.versao_sessao,
      ).update({Usuario.senha: senha_hash, Usuario.versao_sessao: Usuario.versao_sessao + 1}, synchronize_session=False)
      consumidos = TokenRecuperacao.query.filter(
        TokenRecuperacao.id == self.id, TokenRecuperacao.usado.is_(False),
        TokenRecuperacao.email_destino.is_not(None), TokenRecuperacao.versao_sessao.is_not(None),
        TokenRecuperacao.data_expiracao > datetime.now(timezone.utc),
      ).update({TokenRecuperacao.usado: True}, synchronize_session=False)
      if atualizados != 1 or consumidos != 1:
        raise ValueError("Link inválido ou expirado")
      TokenRecuperacao.query.filter_by(usuario_id=self.usuario_id, usado=False).update(
        {TokenRecuperacao.usado: True}, synchronize_session=False,
      )
      db.session.commit()
    except Exception:
      db.session.rollback()
      raise

  @staticmethod
  def deletar_tokens_usuario(usuario_id:int):
    TokenRecuperacao.query.filter_by(usuario_id = usuario_id).delete()

    db.session.commit()
