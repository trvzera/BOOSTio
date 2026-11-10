from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.exc import IntegrityError
from models import db, Oferta


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        Oferta.__table__.create(db.engine)
        yield
        db.session.remove()
        db.engine.dispose()


def oferta(**campos):
    dados = dict(tabela_peca='placa_video', peca_id=1, loja='kabum',
                 produto_id_loja='123', url='https://www.kabum.com.br/produto/123')
    obj = Oferta(**{**dados, **campos})
    db.session.add(obj)
    db.session.commit()
    return obj


def test_mesma_peca_tem_ofertas_em_lojas_diferentes(banco):
    a = oferta(preco=Decimal('999.90'), esgotado=False)
    b = oferta(loja='outra', url='https://loja.example/produto/123', preco=Decimal('899.99'), esgotado=False)
    assert a.peca_id == b.peca_id and a.id != b.id
    assert a.preco == Decimal('999.90') and b.preco == Decimal('899.99')
    assert Oferta.query.count() == 2


def test_mesmo_anuncio_nao_pode_ser_duplicado_nem_vinculado_a_duas_pecas(banco):
    original = oferta()
    with pytest.raises(IntegrityError):
        oferta(peca_id=2)
    db.session.rollback()
    assert Oferta.query.count() == 1
    assert Oferta.query.one().id == original.id


def test_identidade_do_anuncio_independe_do_vendedor(banco):
    oferta(vendedor_id='a', vendedor_nome='Loja A')
    with pytest.raises(IntegrityError):
        oferta(vendedor_id='b', vendedor_nome='Loja B')
    db.session.rollback()
    assert Oferta.query.count() == 1
    oferta(produto_id_loja='456', vendedor_id='b')
    assert Oferta.query.count() == 2


def test_oferta_sem_coleta_nao_inventa_preco_estoque_ou_datas(banco):
    obj = oferta()
    assert obj.preco is None and obj.esgotado is None
    assert obj.preco_atualizado_em is None and obj.consultado_em is None
    assert obj.ativa is True and obj.vendedor_id == ''


@pytest.mark.parametrize('campos', [dict(preco=0), dict(preco=-1), dict(esgotado=False), dict(peca_id=0)])
def test_rejeita_valores_que_falseariam_oferta(banco, campos):
    with pytest.raises(IntegrityError):
        oferta(**campos)
    db.session.rollback()
    assert Oferta.query.count() == 0


def test_indisponibilidade_preserva_ultimo_preco_ou_ausencia_de_valor(banco):
    a = oferta(esgotado=True)
    b = oferta(produto_id_loja='456', esgotado=True, preco=Decimal('100.00'))
    assert a.preco is None and b.preco == Decimal('100.00')


def ficha(*ofertas, preco=999.0):
    return {'preco': preco, 'esgotado': None, 'preco_atualizado_em': None, 'ofertas': list(ofertas)}


def anuncio(id, loja, preco, esgotado=False):
    return {'id': id, 'loja': loja, 'preco': preco, 'esgotado': esgotado, 'atualizadoEm': f'2026-11-10T00:00:{id:02d}+00:00'}


def test_catalogo_mostra_so_o_anuncio_mais_barato_de_cada_loja():
    peca = ficha(anuncio(1, 'shopee', 300.0), anuncio(2, 'shopee', 250.0), anuncio(3, 'shopee', 280.0),
                 anuncio(4, 'mercado_livre', 400.0), anuncio(5, 'mercado_livre', 390.0))
    Oferta._manter_mais_barata_por_loja(peca)
    assert [(o['loja'], o['id']) for o in peca['ofertas']] == [('shopee', 2), ('mercado_livre', 5)]


def test_preco_de_referencia_e_o_menor_entre_todas_as_lojas():
    peca = ficha(anuncio(1, 'kabum', 500.0), anuncio(2, 'shopee', 250.0), anuncio(3, 'mercado_livre', 390.0))
    Oferta._manter_mais_barata_por_loja(peca)
    assert peca['preco'] == 250.0 and peca['esgotado'] is False
    assert peca['preco_atualizado_em'] == '2026-11-10T00:00:02+00:00'


def test_oferta_esgotada_so_vira_referencia_se_nao_houver_disponivel():
    peca = ficha(anuncio(1, 'kabum', 100.0, esgotado=True), anuncio(2, 'mercado_livre', 390.0))
    Oferta._manter_mais_barata_por_loja(peca)
    assert peca['preco'] == 390.0
    assim = ficha(anuncio(1, 'kabum', 100.0, esgotado=True), anuncio(2, 'mercado_livre', 90.0, esgotado=True))
    Oferta._manter_mais_barata_por_loja(assim)
    assert assim['preco'] == 90.0 and assim['esgotado'] is True


def test_sem_ofertas_mantem_o_preco_da_peca():
    peca = ficha(preco=123.0)
    Oferta._manter_mais_barata_por_loja(peca)
    assert peca['preco'] == 123.0 and peca['ofertas'] == []
