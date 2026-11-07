from . import db
from . import Peca

class AirCooler(Peca):
    __tablename__ = "air_cooler"

    compatibilidade = db.Column(db.String(100), nullable=True)
    dimensoes = db.Column(db.Integer(), nullable=True)
    iluminacao = db.Column(db.Boolean(), default=False)

    @classmethod
    def listar_candidatos_disponiveis(cls, preco_maximo):
        """Cooler cujo texto de compatibilidade não lista sockets (ex.: "AMD,Intel") nunca passa na
        conferência de encaixe com a CPU; oferecê-lo à montagem só produz uma build recusada."""
        from utils.sockets import listar_sockets
        return [p for p in super().listar_candidatos_disponiveis(preco_maximo) if listar_sockets(p.compatibilidade)]
