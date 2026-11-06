from utils.ofertas_catalogo import ofertas_catalogo
from datetime import timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import isfinite

from . import db
from sqlalchemy.orm import declared_attr, validates
from . import ModeloBase
from .medidas_fisicas import completar_medidas
from .imagens_referencia import imagem_referencia




class Peca(ModeloBase):
  __abstract__ = True
  
  fabricante = db.Column(db.String(30),nullable = False)
  modelo = db.Column(db.String(120),nullable = False)
  consumo_energia = db.Column(db.Float(),nullable = True)
  preco = db.Column(db.Float(),nullable = True)
  part_number = db.Column(db.String(100), nullable=True)
  referencia_interna = db.Column(db.String(100), nullable=True)
  codigo_modelo_fabricante = db.Column(db.String(150), nullable=True)
  fontes_especificacoes = db.Column(db.JSON, nullable=True)
  kabum_external = db.Column(db.Text, nullable=True)
  preco_atualizado_em = db.Column(db.DateTime, nullable=True)
  esgotado = db.Column(db.Boolean(), nullable=True, default=False)
  imagem_url = db.Column(db.Text, nullable=True)

  ficha_montagem_validada = db.Column(db.Boolean(), nullable=True)

  # NULL identifica exclusivamente os registros anteriores à migração.
  # Legado preserva publicação sem afirmar que a ficha já foi auditada.
  status_validacao = db.Column(db.String(20), nullable=True, default='pendente', server_default='pendente')
  validacao_motivo = db.Column(db.Text, nullable=True)
  validado_em = db.Column(db.DateTime, nullable=True)

  @declared_attr
  def __table_args__(cls):
    return (
      db.CheckConstraint("status_validacao IS NULL OR status_validacao IN ('pendente','em_revisao','aprovado','rejeitado','legado')", name=f'ck_{cls.__tablename__}_validacao'),
      db.Index(f'ix_{cls.__tablename__}_publicacao', 'status_validacao', 'esgotado', 'preco'),
      db.Index(f'ix_{cls.__tablename__}_nome', 'fabricante', 'modelo'),
      db.Index(f'ix_{cls.__tablename__}_part_number', 'part_number'),
      db.Index(f'ix_{cls.__tablename__}_referencia', 'referencia_interna'),
    )

  @validates('status_validacao')
  def validar_status(self, chave, valor):
    if valor not in (None, 'pendente', 'em_revisao', 'aprovado', 'rejeitado', 'legado'):
      raise ValueError('Status de validação inválido')
    return valor

  def __init__(self, **dados):
    from utils.codigos_peca import separar_codigos
    super().__init__(**separar_codigos(dados))

  @validates('part_number')
  def validar_part_number(self, chave, valor):
    from utils.codigos_peca import codigo_interno
    if codigo_interno(valor):
      if self.referencia_interna and self.referencia_interna != valor:
        raise ValueError('Referências internas divergentes')
      self.referencia_interna = valor
      return None
    return valor.strip() if isinstance(valor, str) and valor.strip() else None

  @property
  def publicavel(self):
    return self.status_validacao in ('aprovado', 'legado') or (self.status_validacao is None and self.id is not None)


  def situacao_catalogo(self):
    if not self.publicavel:return 'pendente_validacao'
    if self.ficha_montagem_validada is False:return 'ficha_incompleta_para_montagem'
    if self.preco is None:return 'sem_preco'
    if self.esgotado is None:return 'disponibilidade_desconhecida'
    return 'indisponivel' if self.esgotado else 'disponivel'

  @classmethod
  def consulta_publicavel(cls):
    return cls.query.filter(db.or_(cls.status_validacao.is_(None), cls.status_validacao.in_(('aprovado', 'legado'))))

  @classmethod
  def consulta_para_montagem(cls):
    return cls.consulta_publicavel().filter(cls.ficha_montagem_validada.is_not(False))

  @classmethod
  def listar_publicadas(cls):
    return cls.consulta_publicavel().all()

  @classmethod
  def buscar_publicada_por_id(cls, peca_id):
    return cls.consulta_publicavel().filter_by(id=peca_id).first()

  @classmethod
  def fabricantes_para_descoberta(cls):
    """Marcas por presença no catálogo publicável, com desempate estável."""
    from sqlalchemy import func
    return [linha[0] for linha in cls.consulta_publicavel().with_entities(
      cls.fabricante).group_by(cls.fabricante).order_by(
      func.count(cls.id).desc(), cls.fabricante).all() if linha[0] and linha[0].strip()]

  @classmethod
  def pool_para_matching(cls, limite=2001):
    return cls.query.order_by(cls.id).limit(limite).all()

  @classmethod
  def iterar_para_matching(cls, tamanho_lote=500):
    """Catálogo completo, incluindo fichas em revisão para detectar duplicatas."""
    if type(tamanho_lote) is not int or not 1 <= tamanho_lote <= 1000:
      raise ValueError('Tamanho do lote entre 1 e 1000')
    ultimo_id = 0
    while True:
      # Materializa e fecha o cursor antes de consultar identidades. MySQL
      # não permite outra consulta durante a leitura de cursor não bufferizado.
      lote = cls.query.filter(cls.id > ultimo_id).order_by(cls.id).limit(tamanho_lote).all()
      if not lote:
        return
      ultimo_id = lote[-1].id
      yield from lote

  @classmethod
  def lote_para_identificadores(cls, depois_id=0, limite=100):
    return cls.query.filter(cls.id > depois_id).order_by(cls.id).limit(limite).all()

  def separar_identificadores(self, *, simular=True, ids_ambiguos=None):
    from .identificadores_peca import separar_identificadores
    return separar_identificadores(self, simular=simular, ids_ambiguos=ids_ambiguos)

  def preencher_especificacoes(self, proposta, assinatura, *, simular=True):
    from .especificacoes_peca import preencher_especificacoes
    return preencher_especificacoes(self, proposta, assinatura, simular=simular)

  @classmethod
  def lote_para_ofertas(cls, depois_id=0, limite=50, *, somente_vinculadas=False):
    consulta = cls.query.filter(cls.id > depois_id)
    if somente_vinculadas:
      from . import VinculoMercadoLivre
      consulta = consulta.join(VinculoMercadoLivre, db.and_(
        VinculoMercadoLivre.tabela_peca == cls.__tablename__, VinculoMercadoLivre.peca_id == cls.id))
    return consulta.order_by(cls.id).limit(limite).all()

  @classmethod
  def com_link_kabum(cls):
    return cls.query.filter(cls.kabum_external.isnot(None), cls.kabum_external != "").all()

  @classmethod
  def sem_imagem_com_link(cls):
    return cls.query.filter(cls.imagem_url.is_(None), cls.kabum_external.isnot(None), cls.kabum_external != "").all()

  @classmethod
  def restaurar_links_ausentes(cls, links):
    pecas = cls.query.filter(db.or_(cls.part_number.in_(links), cls.referencia_interna.in_(links))).all()
    atualizadas = 0
    for peca in pecas:
      if not peca.kabum_external:
        peca.kabum_external = links.get(peca.referencia_interna) or links.get(peca.part_number)
        atualizadas += 1
    db.session.commit()
    return atualizadas

  @classmethod
  def buscar_por_id(cls, peca_id):
    return db.session.get(cls, peca_id)

  @classmethod
  def buscar_por_nome(cls, nome):
    normalizado = " ".join(nome.split()).casefold()
    exatas = [peca for peca in cls.query.all()
              if normalizado in (" ".join(f"{peca.fabricante} {peca.modelo}".split()).casefold(), " ".join(peca.modelo.split()).casefold())]
    return exatas[0] if len(exatas) == 1 else None

  def recarregar(self):
    db.session.refresh(self)

  def to_catalogo(self):
    dados = {coluna.name: getattr(self, coluna.name) for coluna in self.__table__.columns
             if coluna.name not in ("preco_atualizado_em", "criado_em", "atualizado_em", "status_validacao", "validacao_motivo", "validado_em", "fontes_especificacoes", "ficha_montagem_validada")}
    dados["id"] = f"{self.__tablename__}:{self.id}"
    if self.__tablename__ == "cabo_rede":
      dados["categoria_cabo"] = dados.get("categoria")
    dados["categoria"] = self.__tablename__
    dados["link"] = dados.pop("kabum_external", None)
    data = self.preco_atualizado_em
    # As coletas gravam UTC sem tzinfo no SQLite; o contrato explicita o fuso.
    if data and data.tzinfo is None:
      data = data.replace(tzinfo=timezone.utc)
    dados["preco_atualizado_em"] = data.isoformat() if data else None
    dados["ofertas"] = ofertas_catalogo(dados)
    dados["imagem"] = dados.pop("imagem_url", None) or imagem_referencia(dados)
    return completar_medidas(dados)

  def definir_imagem(self, caminho):
    self.imagem_url = caminho
    db.session.commit()

  def aplicar_cotacao(self, resultado, atualizado_em):
    preco_alterado = False
    if resultado["preco"] is not None:
      novo = Decimal(str(resultado["preco"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
      try:
        atual = Decimal(str(self.preco)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
      except InvalidOperation:
        atual = None
      if novo != atual:
        self.preco = float(novo)
        self.preco_atualizado_em = atualizado_em
        preco_alterado = True
    estoque_alterado = self.esgotado != resultado["esgotado"]
    if estoque_alterado:
      self.esgotado = resultado["esgotado"]
    return {"preco_alterado": preco_alterado, "estoque_alterado": estoque_alterado}

  @classmethod
  def cadastrar_ausentes(cls, itens):
    from utils.codigos_peca import separar_codigos
    novos = []
    try:
      for original in itens:
        item = separar_codigos(original)
        referencia, numero = item.get('referencia_interna'), item.get('part_number')
        if referencia:
          existente = cls.query.filter(db.or_(cls.referencia_interna == referencia, cls.part_number == referencia)).first()
        elif numero:
          existente = cls.query.filter_by(part_number=numero, fabricante=item['fabricante']).first()
        else:
          raise ValueError('Cadastro sem identificador estável')
        if existente is None:
          existente = cls(status_validacao='legado', **{k:v for k,v in item.items() if k != 'status_validacao'})
          db.session.add(existente)
          db.session.flush()
          novos.append(existente)
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
    pecas = cls.listar_candidatos_disponiveis(preco_maximo)
    if len(pecas) <= limite:
      return pecas
    # Distribui as opções pela faixa de preços, sem enviar o catálogo inteiro ao LLM.
    return [pecas[indice * (len(pecas) - 1) // (limite - 1)] for indice in range(limite)]


  @classmethod
  def buscar_mais_barata_por_part_number(cls, part_number: str) -> "Peca | None":
    return cls.query.filter_by(part_number=part_number).order_by(cls.preco.asc()).first()

  @classmethod
  def listar_candidatos_disponiveis(cls, preco_maximo):
    """Pool completo para planejamento; não aplica corte/amostragem prematuros."""
    return (cls.consulta_para_montagem().filter(cls.preco > 0, cls.preco <= preco_maximo, cls.esgotado.is_(False))
            .order_by(cls.preco.asc(), cls.id.asc()).all())
