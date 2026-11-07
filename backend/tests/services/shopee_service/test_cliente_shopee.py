import hashlib
import json
from contextlib import contextmanager

import pytest
import requests

from services.marketplace_service.erros import FalhaMarketplace
from services.shopee_service.cliente_service import ClienteShopeeService


class Resposta:
    def __init__(self, corpo, status=200, headers=None):
        self.status_code, self.headers = status, headers or {}
        self._corpo = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode()

    def iter_content(self, tamanho):
        yield self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Sessao:
    def __init__(self, resposta):
        self.resposta, self.chamadas = resposta, []

    def post(self, url, **kwargs):
        self.chamadas.append((url, kwargs))
        if isinstance(self.resposta, Exception):
            raise self.resposta
        return self.resposta


OK = {'data': {'productOfferV2': {'nodes': [], 'pageInfo': {'page': 1, 'limit': 20, 'hasNextPage': False}}}}


def cliente(resposta):
    sessao = Sessao(resposta)
    return ClienteShopeeService(app_id='123', secret='segredo', sessao=sessao, relogio=lambda: 1700000000), sessao


def test_exige_credenciais(monkeypatch):
    monkeypatch.delenv('SHOPEE_APP_ID', raising=False)
    monkeypatch.delenv('SHOPEE_APP_SECRET', raising=False)
    with pytest.raises(ValueError, match='SHOPEE_APP_ID'):
        ClienteShopeeService()


def test_assina_a_requisicao_e_nao_segue_redirecionamento():
    c, sessao = cliente(Resposta(OK))
    assert c.buscar('Ryzen 5 5500')['pageInfo']['hasNextPage'] is False
    url, kw = sessao.chamadas[0]
    payload = kw['data'].decode()
    assinatura = hashlib.sha256(('123' + '1700000000' + payload + 'segredo').encode()).hexdigest()
    assert kw['headers']['Authorization'] == f'SHA256 Credential=123, Timestamp=1700000000, Signature={assinatura}'
    assert kw['allow_redirects'] is False and 'segredo' not in payload and url.startswith('https://open-api.affiliate.shopee.com.br/')


@pytest.mark.parametrize('termo', ['', '   ', 'x' * 201, None])
def test_recusa_busca_invalida(termo):
    c, sessao = cliente(Resposta(OK))
    with pytest.raises(ValueError):
        c.buscar(termo)
    assert sessao.chamadas == []


@pytest.mark.parametrize('pagina,limite', [(0, 20), (1, 0), (1, 51), (True, 20)])
def test_recusa_paginacao_invalida(pagina, limite):
    c, _ = cliente(Resposta(OK))
    with pytest.raises(ValueError):
        c.buscar('SSD', pagina=pagina, limite=limite)


@pytest.mark.parametrize('codigo,status', [('10020', 403), ('10030', 429), ('10000', 500), ('99999', 400)])
def test_traduz_erros_graphql(codigo, status):
    c, _ = cliente(Resposta({'errors': [{'extensions': {'code': codigo}}]}))
    with pytest.raises(FalhaMarketplace) as erro:
        c.buscar('SSD')
    assert erro.value.status == status


def test_http_diferente_de_200_e_resposta_invalida():
    c, _ = cliente(Resposta({}, status=503))
    with pytest.raises(FalhaMarketplace) as erro:
        c.buscar('SSD')
    assert erro.value.status == 503
    for corpo in (b'<html>', {'data': {}}, {'data': {'productOfferV2': {'nodes': [], 'pageInfo': {}}}}):
        c, _ = cliente(Resposta(corpo))
        with pytest.raises(ValueError):
            c.buscar('SSD')


def test_falha_de_rede_e_temporaria():
    c, _ = cliente(requests.ConnectionError('rede'))
    with pytest.raises(FalhaMarketplace) as erro:
        c.buscar('SSD')
    assert erro.value.temporaria


def test_consulta_de_anuncio_valida_identificadores():
    c, _ = cliente(Resposta(OK))
    with pytest.raises(ValueError):
        c.consultar_anuncio('abc', '1')
    assert c.consultar_anuncio('10', '2')['nodes'] == []
