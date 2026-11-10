from . import db
from . import Peca

class PlacaMae(Peca):
    __tablename__ = "placa_mae"

    socket = db.Column(db.String(50), nullable=False)
    chipset = db.Column(db.String(50))
    formato = db.Column(db.String(50))
    tipo_memoria = db.Column(db.String(50))
    quantidade_slots_ram = db.Column(db.Integer())
    memoria_maxima_gb = db.Column(db.Integer())
    quantidade_slots_m2 = db.Column(db.Integer())
    @classmethod
    def listar_disponiveis_por_sockets(cls, preco_maximo, sockets, limite_por_socket=24):
        from utils.sockets import normalizar_socket

        grupos = {socket: [] for valor in sockets if (socket := normalizar_socket(valor))}
        if not grupos:
            return grupos
        pecas = (cls.consulta_para_montagem().filter(cls.preco > 0, cls.preco <= preco_maximo, cls.esgotado.is_(False))
                 .order_by(cls.preco.asc(), cls.id.asc()).yield_per(200))
        for peca in pecas:
            socket = normalizar_socket(peca.socket)
            if socket in grupos and len(grupos[socket]) < limite_por_socket:
                grupos[socket].append(peca)
        return grupos
