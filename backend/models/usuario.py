from . import db
from .base import ModeloBase
from flask_login import UserMixin

class Usuario(ModeloBase,UserMixin):
  __tablename__ = "usuario"

  nome = db.Column(db.String(30),nullable = False)
  email = db.Column(db.String(150),nullable = False,unique = True)
  senha = db.Column(db.String(100),nullable = True)
  verificado = db.Column(db.Boolean, default=False ,nullable= False)
  ativo = db.Column(db.Boolean, default=True ,nullable= False)
  login_google = db.Column(db.Boolean,default=False,nullable = False)
  google_sub = db.Column(db.String(255), nullable=True, unique=True)
  versao_sessao = db.Column(db.Integer, nullable=False, default=1, server_default="1")
  budget = db.Column(db.Numeric(12, 2), nullable=True)
  usar_budget = db.Column(db.Boolean, default=False, server_default=db.false(), nullable=False)

  @property
  def is_active(self):
    return bool(self.ativo)

  def get_id(self):
    return f"{self.id}:{self.versao_sessao}"

  @staticmethod
  def buscar_por_sessao(identificador: str) -> "Usuario | None":
    if not isinstance(identificador, str):
      return None
    partes = identificador.split(":")
    if len(partes) != 2 or any(not p.isascii() or not p.isdecimal() or len(p) > 18 for p in partes):
      return None
    return Usuario.query.filter_by(
      id=int(partes[0]), versao_sessao=int(partes[1]), ativo=True,
    ).first()

  def to_dict(self, incluir_budget=False) -> dict:
    dados = {
      "id":self.id,
      "nome": self.nome,
      "email": self.email,
      "verificado": self.verificado,
      "criado_em":self.criado_em
    }
    # A listagem geral de usuários não deve expor o orçamento de cada conta.
    if incluir_budget:
      dados.update(budget=float(self.budget) if self.budget is not None else None,
                   usar_budget=bool(self.usar_budget))
    return dados

  def atualizar_dados(self, nome: str | None = None, email: str | None = None, senha: str | None = None,ativo = None) -> None:
    if nome is not None:
      self.nome = nome

    if email is not None:
      self.email = email

    if senha is not None:
      self.senha = senha
      self.versao_sessao = Usuario.versao_sessao + 1

    if ativo is not None:
      self.ativo = ativo
    db.session.commit()

  def atualizar_budget(self, budget, usar_budget: bool) -> None:
    self.budget = budget
    self.usar_budget = usar_budget
    db.session.commit()


  def desativar(self):
    self.email = f"usuario_deletado_{self.id}@removido.local"
    self.senha = ""
    self.ativo = False
    self.versao_sessao = Usuario.versao_sessao + 1
    db.session.commit()

  @staticmethod
  def buscar_por_google_sub(google_sub: str) -> "Usuario | None":
    return Usuario.query.filter_by(google_sub=google_sub).first()

  def vincular_google_legado(self, google_sub: str) -> None:
    atualizados = Usuario.query.filter_by(
      id=self.id, email=self.email, google_sub=None, login_google=True,
      verificado=True, ativo=True, senha=None,
    ).update({Usuario.google_sub: google_sub}, synchronize_session=False)
    if atualizados != 1:
      db.session.rollback()
      raise ValueError("Não foi possível vincular esta conta ao Google")
    db.session.commit()

  @staticmethod
  def buscar_por_email(email:str) -> "Usuario | None":
    usuario = Usuario.query.filter_by(email=email).first()

    return usuario

  @staticmethod
  def listar_todos() -> list["Usuario"]:
    return Usuario.query.all()

  @staticmethod
  def buscar_por_id(id: int | str) -> "Usuario | None":
    return Usuario.query.get(id)


