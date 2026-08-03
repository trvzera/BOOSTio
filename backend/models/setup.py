from . import db
from . import ModeloBase

class Setup(ModeloBase):
  titulo = db.Column(db.String(30))
  
