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
    def registrar_observacao(cls, consulta, resultado, coletado_em, *, loja, produto_id_loja):
        """Inclui na sessão; o service confirma junto da peça e da tentativa."""
        from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

        if consulta.status != "reservada":
            raise ValueError("A consulta já foi finalizada")
        if type(resultado.get("esgotado")) is not bool:
            raise ValueError("Disponibilidade inválida na cotação")
        preco = resultado.get("preco")
        if preco is None and not resultado["esgotado"]:
            raise ValueError("Produto disponível sem preço na cotação")
        if preco is not None:
            try:
                if isinstance(preco, bool):
                    raise ValueError("Preço inválido na cotação")
                preco = Decimal(str(preco))
                if not preco.is_finite() or not 0 < preco < Decimal("1000000000000"):
                    raise ValueError("Preço inválido na cotação")
                preco = preco.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if not 0 < preco < Decimal("1000000000000"):
                    raise ValueError("Preço fora do intervalo do histórico")
            except InvalidOperation as erro:
                raise ValueError("Preço inválido na cotação") from erro
        if not isinstance(loja, str) or not loja.strip() or len(loja) > 20:
            raise ValueError("Loja da cotação inválida")
        if not isinstance(produto_id_loja, str) or not produto_id_loja.strip() or len(produto_id_loja) > 80:
            raise ValueError("Código do anúncio inválido")
        if type(consulta.id) is not int or consulta.id <= 0:
            raise ValueError("Reserve a consulta antes de registrar a observação")
        if not isinstance(coletado_em, datetime):
            raise ValueError("Data da cotação inválida")
        data = (coletado_em.astimezone(timezone.utc).replace(tzinfo=None)
                if coletado_em.tzinfo else coletado_em)
        # Não assumir que uma segunda resposta para a mesma tentativa é outra coleta.
        if cls.query.filter_by(consulta_id=consulta.id).first() is not None:
            raise ValueError("A consulta já tem uma observação registrada")
        observacao = cls(consulta_id=consulta.id, tabela_peca=consulta.tabela_peca,
                        peca_id=consulta.peca_id, loja=loja, produto_id_loja=produto_id_loja,
                        url=consulta.url, preco=preco, esgotado=resultado["esgotado"], coletado_em=data)
        db.session.add(observacao)
        return observacao

    @classmethod
    def verificar_esquema(cls):
        from sqlalchemy import inspect
        if not inspect(db.engine).has_table(cls.__tablename__):
            raise ValueError("Execute historico-precos-preparar antes de atualizar preços")
