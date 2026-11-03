import base64
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlsplit, parse_qs
from unittest.mock import patch

import pytest
from flask import Flask, jsonify
from cryptography.fernet import Fernet
from models import db, AutorizacaoMercadoLivre, TokenIntegracao
from commands.mercadolivre import registrar_comandos_mercadolivre
from migrations.autorizacao_mercado_livre import preparar_autorizacao_mercado_livre
from controllers.mercadolivre_auth_controller import mercadolivre_auth_bp
from services.mercadolivre_service.autorizar_conta_service import AutorizarContaMercadoLivreService as Service
from utils.csrf import configurar_csrf, token_csrf
from utils.limite_requisicoes import limiter


@pytest.fixture
def contexto():
    app = Flask(__name__, template_folder='../../../templates')
    # Caminho absoluto evita depender de onde pytest é chamado.
    from pathlib import Path
    app.template_folder = str(Path(__file__).resolve().parents[3] / 'templates')
    app.config.update(SECRET_KEY='teste', SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        INTEGRACOES_TOKEN_CHAVE=Fernet.generate_key().decode(), MERCADO_LIVRE_CLIENT_ID='123',
        MERCADO_LIVRE_CLIENT_SECRET='secret', MERCADO_LIVRE_CONTA_ID='42',
        API_PUBLIC_URL='https://api.example.test', RATELIMIT_ENABLED=False, RATELIMIT_STORAGE_URI='memory://')
    anterior = limiter.enabled
    db.init_app(app); limiter.init_app(app); configurar_csrf(app)
    app.register_blueprint(mercadolivre_auth_bp); registrar_comandos_mercadolivre(app)
    @app.get('/auth/csrf')
    def csrf(): return jsonify(csrf_token=token_csrf())
    with app.app_context():
        TokenIntegracao.__table__.create(db.engine)
        assert preparar_autorizacao_mercado_livre()['criadas'] == ['autorizacao_mercado_livre']
        assert preparar_autorizacao_mercado_livre()['criadas'] == []
        yield app, Service()
        db.session.remove(); db.engine.dispose()
        limiter.enabled = anterior


def iniciar(service, navegador='n'*32):
    url = service.convite()
    convite = parse_qs(urlsplit(url).fragment)['convite'][0]
    params = parse_qs(urlsplit(service.iniciar(convite, navegador)).query)
    return convite, params


def resposta(**alteracoes):
    return dict(access_token='access-novo', refresh_token='refresh-novo', expires_in=21600,
                token_type='bearer', user_id=42, **alteracoes)


def test_pkce_cifrado_uso_unico_e_persistencia(contexto):
    _, service = contexto
    convite, params = iniciar(service)
    assert params['code_challenge_method'] == ['S256']
    with pytest.raises(ValueError): service.iniciar(convite, 'n'*32)
    row = AutorizacaoMercadoLivre.query.filter_by(tipo='estado').one()
    verifier = TokenIntegracao._cifra().decrypt(row.verificador_cifrado.encode()).decode()
    assert params['code_challenge'][0] == base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    with patch.object(Service, '_trocar', return_value=resposta()) as trocar:
        assert service.concluir(params['state'][0], 'n'*32, 'codigo') == {'conectado':True}
        assert trocar.call_args.args[0]['code_verifier'] == verifier
        with pytest.raises(ValueError): service.concluir(params['state'][0], 'n'*32, 'codigo')
        assert trocar.call_count == 1
    obj = TokenIntegracao.query.one()
    assert obj.access_token == 'access-novo' and not obj.renovacao_pendente
    assert 'access-novo' not in obj._access_token


def test_outro_navegador_e_estado_falso_nao_chamam_rede(contexto):
    _, service = contexto
    _, params = iniciar(service)
    with patch.object(Service, '_trocar') as trocar:
        for estado, navegador in [(params['state'][0], 'x'*32), ('x'*32,'n'*32)]:
            with pytest.raises(ValueError): service.concluir(estado, navegador, 'codigo')
        trocar.assert_not_called()
    assert not AutorizacaoMercadoLivre.query.filter_by(tipo='estado').one().consumido


def test_expirado_recusa_e_conta_errada_preservam_tokens(contexto):
    _, service = contexto
    _, params = iniciar(service)
    with patch.object(Service, '_trocar', return_value={**resposta(), 'user_id':99}):
        with pytest.raises(ValueError, match='conta autorizada difere'): service.concluir(params['state'][0],'n'*32,'codigo')
    assert TokenIntegracao.query.count() == 0
    _, params = iniciar(service)
    with patch.object(Service, '_trocar') as trocar:
        with pytest.raises(ValueError, match='recusada'): service.concluir(params['state'][0],'n'*32,None,recusado=True)
        trocar.assert_not_called()
    url = service.convite(); convite=parse_qs(urlsplit(url).fragment)['convite'][0]
    row=AutorizacaoMercadoLivre.query.filter_by(segredo_hash=service.hash(convite)).one()
    row.expira_em=datetime.now()-timedelta(hours=1); db.session.commit()
    with pytest.raises(ValueError): service.iniciar(convite,'n'*32)


def test_fluxo_http_csrf_sessao_e_callback(contexto):
    app, service = contexto
    cliente = app.test_client()
    page=cliente.get('/auth/mercadolivre/conectar')
    assert page.status_code==200 and b'Conectar Mercado Livre' in page.data
    assert page.headers['Cache-Control']=='no-store' and page.headers['Referrer-Policy']=='no-referrer'
    assert cliente.post('/auth/mercadolivre/conectar',json={'convite':'x'*32}).status_code==403
    csrf=cliente.get('/auth/csrf').json['csrf_token']
    convite=parse_qs(urlsplit(service.convite()).fragment)['convite'][0]
    inicio=cliente.post('/auth/mercadolivre/conectar',json={'convite':convite},headers={'X-CSRF-Token':csrf})
    assert inicio.status_code==200
    estado=parse_qs(urlsplit(inicio.json['url']).query)['state'][0]
    with patch.object(Service,'_trocar',return_value=resposta()) as trocar:
        assert app.test_client().get('/auth/mercadolivre/callback',query_string={'state':estado,'code':'codigo'}).status_code==400
        assert not trocar.called
        final=cliente.get('/auth/mercadolivre/callback',query_string={'state':estado,'code':'codigo'})
        assert final.status_code==200 and b'access-novo' not in final.data
        assert cliente.get('/auth/mercadolivre/callback',query_string={'state':estado,'code':'codigo'}).status_code==400


def test_config_insegura_e_parametros_duplicados(contexto):
    app, service=contexto
    app.config['MERCADO_LIVRE_REDIRECT_URI']='https://evil.test/auth/mercadolivre/callback'
    with pytest.raises(ValueError):service.convite()
    assert app.test_client().get('/auth/mercadolivre/callback?state=a&state=b&code=c').status_code==400


def test_reautorizacao_substitui_par_invalido_e_limpa_bloqueio(contexto):
    _, service=contexto
    from repositories.mercado_livre_token_repository import MercadoLivreTokenRepository
    import time
    repo=MercadoLivreTokenRepository('123','42')
    repo.ler();repo.salvar(dict(access_token='antigo',refresh_token='antigo-refresh',expires_at=time.time()-10,renovacao_pendente=True))
    _, params=iniciar(service)
    with patch.object(Service,'_trocar',return_value=resposta()):service.concluir(params['state'][0],'n'*32,'codigo')
    dados=repo.ler()
    assert dados['access_token']=='access-novo' and dados['refresh_token']=='refresh-novo' and not dados['renovacao_pendente']


@pytest.mark.parametrize('tipo',['http','json','grande','rede'])
def test_falhas_http_sanitizadas(contexto,tipo):
    from unittest.mock import Mock
    import requests
    response=Mock(status_code=200,headers={'Content-Type':'application/json'})
    response.iter_content.return_value=[b'{}']
    if tipo=='http':response.status_code=400
    if tipo=='json':response.iter_content.return_value=[b'nao-json']
    if tipo=='grande':response.iter_content.return_value=[b'x'*65537]
    with patch('services.mercadolivre_service.autorizar_conta_service.requests.post',return_value=response,
               side_effect=requests.Timeout('segredo') if tipo=='rede' else None):
        with pytest.raises(ValueError) as erro:Service._trocar({'code':'segredo'})
        assert 'segredo' not in str(erro.value)
    if tipo!='rede':response.close.assert_called_once()
