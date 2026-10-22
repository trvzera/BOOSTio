from . import db
from . import Peca
import re

class Fan(Peca):
    __tablename__ = "fan"

    tamanho_mm = db.Column(db.Integer(), nullable=False)
    quantidade = db.Column(db.Integer(), nullable=False)
    iluminacao = db.Column(db.Boolean(), default=False)

    def to_catalogo(self):
        dados = super().to_catalogo()
        if "fluxo_ar" not in dados and re.search(r"\b(reverse|reversa|reverso)\b", self.modelo or "", re.I):
            dados.update(fluxo_ar="reverso", fonte_fluxo_ar="nome_comercial")
        return dados
