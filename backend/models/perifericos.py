from . import db
from . import Peca

class Periferico(Peca):
    __abstract__ = True

    conexao = db.Column(db.String(100), nullable=False)
    iluminacao = db.Column(db.Boolean(), default=False)
