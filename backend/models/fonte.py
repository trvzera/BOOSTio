from . import db
from . import Peca

class Fonte(Peca):
  __tablename__ = "fonte"

  potencia = db.Column(db.Float(),nullable = False)
  tamanho_mm = db.Column(db.Float(),nullable = False)