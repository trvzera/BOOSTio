import json
from cryptography.fernet import Fernet
from models import db, TokenIntegracao
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pytest
import requests
from flask import Flask

from repositories.mercado_livre_token_repository import MercadoLivreTokenRepository
from services.mercadolivre_service.token_mercado_livre_service import TokenMercadoLivreService

@pytest.fixture
def contexto(tmp_path):
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'tokens.db'),
                      INTEGRACOES_TOKEN_CHAVE=Fernet.generate_key().decode(),
                      MERCADO_LIVRE_CLIENT_ID='123', MERCADO_LIVRE_CLIENT_SECRET='secret',
                      MERCADO_LIVRE_CONTA_ID='42')
    db.init_app(app)
    with app.app_context():
        TokenIntegracao.__table__.create(db.engine)
        repo = MercadoLivreTokenRepository('123', '42')
        with repo.bloquear():
            repo.ler()
            repo.salvar({'access_token':'access-inicial', 'refresh_token':'refresh-inicial',
                         'expires_at':0, 'renovacao_pendente':False})
        yield app
        db.session.remove()
        db.engine.dispose()


def resposta(**changes):
    d = dict(access_token='novo-access', refresh_token='novo-refresh', expires_in=21600, token_type='bearer')
    d.update(changes)
    return Mock(status_code=200, headers={'Content-Type':'application/json'},
                iter_content=Mock(return_value=[json.dumps(d).encode()]))


def test_rotacao_persistida_e_reuso_apos_reinicio(contexto):
    r=resposta()
    with patch('requests.post',return_value=r) as post:
        s=TokenMercadoLivreService(relogio=lambda:1000)
        assert s.executar()=='novo-access'
        assert TokenMercadoLivreService(relogio=lambda:1100).executar()=='novo-access'
        post.assert_called_once()
        d=s.repository.ler()
        assert d['refresh_token']=='novo-refresh' and d['expires_at']==22600
        assert TokenIntegracao.query.one()._refresh_token != 'novo-refresh'
        assert post.call_args.kwargs['allow_redirects'] is False
    r.close.assert_called_once()


def test_segunda_rotacao_usa_refresh_mais_recente(contexto):
    s=TokenMercadoLivreService(relogio=lambda:1000)
    with patch('requests.post',return_value=resposta()): s.executar()
    with patch('requests.post',return_value=resposta(access_token='access-2',refresh_token='refresh-2')) as post:
        assert TokenMercadoLivreService(relogio=lambda:23000).executar()=='access-2'
        assert post.call_args.kwargs['data']['refresh_token']=='novo-refresh'


@pytest.mark.parametrize('falha',['timeout','403','json','incompleta'])
def test_resultado_incerto_nao_reutiliza_refresh(contexto,falha):
    r=resposta()
    if falha=='403': r.status_code=403
    if falha=='json': r.iter_content.return_value=[b'{']
    if falha=='incompleta': r=resposta(refresh_token=None)
    with patch('requests.post',side_effect=requests.Timeout('secret') if falha=='timeout' else None,return_value=r) as post:
        s=TokenMercadoLivreService(relogio=lambda:1000)
        with pytest.raises(ValueError) as e: s.executar()
        assert 'secret' not in str(e.value)
        with pytest.raises(ValueError,match='inconclusiva'): s.executar()
        post.assert_called_once()


def test_sem_client_secret_nao_consume_refresh(contexto):
    contexto.config['MERCADO_LIVRE_CLIENT_SECRET']=None
    with patch('requests.post') as post,pytest.raises(ValueError): TokenMercadoLivreService().executar()
    post.assert_not_called()


def test_sem_registro_nao_usa_fallback_env(contexto):
    TokenIntegracao.query.delete(); db.session.commit()
    contexto.config['MERCADO_LIVRE_ACCESS_TOKEN']='estatico'
    with patch('requests.post') as post,pytest.raises(ValueError, match='Cadastre'):
        TokenMercadoLivreService().executar()
    post.assert_not_called()


def test_concorrencia_reserva_uma_unica_renovacao(contexto):
    config=dict(contexto.config)
    def executar(_):
        app=Flask(__name__); app.config.update(config)
        db.init_app(app)
        with app.app_context():
            try: return TokenMercadoLivreService(relogio=lambda:1000).executar()
            except ValueError: return 'concorrente'
            finally: db.session.remove()
    with patch('requests.post',return_value=resposta()) as post,ThreadPoolExecutor(max_workers=2) as pool:
        resultados=list(pool.map(executar,range(2)))
        assert 'novo-access' in resultados
        assert all(r in ('novo-access','concorrente') for r in resultados)
        post.assert_called_once()


def test_tokens_corrompidos_nao_consultam_api(contexto):
    token=TokenIntegracao.query.one(); token._refresh_token='adulterado'; db.session.commit()
    with patch('requests.post') as post,pytest.raises(ValueError): TokenMercadoLivreService().executar()
    post.assert_not_called()


def test_comando_registra_sem_exibir_segredos(contexto):
    from commands.precos import registrar_comandos_precos
    registrar_comandos_precos(contexto)
    resultado=contexto.test_cli_runner().invoke(args=['mercadolivre-tokens-configurar'],
                                               input='access-inicial\nrefresh-inicial\n')
    assert resultado.exit_code==0
    assert 'access-inicial' not in resultado.output and 'refresh-inicial' not in resultado.output
    dados=MercadoLivreTokenRepository('123','42').ler()
    assert dados['refresh_token']=='refresh-inicial' and dados['renovacao_pendente'] is False


@pytest.mark.parametrize('changes',[{'token_type':None},{'expires_in':True},{'expires_in':0}])
def test_resposta_renovacao_invalida(contexto,changes):
    with patch('requests.post',return_value=resposta(**changes)),pytest.raises(ValueError):
        TokenMercadoLivreService().executar()
