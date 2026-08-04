from . import db
from .base import ModeloBase

class Usuario(ModeloBase):
  __tablename__ = "usuarios"

  nome = db.Column(db.String(30),nullable = False)
  email = db.Column(db.String(150),nullable = False,unique = True)
  senha = db.Column(db.String(100),nullable = False)
  
  @staticmethod
  def buscar_por_email(email:str):
    usuario = Usuario.query.filter_by(email=email).first()

    return usuario

  #Excluir o campo senha para segurança(mesmo com hash é um dado sensível)
  def to_dict(self):
    return {
      "id":self.senha,
      "nome": self.nome,
      "email": self.email,
    }

  @staticmethod
  def listar_todos():
    return Usuario.query.all()
  
  @staticmethod
  def buscar_por_id(id):
    return Usuario.query.get(id)



