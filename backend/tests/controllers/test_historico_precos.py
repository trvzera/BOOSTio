from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin
from sqlalchemy.exc import OperationalError

from models import db, PlacaVideo, HistoricoOferta, Oferta
from controllers.build_controller import build_bp
from services.peca_service.consultar_historico_precos_service import ConsultarHistoricoPrecosService


@pytest.fixture
def banco():
    app=Flask(__name__); app.config.update(SECRET_KEY='teste',SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
    db.init_app(app)
    login=LoginManager(app)
    class Conta(UserMixin): id='1'
    login.user_loader(lambda id: Conta())
    app.register_blueprint(build_bp)
    with app.app_context():
        db.create_all()
        p=PlacaVideo(status_validacao='aprovado', fabricante='Teste',modelo='GPU',memoria_gb=8,consumo_energia=65,preco=100,esgotado=False,kabum_external='https://www.kabum.com.br/produto/123/gpu')
        db.session.add(p); db.session.commit()
        client=app.test_client()
        with client.session_transaction() as sessao: sessao['_user_id']='1'; sessao['_fresh']=True
        yield app,client,p
        db.session.remove(); db.engine.dispose()


def registrar(p,preco=100,esgotado=False,anuncio='123',data=None,tabela='placa_video'):
    """Observação de uma oferta da KaBuM; cria a oferta do anúncio quando ainda não existe."""
    o=Oferta.query.filter_by(loja='kabum',produto_id_loja=anuncio).first()
    if o is None:
        o=Oferta(tabela_peca=tabela,peca_id=p.id,loja='kabum',produto_id_loja=anuncio,
                 url='https://www.kabum.com.br/produto/'+anuncio,ativa=False)
        db.session.add(o);db.session.flush()
    db.session.add(HistoricoOferta(oferta_id=o.id,preco=preco,esgotado=esgotado,coletado_em=data or datetime(2026,11,2,12,0,0,123456)))
    db.session.commit()


def url(p): return f'/build/catalogo/placa_video/{p.id}/historico-precos'


def test_rota_retorna_historico_real_do_anuncio_sem_misturar(banco):
    _,client,p=banco
    registrar(p,120,data=datetime(2026,11,1)); registrar(p,100)
    registrar(p,1,anuncio='999'); registrar(p,3,tabela='processador',anuncio='777')
    r=client.get(url(p)); d=r.get_json()
    assert r.status_code==200 and r.headers['Cache-Control']=='no-store'
    assert [h['preco'] for h in d['historico_precos']]==[120.0,100.0]
    assert d['historico_precos'][1]['data']=='2026-11-02T12:00:00.123+00:00'
    assert d['peca_id']==f'placa_video:{p.id}' and d['tem_mais'] is False and d['loja']=='kabum'
    assert 'url' not in d['historico_precos'][0]


def test_sem_historico_nao_fabrica_preco_atual(banco):
    _,client,p=banco
    assert client.get(url(p)).get_json()['historico_precos']==[]
    Oferta.query.update({'ativa':False});db.session.commit()
    assert client.get(url(p)).status_code==404


def test_exige_sessao(banco):
    app,_,p=banco
    assert app.test_client().get(url(p)).status_code==401


@pytest.mark.parametrize('caminho,status',[('/build/catalogo/desconhecida/1/historico-precos',400),('/build/catalogo/placa_video/0/historico-precos',400),('/build/catalogo/placa_video/999/historico-precos',404)])
def test_identidade_validada(banco,caminho,status): assert banco[1].get(caminho).status_code==status


def test_parametros_rejeitados(banco):
    _,client,p=banco
    assert client.get(url(p)+'?loja=outra').status_code==400


def test_banco_indisponivel_nao_parece_historico_vazio(banco):
    _,client,p=banco
    with patch.object(HistoricoOferta,'listar',side_effect=OperationalError('segredo',{},None)):
        r=client.get(url(p))
    assert r.status_code==503 and 'segredo' not in r.get_data(as_text=True)


def test_limite_e_ordem_deterministica(banco):
    _,client,p=banco
    o=Oferta.query.filter_by(loja='kabum',produto_id_loja='123').one()
    for i in range(1001):
        db.session.add(HistoricoOferta(oferta_id=o.id,preco=i+1,esgotado=False,coletado_em=datetime(2026,11,2)))
    db.session.commit()
    r=client.get(url(p)).get_json()
    assert r['tem_mais'] is True and len(r['historico_precos'])==1000
    assert r['historico_precos'][0]['preco']==2 and r['historico_precos'][-1]['preco']==1001


def ofertas_de_varias_lojas(p):
    from decimal import Decimal
    agora = datetime(2026, 11, 5)
    criadas = {}
    for loja, anuncio in (('kabum', '555'), ('shopee', '1:2'), ('mercado_livre', 'MLB9')):
        o = Oferta(tabela_peca='placa_video', peca_id=p.id, loja=loja, produto_id_loja=anuncio, ativa=True,
                   url='https://exemplo.com/' + anuncio, preco=Decimal('500'), consultado_em=agora, preco_atualizado_em=agora)
        db.session.add(o); db.session.flush(); criadas[loja] = o
    for loja, preco, dia in (('kabum', 500, 1), ('kabum', 450, 3), ('shopee', 400, 2), ('shopee', 480, 3), ('mercado_livre', 420, 3)):
        db.session.add(HistoricoOferta(oferta_id=criadas[loja].id, preco=preco, esgotado=False, coletado_em=datetime(2026, 11, dia, 12)))
    db.session.commit()


def pontos(resposta):
    return [(h['data'][:10], h['preco'], h['loja']) for h in resposta.get_json()['historico_precos']]


def test_historico_geral_mostra_o_menor_preco_do_dia_entre_as_lojas(banco):
    _, client, p = banco
    ofertas_de_varias_lojas(p)
    with patch.object(ConsultarHistoricoPrecosService, '_exibivel', return_value=True):
        r = client.get(url(p) + '?loja=todas')
    assert r.status_code == 200 and r.get_json()['loja'] == 'todas'
    assert r.get_json()['lojas'] == ['kabum', 'mercado_livre', 'shopee']
    assert pontos(r) == [('2026-11-01', 500.0, 'kabum'), ('2026-11-02', 400.0, 'shopee'), ('2026-11-03', 420.0, 'mercado_livre')]


def test_historico_filtrado_por_loja_traz_so_aquela_loja(banco):
    _, client, p = banco
    ofertas_de_varias_lojas(p)
    with patch.object(ConsultarHistoricoPrecosService, '_exibivel', return_value=True):
        kabum, shopee = client.get(url(p) + '?loja=kabum'), client.get(url(p) + '?loja=shopee')
    assert pontos(kabum) == [('2026-11-01', 500.0, 'kabum'), ('2026-11-03', 450.0, 'kabum')]
    assert pontos(shopee) == [('2026-11-02', 400.0, 'shopee'), ('2026-11-03', 480.0, 'shopee')]


def test_historico_ignora_oferta_nao_exibivel(banco):
    _, client, p = banco
    ofertas_de_varias_lojas(p)
    with patch.object(ConsultarHistoricoPrecosService, '_exibivel', side_effect=lambda o, peca: o.loja != 'shopee'):
        r = client.get(url(p) + '?loja=todas')
    assert r.get_json()['lojas'] == ['kabum', 'mercado_livre']
    assert pontos(r) == [('2026-11-01', 500.0, 'kabum'), ('2026-11-03', 420.0, 'mercado_livre')]
