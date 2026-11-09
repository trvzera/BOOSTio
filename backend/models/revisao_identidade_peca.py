"""Auditoria de conversões explícitas de referências genéricas em SKUs comerciais."""
from . import db, ModeloBase
from utils.identidade_peca import assinatura_peca, assinatura_tecnica


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

    @classmethod
    def aplicar(cls, peca, proposta, *, simular=True):
        from repositories.identificadores_peca_repository import _vinculos
        from . import Oferta
        try:
            db.session.refresh(peca, with_for_update=True)
            if assinatura_tecnica(peca) != proposta['assinatura_tecnica']:
                raise ValueError('Peça mudou; revise novamente')
            from .medidas_fisicas import produto_kabum
            codigo = produto_kabum(proposta['fonte'])
            if (not codigo or codigo != produto_kabum(peca.kabum_external)
                    or not Oferta.corresponde_origem(peca, 'kabum', codigo, bloquear=True)):
                raise ValueError('Oferta original mudou ou não foi comprovada')
            if _vinculos(peca) or Oferta.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id, loja='mercado_livre').first():
                raise ValueError('Peça já possui identidade ou oferta externa; exige revisão do vínculo')
            campos = proposta['dados']
            permitidos = {'fabricante','modelo','fabricante_chip','modelo_referencia','codigo_modelo_fabricante','tipo_memoria'}
            if not campos or set(campos)-permitidos or peca.__tablename__ != 'placa_video':
                raise ValueError('Campos ou categoria não autorizados para a conversão')
            from services.catalogo_service.normalizar_produto import variante
            if (campos.get('fabricante_chip') != peca.fabricante or campos.get('modelo_referencia') != peca.modelo
                    or variante('placa_video', campos.get('modelo','')) != variante('placa_video', peca.modelo)):
                raise ValueError('Referência ou chip mudou durante a conversão')
            for campo, valor in campos.items():
                limite = getattr(peca.__table__.columns[campo].type, 'length', None)
                if not isinstance(valor,str) or not valor.strip() or limite and len(valor)>limite:
                    raise ValueError('Identidade comercial inválida')
            antes = {k:getattr(peca,k) for k in campos}
            assinatura = assinatura_peca(peca)
            for campo, valor in campos.items():
                setattr(peca,campo,valor)
            fontes = dict(peca.fontes_especificacoes or {})
            for campo, origem in proposta['fontes'].items():
                fontes[campo] = {**origem, 'valor':getattr(peca,campo), 'assinatura_peca':assinatura_peca(peca),
                    'criterio':'anuncio_original_e_especificacoes_compativeis',
                    'sha256_especificacoes':proposta['sha256'], 'titulo_origem':proposta['titulo_origem']}
            peca.fontes_especificacoes = fontes
            registro = cls(tabela_peca=peca.__tablename__,peca_id=peca.id,assinatura_antes=assinatura,
                assinatura_depois=assinatura_peca(peca),campos_antes=antes,campos_depois=campos,
                fonte=proposta['fonte'],criterio='mesmo_chip_e_memoria_anuncio_original',evidencias=proposta['evidencias'])
            db.session.add(registro)
            resultado = dict(status='proposta' if simular else 'convertida',peca=f'{peca.__tablename__}:{peca.id}',
                             antes=antes,depois=campos,fonte=proposta['fonte'])
            if simular:db.session.rollback()
            else:db.session.commit()
            return resultado
        except Exception:
            db.session.rollback()
            raise
