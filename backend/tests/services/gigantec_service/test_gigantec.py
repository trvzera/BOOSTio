import gzip
from decimal import Decimal

import pytest
from flask import Flask

from models import db, Processador, ControleColeta, Oferta, HistoricoOferta
from services.gigantec_service.associar_feed_service import AssociarFeedGigantecService
from services.gigantec_service.feed_service import FeedGigantecService
from services.marketplace_service.atualizar_precos_marketplace_service import AtualizarPrecosMarketplaceService

CABECALHO = 'aw_deep_link,product_name,search_price,brand_name,mpn,merchant_product_id,in_stock,merchant_deep_link\n'


def linha(ident, titulo, preco, mpn, marca='AMD', estoque='1', afiliado=None, loja=None):
    return (f'{afiliado or f"https://www.awin1.com/pclick.php?p={ident}&a=1&m=2"},"{titulo}",{preco},{marca},{mpn},{ident},{estoque},'
            f'{loja or f"https://www.gigantec.com.br/produto-{ident}.html"}\n')


def feed(tmp_path, *linhas, comprimir=False):
    texto = (CABECALHO + ''.join(linhas)).encode()
    arquivo = tmp_path / ('feed.csv.gz' if comprimir else 'feed.csv')
    arquivo.write_bytes(gzip.compress(texto) if comprimir else texto)
    return FeedGigantecService(arquivo=str(arquivo))


class FeedFalso:
    def __init__(self, itens):
        self._itens = itens

    def itens(self):
        return self._itens


def item(ident, preco, disponivel=True):
    return {'id': ident, 'titulo': 't', 'marca': 'AMD', 'mpn': 'X', 'preco': Decimal(preco), 'disponivel': disponivel,
            'url': 'https://www.gigantec.com.br/p.html', 'url_afiliado': 'https://www.awin1.com/pclick.php?p=1&a=1&m=2'}


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        ControleColeta.inicializar()
        cpu = Processador(fabricante='AMD', modelo='Ryzen 5 5500', part_number='100-100000457BOX', soquete='AM4',
                          nucleo=6, thread=12, clockbase=3.6, clockmax=4.2, consumo_energia=65, status_validacao='aprovado')
        db.session.add(cpu)
        db.session.commit()
        yield cpu
        db.session.remove()
        db.engine.dispose()


def test_feed_le_itens_validos_com_ou_sem_gzip(tmp_path):
    for comprimir in (False, True):
        itens = feed(tmp_path, linha('10', 'CPU A', '1299.9', 'ABC-1'), comprimir=comprimir).itens()
        assert itens['10']['preco'] == Decimal('1299.90')
        assert itens['10']['mpn'] == 'ABC-1' and itens['10']['disponivel'] is True
        assert itens['10']['url_afiliado'].startswith('https://www.awin1.com/')


def test_feed_ignora_preco_zero_link_de_outro_host_e_id_invalido(tmp_path):
    itens = feed(tmp_path, linha('1', 'a', '0', 'A'), linha('2', 'b', '10', 'B', loja='https://outro.com.br/p'),
                 linha('3', 'c', '10', 'C', afiliado='http://www.awin1.com/x'), linha('x4', 'd', '10', 'D'),
                 linha('5', 'e', 'abc', 'E'), linha('6', 'ok', '10', 'F')).itens()
    assert list(itens) == ['6']


def test_feed_sem_colunas_esperadas_falha_sem_vazar_caminho(tmp_path):
    arquivo = tmp_path / 'ruim.csv'
    arquivo.write_text('a,b\n1,2\n')
    with pytest.raises(ValueError, match='colunas'):
        FeedGigantecService(arquivo=str(arquivo)).itens()


def test_feed_exige_url_configurada(monkeypatch):
    monkeypatch.delenv('GIGANTEC_FEED_URL', raising=False)
    with pytest.raises(ValueError, match='GIGANTEC_FEED_URL'):
        FeedGigantecService()


def test_simular_nao_grava_e_aplicar_cria_so_para_mpn_e_marca_iguais(banco, tmp_path):
    itens = feed(tmp_path,
                 linha('1', 'Processador AMD Ryzen 5 5500 AM4', '700', '100-100000457BOX'),
                 linha('2', 'Processador AMD Ryzen 5 5500 AM4', '650', '100-100000457BOX', estoque='0'),
                 linha('3', 'Outro produto qualquer', '50', 'ZZZ-999'),
                 linha('4', 'Sem código', '50', '')).itens()
    simulado = AssociarFeedGigantecService().executar(itens, simular=True)
    assert (simulado['ligadas'], simulado['criadas'], simulado['sem_correspondencia'], simulado['sem_mpn'], simulado['indisponiveis']) == (1, 1, 1, 1, 1)
    assert Oferta.query.count() == 0
    real = AssociarFeedGigantecService().executar(itens, simular=False)
    assert real['criadas'] == 1
    oferta = Oferta.query.one()
    assert (oferta.loja, oferta.produto_id_loja, oferta.preco, oferta.esgotado) == ('gigantec', '1', Decimal('700.00'), False)
    assert oferta.url_afiliado.startswith('https://www.awin1.com/')
    assert HistoricoOferta.query.count() == 1
    assert AssociarFeedGigantecService().executar(itens, simular=False)['inalteradas'] == 1


def test_marca_diferente_vai_para_revisao_sem_gravar(banco, tmp_path):
    itens = feed(tmp_path, linha('1', 'Processador Intel Core i5', '700', '100-100000457BOX', marca='Intel')).itens()
    resumo = AssociarFeedGigantecService().executar(itens, simular=False)
    assert resumo['ligadas'] == 0 and resumo['revisao'] == 1 and Oferta.query.count() == 0


def test_precos_atualiza_marca_esgotado_quando_sai_do_feed_e_nao_baixa_sem_ofertas(banco):
    cpu = banco
    for ident, preco in (('1', '700.00'), ('2', '800.00'), ('3', '900.00')):
        db.session.add(Oferta(tabela_peca='processador', peca_id=cpu.id, loja='gigantec', produto_id_loja=ident,
                              url=f'https://www.gigantec.com.br/p{ident}.html', preco=Decimal(preco), esgotado=False))
    db.session.commit()
    feed_falso = FeedFalso({'1': item('1', '650.00'), '2': item('2', '800.00', disponivel=False)})
    resumo = AtualizarPrecosMarketplaceService(feed_gigantec=feed_falso).executar('gigantec', horas=0)
    assert (resumo['atualizadas'], resumo['ausentes'], resumo['esgotadas']) == (3, 1, 2)
    por_id = {o.produto_id_loja: o for o in Oferta.query.all()}
    assert por_id['1'].preco == Decimal('650.00') and por_id['1'].esgotado is False
    assert por_id['2'].esgotado is True and por_id['3'].esgotado is True and por_id['3'].preco == Decimal('900.00')
    assert por_id['1'].url_afiliado.startswith('https://www.awin1.com/')

    Oferta.query.delete()
    db.session.commit()
    assert AtualizarPrecosMarketplaceService(feed_gigantec=object()).executar('gigantec')['ofertas'] == 0


def test_oferta_aparece_na_exibicao_com_link_afiliado(banco):
    oferta = Oferta(tabela_peca='processador', peca_id=banco.id, loja='gigantec', produto_id_loja='1', preco=Decimal('700'),
                    url='https://www.gigantec.com.br/p.html', url_afiliado='https://www.awin1.com/pclick.php?p=1&a=1&m=2',
                    esgotado=False, consultado_em=__import__('datetime').datetime(2026, 11, 24))
    db.session.add(oferta)
    db.session.commit()
    dados = oferta.para_exibicao()
    assert dados['url'].startswith('https://www.awin1.com/') and dados['esgotado'] is False
    oferta.url = 'https://falso.com/p'
    assert oferta.para_exibicao() is None
