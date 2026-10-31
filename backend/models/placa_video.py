from . import db
from . import Peca
from .benchmark import BenchmarkMixin

class PlacaVideo(BenchmarkMixin, Peca):
    __tablename__ = "placa_video"

    memoria_gb = db.Column(db.Integer(), nullable=False)
    tipo_memoria = db.Column(db.String(20))
    interface_memoria = db.Column(db.String(20))
    consumo_w = db.Column(db.Integer())
    quantidade_fans = db.Column(db.Integer())
    conectores_energia = db.Column(db.String(50))
    benchmark_g2d = db.Column(db.Numeric(14, 2), nullable=True)
    benchmark_g3d = db.Column(db.Numeric(14, 2), nullable=True)
