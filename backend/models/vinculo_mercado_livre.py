"""Associação revisada ou comprovada por MPN, sem duplicar peças."""
from . import db, ModeloBase


class VinculoMercadoLivre(ModeloBase):
    __tablename__ = 'vinculo_mercado_livre'
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    catalogo_id = db.Column(db.String(80), nullable=False, unique=True)
    assinatura_peca = db.Column(db.String(64), nullable=False)
    assinatura_catalogo = db.Column(db.String(64), nullable=False)
    criterio = db.Column(db.String(20), nullable=False)
    __table_args__ = (db.UniqueConstraint('tabela_peca', 'peca_id', name='uq_vinculo_ml_peca'),)

    @classmethod
    def buscar(cls, tabela, peca_id, *, bloquear=False):
        consulta = cls.query.filter_by(tabela_peca=tabela, peca_id=peca_id)
        if bloquear:
            consulta = consulta.populate_existing().with_for_update()
        return consulta.first()


    @classmethod
    def registrar_revisado(cls, peca, catalogo_id, assinatura, assinatura_catalogo):
        try:
            existente = cls.buscar(peca.__tablename__, peca.id)
            if existente:
                raise ValueError('A peça já tem vínculo; revise o registro existente antes de substituir')
            obj = cls(tabela_peca=peca.__tablename__, peca_id=peca.id, catalogo_id=catalogo_id,
                      assinatura_peca=assinatura, assinatura_catalogo=assinatura_catalogo, criterio='revisado')
            db.session.add(obj)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
