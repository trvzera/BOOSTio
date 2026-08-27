from . import db
from . import Peca

class PlacaVideo(Peca):
    __tablename__ = "placa_video"

    memoria_gb = db.Column(db.Integer(), nullable=False)
    tipo_memoria = db.Column(db.String(20))
    interface_memoria = db.Column(db.String(20))
    consumo_w = db.Column(db.Integer())
    quantidade_fans = db.Column(db.Integer())
    conectores_energia = db.Column(db.String(50))