import time
from decimal import Decimal

import pytest
from flask import Flask

from models import db, Oferta, HistoricoOferta
from services.marketplace_service.atualizar_precos_marketplace_service import AtualizarPrecosMarketplaceService
from services.marketplace_service.erros import FalhaMarketplace


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        Oferta.__table__.create(db.engine)
        HistoricoOferta.__table__.create(db.engine)
        yield
        db.session.remove()
        db.engine.dispose()


def criar(loja, anuncio, preco, **campos):
    oferta = Oferta(tabela_peca='processador', peca_id=1, loja=loja, produto_id_loja=anuncio,
                    url='https://exemplo.com/' + anuncio, preco=Decimal(preco), **campos)
    db.session.add(oferta)
    db.session.commit()
    return oferta


class RespostaFalsa:
    def __init__(self, dados, status=200):
        self.dados, self.status_code, self.headers = dados, status, {}

    def json(self, **_):
        return self.dados


class HttpFalso:
    def __init__(self, dados, status=200):
        self.resposta, self.chamadas = RespostaFalsa(dados, status), []

    def get(self, url, **kwargs):
        self.chamadas.append((url, kwargs['params']))
        return self.resposta


class ShopeeFalsa:
    def __init__(self, por_anuncio):
        self.por_anuncio, self.chamadas = por_anuncio, []

    def consultar_anuncio(self, vendedor, item):
        self.chamadas.append((vendedor, item))
        return {'nodes': self.por_anuncio.get(f'{vendedor}:{item}', [])}


def servico_ml(dados, status=200):
    http = HttpFalso(dados, status)
    return AtualizarPrecosMarketplaceService(http=http, token='token'), http


def test_mercado_livre_consulta_em_lote_e_grava_preco_e_historico(banco):
    a, b = criar('mercado_livre', 'MLB1', '100.00'), criar('mercado_livre', 'MLB2', '200.00')
    servico, http = servico_ml([
        {'code': 200, 'body': {'id': 'MLB1', 'price': Decimal('90.50'), 'available_quantity': 3, 'status': 'active'}},
        {'code': 200, 'body': {'id': 'MLB2', 'price': Decimal('200.00'), 'available_quantity': 0, 'status': 'active'}}])
    resumo = servico.executar('mercado_livre')
    assert len(http.chamadas) == 1 and http.chamadas[0][1]['ids'] == 'MLB1,MLB2'
    assert resumo['atualizadas'] == 2 and resumo['historicos'] == 2 and resumo['interrompido'] is None
    assert a.preco == Decimal('90.50') and a.esgotado is False and a.preco_atualizado_em is not None
    assert b.esgotado is True and HistoricoOferta.query.count() == 2


def test_mercado_livre_item_removido_desativa_e_pausado_fica_esgotado(banco):
    removido, pausado = criar('mercado_livre', 'MLB1', '100.00'), criar('mercado_livre', 'MLB2', '200.00')
    servico, _ = servico_ml([{'code': 404, 'body': {'message': 'Item not found'}},
        {'code': 200, 'body': {'id': 'MLB2', 'price': Decimal('200.00'), 'available_quantity': 5, 'status': 'paused'}}])
    resumo = servico.executar('mercado_livre')
    assert removido.ativa is False and resumo['ausentes'] == 1
    assert pausado.esgotado is True and pausado.ativa is True


def test_simulacao_nao_grava(banco):
    oferta = criar('mercado_livre', 'MLB1', '100.00')
    servico, _ = servico_ml([{'code': 200, 'body': {'id': 'MLB1', 'price': Decimal('80.00'), 'available_quantity': 1, 'status': 'active'}}])
    resumo = servico.executar('mercado_livre', simular=True)
    db.session.refresh(oferta)
    assert resumo['atualizadas'] == 1 and oferta.preco == Decimal('100.00') and oferta.consultado_em is None
    assert HistoricoOferta.query.count() == 0


def test_so_consulta_ofertas_antigas_e_respeita_o_limite(banco):
    from datetime import datetime
    criar('mercado_livre', 'MLB1', '100.00', consultado_em=datetime.utcnow())
    criar('mercado_livre', 'MLB2', '100.00')
    criar('mercado_livre', 'MLB3', '100.00')
    servico, http = servico_ml([{'code': 404, 'body': {}}])
    servico.executar('mercado_livre', limite=1)
    assert http.chamadas[0][1]['ids'] == 'MLB2'


def test_preco_invalido_e_resposta_com_id_diferente_nao_alteram_a_oferta(banco):
    oferta = criar('mercado_livre', 'MLB1', '100.00')
    servico, _ = servico_ml([{'code': 200, 'body': {'id': 'MLB1', 'price': Decimal('0'), 'status': 'active'}}])
    assert servico.executar('mercado_livre')['invalidas'] == 1 and oferta.preco == Decimal('100.00')
    outra = criar('mercado_livre', 'MLB9', '50.00')
    servico, _ = servico_ml([{'code': 200, 'body': {'id': 'MLB7', 'price': Decimal('1.00'), 'status': 'active'}}])
    assert servico.executar('mercado_livre', horas=0, limite=1)['sem_retorno'] == 1 and outra.preco == Decimal('50.00')


def test_falha_da_loja_interrompe_sem_perder_o_que_ja_foi_gravado(banco):
    criar('mercado_livre', 'MLB1', '100.00')
    servico, _ = servico_ml({'message': 'forbidden'}, status=403)
    assert servico.executar('mercado_livre')['interrompido'] == 'HTTP 403'


def test_shopee_usa_loja_e_item_do_identificador(banco):
    oferta = criar('shopee', '111:222', '300.00')
    agora = int(time.time())
    cliente = ShopeeFalsa({'111:222': [{'priceMin': '250.00', 'priceMax': '250.00',
                                        'periodStartTime': agora - 10, 'periodEndTime': agora + 3600}]})
    resumo = AtualizarPrecosMarketplaceService(cliente_shopee=cliente).executar('shopee')
    assert cliente.chamadas == [('111', '222')] and resumo['atualizadas'] == 1
    assert oferta.preco == Decimal('250.00') and oferta.esgotado is None and HistoricoOferta.query.count() == 1


def test_shopee_sem_retorno_mantem_oferta_e_periodo_encerrado_marca_esgotada(banco):
    sem_retorno, encerrada = criar('shopee', '1:1', '300.00'), criar('shopee', '2:2', '400.00')
    agora = int(time.time())
    cliente = ShopeeFalsa({'2:2': [{'priceMin': '400.00', 'periodStartTime': agora - 100, 'periodEndTime': agora - 1}]})
    resumo = AtualizarPrecosMarketplaceService(cliente_shopee=cliente).executar('shopee')
    assert resumo['sem_retorno'] == 1 and sem_retorno.consultado_em is None
    assert encerrada.esgotado is True


def test_marketplace_invalido():
    with pytest.raises(ValueError):
        AtualizarPrecosMarketplaceService().executar('kabum')
