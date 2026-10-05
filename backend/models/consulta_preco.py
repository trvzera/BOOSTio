from . import db, ModeloBase


class ConsultaPreco(ModeloBase):
    """Uma tentativa reservada antes da rede; falhas também contam no orçamento."""

    __tablename__ = "consulta_preco"
    loja = db.Column(db.String(10), nullable=False)
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    url = db.Column(db.Text, nullable=False)
    dia = db.Column(db.String(10), nullable=False, index=True)
    mes = db.Column(db.String(7), nullable=False, index=True)
    usa_brightdata = db.Column(db.Boolean, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="reservada")
    snapshot_id = db.Column(db.String(100))
    erro = db.Column(db.String(300))


class ControleColeta(db.Model):
    """Linha única usada para serializar reservas concorrentes no banco."""

    __tablename__ = "controle_coleta"
    id = db.Column(db.Integer, primary_key=True)
    versao = db.Column(db.Integer, nullable=False, default=0)
