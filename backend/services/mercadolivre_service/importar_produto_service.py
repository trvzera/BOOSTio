"""Consulta antes da transação; revalida duplicados sob bloqueio e importa atomicamente."""
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from models import ProdutoPendente, IdentidadeFabricante, Oferta
from repositories.importacao_catalogo_repository import RepositorioImportacaoCatalogo
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_peca, assinatura_catalogo, assinatura_documento
from .comparar_produtos_service import CompararProdutosService
from .enriquecer_produto_service import EnriquecerProdutoService
from .buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from .token_mercado_livre_service import TokenMercadoLivreService
from .controle_requisicoes_service import ControleRequisicoesService, ErroMercadoLivre, OrcamentoRequisicoesEsgotado


class ImportarProdutoService:
    def __init__(self, cliente=None, tokens=None, controle=None, enriquecedor=None, repositorio=None, verificar_execucao=None):
        self.controle=controle or ControleRequisicoesService(50,1.0)
        self.cliente=cliente or BuscarOfertasMercadoLivreService(self.controle)
        self.tokens=tokens;self.enriquecedor=enriquecedor or EnriquecerProdutoService()
        self.repositorio=repositorio or RepositorioImportacaoCatalogo()
        self.verificar_execucao=verificar_execucao or (lambda: None)

    def executar(self, pendencia_id, *, simular=True, permitir_novos=False):
        if type(pendencia_id) is not int or pendencia_id<1 or type(simular) is not bool or type(permitir_novos) is not bool:
            raise ValueError('Opções de importação inválidas')
        p=ProdutoPendente.buscar_por_id(pendencia_id)
        if p is None or p.loja!='mercado_livre' or p.status=='rejeitado':
            raise ValueError('Pendência ausente, rejeitada ou de loja não suportada')
        if p.status=='importado':return dict(acao='inalterada',pendencia_id=p.id,oferta_id=p.oferta_id)
        modelos={m.__tablename__:m for m in MODELOS_PECAS}
        if p.categoria_sugerida not in modelos:raise ValueError('Categoria precisa de revisão')
        categoria=p.categoria_sugerida;bruto=p.dados_originais;assinatura=assinatura_documento(bruto)
        catalogo=(bruto.get('catalogo') or {}).get('id') or (bruto.get('anuncio') or {}).get('catalog_product_id')
        self.cliente._validar_id(catalogo,'catálogo')
        token=(self.tokens or TokenMercadoLivreService()).executar()
        produto=self.cliente._consultar('/products/'+catalogo,token)
        if produto.get('id')!=catalogo:raise ValueError('Catálogo retornado diverge')
        resultado=self.cliente.executar(catalogo,access_token=token,produto=produto)
        ofertas=[a for a in resultado['ofertas'] if a['produto_id_loja']==p.produto_id_loja and a['condicao']=='new']
        if len(ofertas)!=1:raise ValueError('Anúncio não está mais disponível como oferta nova no catálogo')
        anuncio=ofertas[0]
        if p.vendedor_id is not None and p.vendedor_id!=anuncio['vendedor_id']:
            raise ValueError('Vendedor mudou desde a descoberta')
        # Somente preço e estoque atuais; nunca reutilizar a cotação antiga da descoberta.
        entrada={'price':anuncio['preco'],'available_quantity':anuncio.get('quantidade_disponivel')}
        if (bruto.get('anuncio') or {}).get('title'):entrada['title']=bruto['anuncio']['title']
        ficha=self.enriquecedor.executar(categoria,produto,entrada)
        agora=datetime.now(timezone.utc).replace(tzinfo=None)
        self.verificar_execucao()
        with self.repositorio.transacao(pendencia_id,simular=simular) as atual:
            if atual.status=='importado':return dict(acao='inalterada',pendencia_id=atual.id,oferta_id=atual.oferta_id)
            if atual.categoria_sugerida!=categoria or assinatura_documento(atual.dados_originais)!=assinatura:
                raise ValueError('Pendência mudou durante a consulta')
            pool=modelos[categoria].pool_para_matching(2001)
            decisao=CompararProdutosService().selecionar(pool[:2000],produto,
                identidades=IdentidadeFabricante.para_matching(pool[:2000]),completo=len(pool)<=2000)
            if decisao['classificacao']=='ambigua':
                motivo='Vários candidatos ou evidências insuficientes; revisão necessária'
                if not simular:self.repositorio.registrar_revisao(atual,ficha,motivo)
                return dict(acao='revisao',pendencia_id=atual.id,motivo=motivo)
            novo=decisao['classificacao']!='confirmada'
            if novo and (not permitir_novos or not ficha['pronto']):
                if not simular:self.repositorio.registrar_revisao(atual,ficha)
                return dict(acao='revisao',pendencia_id=atual.id,campos_pendentes=ficha['campos_pendentes'],conflitos=ficha['conflitos'])
            peca=next((a for a in pool if f'{a.__tablename__}:{a.id}'==decisao['peca']),None)
            if not novo and (not peca.publicavel or CompararProdutosService().avaliar(peca,{**produto,'name':entrada.get('title',produto.get('name'))},identidade=IdentidadeFabricante.para_matching([peca]).get(peca.id))['classificacao']!='confirmada'):
                motivo='Ficha local não publicada ou título divergente'
                if not simular:self.repositorio.registrar_revisao(atual,ficha,motivo)
                return dict(acao='revisao',pendencia_id=atual.id,motivo=motivo)
            if simular:
                return dict(acao='proposta',novo_componente=novo,pendencia_id=atual.id,peca=None if novo else decisao['peca'],preco=str(anuncio['preco']))
            if novo:peca=self.repositorio.criar_componente(modelos[categoria],ficha)
            propostas=Oferta.aplicar_lote_mercado_livre(peca,catalogo,assinatura_peca(peca),assinatura_catalogo(produto),
                'mpn' if 'mpn' in CompararProdutosService().avaliar(peca,produto,identidade=ficha['identidade'])['evidencias'] else 'gtin',
                [anuncio],agora,simular=False,confirmar=False,desativar_ausentes=False)
            self.repositorio.concluir(atual,peca,ficha,anuncio,propostas,agora)
            return dict(acao='importada',novo_componente=novo,pendencia_id=atual.id,peca=f'{peca.__tablename__}:{peca.id}',ofertas=propostas)

    def executar_lote(self, *, limite=20, depois_id=0, categoria=None, simular=True, permitir_novos=False):
        ids=[p.id for p in ProdutoPendente.listar_para_revisao(depois_id,limite,categoria)]
        resumo=dict(simulacao=simular,importadas=0,propostas=0,inalteradas=0,revisao=0,falhas=0,interrompido=False,detalhes=[])
        for identificador in ids:
            try:
                r=self.executar(identificador,simular=simular,permitir_novos=permitir_novos)
                resumo[{'importada':'importadas','proposta':'propostas','inalterada':'inalteradas','revisao':'revisao'}[r['acao']]]+=1
                resumo['detalhes'].append(r)
            except (ValueError,SQLAlchemyError) as erro:
                resumo['falhas']+=1
                try:ProdutoPendente.registrar_falha_importacao(identificador,simular=simular)
                except SQLAlchemyError:resumo['interrompido']=True
                resumo['detalhes'].append(dict(pendencia_id=identificador,erro='Importação não confirmada; revise identidade, ficha ou persistência',http=erro.status if isinstance(erro,ErroMercadoLivre) else None))
                if isinstance(erro,(ErroMercadoLivre,OrcamentoRequisicoesEsgotado,SQLAlchemyError)):
                    resumo['interrompido']=True;break
        resumo['requisicoes']=self.controle.total
        return resumo
