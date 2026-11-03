from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from flask import Flask, g
from flask_login import LoginManager, UserMixin

from models import db, Oferta, HistoricoOferta, Processador, TokenIntegracao, ControleColeta, VinculoMercadoLivre
from utils.identidade_peca import assinatura_peca
from controllers.build_controller import build_bp
from commands.mercadolivre import registrar_comandos_mercadolivre
from services.build_service.listar_catalogo_build_service import ListarCatalogoBuildService
from services.mercadolivre_service.validar_integracao_service import ValidarIntegracaoMercadoLivreService

@pytest.fixture
def banco():
    app=Flask(__name__);app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',SECRET_KEY='teste',
        INTEGRACOES_TOKEN_CHAVE=Fernet.generate_key().decode(),MERCADO_LIVRE_CLIENT_ID='123',
        MERCADO_LIVRE_CONTA_ID='42',MERCADO_LIVRE_CLIENT_SECRET='secret')
    db.init_app(app);registrar_comandos_mercadolivre(app)
    login=LoginManager(app)
    class Conta(UserMixin):id='1'
    login.user_loader(lambda id:Conta())
    app.register_blueprint(build_bp)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        p=Processador(status_validacao='aprovado', fabricante='AMD',modelo='Ryzen 5500',soquete='AM4',nucleo=6,thread=12,
            clockbase=3.6,clockmax=4.2,consumo_energia=65,preco=600,esgotado=True)
        db.session.add(p);db.session.commit()
        db.session.add(VinculoMercadoLivre(tabela_peca='processador',peca_id=p.id,catalogo_id='MLB777',
            assinatura_peca=assinatura_peca(p),assinatura_catalogo='0'*64,criterio='revisado'));db.session.commit()
        cliente=app.test_client()
        with cliente.session_transaction() as sessao:sessao['_user_id']='1';sessao['_fresh']=True
        yield app,p,cliente
        db.session.remove();db.engine.dispose()


def oferta(p,**changes):
    dados=dict(tabela_peca='processador',peca_id=p.id,loja='mercado_livre',produto_id_loja='MLB123',
        vendedor_id='4',url='https://produto.mercadolivre.com.br/MLB-123-_JM',preco=100,esgotado=None,
        consultado_em=datetime(2026,11,3),ativa=True)
    o=Oferta(**{**dados,**changes});db.session.add(o);db.session.commit();return o


def test_catalogo_exibe_ofertas_ativas_sem_trocar_preco_da_peca(banco):
    _,p,cliente=banco
    o=oferta(p)
    oferta(p,produto_id_loja='MLB456',url='https://produto.mercadolivre.com.br/MLB-456-_JM',ativa=False)
    resposta=cliente.get('/build/catalogo')
    assert resposta.status_code==200
    ficha=next(x for x in resposta.json['pecas'] if x['id']==f'processador:{p.id}')
    assert ficha['preco']==600 and ficha['esgotado'] is True
    assert len(ficha['ofertas'])==1
    dados=ficha['ofertas'][0]
    assert dados['id']==o.id and dados['vendedor_id']=='4' and dados['preco']==100
    assert dados['esgotado'] is None and dados['atualizadoEm'].endswith('+00:00')
    assert 'client_secret' not in resposta.get_data(as_text=True)


def test_urls_invalidas_e_anuncio_divergente_nao_sao_expostos(banco):
    _,p,_=banco
    o=oferta(p,url='https://evil.test/MLB-123-_JM')
    assert o.para_exibicao() is None
    o.url='https://produto.mercadolivre.com.br/MLB-456-_JM'
    assert o.para_exibicao() is None
    o.url='https://produto.mercadolivre.com.br/MLB-123-_JM';o.url_afiliado='javascript:alert(1)'
    assert o.para_exibicao()['url']==o.url
    o.url_afiliado='https://www.mercadolivre.com.br/p/MLB123?matt_tool=1'
    assert o.para_exibicao()['url']==o.url_afiliado


def test_historico_separado_por_anuncio_e_sessao(banco):
    app,p,cliente=banco;o=oferta(p)
    outro=oferta(p,produto_id_loja='MLB456',vendedor_id='5',url='https://produto.mercadolivre.com.br/MLB-456-_JM')
    db.session.add_all([HistoricoOferta(oferta_id=o.id,preco=100,coletado_em=datetime(2026,11,2)),
        HistoricoOferta(oferta_id=outro.id,preco=50,coletado_em=datetime(2026,11,2))]);db.session.commit()
    url=f'/build/catalogo/processador/{p.id}/ofertas/{o.id}/historico-precos'
    r=cliente.get(url)
    assert r.status_code==200 and r.json['loja']=='mercado_livre' and r.json['oferta_id']==o.id
    assert [x['preco'] for x in r.json['historico_precos']]==[100]
    assert r.json['historico_precos'][0]['esgotado'] is None
    g.pop('_login_user',None)
    assert app.test_client().get(url).status_code==401
    g.pop('_login_user',None)
    assert cliente.get(url.replace(f'processador/{p.id}',f'processador/{p.id+1}')).status_code==404
    o.ativa=False;db.session.commit()
    assert cliente.get(url).status_code==404


def test_validacao_nao_consulta_rede_nem_renova(banco):
    app,_,_=banco
    t=TokenIntegracao(integracao='mercado_livre',client_id='123',conta_id='42')
    t.definir_tokens('access','refresh',datetime.now(timezone.utc)-timedelta(seconds=1));t.salvar()
    with patch('requests.post') as post,patch('requests.get') as get:
        r=app.test_cli_runner().invoke(args=['mercadolivre-validar'])
    assert r.exit_code==0 and '"renovacao_necessaria": true' in r.output
    assert 'refresh' not in r.output and 'access' not in r.output
    post.assert_not_called();get.assert_not_called()


def test_validacao_exige_chave_e_tokens(banco):
    app,_,_=banco
    r=app.test_cli_runner().invoke(args=['mercadolivre-validar'])
    assert r.exit_code!=0 and 'Cadastre' in r.output
    app.config['INTEGRACOES_TOKEN_CHAVE']='invalida'
    with pytest.raises(ValueError):ValidarIntegracaoMercadoLivreService().executar()


def test_identidade_local_alterada_oculta_oferta_antiga(banco):
    _,p,cliente=banco;o=oferta(p)
    p.modelo='Outro processador';db.session.commit()
    ficha=next(x for x in cliente.get('/build/catalogo').json['pecas'] if x['id']==f'processador:{p.id}')
    assert not any(o['loja']=='mercado_livre' for o in ficha['ofertas'])
    assert cliente.get(f'/build/catalogo/processador/{p.id}/ofertas/{o.id}/historico-precos').status_code==404


@pytest.mark.parametrize('status', ['pendente', 'em_revisao', 'rejeitado'])
def test_peca_nao_aprovada_nao_publica_oferta_nem_historico(banco, status):
    _, p, cliente = banco
    o = oferta(p)
    p.status_validacao = status
    db.session.commit()
    assert cliente.get('/build/catalogo').json['pecas'] == []
    resposta = cliente.get(f'/build/catalogo/processador/{p.id}/ofertas/{o.id}/historico-precos')
    assert resposta.status_code == 404
    from models import BuildSalva
    with pytest.raises(ValueError, match='não encontrada'):
        BuildSalva.validar_estado({'titulo': 'Teste', 'componentes': {'processador': {'id': p.id}}})
