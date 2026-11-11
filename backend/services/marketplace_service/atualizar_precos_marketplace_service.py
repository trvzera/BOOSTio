import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from models import Oferta, VinculoMercadoLivre
from services.marketplace_service.erros import FalhaMarketplace
from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.mercadolivre_service.controle_requisicoes_service import ErroMercadoLivre
from services.mercadolivre_service.token_mercado_livre_service import TokenMercadoLivreService
from services.shopee_service.cliente_service import ClienteShopeeService

LOJAS = ('mercado_livre', 'shopee')
ITENS_POR_CHAMADA = 20


class AtualizarPrecosMarketplaceService:
    def __init__(self, cliente_ml=None, cliente_shopee=None, token=None):
        self.cliente_ml = cliente_ml
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
        por_peca = {}
        for oferta in ofertas:
            por_peca.setdefault((oferta.tabela_peca, oferta.peca_id), []).append(oferta)
        cliente = self.cliente_ml or BuscarOfertasMercadoLivreService()
        token = self.token or TokenMercadoLivreService().executar()
        for (tabela, peca_id), lote in por_peca.items():
            anuncios = self._anuncios_do_catalogo(cliente, VinculoMercadoLivre.buscar(tabela, peca_id), token)
            for oferta in lote:
                if anuncios is None:
                    resumo['sem_retorno'] += 1
                elif oferta.produto_id_loja in anuncios:
                    anuncio = anuncios[oferta.produto_id_loja]
                    self._gravar(oferta, anuncio['preco'], anuncio['esgotado'], agora, resumo, simular)
                else:
                    # Anúncio que saiu da lista do catálogo: mantém o último preço, mas fica esgotado.
                    resumo['ausentes'] += 1
                    self._gravar(oferta, oferta.preco, True, agora, resumo, simular)
            if not simular:
                Oferta.confirmar_coletas()

    @staticmethod
    def _anuncios_do_catalogo(cliente, vinculo, token):
        if vinculo is None:
            return None
        try:
            ofertas = cliente.executar(vinculo.catalogo_id, access_token=token)['ofertas']
        except ErroMercadoLivre as erro:
            if erro.status in (401, 403, 429) or erro.status >= 500:
                raise FalhaMarketplace(erro.status) from None
            return None
        except ValueError:
            return None
        return {oferta['produto_id_loja']: oferta for oferta in ofertas}

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
