from . import db
from . import Peca

class MemoriaRAM(Peca):
    __tablename__ = "memoria_ram"

    capacidade_gb = db.Column(db.Integer(), nullable=False)
    ddr = db.Column(db.String(20), nullable=False)  
    frequencia_mhz = db.Column(db.Integer(), nullable=False)
    latencia = db.Column(db.String(20))  
    quantidade_pentes = db.Column(db.Integer(), nullable=False)
    iluminacao = db.Column(db.Boolean(), default=False)