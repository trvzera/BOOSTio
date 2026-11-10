"""Associação revisada ou comprovada por MPN, sem duplicar peças."""
from . import db, ModeloBase


class VinculoMercadoLivre(ModeloBase):
    __tablename__ = 'vinculo_mercado_livre'
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    catalogo_id = db.Column(db.String(80), nullable=False, unique=True)
    assinatura_peca = db.Column(db.String(64), nullable=False)
    assinatura_catalogo = db.Column(db.String(64), nullable=False)
    criterio = db.Column(db.String(100), nullable=False)
    especificacoes_revisadas = db.Column(db.JSON, nullable=True)
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

    @classmethod
    def tabela_preparada(cls):
        from sqlalchemy import inspect
        inspetor = inspect(db.engine)
        return (inspetor.has_table(cls.__tablename__) and 'especificacoes_revisadas' in
                {c['name'] for c in inspetor.get_columns(cls.__tablename__)})

    @classmethod
    def aplicar_revisado(cls, peca, catalogo_id, assinatura, assinatura_catalogo, especificacoes, *, simular=True):
        from .identidade_fabricante import IdentidadeFabricante
        from utils.identidade_peca import assinatura_peca
        try:
            db.session.refresh(peca, with_for_update=True)
            if assinatura_peca(peca) != assinatura or not IdentidadeFabricante.conferem(peca, especificacoes):
                raise ValueError('Ficha local mudou ou diverge da revisão')
            existente = cls.buscar(peca.__tablename__, peca.id, bloquear=True)
            if existente:
                if existente.assinatura_peca != assinatura or existente.catalogo_id != catalogo_id or existente.assinatura_catalogo != assinatura_catalogo or (existente.especificacoes_revisadas is not None and existente.especificacoes_revisadas != especificacoes):
                    raise ValueError('Vínculo existente diverge; revisar antes de substituir')
                if existente.especificacoes_revisadas is None:
                    if not simular:
                        existente.especificacoes_revisadas = especificacoes
                        db.session.commit()
                    return 'proposto' if simular else 'cadastrado'
                return 'inalterado'
            outro = cls.query.filter_by(catalogo_id=catalogo_id).first()
            if outro:
                raise ValueError('Catálogo já vinculado a outra peça; revisar duplicidade')
            if not simular:
                db.session.add(cls(tabela_peca=peca.__tablename__, peca_id=peca.id, catalogo_id=catalogo_id,
                    assinatura_peca=assinatura, assinatura_catalogo=assinatura_catalogo, criterio='revisado', especificacoes_revisadas=especificacoes))
                db.session.commit()
            return 'proposto' if simular else 'cadastrado'
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.rollback()

    def especificacoes_compativeis(self, peca):
        from .identidade_fabricante import IdentidadeFabricante
        return self.especificacoes_revisadas is None or IdentidadeFabricante.conferem(peca, self.especificacoes_revisadas)
