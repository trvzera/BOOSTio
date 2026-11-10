from services.marketplace_service.gravar_ofertas_service import aplicar_lote_mercado_livre
from services.marketplace_service.gravar_ofertas_service import aplicar_ofertas_loja
from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
"""Unidade de trabalho por anúncio, reaproveitando o bloqueio de coleta."""
from contextlib import contextmanager
from datetime import datetime, timezone
from sqlalchemy import null
from models import db, ProdutoPendente, ControleColeta, Oferta, IdentidadeFabricante
from utils.identidade_peca import assinatura_peca


class GravarImportacaoCatalogoService:
    @contextmanager
    def transacao(self, pendencia_id, *, simular):
        try:
            db.session.rollback()
            if not ControleColeta.bloquear():
                raise ValueError('Prepare o controle de coleta antes de importar')
            p = ProdutoPendente.buscar_por_id_com_trava(pendencia_id)
            if p is None or p.status == 'rejeitado':
                raise ValueError('Pendência ausente ou rejeitada')
            yield p
            if simular:db.session.rollback()
            else:
                from services.marketplace_service.controle_requisicoes_service import verificar_execucao
                verificar_execucao()
                db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def criar_componente(self, modelo, ficha):
        dados={**ficha['dados'],'part_number':ficha.get('identidade',{}).get('mpn'),'status_validacao':'aprovado',
               'validacao_motivo':'Identidade e ficha estruturada verificadas na importação',
               'validado_em':datetime.now(timezone.utc).replace(tzinfo=None)}
        for c in modelo.__table__.columns:
            if c.nullable and c.default is not None and c.name not in dados and c.name!='atualizado_em':
                dados[c.name]=null()
        dados.update(ficha.get('benchmark',{}).get('dados',{}))
        if ficha.get('benchmark',{}).get('dados'):
            dados['benchmark_atualizado_em']=datetime.now(timezone.utc).replace(tzinfo=None)
        dados['fontes_especificacoes']=ficha.get('fontes',{})
        peca=modelo(**{k:v for k,v in dados.items() if k not in modelo.CAMPOS_DA_OFERTA});db.session.add(peca);db.session.flush();db.session.refresh(peca)
        peca.ficha_montagem_validada=not pendencias_para_montagem(peca)
        if ficha.get('icecat',{}).get('status')=='encontrada':
            from utils.identidade_peca import assinatura_tecnica
            peca.fontes_especificacoes={**(peca.fontes_especificacoes or {}), '_identidade_tecnica':dict(
                **ficha['identidade'],assinatura_peca=assinatura_peca(peca),assinatura_tecnica=assinatura_tecnica(peca),
                provedor='Icecat',id_externo=ficha['referencia_icecat'])}
        if ficha.get('identidade',{}).get('mpn'):
            db.session.add(IdentidadeFabricante(tabela_peca=modelo.__tablename__,peca_id=peca.id,
                assinatura_peca=assinatura_peca(peca),mpn=ficha['identidade']['mpn'],gtin=ficha['identidade'].get('gtin'),
                fonte=ficha['fonte_identidade'],especificacoes={k:v for k,v in ficha['dados'].items() if k not in ('preco','esgotado')}))
            db.session.flush()
        return peca

    def concluir(self, pendencia, peca, ficha, anuncio, propostas, agora, decisao=None):
        oferta=Oferta.buscar_unica_por_anuncio(pendencia.loja,anuncio['produto_id_loja'])
        pendencia.oferta_id=oferta.id;pendencia.status='importado';pendencia.revisado_em=agora
        pendencia.motivo='Importação validada e concluída'
        import json
        pendencia.evidencias={**(pendencia.evidencias or {}),
            'enriquecimento':json.loads(json.dumps(ficha,default=str)),
            'importacao':dict(peca=f'{peca.__tablename__}:{peca.id}',oferta_id=oferta.id,
                origem=pendencia.loja,catalogo_id=ficha['produto'].get('id'),coletado_em=agora.isoformat(),resultado=propostas,associacao=decisao)}
        if pendencia.loja == 'shopee':
            from utils.identidade_peca import assinatura_tecnica
            pendencia.evidencias = {**pendencia.evidencias, 'vinculo': {
                'assinatura_peca': assinatura_peca(peca), 'assinatura_tecnica': assinatura_tecnica(peca)}}


    def registrar_revisao(self, pendencia, ficha, motivo=None):
        import json
        pendencia.evidencias={**(pendencia.evidencias or {}),'enriquecimento':json.loads(json.dumps(ficha,default=str))}
        pendencia.status='em_revisao'
        pendencia.motivo=motivo or 'Novo componente não autorizado, ficha incompleta ou conflitante'


    def registrar_oferta(self,pendencia,peca,ficha,anuncio,criterio,agora):
        if pendencia.loja=='mercado_livre':
            return aplicar_lote_mercado_livre(peca,ficha['produto']['id'],assinatura_peca(peca),
                ficha['assinatura_catalogo'],criterio,[anuncio],agora,simular=False,confirmar=False,desativar_ausentes=False)
        return aplicar_ofertas_loja(peca,pendencia.loja,[anuncio],agora)


    def validar_referencia(self,pendencia,peca,ficha):
        existente=Oferta.buscar_por_anuncio(pendencia.loja,pendencia.produto_id_loja,bloquear=True)
        if existente and (peca is None or existente.tabela_peca!=peca.__tablename__ or existente.peca_id!=peca.id):
            return 'Anúncio já associado a outra peça; avaliar'
        if pendencia.loja=='mercado_livre':
            from models import VinculoMercadoLivre
            catalogo=ficha['produto']['id']
            vinculado=VinculoMercadoLivre.buscar_por_catalogo(catalogo,bloquear=True)
            if vinculado and (peca is None or vinculado.tabela_peca!=peca.__tablename__ or vinculado.peca_id!=peca.id):
                return 'Produto de catálogo já vinculado; avaliar ficha local'
            if peca is not None:
                atual=VinculoMercadoLivre.buscar(peca.__tablename__,peca.id,bloquear=True)
                if atual and atual.catalogo_id!=catalogo:return 'Outro produto de catálogo já vinculado à peça; avaliar'
        return None
