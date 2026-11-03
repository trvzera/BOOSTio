from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin
from sqlalchemy.exc import OperationalError

from models import db, PlacaVideo, ConsultaPreco, HistoricoPreco
from controllers.build_controller import build_bp


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
        p=PlacaVideo(fabricante='Teste',modelo='GPU',memoria_gb=8,consumo_energia=65,preco=100,esgotado=False,kabum_external='https://www.kabum.com.br/produto/123/gpu')
        db.session.add(p); db.session.commit()
        client=app.test_client()
        with client.session_transaction() as sessao: sessao['_user_id']='1'; sessao['_fresh']=True
        yield app,client,p
        db.session.remove(); db.engine.dispose()


def registrar(p,preco=100,esgotado=False,anuncio='123',loja='kabum',data=None,tabela='placa_video'):
    c=ConsultaPreco(tabela_peca=tabela,peca_id=p.id,url='https://www.kabum.com.br/produto/'+anuncio,dia='2026-11-02',status='concluida')
    db.session.add(c);db.session.flush()
    h=HistoricoPreco(consulta_id=c.id,tabela_peca=tabela,peca_id=p.id,loja=loja,produto_id_loja=anuncio,url=c.url,preco=preco,esgotado=esgotado,coletado_em=data or datetime(2026,11,2,12,0,0,123456))
    db.session.add(h); db.session.commit()


def url(p): return f'/build/catalogo/placa_video/{p.id}/historico-precos'


def test_rota_retorna_historico_real_do_anuncio_sem_misturar(banco):
    _,client,p=banco
    registrar(p,120,data=datetime(2026,11,1)); registrar(p,100);registrar(p,None,True)
    registrar(p,1,anuncio='999'); registrar(p,2,loja='mercado_livre'); registrar(p,3,tabela='processador')
    r=client.get(url(p)); d=r.get_json()
    assert r.status_code==200 and r.headers['Cache-Control']=='no-store'
    assert [h['preco'] for h in d['historico_precos']]==[120.0,100.0,None]
    assert d['historico_precos'][1]['data']=='2026-11-02T12:00:00.123+00:00'
    assert d['historico_precos'][2]['esgotado'] is True
    assert d['peca_id']==f'placa_video:{p.id}' and d['tem_mais'] is False
    assert 'url' not in d['historico_precos'][0]


def test_sem_historico_nao_fabrica_preco_atual(banco):
    _,client,p=banco
    assert client.get(url(p)).get_json()['historico_precos']==[]
    p.kabum_external=None;db.session.commit()
    assert client.get(url(p)).get_json()['historico_precos']==[]


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
    with patch.object(HistoricoPreco,'listar_por_peca_anuncio',side_effect=OperationalError('segredo',{},None)):
        r=client.get(url(p))
    assert r.status_code==503 and 'segredo' not in r.get_data(as_text=True)


def test_limite_e_ordem_deterministica(banco):
    _,client,p=banco
    # Mesmo instante: IDs desempatem, sem perder a indicação de recorte.
    for i in range(1001):
        c=ConsultaPreco(tabela_peca='placa_video',peca_id=p.id,url='url',dia='2026-11-02',status='concluida')
        db.session.add(c);db.session.flush()
        db.session.add(HistoricoPreco(consulta_id=c.id,tabela_peca='placa_video',peca_id=p.id,loja='kabum',produto_id_loja='123',url='url',preco=i+1,esgotado=False,coletado_em=datetime(2026,11,2)))
    db.session.commit()
    r=client.get(url(p)).get_json()
    assert r['tem_mais'] is True and len(r['historico_precos'])==1000
    assert r['historico_precos'][0]['preco']==2 and r['historico_precos'][-1]['preco']==1001
