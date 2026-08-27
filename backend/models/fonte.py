from . import db
from . import Peca

class Fonte(Peca):
    __tablename__ = "fonte" 

    potencia_w = db.Column(db.Integer(), nullable=False)
    formato = db.Column(db.String(50))