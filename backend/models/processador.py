from . import db
from . import Peca
from .benchmark import BenchmarkMixin

class Processador(BenchmarkMixin, Peca):
    __tablename__ = "processador"
    BENCHMARK_CAMPO = "benchmark_multi_core"
    BENCHMARK_TESTE = "PassMark CPU Mark / Single Thread"

    soquete = db.Column(db.String(100), nullable=True)
    nucleo = db.Column(db.Integer(), nullable=False)
    thread = db.Column(db.Integer(), nullable=True)
    clockbase = db.Column(db.Numeric(), nullable=False)
    clockmax = db.Column(db.Numeric(), nullable=True)
    videointegrado = db.Column(db.Boolean(), default=False)
    modelo_videointegrado = db.Column(db.String(100))
    cooler = db.Column(db.Boolean(), default=False)
    modelo_cooler = db.Column(db.String(100))
    benchmark_multi_core = db.Column(db.Numeric(14, 2), nullable=True)
    benchmark_single_thread = db.Column(db.Numeric(14, 2), nullable=True)
