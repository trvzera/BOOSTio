from . import db
from . import ModeloBase

class Peca(ModeloBase):
  __abstract__ = True
  
  fabricante = db.Column(db.String(30),nullable = False)
  modelo = db.Column(db.String(30),nullable = False)
  consumo_energia = db.Column(db.Float(),nullable = False)
  preco = db.Column(db.Float(),nullable = False)

  def atualizar_preco(self, preco: float) -> None:
    if preco < 0: 
      raise Exception("O preço não pode ser negativo")
      
    self.preco = preco
    db.session.commit()
      

