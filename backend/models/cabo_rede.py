from . import db, Peca


class CaboRede(Peca):
    __tablename__ = "cabo_rede"

    categoria = db.Column(db.String(10), nullable=False)
    comprimento_m = db.Column(db.Float, nullable=False)
    conector = db.Column(db.String(20), nullable=False, default="RJ45")
