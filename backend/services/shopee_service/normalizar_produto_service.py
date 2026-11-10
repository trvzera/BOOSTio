from decimal import Decimal, InvalidOperation
import re
import time
from urllib.parse import urlsplit

from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.conferir_especificacoes_service import extrair_titulo
from services.catalogo_service.comparar_nomes_service import marca as normalizar_marca
from services.catalogo_service.normalizar_produto import nome as normalizar_nome
from utils.url_shopee import validar_url_shopee


_RUIDO = re.compile(
    r'[\U0001F000-\U0001FAFF\u2600-\u27BF\u3010\u3011\u300A\u300B\u2B50]|'
    r'\b(?:frete\s+gr[aá]tis|envio\s+(?:imediato|r[aá]pido|em\s+24\s*h)|pronta\s+entrega|entrega\s+r[aá]pida|'
    r'nota\s+fiscal|nf-?e?|garantia(?:\s+de)?\s+\d+\s*(?:meses|mes|anos?|dias)|100%\s*original|original|lacrad[oa]|'
    r'promo[cç][aã]o|oferta|lan[cç]amento|melhor\s+pre[cç]o|novo|nova)\b', re.I)
_USADO = re.compile(r'\b(?:usad[oa]|seminov[oa]|recondicionad[oa]|open\s*box|vitrine|retirada\s+de\s+pe[cç]as)\b', re.I)


def limpar_titulo(titulo):
    return re.sub(r'\s+', ' ', _RUIDO.sub(' ', titulo)).strip(' -|/,.')


_PREFIXO_CATEGORIA = re.compile(
    r'^(?:mem[oó]ria(?:\s+ram)?|processador|placa\s+de\s+v[ií]deo|placa[\s-]+m[aã]e|ssd|hd|fonte|gabinete|cooler|water\s*cooler|ventoinha|fan|teclado|mouse|monitor|headset|fone)\b[\s:-]*', re.I)


def identificar_marca(titulo, marcas):
    texto = normalizar_nome(titulo)
    achadas = {}
    for original in marcas:
        chave = normalizar_marca(original)
        if chave and re.search(r'(?<!\w)' + re.escape(chave) + r'(?!\w)', texto):
            achadas.setdefault(chave, original)
    finais = {c: o for c, o in achadas.items() if not any(c != d and c in d for d in achadas)}
    return finais


def derivar_modelo(titulo, marca):
    restante = _PREFIXO_CATEGORIA.sub('', titulo)
    restante = re.sub(r'(?<!\w)' + re.escape(marca) + r'(?!\w)', ' ', restante, count=1, flags=re.I)
    restante = re.sub(r'\s+', ' ', restante).strip(' -|/,.:')
    return restante or None


class NormalizarProdutoShopeeService:
    def __init__(self, marcas=()):
        self.marcas = tuple(marcas)
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
        original, titulo = titulo, limpar_titulo(titulo) or titulo
        contexto = {'variantes_nao_resolvidas': self._variantes(titulo, categoria),
                    'titulo_original': original, 'usado': bool(_USADO.search(original))}
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
        marcas = identificar_marca(titulo, self.marcas)
        if len(marcas) > 1:
            contexto['marcas_multiplas'] = True
        marca = next(iter(marcas.values())) if len(marcas) == 1 else None
        modelo = derivar_modelo(titulo, marca) if marca else None
        produto = ProdutoNormalizado(loja='shopee', marca=marca, modelo=modelo, id_externo=f'{shop}:{item}', categoria=categoria,
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
