"""Cotações observadas em BRL; registros anteriores não são sobrescritos pela coleta."""
from datetime import datetime, timezone

from . import db, ModeloBase


class HistoricoPreco(ModeloBase):
    __tablename__ = "historico_preco"

    consulta_id = db.Column(
        db.Integer, db.ForeignKey("consulta_preco.id", ondelete="RESTRICT"),
        nullable=False, unique=True,
    )
    # Referência polimórfica, seguindo ConsultaPreco: o ID pertence à tabela indicada.
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    loja = db.Column(db.String(20), nullable=False)
    produto_id_loja = db.Column(db.String(80), nullable=False)
    url = db.Column(db.Text, nullable=False)
    preco = db.Column(db.Numeric(14, 2), nullable=True)
    esgotado = db.Column(db.Boolean, nullable=False, default=False)
    # UTC sem tzinfo, como as cotações atuais do projeto no SQLite/MySQL.
    coletado_em = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    __table_args__ = (
        db.CheckConstraint("preco IS NULL OR preco > 0", name="ck_historico_preco_preco_positivo"),
        db.CheckConstraint("esgotado = 1 OR preco IS NOT NULL", name="ck_historico_preco_disponivel_com_preco"),
        db.Index("ix_historico_preco_peca_anuncio_data", "tabela_peca", "peca_id", "loja", "produto_id_loja", "coletado_em"),
    )


    @classmethod
    def verificar_esquema(cls):
        from sqlalchemy import inspect
        if not inspect(db.engine).has_table(cls.__tablename__):
            raise ValueError("Execute historico-precos-preparar antes de atualizar preços")

