from . import db
from .base import ModeloBase

class Usuario(ModeloBase):
  __tablename__ = "usuarios"

  #Colunas
  nome = db.Column(db.String(30),nullable = False)
  email = db.Column(db.String(150),nullable = False)
  senha = db.Column(db.String(100),nullable = False)




