"""MPN revisado sem substituir a referência interna usada por imagens e fichas."""
from decimal import Decimal
from sqlalchemy import inspect
from . import db, ModeloBase
from utils.identidade_peca import assinatura_peca


class IdentidadeFabricante(ModeloBase):
    __tablename__ = 'identidade_fabricante'
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    assinatura_peca = db.Column(db.String(64), nullable=False)
    mpn = db.Column(db.String(255), nullable=False)
    gtin = db.Column(db.String(14), nullable=True)
    fonte = db.Column(db.Text, nullable=False)
    especificacoes = db.Column(db.JSON, nullable=False)
    __table_args__ = (db.UniqueConstraint('tabela_peca', 'peca_id', name='uq_identidade_fabricante_peca'),)

    @classmethod
    def buscar(cls, peca):
        # Compatível com instalações que ainda não fizeram esta migração.
        if not inspect(db.engine).has_table(cls.__tablename__):
            return None
        obj = cls.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id).first()
        if not obj or obj.assinatura_peca != assinatura_peca(peca):
            return None
        if not cls._conferem(peca, obj.especificacoes):
            return None
        return obj

    @classmethod
    def registrar(cls, peca, mpn, fonte, especificacoes, *, simular=True, gtin=None):
        try:
            # Releitura bloqueada protege contra mudança da peça durante a importação.
            db.session.refresh(peca, with_for_update=True)
            if not cls._conferem(peca, especificacoes):
                raise ValueError('Especificações locais divergem da fonte revisada')
            atual = cls.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id).with_for_update().first()
            dados = dict(assinatura_peca=assinatura_peca(peca), mpn=mpn, fonte=fonte, especificacoes=especificacoes, gtin=gtin)
            if atual:
                if any(getattr(atual, k) != v for k, v in dados.items()):
                    raise ValueError('Identidade existente diverge; exige revisão manual')
                return 'inalterada'
            if not simular:
                db.session.add(cls(tabela_peca=peca.__tablename__, peca_id=peca.id, **dados))
                db.session.commit()
            return 'proposta' if simular else 'cadastrada'
        except Exception:
            db.session.rollback()
            raise
        finally:
            # Encerra também transações de leitura e simulações.
            db.session.rollback()

    @staticmethod
    def localizar(modelo, referencia, fabricante, nome):
        return modelo.query.filter_by(part_number=referencia, fabricante=fabricante, modelo=nome).all()

    @staticmethod
    def _conferem(peca, especificacoes):
        for campo, esperado in especificacoes.items():
            atual = getattr(peca, campo, None)
            if isinstance(atual, (Decimal, float, int)) and isinstance(esperado, (float, int)):
                if Decimal(str(int(atual) if isinstance(atual, bool) else atual)) != Decimal(str(int(esperado) if isinstance(esperado, bool) else esperado)):
                    return False
            elif atual != esperado:
                return False
        return True


    @classmethod
    def para_matching(cls, pecas):
        if not pecas or not inspect(db.engine).has_table(cls.__tablename__):
            return {}
        tabela = pecas[0].__tablename__
        locais = {p.id: p for p in pecas}
        registros = cls.query.filter(cls.tabela_peca == tabela, cls.peca_id.in_(locais)).all()
        return {r.peca_id: {'mpn': r.mpn, 'gtin': r.gtin} for r in registros
                if r.assinatura_peca == assinatura_peca(locais[r.peca_id]) and cls._conferem(locais[r.peca_id], r.especificacoes)}
