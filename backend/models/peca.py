from . import db
from . import ModeloBase

class Peca(ModeloBase):
  __abstract__ = True
  
  fabricante = db.Column(db.String(30),nullable = False)
  modelo = db.Column(db.String(30),nullable = False)
  consumo_energia = db.Column(db.Float(),nullable = False)
  preco = db.Column(db.Float(),nullable = False)
  part_number = db.Column(db.String(100), nullable=True)
  kabum_external = db.Column(db.Text, nullable=True)
  meli_external = db.Column(db.Text, nullable=True)
  preco_atualizado_em = db.Column(db.DateTime, nullable=True)
  esgotado = db.Column(db.Boolean(), nullable=False, default=False)
  
  def atualizar_preco(self, preco: float) -> None:
    if preco < 0:
      raise Exception("O preço não pode ser negativo")

    self.preco = preco
    db.session.commit()

  @classmethod
  def mostrar_pecas(cls):
    return cls.query.all()


  @classmethod
  def buscar_mais_barata_por_part_number(cls, part_number: str) -> "Peca | None":
    return cls.query.filter_by(part_number=part_number).order_by(cls.preco.asc()).first()
