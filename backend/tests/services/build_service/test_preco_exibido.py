from datetime import datetime

import pytest
from flask import Flask

from models import db, Oferta, PlacaVideo
from services.build_service.catalogo_geracao_service import gerar_catalogo
from services.build_service.preco_exibido_service import PrecoExibidoService

AGORA = datetime(2026, 11, 13, 12, 0)


@pytest.fixture
def banco(tmp_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_path / 'preco.db'}"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.engine.dispose()


def gpu(preco_kabum, esgotado_kabum=False, codigo=1062024):
    peca = PlacaVideo(status_validacao='aprovado', fabricante='NVIDIA', modelo=f'GeForce GTX 1050 Ti {codigo}',
                      memoria_gb=4, consumo_energia=75, preco=preco_kabum, esgotado=esgotado_kabum,
                      kabum_external=f'https://www.kabum.com.br/produto/{codigo}/placa', preco_atualizado_em=AGORA)
    db.session.add(peca)
    db.session.commit()
    return peca


def shopee_nao_conferida(peca, preco):
    db.session.add(Oferta(tabela_peca='placa_video', peca_id=peca.id, loja='shopee', produto_id_loja='746624425:2399976898',
                          vendedor_id='746624425', url='https://shopee.com.br/product/746624425/2399976898',
                          preco=preco, esgotado=None, ativa=True, consultado_em=AGORA))
    db.session.commit()


def test_oferta_barata_que_o_site_nao_mostra_nao_vira_preco_da_geracao(banco):
    peca = gpu(1248.90)
    shopee_nao_conferida(peca, 600)
    assert db.session.get(PlacaVideo, peca.id).preco == 600
    item, = PrecoExibidoService.catalogo([db.session.get(PlacaVideo, peca.id)])
    assert item['preco'] == 1248.90


def test_peca_cuja_oferta_exibida_esta_esgotada_sai_da_geracao(banco):
    peca = gpu(1248.90, esgotado_kabum=True)
    shopee_nao_conferida(peca, 600)
    assert PrecoExibidoService.catalogo([db.session.get(PlacaVideo, peca.id)]) == []


def test_preco_exibido_acima_do_teto_sai_da_geracao(banco):
    peca = gpu(1248.90)
    shopee_nao_conferida(peca, 600)
    assert PrecoExibidoService.catalogo([db.session.get(PlacaVideo, peca.id)], teto=1000) == []
    assert len(PrecoExibidoService.catalogo([db.session.get(PlacaVideo, peca.id)], teto=1300)) == 1


def test_catalogo_da_geracao_usa_o_preco_que_o_site_mostra(banco):
    cara = gpu(1248.90, codigo=1062024)
    shopee_nao_conferida(cara, 600)
    barata = gpu(900, codigo=1062025)
    catalogo = gerar_catalogo(1000)
    assert [(p['id'], p['preco']) for p in catalogo['placa_video']] == [(barata.id, 900.0)]
