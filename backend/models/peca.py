from datetime import timezone

from . import db
from . import ModeloBase

class Peca(ModeloBase):
  __abstract__ = True
  
  fabricante = db.Column(db.String(30),nullable = False)
  modelo = db.Column(db.String(120),nullable = False)
  consumo_energia = db.Column(db.Float(),nullable = False)
  preco = db.Column(db.Float(),nullable = False)
  part_number = db.Column(db.String(100), nullable=True)
  kabum_external = db.Column(db.Text, nullable=True)
  preco_atualizado_em = db.Column(db.DateTime, nullable=True)
  esgotado = db.Column(db.Boolean(), nullable=False, default=False)
  imagem_url = db.Column(db.Text, nullable=True)

  @classmethod
  def com_link_kabum(cls):
    return cls.query.filter(cls.kabum_external.isnot(None), cls.kabum_external != "").all()

  @classmethod
  def sem_imagem_com_link(cls):
    return cls.query.filter(cls.imagem_url.is_(None), cls.kabum_external.isnot(None), cls.kabum_external != "").all()

  @classmethod
  def restaurar_links_ausentes(cls, links):
    pecas = cls.query.filter(cls.part_number.in_(links)).all()
    atualizadas = 0
    for peca in pecas:
      if not peca.kabum_external:
        peca.kabum_external = links[peca.part_number]
        atualizadas += 1
    db.session.commit()
    return atualizadas

  @classmethod
  def buscar_por_id(cls, peca_id):
    return db.session.get(cls, peca_id)

  @classmethod
  def buscar_por_nome(cls, nome):
    normalizado = " ".join(nome.split()).casefold()
    return next((peca for peca in cls.query.all()
                 if normalizado in (f"{peca.fabricante} {peca.modelo}".casefold(), peca.modelo.casefold())), None)

  def recarregar(self):
    db.session.refresh(self)

  def to_catalogo(self):
    dados = {coluna.name: getattr(self, coluna.name) for coluna in self.__table__.columns
             if coluna.name not in ("preco_atualizado_em", "criado_em", "atualizado_em")}
    dados["id"] = f"{self.__tablename__}:{self.id}"
    dados["categoria"] = self.__tablename__
    dados["link"] = dados.pop("kabum_external", None)
    data = self.preco_atualizado_em
    # As coletas gravam UTC sem tzinfo no SQLite; o contrato explicita o fuso.
    if data and data.tzinfo is None:
      data = data.replace(tzinfo=timezone.utc)
    dados["preco_atualizado_em"] = data.isoformat() if data else None
    dados["imagem"] = dados.pop("imagem_url", None)
    return dados

  def definir_imagem(self, caminho):
    self.imagem_url = caminho
    db.session.commit()

  def aplicar_cotacao(self, resultado, atualizado_em):
    if resultado["preco"] is not None:
      self.preco = float(resultado["preco"])
      self.preco_atualizado_em = atualizado_em
    self.esgotado = resultado["esgotado"]

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
  def listar_disponiveis_ate(cls, preco_maximo: float, limite: int = 30):
    pecas = (cls.query
      .filter(cls.preco > 0, cls.preco <= preco_maximo, cls.esgotado.is_(False))
      .order_by(cls.preco.asc(), cls.id.asc())
      .all())
    if len(pecas) <= limite:
      return pecas
    # Distribui as opções pela faixa de preços, sem enviar o catálogo inteiro ao LLM.
    return [pecas[indice * (len(pecas) - 1) // (limite - 1)] for indice in range(limite)]


  @classmethod
  def buscar_mais_barata_por_part_number(cls, part_number: str) -> "Peca | None":
    return cls.query.filter_by(part_number=part_number).order_by(cls.preco.asc()).first()
