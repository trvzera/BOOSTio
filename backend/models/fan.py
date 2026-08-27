from . import db
from . import Peca

class Fan(Peca):
    __tablename__ = "fan"

    tamanho_mm = db.Column(db.Integer(), nullable=False)
    quantidade = db.Column(db.Integer(), nullable=False)
    iluminacao = db.Column(db.Boolean(), default=False)