from . import db
from . import Periferico

class Monitor(Periferico):
    __tablename__ = "monitor"

    tamanho_polegadas = db.Column(db.Numeric(4, 1), nullable=False)
    resolucao = db.Column(db.String(20), nullable=False)
    taxa_atualizacao_hz = db.Column(db.Integer(), nullable=False)
    tipo_painel = db.Column(db.String(20))
    tempo_resposta_ms = db.Column(db.Numeric(4, 1))
    hdr = db.Column(db.Boolean(), default=False)