"""Observações de marketplace; disponibilidade não informada permanece NULL."""
from . import db, ModeloBase


class HistoricoOferta(ModeloBase):
    __tablename__ = 'historico_oferta'
    oferta_id = db.Column(db.Integer, db.ForeignKey('oferta.id', ondelete='RESTRICT'), nullable=False)
    preco = db.Column(db.Numeric(14, 2), nullable=False)
    esgotado = db.Column(db.Boolean, nullable=True)
    coletado_em = db.Column(db.DateTime, nullable=False)
    __table_args__ = (
        db.CheckConstraint('preco > 0', name='ck_historico_oferta_preco'),
        db.Index('ix_historico_oferta_data', 'oferta_id', 'coletado_em'),
    )

    @classmethod
    def ultimo(cls, oferta_id, *, bloquear=False):
        consulta = cls.query.filter_by(oferta_id=oferta_id).order_by(cls.coletado_em.desc(), cls.id.desc())
        if bloquear:
            consulta = consulta.populate_existing().with_for_update()
        return consulta.first()

    @classmethod
    def listar(cls, oferta_id, limite=1000):
        return cls.query.filter_by(oferta_id=oferta_id).order_by(
            cls.coletado_em.desc(), cls.id.desc()).limit(limite + 1).all()
