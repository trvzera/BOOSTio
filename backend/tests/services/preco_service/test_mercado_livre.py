import json
from decimal import Decimal
from unittest.mock import Mock, patch
import pytest
import requests
from flask import Flask
from services.preco_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService as Service

CAT = 'MLB47814270'
def oferta():
    return dict(item_id='MLB4171634813', seller_id=2338890054, site_id='MLB', currency_id='BRL', price=44, original_price=99.9, condition='new')
def pagina(linhas, offset=0, total=None):
    return {'paging': {'total':len(linhas) if total is None else total, 'offset':offset}, 'results':linhas}
def executar(*paginas):
    s=Service()
    with patch.object(s,'_consultar',side_effect=[{'id':CAT,'name':'Carregador','status':'active'},*paginas]) as consultar:
        r=s.executar(CAT,access_token='teste')
    return r,consultar

def test_normalizacao_e_repetibilidade():
    r,_=executar(pagina([oferta()])); o=r['ofertas'][0]
    assert o['preco']==Decimal('44.00') and o['preco_original']==Decimal('99.90')
    assert o['vendedor_id']=='2338890054' and o['produto_id_loja']=='MLB4171634813'
    assert o['esgotado'] is None and o['url_afiliado'] is None and o['condicao_pagamento'] is None
    assert executar(pagina([oferta()]))[0]==r

def test_paginacao_e_vendedores():
    segunda=oferta(); segunda.update(item_id='MLB123',seller_id=2,condition='used')
    r,c=executar(pagina([oferta()],total=2),pagina([segunda],offset=1,total=2))
    assert len(r['ofertas'])==2 and c.call_args.kwargs['params']['offset']==1

@pytest.mark.parametrize('campo,valor',[('price',0),('price',-1),('price',True),('price','NaN'),('price','Infinity'),('price','1.001'),('currency_id','USD'),('site_id','MLA'),('seller_id',None),('seller_id',True),('item_id','../users'),('condition','unknown')])
def test_invalidas(campo,valor):
    o=oferta(); o[campo]=valor
    with pytest.raises(ValueError): executar(pagina([o]))

@pytest.mark.parametrize('paginas',[[pagina([],total=1)],[pagina([oferta()],total=2),pagina([oferta()],offset=1,total=2)],[pagina([oferta()],total=2),pagina([],offset=1,total=3)],[pagina([],total=1001)],[{'results':[]}]])
def test_paginacao_nao_aceita_parcial_duplicada_ou_mutavel(paginas):
    with pytest.raises(ValueError): executar(*paginas)

def test_sem_ofertas(): assert executar(pagina([]))[0]['ofertas']==[]

@pytest.mark.parametrize('id',['MLA123','../users/me','MLB123?x=y',None])
def test_id_sem_rede(id):
    with patch('requests.get') as get:
        with pytest.raises(ValueError): Service().executar(id,access_token='t')
        get.assert_not_called()

def test_token_do_service():
    s=Service()
    with patch('services.preco_service.buscar_ofertas_mercado_livre_service.TokenMercadoLivreService') as token, patch.object(s,'_consultar',side_effect=[{'id':CAT,'name':'CPU','status':'active'},pagina([])]) as c:
        token.return_value.executar.return_value='configurado'
        s.executar(CAT); assert c.call_args.args[1]=='configurado'


def test_sem_token():
    with patch('requests.get') as get:
        with pytest.raises(ValueError): Service().executar(CAT,access_token='')
        get.assert_not_called()

def resposta(d,status=200,tipo='application/json'):
    return Mock(status_code=status,headers={'Content-Type':tipo},iter_content=Mock(return_value=[json.dumps(d).encode()]))

def test_transporte():
    r=resposta({'id':CAT,'name':'CPU','status':'active'}); v=resposta(pagina([]))
    with patch('requests.get',side_effect=[r,v]) as get:
        Service().executar(CAT,access_token='secreto')
        assert get.call_args.kwargs['timeout']==(10,30)
        assert get.call_args.kwargs['allow_redirects'] is False
        assert get.call_args.kwargs['headers']['Authorization']=='Bearer secreto'
    r.close.assert_called_once(); v.close.assert_called_once()

@pytest.mark.parametrize('status,tipo',[(403,'application/json'),(429,'application/json'),(500,'application/json'),(302,'application/json'),(200,'text/html')])
def test_erros_sem_segredos(status,tipo):
    r=resposta({},status,tipo)
    with patch('requests.get',return_value=r),pytest.raises(ValueError) as e: Service().executar(CAT,access_token='segredo')
    assert 'segredo' not in str(e.value); r.close.assert_called_once()

def test_timeout():
    with patch('requests.get',side_effect=requests.Timeout('segredo')),pytest.raises(ValueError) as e: Service().executar(CAT,access_token='segredo')
    assert 'segredo' not in str(e.value)

def test_tamanho_e_json():
    for bloco in [b'x'*(2*1024*1024+1),b'{invalido']:
        r=resposta({}); r.iter_content.return_value=[bloco]
        with patch('requests.get',return_value=r),pytest.raises(ValueError): Service().executar(CAT,access_token='t')
        r.close.assert_called_once()
