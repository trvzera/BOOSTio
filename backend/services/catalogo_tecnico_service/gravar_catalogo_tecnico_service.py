from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
from contextlib import contextmanager
from datetime import datetime, timezone
from sqlalchemy import null
from models import db, ControleColeta, FichaTecnicaCatalogo
from utils.identidade_peca import assinatura_documento, assinatura_peca, assinatura_tecnica


class GravarCatalogoTecnicoService:
    @contextmanager
    def transacao(self, *, simular):
        db.session.rollback()
        try:
            if not ControleColeta.bloquear():raise ValueError('Execute catalogo-tecnico-preparar')
            yield
            if simular:db.session.rollback()
            else:db.session.commit()
        except Exception:
            db.session.rollback();raise

    def receber(self, documento):
        f=FichaTecnicaCatalogo.buscar_origem(documento['provedor'],documento['id_externo'],bloquear=True)
        assinatura=assinatura_documento(documento)
        if f is None:
            f=FichaTecnicaCatalogo(provedor=documento['provedor'],id_externo=documento['id_externo'],
                categoria=documento['categoria'],documento=documento,assinatura_documento=assinatura)
            db.session.add(f);db.session.flush()
            return f,'nova'
        if f.estado=='rejeitada':return f,'rejeitada'
        if f.assinatura_documento==assinatura:return f,'igual'
        if f.categoria!=documento['categoria']:raise ValueError('A categoria da origem mudou; revisão manual necessária')
        f.transicionar('em_revisao',motivo='A fonte enviou outra versão da ficha',responsavel='importador')
        f.documento=documento;f.assinatura_documento=assinatura
        return f,'alterada'

    @staticmethod
    def criar_peca(modelo, dados, identidade, fontes, ficha):
        valores={**dados,'part_number':identidade.get('mpn'),'status_validacao':'aprovado',
            'validacao_motivo':'Identidade e ficha técnica validadas, sem presumir oferta',
            'validado_em':datetime.now(timezone.utc).replace(tzinfo=None)}
        # Ausência é NULL explícito: defaults booleanos antigos não viram evidência.
        for c in modelo.__table__.columns:
            if c.nullable and c.default is not None and c.name not in valores:valores[c.name]=null()
        p=modelo(**valores);db.session.add(p);db.session.flush();db.session.refresh(p)
        p.ficha_montagem_validada=not pendencias_para_montagem(p)
        GravarCatalogoTecnicoService.registrar_fontes(p,fontes,identidade,ficha)
        return p

    @staticmethod
    def registrar_fontes(peca,fontes,identidade,ficha):
        agora=datetime.now(timezone.utc).isoformat()
        evidencias=dict(peca.fontes_especificacoes or {})
        for campo,fonte in fontes.items():
            if campo in peca.__table__.columns:
                evidencias.setdefault(campo,{**fonte,'provedor':ficha.provedor,'id_externo':ficha.id_externo,
                    'importado_em':agora,'assinatura_documento':ficha.assinatura_documento})
        evidencias['_identidade_tecnica']=dict(mpn=identidade.get('mpn'),gtin=identidade.get('gtin'),
            assinatura_peca=assinatura_peca(peca),assinatura_tecnica=assinatura_tecnica(peca),
            provedor=ficha.provedor,id_externo=ficha.id_externo,assinatura_documento=ficha.assinatura_documento)
        peca.fontes_especificacoes=evidencias
