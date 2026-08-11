from . import db
from .base import ModeloBase
from datetime import datetime, timedelta

class Codigo(ModeloBase):
  __tablename__ = "codigo"

  usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"),nullable = False)
  codigo = db.Column(db.String(4),nullable = False)
  data_expiracao = db.Column(db.DateTime,default = lambda: datetime.utcnow() + timedelta(minutes=5))
  usado = db.Column(db.Boolean, default=False ,nullable = False)

  usuario = db.relationship('Usuario', backref='codigo')

  def marcar_como_usado(self):
    self.usado = True
    db.session.commit()

  def esta_expirado(self):
    return self.data_expiracao < datetime.utcnow()