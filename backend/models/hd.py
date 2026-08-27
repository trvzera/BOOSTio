from . import db
from . import Peca

class HD(Peca):
    __tablename__ = "hd"

    capacidade_gb = db.Column(db.Integer(), nullable=False)
    velocidade_rpm = db.Column(db.Integer())
    interface = db.Column(db.String(30))
    memoria_cache_mb = db.Column(db.Integer())