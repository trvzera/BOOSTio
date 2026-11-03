"""Anúncio de uma loja vinculado a uma peça; valores monetários em BRL."""
from . import db, ModeloBase


class Oferta(ModeloBase):
    __tablename__ = "oferta"

    # Peca é abstrato; o vínculo segue a referência usada por ConsultaPreco.
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    loja = db.Column(db.String(20), nullable=False)
    produto_id_loja = db.Column(db.String(80), nullable=False)
    # Vazio identifica venda direta. Em marketplace, informar o ID do vendedor.
    # Não usar NULL na identidade: índices únicos permitem vários NULLs.
    vendedor_id = db.Column(db.String(80), nullable=False, default="")
    vendedor_nome = db.Column(db.String(120), nullable=True)
    # Endereço original do anúncio para consultar preço e disponibilidade.
    url = db.Column(db.Text, nullable=False)
    # Link de divulgação; permanece None enquanto não houver afiliação configurada.
    url_afiliado = db.Column(db.Text, nullable=True, default=None)

    preco = db.Column(db.Numeric(14, 2), nullable=True)
    condicao_pagamento = db.Column(db.String(120), nullable=True)
    # NULL: disponibilidade ainda desconhecida; não assumir estoque sem coleta.
    esgotado = db.Column(db.Boolean, nullable=True)
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    # UTC sem tzinfo, seguindo as datas de cotação do projeto.
    preco_atualizado_em = db.Column(db.DateTime, nullable=True)
    consultado_em = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("loja", "produto_id_loja", "vendedor_id", name="uq_oferta_loja_produto_vendedor"),
        db.CheckConstraint("peca_id > 0", name="ck_oferta_peca_positiva"),
        db.CheckConstraint("preco IS NULL OR preco > 0", name="ck_oferta_preco_positivo"),
        db.CheckConstraint("esgotado IS NULL OR esgotado = 1 OR preco IS NOT NULL", name="ck_oferta_disponivel_com_preco"),
        db.Index("ix_oferta_peca", "tabela_peca", "peca_id"),
        db.Index("ix_oferta_coleta", "loja", "ativa", "consultado_em"),
    )
