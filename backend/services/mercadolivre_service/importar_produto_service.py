"""Consulta antes da transação; revalida duplicados sob bloqueio e importa atomicamente."""
from services.icecat_service.obter_ficha_icecat_service import ErroConsultaIcecat
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from models import db, ProdutoPendente, IdentidadeFabricante, Oferta
from repositories.importacao_catalogo_repository import RepositorioImportacaoCatalogo
from models.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_peca, assinatura_catalogo, assinatura_documento
from .comparar_produtos_service import CompararProdutosService
from .enriquecer_produto_service import EnriquecerProdutoService
from .buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from .token_mercado_livre_service import TokenMercadoLivreService
from .controle_requisicoes_service import ControleRequisicoesService, ErroMercadoLivre, OrcamentoRequisicoesEsgotado


class ImportarProdutoService:
    def __init__(self, cliente=None, tokens=None, controle=None, enriquecedor=None, repositorio=None, verificar_execucao=None, base_icecat=None, fabricantes=None):
        self.controle=controle or ControleRequisicoesService(50,1.0)
        self.cliente=cliente or BuscarOfertasMercadoLivreService(self.controle)
        self.tokens=tokens;self.enriquecedor=enriquecedor or EnriquecerProdutoService()
        from services.icecat_service.completar_ficha_icecat_service import CompletarFichaIcecatService
        from services.fabricante_service.completar_ficha_service import CompletarFichaFabricanteService
        self.fabricantes=fabricantes if fabricantes is not None else CompletarFichaFabricanteService.configurado()
        self.base_icecat=base_icecat if base_icecat is not None else CompletarFichaIcecatService.configurado()
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
        produto,anuncio=self._consultar_anuncio(p)
        # Somente preço e estoque atuais; nunca reutilizar a cotação antiga da descoberta.
        entrada={'price':anuncio['preco'],'available_quantity':anuncio.get('quantidade_disponivel')}
        if (bruto.get('anuncio') or {}).get('title'):entrada['title']=bruto['anuncio']['title']
        ficha=self.enriquecedor.executar(categoria,produto,entrada)
        from services.catalogo_service.importar_catalogo_service import ImportarCatalogoService
        from .normalizar_produto_service import NormalizarProdutoService
        from services.catalogo_service.produto_normalizado import ProdutoNormalizado
        normalizado=ProdutoNormalizado(**ficha['normalizado']) if ficha.get('normalizado') else NormalizarProdutoService().executar(produto,categoria)
        if entrada.get('title'):
            from dataclasses import replace
            normalizado=replace(normalizado,titulo=entrada['title'])
        if permitir_novos and (self.base_icecat is not None or self.fabricantes is not None):
            from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
            decisao=IndiceCandidatosService.carregar(modelos[categoria]).avaliar(normalizado)
            # Uma ficha técnica também pode resolver lacunas de uma associação
            # ambígua. A decisão é refeita sob bloqueio depois do enriquecimento.
            if decisao['classificacao']!='confirmada':
                if self.base_icecat is not None:
                    normalizado,ficha=self.base_icecat.executar(normalizado,ficha)
                if self.fabricantes is not None and not ficha.get('pronto'):
                    normalizado,ficha=self.fabricantes.executar(normalizado,ficha)
        resultado_importacao=ImportarCatalogoService(self.repositorio,self.verificar_execucao).executar(
            pendencia_id,normalizado,ficha,anuncio,assinatura,simular=simular,permitir_novos=permitir_novos)
        if ficha.get('icecat'):
            resultado_importacao['icecat']=ficha['icecat']
        if ficha.get('fabricante_oficial'):
            resultado_importacao['fabricante_oficial']=ficha['fabricante_oficial']
        return resultado_importacao

    def _consultar_anuncio(self,p):
        """Rede antes da transação: catálogo atual e o anúncio como oferta nova do mesmo vendedor."""
        bruto=p.dados_originais
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
        return produto,anuncio

    def aceitar_revisado(self,pendencia_id,peca,revisao):
        """Associação decidida por uma pessoa: a decisão automática não é refeita, mas o anúncio é
        reconsultado e a gravação (trava, vínculo do catálogo, posse do anúncio e histórico) é a mesma."""
        p=ProdutoPendente.buscar_por_id(pendencia_id)
        if p is None or p.loja!='mercado_livre':raise ValueError('Pendência ausente ou de outra loja')
        if p.status not in ('pendente','em_revisao'):raise ValueError('Esta pendência já foi decidida')
        assinatura_original=assinatura_documento(p.dados_originais);assinatura_da_peca=assinatura_peca(peca)
        produto,anuncio=self._consultar_anuncio(p)
        ficha={'produto':{'id':produto['id']},'assinatura_catalogo':assinatura_catalogo(produto)}
        with self.repositorio.transacao(pendencia_id,simular=False) as atual:
            if atual.status not in ('pendente','em_revisao') or assinatura_documento(atual.dados_originais)!=assinatura_original:
                raise ValueError('A pendência mudou durante a consulta; abra de novo')
            db.session.refresh(peca,with_for_update=True)
            if assinatura_peca(peca)!=assinatura_da_peca or not peca.publicavel:
                raise ValueError('A peça mudou durante a consulta; abra de novo')
            agora=datetime.now(timezone.utc).replace(tzinfo=None)
            propostas=self.repositorio.registrar_oferta(atual,peca,ficha,anuncio,'revisao_manual',agora)
            self.repositorio.concluir(atual,peca,ficha,anuncio,propostas,agora)
            atual.motivo='Associação aprovada por um administrador'
            atual.evidencias={**(atual.evidencias or {}),'revisao_manual':revisao}
        return propostas

    def executar_lote(self, *, limite=20, depois_id=0, categoria=None, simular=True, permitir_novos=False):
        ids=[p.id for p in ProdutoPendente.listar_para_revisao(depois_id,limite,categoria)]
        resumo=dict(simulacao=simular,importadas=0,propostas=0,inalteradas=0,revisao=0,falhas=0,interrompido=False,detalhes=[])
        for identificador in ids:
            try:
                r=self.executar(identificador,simular=simular,permitir_novos=permitir_novos)
                resumo[{'importada':'importadas','proposta':'propostas','inalterada':'inalteradas','revisao':'revisao'}[r['acao']]]+=1
                resumo['detalhes'].append(r)
            except (ValueError,OSError,SQLAlchemyError) as erro:
                resumo['falhas']+=1
                try:ProdutoPendente.registrar_falha_importacao(identificador,simular=simular)
                except SQLAlchemyError:resumo['interrompido']=True
                resumo['detalhes'].append(dict(pendencia_id=identificador,erro='Importação não confirmada; revise identidade, ficha ou persistência',http=erro.status if isinstance(erro,(ErroMercadoLivre,ErroConsultaIcecat)) else None,
                    origem='icecat' if isinstance(erro,ErroConsultaIcecat) else 'importacao'))
                if isinstance(erro,(ErroMercadoLivre,OrcamentoRequisicoesEsgotado,SQLAlchemyError,ErroConsultaIcecat)):
                    resumo['interrompido']=True;break
        resumo['requisicoes']=self.controle.total
        if self.base_icecat is not None:
            resumo['requisicoes_icecat']=self.base_icecat.fichas.requisicoes
        if self.fabricantes is not None:
            resumo['requisicoes_fabricantes']=self.fabricantes.paginas.requisicoes
        return resumo
