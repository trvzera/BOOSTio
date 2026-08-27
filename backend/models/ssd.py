from . import db
from . import Peca

class SSD(Peca):
    __tablename__ = "ssd"

    capacidade_gb = db.Column(db.Integer(), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    interface = db.Column(db.String(30), nullable=False)
    formato = db.Column(db.String(30))
    velocidade_leitura_mbps = db.Column(db.Integer())
    velocidade_gravacao_mbps = db.Column(db.Integer())