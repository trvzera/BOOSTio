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
        if not inspect(db.session.connection()).has_table(cls.__tablename__):
            return None
        obj = cls.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id).first()
        if not obj or obj.assinatura_peca != assinatura_peca(peca):
            return None
        if not cls.conferem(peca, obj.especificacoes):
            return None
        return obj

    @classmethod
    def buscar_com_trava(cls, peca):
        return cls.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id).with_for_update().first()

    @classmethod
    def listar_das_pecas(cls, tabela, ids):
        return cls.query.filter(cls.tabela_peca == tabela, cls.peca_id.in_(ids)).all()

    @staticmethod
    def localizar(modelo, referencia, fabricante, nome):
        return modelo.query.filter(db.or_(modelo.part_number == referencia, modelo.referencia_interna == referencia),
            modelo.fabricante == fabricante, modelo.modelo == nome).all()

    @staticmethod
    def conferem(peca, especificacoes):
        for campo, esperado in especificacoes.items():
            atual = getattr(peca, campo, None)
            if isinstance(atual, (Decimal, float, int)) and isinstance(esperado, (float, int)):
                if Decimal(str(int(atual) if isinstance(atual, bool) else atual)) != Decimal(str(int(esperado) if isinstance(esperado, bool) else esperado)):
                    return False
            elif atual != esperado:
                return False
        return True
