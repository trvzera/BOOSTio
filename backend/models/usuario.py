from . import db
from .base import ModeloBase
from flask_login import UserMixin

class Usuario(ModeloBase,UserMixin):
  __tablename__ = "usuario"

  nome = db.Column(db.String(30),nullable = False)
  email = db.Column(db.String(150),nullable = False,unique = True)
  senha = db.Column(db.String(100),nullable = False)
  verificado = db.Column(db.Boolean, default=False ,nullable= False)
  ativo = db.Column(db.Boolean, default=False ,nullable= False)


  def to_dict(self) -> dict:
    return {
      "id":self.id,
      "nome": self.nome,
      "email": self.email,
      "verificado": self.verificado,
      "criado_em":self.criado_em
    }

  def atualizar_dados(self, nome: str | None = None, email: str | None = None, senha: str | None = None,ativo = None) -> None:
    if nome is not None:
      self.nome = nome

    if email is not None:
      self.email = email

    if senha is not None:
      self.senha = senha

    if ativo is not None:
      self.ativo = ativo
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


