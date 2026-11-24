import csv
import gzip
import io
import os
from decimal import Decimal, InvalidOperation

import requests

from services.marketplace_service.erros import FalhaMarketplace
from utils.url_gigantec import validar_url_gigantec

LIMITE_BYTES = 100 * 1024 * 1024


class FeedGigantecService:
    """Lê o feed de produtos da Gigantec na Awin (CSV, com ou sem gzip) e devolve os itens válidos por id da loja.
    A URL leva a chave da conta, por isso fica só no ambiente e nunca entra em mensagem de erro."""

    def __init__(self, url=None, *, arquivo=None, sessao=None):
        self.arquivo = arquivo
        self._url = url if url is not None else os.getenv('GIGANTEC_FEED_URL', '')
        self.sessao = sessao or requests.Session()
        if not arquivo and not self._url:
            raise ValueError('Configure GIGANTEC_FEED_URL')

    def itens(self):
        conteudo = self._ler_arquivo() if self.arquivo else self._baixar()
        if conteudo[:2] == b'\x1f\x8b':
            try:
                conteudo = gzip.GzipFile(fileobj=io.BytesIO(conteudo)).read(LIMITE_BYTES + 1)
            except (OSError, EOFError):
                raise ValueError('Feed da Gigantec com compactação inválida') from None
            if len(conteudo) > LIMITE_BYTES:
                raise ValueError('Feed da Gigantec excedeu o tamanho permitido')
        try:
            leitor = csv.DictReader(io.StringIO(conteudo.decode('utf-8-sig'), newline=''))
            if not {'merchant_product_id', 'product_name', 'search_price', 'aw_deep_link', 'merchant_deep_link'} <= set(leitor.fieldnames or ()):
                raise ValueError('Feed da Gigantec sem as colunas esperadas')
            itens = {}
            for linha in leitor:
                item = self._item(linha)
                if item:
                    itens[item['id']] = item
        except (UnicodeError, csv.Error):
            raise ValueError('Feed da Gigantec não é um CSV válido') from None
        return itens

    def _ler_arquivo(self):
        with open(self.arquivo, 'rb') as origem:
            return origem.read(LIMITE_BYTES + 1)

    def _baixar(self):
        try:
            with self.sessao.get(self._url, timeout=(10, 120), stream=True) as resposta:
                if resposta.status_code != 200:
                    raise FalhaMarketplace(resposta.status_code, resposta.headers.get('Retry-After'))
                partes, tamanho = [], 0
                for parte in resposta.iter_content(65536):
                    tamanho += len(parte)
                    if tamanho > LIMITE_BYTES:
                        raise ValueError('Feed da Gigantec excedeu o tamanho permitido')
                    partes.append(parte)
                return b''.join(partes)
        except requests.RequestException:
            raise FalhaMarketplace() from None

    @staticmethod
    def _item(linha):
        ident = (linha.get('merchant_product_id') or '').strip()
        if not ident.isdigit() or len(ident) > 80 or not (linha.get('product_name') or '').strip():
            return None
        try:
            preco = Decimal(str(linha.get('search_price')).strip())
        except InvalidOperation:
            return None
        if not preco.is_finite() or not 0 < preco <= Decimal('999999999999.99'):
            return None
        url, afiliado = linha['merchant_deep_link'].strip(), linha['aw_deep_link'].strip()
        if not validar_url_gigantec(url) or not validar_url_gigantec(afiliado, afiliado=True):
            return None
        return {'id': ident, 'titulo': linha['product_name'].strip(), 'marca': (linha.get('brand_name') or '').strip() or None,
                'mpn': (linha.get('mpn') or '').strip() or None, 'preco': preco.quantize(Decimal('.01')),
                'disponivel': (linha.get('in_stock') or '').strip() == '1', 'url': url, 'url_afiliado': afiliado}
