from . import db
from . import ModeloBase

class Perifericos(ModeloBase):
    __abstract__ = True

    fabricante = db.Column(db.String(100), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    conexao = db.Column(db.String(100), nullable=False)
    iluminacao = db.Column(db.Boolean(), default=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    