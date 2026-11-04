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
            from utils.codigos_peca import codigo_interno
            from services.catalogo_service.normalizar_produto import codigo
            from .identificadores_peca import _vinculos, reassinar_vinculos
            if not isinstance(mpn, str) or not mpn.strip() or len(mpn) > 100 or codigo_interno(mpn):
                raise ValueError('Informe um código real do fabricante')
            # Releitura bloqueada protege contra mudança da peça durante a importação.
            db.session.refresh(peca, with_for_update=True)
            if not cls._conferem(peca, especificacoes):
                raise ValueError('Especificações locais divergem da fonte revisada')
            if peca.part_number and not codigo_interno(peca.part_number) and codigo(peca.part_number) != codigo(mpn):
                raise ValueError('Part number existente diverge da fonte revisada')
            antiga, numero = assinatura_peca(peca), peca.part_number
            vinculos = [v for v in _vinculos(peca) if v[0].name == 'vinculo_mercado_livre']
            if codigo_interno(numero):
                peca.referencia_interna = peca.referencia_interna or numero
            peca.part_number = mpn.strip()
            reassinar_vinculos(peca, vinculos, antiga, numero)
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
        return modelo.query.filter(db.or_(modelo.part_number == referencia, modelo.referencia_interna == referencia),
            modelo.fabricante == fabricante, modelo.modelo == nome).all()

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
