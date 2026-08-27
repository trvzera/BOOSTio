from . import db
from . import Peca

class Gabinete(Peca):
    __tablename__ = "gabinete"

    formato = db.Column(db.String(50), nullable=False)
    formatos_placa_mae = db.Column(db.String(100), nullable=False)
    slots_expansao = db.Column(db.Integer())
    bays_disco = db.Column(db.Integer())
    fans_inclusos = db.Column(db.Integer())
    suporte_water_cooler = db.Column(db.Boolean(), default=False)
    tamanho_max_gpu_mm = db.Column(db.Integer())
    tamanho_max_cooler_mm = db.Column(db.Integer())
    painel_vidro = db.Column(db.Boolean(), default=False)