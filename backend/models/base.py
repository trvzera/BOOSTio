from datetime import datetime,timezone
from . import db

def venceu(data):
  if data.tzinfo is None:
    data = data.replace(tzinfo=timezone.utc)
  return data <= datetime.now(timezone.utc)


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


