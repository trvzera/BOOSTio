from . import db
from . import Periferico

class Fone(Periferico):
    __tablename__ = "fone"

    tipo = db.Column(db.String(20))
    microfone = db.Column(db.Boolean(), default=False)
    cancelamento_ruido = db.Column(db.Boolean(), default=False)
    resposta_frequencia = db.Column(db.String(50))