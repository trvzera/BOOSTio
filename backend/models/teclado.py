from . import db
from . import Periferico

class Teclado(Periferico):
    __tablename__ = "teclado"

    layout = db.Column(db.String(20), nullable=False)
    switch = db.Column(db.String(50))
    mecanico = db.Column(db.Boolean(), default=False)
    tamanho = db.Column(db.String(20))