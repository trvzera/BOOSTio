"""Fachada compatível: converte dados Mercado Livre e chama o núcleo comum."""
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
from .normalizar_produto_service import NormalizarProdutoService, DOMINIOS


class CompararProdutosService:
    def avaliar(self,peca,produto,*,identidade=None):
        normalizado=NormalizarProdutoService().executar(produto,peca.__tablename__)
        return AssociacaoInteligenteService().avaliar(peca,normalizado,identidade=identidade)

    def selecionar(self,pecas,produto,*,identidades=None,completo=True):
        categoria=pecas[0].__tablename__ if pecas else None
        normalizado=NormalizarProdutoService().executar(produto,categoria)
        return AssociacaoInteligenteService().selecionar(pecas,normalizado,identidades=identidades,completo=completo)
