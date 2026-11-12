from datetime import timezone

from . import db
from sqlalchemy.orm import declared_attr, validates
from . import ModeloBase
from utils.medidas_fisicas import completar_medidas
from utils.imagens_referencia import imagem_referencia


class Peca(ModeloBase):
  __abstract__ = True
  
  fabricante = db.Column(db.String(30),nullable = False)
  modelo = db.Column(db.String(120),nullable = False)
  consumo_energia = db.Column(db.Float(),nullable = True)
  part_number = db.Column(db.String(100), nullable=True)
  referencia_interna = db.Column(db.String(100), nullable=True)
  codigo_modelo_fabricante = db.Column(db.String(150), nullable=True)
  fontes_especificacoes = db.Column(db.JSON, nullable=True)
  imagem_url = db.Column(db.Text, nullable=True)

  ficha_montagem_validada = db.Column(db.Boolean(), nullable=True)

  status_validacao = db.Column(db.String(20), nullable=True, default='pendente', server_default='pendente')
  validacao_motivo = db.Column(db.Text, nullable=True)
  validado_em = db.Column(db.DateTime, nullable=True)

  @declared_attr
  def __table_args__(cls):
    return (
      db.CheckConstraint("status_validacao IS NULL OR status_validacao IN ('pendente','em_revisao','aprovado','rejeitado','legado')", name=f'ck_{cls.__tablename__}_validacao'),
      db.Index(f'ix_{cls.__tablename__}_publicacao', 'status_validacao'),
      db.Index(f'ix_{cls.__tablename__}_nome', 'fabricante', 'modelo'),
      db.Index(f'ix_{cls.__tablename__}_part_number', 'part_number'),
      db.Index(f'ix_{cls.__tablename__}_referencia', 'referencia_interna'),
    )

  @validates('status_validacao')
  def validar_status(self, chave, valor):
    if valor not in (None, 'pendente', 'em_revisao', 'aprovado', 'rejeitado', 'legado'):
      raise ValueError('Status de validação inválido')
    return valor

  CAMPOS_DA_OFERTA = ('preco', 'esgotado', 'preco_atualizado_em', 'kabum_external')

  def __init__(self, **dados):
    from utils.codigos_peca import separar_codigos
    invalidos = [campo for campo in self.CAMPOS_DA_OFERTA if campo in dados]
    if invalidos:
      raise ValueError(f"Preço e link pertencem à oferta, não à peça: {', '.join(invalidos)}")
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
  def consulta_catalogo(cls):
    return cls.consulta_publicavel().filter(cls.preco > 0)

  @classmethod
  def consulta_para_montagem(cls):
    return cls.consulta_catalogo().filter(cls.ficha_montagem_validada.is_not(False))

  @classmethod
  def listar_publicadas(cls):
    return cls.consulta_catalogo().all()

  @classmethod
  def buscar_publicada_por_id(cls, peca_id):
    return cls.consulta_catalogo().filter_by(id=peca_id).first()

  @classmethod
  def fabricantes_para_descoberta(cls):
    from sqlalchemy import func
    return [linha[0] for linha in cls.consulta_publicavel().with_entities(
      cls.fabricante).group_by(cls.fabricante).order_by(
      func.count(cls.id).desc(), cls.fabricante).all() if linha[0] and linha[0].strip()]


  @classmethod
  def iterar_para_matching(cls, tamanho_lote=500):
    if type(tamanho_lote) is not int or not 1 <= tamanho_lote <= 1000:
      raise ValueError('Tamanho do lote entre 1 e 1000')
    ultimo_id = 0
    while True:
      lote = cls.query.filter(cls.id > ultimo_id).order_by(cls.id).limit(tamanho_lote).all()
      if not lote:
        return
      ultimo_id = lote[-1].id
      yield from lote

  @classmethod
  def lote_para_identificadores(cls, depois_id=0, limite=100):
    return cls.query.filter(cls.id > depois_id).order_by(cls.id).limit(limite).all()


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
             if coluna.name not in ("criado_em", "atualizado_em", "status_validacao", "validacao_motivo", "validado_em", "fontes_especificacoes", "ficha_montagem_validada")}
    dados["preco"] = float(self.preco) if self.preco is not None else None
    dados["esgotado"] = self.esgotado
    dados["id"] = f"{self.__tablename__}:{self.id}"
    if self.__tablename__ == "cabo_rede":
      dados["categoria_cabo"] = dados.get("categoria")
    dados["categoria"] = self.__tablename__
    dados["link"] = self.kabum_external
    data = self.preco_atualizado_em
    if data and data.tzinfo is None:
      data = data.replace(tzinfo=timezone.utc)
    dados["preco_atualizado_em"] = data.isoformat() if data else None
    dados["ofertas"] = []
    dados["imagem"] = dados.pop("imagem_url", None) or imagem_referencia(dados)
    return completar_medidas(dados)

  def definir_imagem(self, caminho):
    self.imagem_url = caminho
    db.session.commit()

  @classmethod
  def mostrar_pecas(cls):
    return cls.query.all()

  @classmethod
  def aprovar_ids(cls, ids, motivo, validado_em):
    return cls.query.filter(cls.id.in_(ids), cls.status_validacao == "em_revisao").update(
      {"status_validacao": "aprovado", "validacao_motivo": motivo, "validado_em": validado_em},
      synchronize_session=False)

  @classmethod
  def consultar_aprovadas_sem_oferta(cls, motivo):
    from models import Oferta
    com_oferta = db.session.query(Oferta.peca_id).filter(Oferta.tabela_peca == cls.__tablename__)
    return cls.query.filter(cls.status_validacao == "aprovado", cls.validacao_motivo == motivo,
                            ~cls.id.in_(com_oferta))

  @classmethod
  def listar_por_ids(cls, ids):
    return cls.query.filter(cls.id.in_(ids)).all()

  @classmethod
  def iterar_todas(cls, lote=500):
    return cls.query.yield_per(lote)

  @classmethod
  def buscar_por_codigo(cls, codigo):
    return cls.query.filter(db.or_(cls.referencia_interna == codigo, cls.part_number == codigo)).first()

  @classmethod
  def buscar_por_part_number(cls, part_number, fabricante):
    return cls.query.filter_by(part_number=part_number, fabricante=fabricante).first()

  @classmethod
  def listar_por_codigos(cls, codigos):
    return cls.query.filter(db.or_(cls.part_number.in_(codigos), cls.referencia_interna.in_(codigos))).all()

  @classmethod
  def listar_por_link_kabum(cls, url):
    return cls.query.filter(cls.kabum_external == url).all()

  @classmethod
  def listar_disponiveis_ate(cls, preco_maximo: float, limite: int = 30):
    pecas = cls.listar_candidatos_disponiveis(preco_maximo)
    if len(pecas) <= limite:
      return pecas
    return [pecas[indice * (len(pecas) - 1) // (limite - 1)] for indice in range(limite)]


  @classmethod
  def listar_candidatos_disponiveis(cls, preco_maximo):
    return (cls.consulta_para_montagem().filter(cls.preco > 0, cls.preco <= preco_maximo, cls.esgotado.is_(False))
            .order_by(cls.preco.asc(), cls.id.asc()).all())
