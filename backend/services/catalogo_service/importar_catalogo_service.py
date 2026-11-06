"""Importação reutilizável. A consulta externa pertence ao adaptador de cada loja."""
from datetime import datetime, timezone
from repositories.importacao_catalogo_repository import RepositorioImportacaoCatalogo
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_documento
from .indice_candidatos_service import IndiceCandidatosService
from .validar_ficha_tecnica_service import ValidarFichaTecnicaService


class ImportarCatalogoService:
    def __init__(self,repositorio=None,verificar_execucao=None):
        self.repositorio=repositorio or RepositorioImportacaoCatalogo()
        self.verificar_execucao=verificar_execucao or (lambda:None)

    def executar(self,pendencia_id,produto,ficha,anuncio,assinatura_original,*,simular=True,permitir_novos=False):
        modelos={m.__tablename__:m for m in MODELOS_PECAS};categoria=produto.categoria
        if categoria not in modelos:raise ValueError('Categoria não suportada')
        agora=datetime.now(timezone.utc).replace(tzinfo=None);self.verificar_execucao()
        with self.repositorio.transacao(pendencia_id,simular=simular) as atual:
            if atual.status=='importado':return dict(acao='inalterada',pendencia_id=atual.id,oferta_id=atual.oferta_id)
            if atual.loja!=produto.loja or atual.categoria_sugerida!=categoria or assinatura_documento(atual.dados_originais)!=assinatura_original:
                raise ValueError('Pendência mudou durante a consulta')
            indice=IndiceCandidatosService.carregar(modelos[categoria])
            pool=indice.pecas
            decisao=indice.avaliar(produto)
            if decisao['classificacao']=='ambigua':
                motivo='Pontuação entre 60 e 80, candidatos próximos ou busca incompleta; avaliar'
                if not simular:self.repositorio.registrar_revisao(atual,ficha,motivo)
                return dict(acao='revisao',pendencia_id=atual.id,percentual=decisao['percentual'],motivo=motivo)
            if ficha.get('conflitos'):
                if not simular:self.repositorio.registrar_revisao(atual,ficha,'Fontes técnicas contraditórias; avaliar')
                return dict(acao='revisao',pendencia_id=atual.id,percentual=decisao['percentual'],conflitos=ficha['conflitos'])
            novo=decisao['classificacao']=='rejeitada'
            if novo and ficha.get('fabricante_oficial',{}).get('status') in ('pendente','revisao'):
                if not simular:self.repositorio.registrar_revisao(atual,ficha,'Fonte oficial pendente ou conflitante')
                return dict(acao='revisao',pendencia_id=atual.id,motivo='Fonte oficial pendente ou conflitante')
            if (novo and ficha.get('icecat', {}).get('status') in ('ambigua', 'revisao')
                    and ficha.get('fabricante_oficial',{}).get('status')!='encontrada'):
                motivo = 'Ficha Icecat ambígua ou divergente; revisar antes de criar a peça'
                if not simular:
                    self.repositorio.registrar_revisao(atual, ficha, motivo)
                return dict(acao='revisao', pendencia_id=atual.id, percentual=decisao['percentual'], motivo=motivo)
            if novo:
                validacao = ValidarFichaTecnicaService().executar(
                    categoria, ficha['dados'], produto, ficha.get('identidade'), fontes=ficha.get('fontes', {}),
                    finalidade='catalogo' if (ficha.get('icecat', {}).get('status')=='encontrada' or ficha.get('fabricante_oficial',{}).get('status')=='encontrada') else 'comercial')
            if novo and (not permitir_novos or not ficha.get('pronto') or not validacao['pronto']):
                if not simular:self.repositorio.registrar_revisao(atual,ficha,'Abaixo de 60: sem associação; ficha insuficiente para novo cadastro')
                return dict(acao='revisao',pendencia_id=atual.id,percentual=decisao['percentual'],campos_pendentes=validacao['campos_pendentes'],conflitos=validacao['conflitos'])
            peca=next((p for p in pool if f'{p.__tablename__}:{p.id}'==decisao['peca']),None)
            motivo=self.repositorio.validar_referencia(atual,peca,ficha)
            if motivo:
                if not simular:self.repositorio.registrar_revisao(atual,ficha,motivo)
                return dict(acao='revisao',pendencia_id=atual.id,percentual=decisao['percentual'],motivo=motivo)
            if not novo and not peca.publicavel:
                if not simular:self.repositorio.registrar_revisao(atual,ficha,'Ficha local ainda não aprovada')
                return dict(acao='revisao',pendencia_id=atual.id,percentual=decisao['percentual'])
            if simular:return dict(acao='proposta',pendencia_id=atual.id,novo_componente=novo,percentual=decisao['percentual'],peca=None if novo else decisao['peca'],preco=str(anuncio['preco']))
            if novo and not ficha.get('fonte_identidade'):
                ficha={**ficha,'fonte_identidade':produto.fonte or ficha.get('fontes',{}).get('modelo',{}).get('url')}
            if novo:peca=self.repositorio.criar_componente(modelos[categoria],ficha)
            criterio=decisao['criterio'] if not novo else validacao['comparacao']['criterio']
            propostas=self.repositorio.registrar_oferta(atual,peca,ficha,anuncio,criterio,agora)
            self.repositorio.concluir(atual,peca,ficha,anuncio,propostas,agora,decisao={k:v for k,v in decisao.items() if k!='candidatos'})
            return dict(acao='importada',pendencia_id=atual.id,novo_componente=novo,percentual=decisao['percentual'],criterio=criterio,peca=f'{peca.__tablename__}:{peca.id}',ofertas=propostas)
