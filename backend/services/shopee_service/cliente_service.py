import hashlib
import json
import os
import time

import requests

from services.marketplace_service.controle_requisicoes_service import executar_requisicao
from services.marketplace_service.erros import FalhaMarketplace


class ClienteShopeeService:
    URL = 'https://open-api.affiliate.shopee.com.br/graphql'
    CAMPOS = '''nodes { itemId shopId productName productLink offerLink
        priceMin priceMax productCatIds periodStartTime periodEndTime }
        pageInfo { page limit hasNextPage }'''

    CAMPOS_IMAGEM = '''nodes { itemId shopId imageUrl } pageInfo { page limit hasNextPage }'''

    def __init__(self, *, app_id=None, secret=None, sessao=None, relogio=time.time):
        self.app_id = app_id if app_id is not None else os.getenv('SHOPEE_APP_ID', '')
        self._secret = secret if secret is not None else os.getenv('SHOPEE_APP_SECRET', '')
        if not self.app_id or not self._secret:
            raise ValueError('Configure SHOPEE_APP_ID e SHOPEE_APP_SECRET')
        self.sessao = sessao or requests.Session()
        self.relogio = relogio

    def buscar(self, termo, *, pagina=1, limite=20):
        if not isinstance(termo, str) or not termo.strip() or len(termo) > 200:
            raise ValueError('Termo de busca inválido')
        if type(pagina) is not int or pagina < 1 or type(limite) is not int or not 1 <= limite <= 50:
            raise ValueError('Paginação inválida')
        argumentos = f'keyword:{json.dumps(termo)},page:{pagina},limit:{limite},sortType:1'
        return self._consultar(argumentos)

    def consultar_anuncio(self, vendedor_id, item_id):
        self._validar_ids(vendedor_id, item_id)
        return self._consultar(f'shopId:{int(vendedor_id)},itemId:{int(item_id)},page:1,limit:1')

    def consultar_imagem(self, vendedor_id, item_id):
        # consulta própria: um campo de imagem recusado não pode derrubar a atualização de preços
        self._validar_ids(vendedor_id, item_id)
        return self._consultar(f'shopId:{int(vendedor_id)},itemId:{int(item_id)},page:1,limit:1', self.CAMPOS_IMAGEM)

    @staticmethod
    def _validar_ids(vendedor_id, item_id):
        for identificador in (vendedor_id, item_id):
            if not str(identificador).isdigit() or not 0 < int(identificador) < 2**63:
                raise ValueError('Identificador Shopee inválido')

    def _consultar(self, argumentos, campos=None):
        payload = json.dumps({'query': '{ productOfferV2(' + argumentos + ') {' + (campos or self.CAMPOS) + '} }'},
                             ensure_ascii=False, separators=(',', ':'))
        return executar_requisicao(lambda: self._enviar(payload), loja='shopee')

    def _enviar(self, payload):
        timestamp = str(int(self.relogio()))
        assinatura = hashlib.sha256((self.app_id + timestamp + payload + self._secret).encode()).hexdigest()
        headers = {'Content-Type': 'application/json', 'Authorization':
                   f'SHA256 Credential={self.app_id}, Timestamp={timestamp}, Signature={assinatura}'}
        try:
            with self.sessao.post(self.URL, data=payload.encode(), headers=headers,
                                  timeout=(10, 30), allow_redirects=False, stream=True) as resposta:
                if resposta.status_code != 200:
                    raise FalhaMarketplace(resposta.status_code, resposta.headers.get('Retry-After'))
                partes, tamanho = [], 0
                for parte in resposta.iter_content(65536):
                    tamanho += len(parte)
                    if tamanho > 2 * 1024 * 1024:
                        raise ValueError('Resposta Shopee excedeu o tamanho permitido')
                    partes.append(parte)
                try:
                    dados = json.loads(b''.join(partes))
                except (ValueError, UnicodeError):
                    raise ValueError('Resposta Shopee não contém JSON válido') from None
                if not isinstance(dados, dict):
                    raise ValueError('Formato de resposta Shopee inválido')
                if dados.get('errors'):
                    self._falha_graphql(dados['errors'], resposta.headers.get('Retry-After'))
                resultado = (dados.get('data') or {}).get('productOfferV2')
                if not isinstance(resultado, dict) or not isinstance(resultado.get('nodes'), list):
                    raise ValueError('Ofertas ausentes na resposta Shopee')
                pagina = resultado.get('pageInfo')
                if not isinstance(pagina, dict) or type(pagina.get('hasNextPage')) is not bool:
                    raise ValueError('Paginação ausente na resposta Shopee')
                return resultado
        except requests.RequestException:
            raise FalhaMarketplace(temporaria=True) from None

    @staticmethod
    def _falha_graphql(erros, retry_after):
        codigos = {str(e.get('extensions', {}).get('code')) for e in erros if isinstance(e, dict)}
        if codigos & {'10020', '10031', '10032', '10033', '10034', '10035', '11002'}:
            raise FalhaMarketplace(403)
        if '10030' in codigos:
            raise FalhaMarketplace(429, retry_after)
        if '10000' in codigos:
            raise FalhaMarketplace(500)
        raise FalhaMarketplace(400)
