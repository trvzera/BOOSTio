from datetime import datetime,timezone
from . import db

class ModeloBase(db.Model):
  __abstract__ = True
  id = db.Column(db.Integer,primary_key = True)
  criado_em = db.Column(
    db.DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc),
    nullable=False
)
  atualizado_em = db.Column( db.DateTime,default=datetime.now,onupdate=datetime.now)
