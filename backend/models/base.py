from flask import Flask
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

  def salvar(self) -> None:
    db.session.add(self)
    db.session.commit()

  def deletar(self) -> None:
    db.session.delete(self)
    db.session.commit()

