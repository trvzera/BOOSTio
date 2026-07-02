from . import db
from . import Setup

class Peca(Setup):
  fabricante = db.Column(db.String(30),nullable = False)
  modelo = db.Column(db.String(30),nullable = False)
  consumo_energia = db.Column(db.Float(),nullable = False)