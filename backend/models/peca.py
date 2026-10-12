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
  preco_atualizado_em = db.Column(db.DateTime, nullable=True)
  esgotado = db.Column(db.Boolean(), nullable=False, default=False)

  @classmethod
  def com_link_kabum(cls):
    return cls.query.filter(cls.kabum_external.isnot(None), cls.kabum_external != "").all()

  @classmethod
  def buscar_por_id(cls, peca_id):
    return db.session.get(cls, peca_id)

  def recarregar(self):
    db.session.refresh(self)

  def aplicar_cotacao(self, resultado, atualizado_em):
    if resultado["preco"] is not None:
      self.preco = float(resultado["preco"])
    self.esgotado = resultado["esgotado"]
    self.preco_atualizado_em = atualizado_em

  @classmethod
  def cadastrar_ausentes(cls, itens):
    part_numbers = [item["part_number"] for item in itens]
    existentes = {
      row.part_number
      for row in cls.query.filter(cls.part_number.in_(part_numbers)).all()
    }
    novos = [cls(**item) for item in itens if item["part_number"] not in existentes]
    try:
      db.session.add_all(novos)
      db.session.commit()
    except Exception:
      db.session.rollback()
      raise
    return len(novos)
  
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
