import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import requests

from models import Oferta
from services.marketplace_service.controle_requisicoes_service import executar_requisicao
from services.marketplace_service.erros import FalhaMarketplace
from services.mercadolivre_service.token_mercado_livre_service import TokenMercadoLivreService
from services.shopee_service.cliente_service import ClienteShopeeService

LOJAS = ('mercado_livre', 'shopee')
ITENS_POR_CHAMADA = 20
URL_ITENS = 'https://api.mercadolibre.com/items'


class AtualizarPrecosMarketplaceService:
    def __init__(self, http=None, cliente_shopee=None, token=None):
        self.http = http or requests
        self.cliente_shopee = cliente_shopee
        self.token = token

    def executar(self, loja, *, horas=20, limite=None, simular=False):
        if loja not in LOJAS:
            raise ValueError('Marketplace inválido')
        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        ofertas = Oferta.listar_para_atualizar(loja, agora - timedelta(hours=horas), limite)
        resumo = {'loja': loja, 'simulacao': simular, 'ofertas': len(ofertas), 'atualizadas': 0, 'inalteradas': 0,
                  'esgotadas': 0, 'ausentes': 0, 'sem_retorno': 0, 'invalidas': 0, 'historicos': 0, 'interrompido': None}
        try:
            if loja == 'mercado_livre':
                self._mercado_livre(ofertas, agora, resumo, simular)
            else:
                self._shopee(ofertas, agora, resumo, simular)
        except FalhaMarketplace as erro:
            resumo['interrompido'] = f'HTTP {erro.status or "rede"}'
        if not simular:
            Oferta.confirmar_coletas()
        return resumo

    def _mercado_livre(self, ofertas, agora, resumo, simular):
        for inicio in range(0, len(ofertas), ITENS_POR_CHAMADA):
            lote = ofertas[inicio:inicio + ITENS_POR_CHAMADA]
            itens = self._consultar_itens([o.produto_id_loja for o in lote])
            for oferta in lote:
                resposta = itens.get(oferta.produto_id_loja)
                if resposta is None:
                    resumo['sem_retorno'] += 1
                elif isinstance(resposta, dict) and resposta.get('code') == 404:
                    resumo['ausentes'] += 1
                    if not simular:
                        oferta.desativar()
                elif (not isinstance(resposta, dict) or resposta.get('code') != 200 or not isinstance(resposta.get('body'), dict)
                      or resposta['body'].get('id') != oferta.produto_id_loja):
                    resumo['sem_retorno'] += 1
                else:
                    self._gravar(oferta, resposta['body'].get('price'), self._esgotado_ml(resposta['body']), agora, resumo, simular)
            if not simular:
                Oferta.confirmar_coletas()

    def _consultar_itens(self, ids):
        token = self.token or TokenMercadoLivreService().executar()
        resposta = executar_requisicao(lambda: self._requisitar(ids, token), loja='mercado_livre')
        return dict(zip(ids, resposta))

    def _requisitar(self, ids, token):
        try:
            resposta = self.http.get(URL_ITENS, params={'ids': ','.join(ids), 'attributes': 'id,price,available_quantity,status'},
                                     headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'},
                                     timeout=(10, 30), allow_redirects=False)
        except requests.RequestException:
            raise FalhaMarketplace(temporaria=True) from None
        if resposta.status_code != 200:
            raise FalhaMarketplace(resposta.status_code, resposta.headers.get('Retry-After'))
        dados = resposta.json(parse_float=Decimal)
        if not isinstance(dados, list):
            raise ValueError('Formato de resposta inválido no Mercado Livre')
        return dados

    @staticmethod
    def _esgotado_ml(item):
        quantidade = item.get('available_quantity')
        if item.get('status') not in (None, 'active'):
            return True
        return quantidade == 0 if type(quantidade) is int and quantidade >= 0 else None

    def _shopee(self, ofertas, agora, resumo, simular):
        cliente = self.cliente_shopee or ClienteShopeeService()
        for posicao, oferta in enumerate(ofertas, 1):
            vendedor, item = oferta.produto_id_loja.split(':')
            nos = cliente.consultar_anuncio(vendedor, item)['nodes']
            if not nos:
                resumo['sem_retorno'] += 1
                continue
            inicio, fim = nos[0].get('periodStartTime'), nos[0].get('periodEndTime')
            ativo = type(inicio) is int and type(fim) is int and inicio <= time.time() < fim
            self._gravar(oferta, nos[0].get('priceMin'), None if ativo else True, agora, resumo, simular)
            if posicao % ITENS_POR_CHAMADA == 0 and not simular:
                Oferta.confirmar_coletas()

    @staticmethod
    def _preco_valido(valor):
        try:
            preco = Decimal(str(valor))
            if isinstance(valor, bool) or not preco.is_finite() or not 0 < preco <= Decimal('999999999999.99'):
                return None
            return preco.quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError):
            return None

    def _gravar(self, oferta, valor, esgotado, agora, resumo, simular):
        preco = self._preco_valido(valor)
        if preco is None:
            resumo['invalidas'] += 1
            return
        mudou = oferta.preco != preco or oferta.esgotado != esgotado
        resumo['atualizadas' if mudou else 'inalteradas'] += 1
        resumo['esgotadas'] += int(esgotado is True)
        if not simular:
            resumo['historicos'] += int(oferta.registrar_coleta(preco, esgotado, agora))
