from . import db, Peca


class PlacaRede(Peca):
    __tablename__ = "adaptador_wifi"

    interface = db.Column(db.String(20), nullable=False)
    padrao_wifi = db.Column(db.String(20), nullable=False)
    velocidade_mbps = db.Column(db.Integer, nullable=True)
    bluetooth = db.Column(db.Boolean, nullable=True, default=False)
