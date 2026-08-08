from . import db
from .base import ModeloBase
from flask_login import UserMixin

class Usuario(ModeloBase,UserMixin):
  __tablename__ = "usuario"

  nome = db.Column(db.String(30),nullable = False)
  email = db.Column(db.String(150),nullable = False,unique = True)
  senha = db.Column(db.String(100),nullable = False)
  
  #Excluir o campo senha para segurança(mesmo com hash é um dado sensível)
  def to_dict(self):
    return {
      "id":self.id,
      "nome": self.nome,
      "email": self.email,
    }

  def atualizar_dados(self,nome=None,email=None,senha=None):
    if nome is not None:
      self.nome = nome

    if email is not None:
      self.email = email
      
    if senha is not None:
      self.senha = senha
    
    db.session.commit()

  @staticmethod
  def buscar_por_email(email:str):
    usuario = Usuario.query.filter_by(email=email).first()

    return usuario

  @staticmethod
  def listar_todos():
    return Usuario.query.all()
  
  @staticmethod
  def buscar_por_id(id):
    return Usuario.query.get(id)



