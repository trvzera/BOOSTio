from . import db
from . import Peca

class PlacaMae(Peca):
    __tablename__ = "placa_mae"

    socket = db.Column(db.String(50), nullable=False)
    chipset = db.Column(db.String(50))
    formato = db.Column(db.String(50))
    tipo_memoria = db.Column(db.String(50))
    quantidade_slots_ram = db.Column(db.Integer())
    memoria_maxima_gb = db.Column(db.Integer())
    quantidade_slots_m2 = db.Column(db.Integer())