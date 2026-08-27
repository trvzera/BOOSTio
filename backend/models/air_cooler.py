from . import db
from . import Peca

class AirCooler(Peca):
    __tablename__ = "aircooler"

    compatibilidade = db.Column(db.String(100), nullable=False)
    dimensoes = db.Column(db.Integer(), nullable=False)
    iluminacao = db.Column(db.Boolean(), default=False)