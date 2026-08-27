from . import db
from . import Peca

class Processador(Peca):
    __tablename__ = "processador"

    soquete = db.Column(db.String(100), nullable=False)
    nucleo = db.Column(db.Integer(), nullable=False)
    thread = db.Column(db.Integer(), nullable=False)
    clockbase = db.Column(db.Numeric(), nullable=False)
    clockmax = db.Column(db.Numeric(), nullable=False)
    videointegrado = db.Column(db.Boolean(), default=False)
    modelo_videointegrado = db.Column(db.String(100))
    cooler = db.Column(db.Boolean(), default=False)
    modelo_cooler = db.Column(db.String(100))