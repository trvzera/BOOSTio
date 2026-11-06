"""Não transforma uma faixa de variantes numa cotação de uma peça individual."""
from decimal import Decimal, InvalidOperation
import re
import time
from urllib.parse import urlsplit

from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.conferir_especificacoes_service import extrair_titulo


def validar_url_shopee(url, *, afiliado=False):
    try:
        partes = urlsplit(url)
        hosts = {'shopee.com.br', 'www.shopee.com.br'}
        if afiliado:
            hosts |= {'s.shopee.com.br', 'shope.ee'}
        return (partes.scheme == 'https' and partes.hostname in hosts
                and not partes.username and not partes.password and partes.port in (None, 443))
    except (ValueError, TypeError):
        return False


class NormalizarProdutoShopeeService:
    CATEGORIAS_OBSERVADAS = {'processador': 101950, 'placa_mae': 101951,
                            'placa_video': 101952, 'memoria_ram': 101955}
    def executar(self, anuncio, categoria):
        if not isinstance(anuncio, dict):
            raise ValueError('Anúncio Shopee inválido')
        shop, item = str(anuncio.get('shopId', '')), str(anuncio.get('itemId', ''))
        if not all(v.isdigit() and 0 < int(v) < 2**63 for v in (shop, item)):
            raise ValueError('Identidade Shopee inválida')
        titulo = anuncio.get('productName')
        if not isinstance(titulo, str) or not titulo.strip() or len(titulo) > 255:
            raise ValueError('Título Shopee inválido')
        url = anuncio.get('productLink')
        if not validar_url_shopee(url) or urlsplit(url).path != f'/product/{shop}/{item}':
            raise ValueError('Link Shopee diverge do anúncio')
        contexto = {'variantes_nao_resolvidas': self._variantes(titulo, categoria)}
        # Categorias observadas na API oficial. Demais categorias permanecem
        # não confirmadas até existir evidência, nunca inferidas do termo buscado.
        confirmada = self.CATEGORIAS_OBSERVADAS.get(categoria) in anuncio.get('productCatIds', [])
        contexto['variantes_nao_resolvidas'] |= bool(re.search(
            r'\b(organizador|adaptador|conversor|suporte|reposição|reposicao)\b', titulo, re.I))
        agora = time.time()
        inicio, fim = anuncio.get('periodStartTime'), anuncio.get('periodEndTime')
        ativo = (type(inicio) is int and type(fim) is int and inicio <= agora < fim)
        try:
            minimo, maximo = Decimal(str(anuncio.get('priceMin'))), Decimal(str(anuncio.get('priceMax')))
            if not all(v.is_finite() and 0 < v <= Decimal('999999999999.99') and v.quantize(Decimal('.01')) == v for v in (minimo, maximo)):
                raise ValueError('Preço Shopee inválido')
            contexto['variantes_nao_resolvidas'] |= minimo != maximo
        except InvalidOperation:
            raise ValueError('Preço Shopee inválido') from None
        produto = ProdutoNormalizado(loja='shopee', id_externo=f'{shop}:{item}', categoria=categoria,
            titulo=titulo, especificacoes=extrair_titulo(categoria, titulo), ativo=ativo,
            categoria_confirmada=confirmada, fonte=url, contexto=contexto)
        oferta = dict(produto_id_loja=produto.id_externo, vendedor_id=shop, url=url,
                      preco=minimo, esgotado=None)
        link = anuncio.get('offerLink')
        if link and validar_url_shopee(link, afiliado=True):
            oferta['url_afiliado'] = link
        return produto, oferta

    @staticmethod
    def _variantes(titulo, categoria):
        if categoria == 'processador':
            modelos = re.findall(r'\b\d{4,5}(?:x3d|[a-z]{0,3})\b', titulo, re.I)
            return len({v.lower() for v in modelos}) > 1
        return bool(re.search(r'\b(?:opções|opcoes|selecione|escolha|variantes)\b', titulo, re.I))
