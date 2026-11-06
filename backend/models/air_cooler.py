from . import db
from . import Peca

class AirCooler(Peca):
    __tablename__ = "air_cooler"

    compatibilidade = db.Column(db.String(100), nullable=True)
    dimensoes = db.Column(db.Integer(), nullable=True)
    iluminacao = db.Column(db.Boolean(), default=False)