from . import db
from . import Peca

class Periferico(Peca):
    __abstract__ = True

    conexao = db.Column(db.String(100), nullable=True)
    iluminacao = db.Column(db.Boolean(), default=False)
