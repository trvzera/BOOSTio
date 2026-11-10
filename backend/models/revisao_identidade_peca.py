from . import db, ModeloBase


class RevisaoIdentidadePeca(ModeloBase):
    __tablename__ = 'revisao_identidade_peca'
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    assinatura_antes = db.Column(db.String(64), nullable=False)
    assinatura_depois = db.Column(db.String(64), nullable=False)
    campos_antes = db.Column(db.JSON, nullable=False)
    campos_depois = db.Column(db.JSON, nullable=False)
    fonte = db.Column(db.Text, nullable=False)
    criterio = db.Column(db.String(100), nullable=False)
    evidencias = db.Column(db.JSON, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('tabela_peca', 'peca_id', 'assinatura_depois', name='uq_revisao_identidade_destino'),
        db.Index('ix_revisao_identidade_peca', 'tabela_peca', 'peca_id', 'criado_em'),
    )
