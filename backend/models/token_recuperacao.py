from . import db
from .base import ModeloBase
from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash

class TokenRecuperacao(ModeloBase):
  __tablename__ = "token_recuperacao"

  usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"),nullable = False)
  token_hash = db.Column(db.String(255),nullable = False)
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
    return self.data_expiracao < datetime.utcnow()

  @staticmethod
  def buscar_por_token(token:str):
    #O hash do werkzeug usa salt aleatório, então não dá pra buscar por igualdade
    #direto no banco: comparamos o token contra cada hash não usado/não expirado.
    tokens_ativos = TokenRecuperacao.query.filter_by(usado = False).order_by(
      TokenRecuperacao.criado_em.desc()).all()

    for token_recuperacao in tokens_ativos:
      if not token_recuperacao.esta_expirado() and check_password_hash(token_recuperacao.token_hash,token):
        return token_recuperacao

    return None

  @staticmethod
  def deletar_tokens_usuario(usuario_id:int):
    TokenRecuperacao.query.filter_by(usuario_id = usuario_id).delete()

    db.session.commit()
