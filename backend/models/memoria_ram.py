from . import db
from . import Peca

class MemoriaRAM(Peca):
    __tablename__ = "memoria_ram"

    capacidade_gb = db.Column(db.Integer(), nullable=False)
    ddr = db.Column(db.String(20), nullable=False)  
    frequencia_mhz = db.Column(db.Integer(), nullable=False)
    formato = db.Column(db.String(20), nullable=True)
    latencia = db.Column(db.String(20))  
    quantidade_pentes = db.Column(db.Integer(), nullable=False)
    iluminacao = db.Column(db.Boolean(), default=False)
    @classmethod
    def listar_disponiveis_por_ddrs(cls, preco_maximo, ddrs, limite_por_ddr=24):
        from utils.memorias import normalizar_ddr

        grupos = {ddr: [] for valor in ddrs if (ddr := normalizar_ddr(valor))}
        if not grupos:
            return grupos
        pecas = (cls.consulta_para_montagem().filter(cls.preco > 0, cls.preco <= preco_maximo, cls.esgotado.is_(False))
                 .order_by(cls.preco.asc(), cls.id.asc()).yield_per(200))
        for peca in pecas:
            ddr = normalizar_ddr(peca.ddr)
            if ddr in grupos and len(grupos[ddr]) < limite_por_ddr:
                grupos[ddr].append(peca)
        return grupos
