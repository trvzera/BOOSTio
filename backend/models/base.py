from flask import Flask
from datetime import datetime
from . import db

class ModeloBase(db.Model):
  __abstract__ = True
  id = db.Column(db.Integer,primary_key = True)
  criado_em = db.Column(db.DateTime,default = datetime.now())
  atualizado_em = db.Column( db.DateTime,default=datetime.now,onupdate=datetime.now)

  def salvar(self):
    db.add(self)
    db.session.commit(self)
  
  def deletar(self):
    db.delete(self)
    db.session.commit()

  @staticmethod
  def listar_todos():
    return Professor.query.all()
  
  @staticmethod
  def buscar_por_id(id):
    return Professor.query.get(id)