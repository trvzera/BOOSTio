from . import db
from . import Setup

class Peca(Setup):
  __abstract__ = True
  fabricante = db.Column(db.String(30),nullable = False)
  modelo = db.Column(db.String(30),nullable = False)
  consumo_energia = db.Column(db.Float(),nullable = False)
