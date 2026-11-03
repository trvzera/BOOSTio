"""Unidade de trabalho por anúncio, reaproveitando o bloqueio de coleta."""
from contextlib import contextmanager
from datetime import datetime, timezone
from sqlalchemy import null
from models import db, ProdutoPendente, ControleColeta, Oferta, IdentidadeFabricante
from utils.identidade_peca import assinatura_peca


class RepositorioImportacaoCatalogo:
    @contextmanager
    def transacao(self, pendencia_id, *, simular):
        try:
            # Encerra o snapshot de leitura anterior à rede (REPEATABLE READ no MySQL).
            db.session.rollback()
            if not ControleColeta.bloquear():
                raise ValueError('Prepare o controle de coleta antes de importar')
            p = ProdutoPendente.query.filter_by(id=pendencia_id).populate_existing().with_for_update().first()
            if p is None or p.status == 'rejeitado':
                raise ValueError('Pendência ausente ou rejeitada')
            yield p
            if simular:db.session.rollback()
            else:db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def criar_componente(self, modelo, ficha):
        dados={**ficha['dados'],'part_number':ficha['identidade']['mpn'],'status_validacao':'aprovado',
               'validacao_motivo':'Identidade e ficha estruturada verificadas na importação',
               'validado_em':datetime.now(timezone.utc).replace(tzinfo=None)}
        # Um default False não é evidência. NULL explícito mantém campos opcionais desconhecidos.
        for c in modelo.__table__.columns:
            if c.nullable and c.default is not None and c.name not in dados and c.name!='atualizado_em':
                dados[c.name]=null()
        dados.update(ficha['benchmark']['dados'])
        if ficha['benchmark']['dados']:
            dados['benchmark_atualizado_em']=datetime.now(timezone.utc).replace(tzinfo=None)
        peca=modelo(**dados);db.session.add(peca);db.session.flush()
        db.session.add(IdentidadeFabricante(tabela_peca=modelo.__tablename__,peca_id=peca.id,
            assinatura_peca=assinatura_peca(peca),mpn=ficha['identidade']['mpn'],gtin=ficha['identidade']['gtin'],
            fonte=f"https://api.mercadolibre.com/products/{ficha['produto']['id']}",especificacoes={k:v for k,v in ficha['dados'].items() if k not in ('preco','esgotado')}))
        db.session.flush()
        return peca

    def concluir(self, pendencia, peca, ficha, anuncio, propostas, agora):
        oferta=Oferta.query.filter_by(loja='mercado_livre',produto_id_loja=anuncio['produto_id_loja']).one()
        pendencia.oferta_id=oferta.id;pendencia.status='importado';pendencia.revisado_em=agora
        pendencia.motivo='Importação validada e concluída'
        # Evidência e resultado são confirmados na mesma transação da peça/oferta/histórico.
        import json
        pendencia.evidencias={**(pendencia.evidencias or {}),
            'enriquecimento':json.loads(json.dumps(ficha,default=str)),
            'importacao':dict(peca=f'{peca.__tablename__}:{peca.id}',oferta_id=oferta.id,
                origem='mercado_livre',catalogo_id=ficha['produto']['id'],coletado_em=agora.isoformat(),resultado=propostas)}


    def registrar_revisao(self, pendencia, ficha):
        import json
        pendencia.evidencias={**(pendencia.evidencias or {}),'enriquecimento':json.loads(json.dumps(ficha,default=str))}
        pendencia.status='em_revisao'
        pendencia.motivo='Novo componente não autorizado, ficha incompleta ou conflitante'
