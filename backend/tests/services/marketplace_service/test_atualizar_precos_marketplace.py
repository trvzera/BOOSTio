import time
from decimal import Decimal

import pytest
from flask import Flask

from models import db, Oferta, HistoricoOferta, VinculoMercadoLivre
from services.marketplace_service.atualizar_precos_marketplace_service import AtualizarPrecosMarketplaceService
from services.mercadolivre_service.controle_requisicoes_service import ErroMercadoLivre


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        Oferta.__table__.create(db.engine)
        HistoricoOferta.__table__.create(db.engine)
        VinculoMercadoLivre.__table__.create(db.engine)
        yield
        db.session.remove()
        db.engine.dispose()


def criar(loja, anuncio, preco, **campos):
    oferta = Oferta(tabela_peca='processador', peca_id=1, loja=loja, produto_id_loja=anuncio,
                    url='https://exemplo.com/' + anuncio, preco=Decimal(preco), **campos)
    db.session.add(oferta)
    db.session.commit()
    return oferta


class MercadoLivreFalso:
    def __init__(self, por_catalogo=None, erro=None):
        self.por_catalogo, self.erro, self.chamadas = por_catalogo or {}, erro, []

    def executar(self, catalogo_id, *, access_token):
        self.chamadas.append(catalogo_id)
        if self.erro:
            raise self.erro
        return {'ofertas': self.por_catalogo.get(catalogo_id, [])}


def anuncio(item, preco, esgotado=False):
    return {'produto_id_loja': item, 'preco': Decimal(preco), 'esgotado': esgotado}


def vincular(catalogo_id='MLB100', peca_id=1):
    db.session.add(VinculoMercadoLivre(tabela_peca='processador', peca_id=peca_id, catalogo_id=catalogo_id,
                                       assinatura_peca='a', assinatura_catalogo='b', criterio='teste'))
    db.session.commit()


def servico_ml(por_catalogo=None, erro=None):
    cliente = MercadoLivreFalso(por_catalogo, erro)
    return AtualizarPrecosMarketplaceService(cliente_ml=cliente, token='token'), cliente


class ShopeeFalsa:
    def __init__(self, por_anuncio):
        self.por_anuncio, self.chamadas = por_anuncio, []

    def consultar_anuncio(self, vendedor, item):
        self.chamadas.append((vendedor, item))
        return {'nodes': self.por_anuncio.get(f'{vendedor}:{item}', [])}


def test_mercado_livre_consulta_uma_vez_por_produto_de_catalogo_e_grava_historico(banco):
    vincular()
    a, b = criar('mercado_livre', 'MLB1', '100.00'), criar('mercado_livre', 'MLB2', '200.00')
    servico, cliente = servico_ml({'MLB100': [anuncio('MLB1', '90.50'), anuncio('MLB2', '200.00', True)]})
    resumo = servico.executar('mercado_livre')
    assert cliente.chamadas == ['MLB100']
    assert resumo['atualizadas'] == 2 and resumo['historicos'] == 2 and resumo['interrompido'] is None
    assert a.preco == Decimal('90.50') and a.esgotado is False and a.preco_atualizado_em is not None
    assert b.esgotado is True and HistoricoOferta.query.count() == 2


def test_mercado_livre_anuncio_fora_do_catalogo_fica_esgotado_com_ultimo_preco(banco):
    vincular()
    saiu = criar('mercado_livre', 'MLB1', '100.00')
    servico, _ = servico_ml({'MLB100': [anuncio('MLB2', '50.00')]})
    resumo = servico.executar('mercado_livre')
    assert resumo['ausentes'] == 1 and saiu.esgotado is True and saiu.preco == Decimal('100.00') and saiu.ativa is True


def test_mercado_livre_sem_vinculo_ou_catalogo_invalido_nao_altera_a_oferta(banco):
    sem_vinculo = criar('mercado_livre', 'MLB1', '100.00')
    servico, cliente = servico_ml()
    assert servico.executar('mercado_livre')['sem_retorno'] == 1 and cliente.chamadas == []
    vincular()
    servico, _ = servico_ml(erro=ValueError('Produto de catálogo inativo'))
    assert servico.executar('mercado_livre', horas=0)['sem_retorno'] == 1
    assert sem_vinculo.preco == Decimal('100.00') and sem_vinculo.consultado_em is None


def test_simulacao_nao_grava(banco):
    vincular()
    oferta = criar('mercado_livre', 'MLB1', '100.00')
    servico, _ = servico_ml({'MLB100': [anuncio('MLB1', '80.00')]})
    resumo = servico.executar('mercado_livre', simular=True)
    db.session.refresh(oferta)
    assert resumo['atualizadas'] == 1 and oferta.preco == Decimal('100.00') and oferta.consultado_em is None
    assert HistoricoOferta.query.count() == 0


def test_so_consulta_ofertas_antigas_e_respeita_o_limite(banco):
    from datetime import datetime
    vincular()
    criar('mercado_livre', 'MLB1', '100.00', consultado_em=datetime.utcnow())
    criar('mercado_livre', 'MLB2', '100.00')
    criar('mercado_livre', 'MLB3', '100.00')
    servico, _ = servico_ml({'MLB100': [anuncio('MLB2', '90.00'), anuncio('MLB3', '90.00')]})
    resumo = servico.executar('mercado_livre', limite=1)
    assert resumo['ofertas'] == 1 and resumo['atualizadas'] == 1


def test_preco_invalido_nao_altera_a_oferta(banco):
    vincular()
    oferta = criar('mercado_livre', 'MLB1', '100.00')
    servico, _ = servico_ml({'MLB100': [anuncio('MLB1', '0')]})
    assert servico.executar('mercado_livre')['invalidas'] == 1 and oferta.preco == Decimal('100.00')


def test_acesso_negado_interrompe_sem_perder_o_que_ja_foi_gravado(banco):
    vincular()
    criar('mercado_livre', 'MLB1', '100.00')
    servico, _ = servico_ml(erro=ErroMercadoLivre(403))
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
