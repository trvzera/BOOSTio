from sqlalchemy.exc import SQLAlchemyError
from models import ProdutoPendente
from utils.identidade_peca import assinatura_documento
from .enriquecer_produto_service import EnriquecerProdutoService
from .buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from .token_mercado_livre_service import TokenMercadoLivreService
from .controle_requisicoes_service import ControleRequisicoesService, ErroMercadoLivre, OrcamentoRequisicoesEsgotado


class EnriquecerPendenciasService:
    def __init__(self, cliente=None, tokens=None, enriquecedor=None, controle=None):
        self.controle=controle;self.cliente=cliente;self.tokens=tokens;self.enriquecedor=enriquecedor or EnriquecerProdutoService()

    def executar(self, *, limite=20, depois_id=0, max_requisicoes=30, intervalo=1.0, simular=True):
        controle=self.controle or ControleRequisicoesService(max_requisicoes,intervalo)
        cliente=self.cliente or BuscarOfertasMercadoLivreService(controle)
        resumo=dict(simulacao=simular,completas=0,revisao=0,falhas=0,requisicoes=0,interrompido=False,detalhes=[])
        for p in ProdutoPendente.listar_para_revisao(depois_id,limite):
            try:
                bruto=p.dados_originais
                identificador=(bruto.get('catalogo') or {}).get('id') or (bruto.get('anuncio') or {}).get('catalog_product_id')
                cliente._validar_id(identificador,'catálogo')
                token=(self.tokens or TokenMercadoLivreService()).executar()
                produto=cliente._consultar('/products/'+identificador,token)
                if produto.get('id')!=identificador:raise ValueError('Catálogo divergente')
                r=self.enriquecedor.executar(p.categoria_sugerida,produto,bruto.get('anuncio') or {})
                ProdutoPendente.registrar_enriquecimento(p.id,r,assinatura_documento(bruto),simular=simular)
                resumo['completas' if r['pronto'] else 'revisao']+=1
                resumo['detalhes'].append(dict(pendencia_id=p.id,pronto=r['pronto'],campos_pendentes=r['campos_pendentes'],conflitos=r['conflitos']))
            except (ValueError,OSError,SQLAlchemyError) as erro:
                resumo['falhas']+=1
                resumo['detalhes'].append(dict(pendencia_id=p.id,erro='Falha ao consultar ou validar ficha técnica',http=erro.status if isinstance(erro,ErroMercadoLivre) else None))
                if isinstance(erro,(ErroMercadoLivre,OrcamentoRequisicoesEsgotado,SQLAlchemyError)):
                    resumo['interrompido']=True;break
        resumo['requisicoes']=controle.total
        return resumo
