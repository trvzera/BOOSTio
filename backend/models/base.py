from flask import Flask
from datetime import datetime
from . import db

class ModeloBase(db.Model):
  __abstract__ = True
  id = db.Column(db.Integer,primary_key = True)
  criado_em = db.Column(db.DateTime,default = datetime.now())
