from . import db
from . import Peca

class WaterCooler(Peca):
    __tablename__ = "water_cooler"

    compatibilidade = db.Column(db.String(100), nullable=False)
    tamanho_radiador_mm = db.Column(db.Integer(), nullable=False)
    quantidade_fans = db.Column(db.Integer())
    iluminacao = db.Column(db.Boolean(), default=False)