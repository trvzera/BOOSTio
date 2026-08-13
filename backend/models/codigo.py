from . import db
from .base import ModeloBase
from datetime import datetime, timedelta,timezone

class Codigo(ModeloBase):
  __tablename__ = "codigo"

  usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"),nullable = False)
  codigo = db.Column(db.String(4),nullable = False)
  data_expiracao = db.Column(
    db.DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc) + timedelta(minutes=5)
)
  usado = db.Column(db.Boolean, default=False ,nullable = False)

  usuario = db.relationship('Usuario', backref='codigo')

  def marcar_como_usado(self):
    self.usado = True
    db.session.commit()

  def esta_expirado(self):
    return self.data_expiracao < datetime.utcnow()

  @staticmethod
  def buscar_codigo_recente(usuario_id:int):
    codigo = Codigo.query.filter_by(usuario_id = usuario_id,
      usado = False).order_by(Codigo.criado_em.desc()).first()
    
    return codigo