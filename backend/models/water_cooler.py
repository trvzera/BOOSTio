from . import db
from . import Peca

class WaterCooler(Peca):
    __tablename__ = "water_cooler"

    compatibilidade = db.Column(db.String(100), nullable=True)
    tamanho_radiador_mm = db.Column(db.Integer(), nullable=False)
    quantidade_fans = db.Column(db.Integer())
    iluminacao = db.Column(db.Boolean(), default=False)

    @classmethod
    def listar_candidatos_disponiveis(cls, preco_maximo):
        from utils.sockets import listar_sockets
        return [p for p in super().listar_candidatos_disponiveis(preco_maximo) if listar_sockets(p.compatibilidade)]
