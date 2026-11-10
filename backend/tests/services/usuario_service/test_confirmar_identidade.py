import time
from unittest.mock import patch

import pytest
from flask import Flask, redirect
from werkzeug.security import generate_password_hash
from authlib.integrations.base_client.errors import OAuthError

from models import db, lm, Usuario
from controllers.auth_controller import auth_bp
from controllers.usuario_controller import usuario_bp
from utils.csrf import configurar_csrf
from utils.limite_requisicoes import configurar_limites, limiter


@pytest.fixture
def app(monkeypatch):
    # Limiter é compartilhado: restaurar sua configuração ao encerrar o teste.
    monkeypatch.setattr(limiter, "enabled", limiter.enabled)
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="apenas-testes", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
                      FRONTEND_URL="https://boostio.example", RATELIMIT_ENABLED=False)
    db.init_app(app)
    lm.init_app(app)
    configurar_csrf(app)
    configurar_limites(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuario_bp)
    with app.app_context():
        db.create_all()
        Usuario(nome="Local", email="local@example.com", senha=generate_password_hash("Original.123"), verificado=True).salvar()
        Usuario(nome="Google", email="google@example.com", google_sub="google-123", login_google=True, verificado=True).salvar()
    with patch("controllers.auth_controller.oauth"):
        yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def cliente(app, usuario_id=1):
    client = app.test_client()
    with client.session_transaction() as sessao:
        sessao["_user_id"] = f"{usuario_id}:1"
        sessao["_fresh"] = True
        sessao["csrf_token"] = "teste-csrf"
    return client


def enviar(client, metodo, caminho, dados=None):
    return client.open(caminho, method=metodo, json=dados or {}, headers={"X-CSRF-Token": "teste-csrf"})


@pytest.mark.parametrize("operacao", ["PUT", "DELETE"])
@pytest.mark.parametrize("senha", [None, "errada", 123])
def test_conta_local_exige_senha_correta(app, operacao, senha):
    resposta = enviar(cliente(app), operacao, "/usuarios/1", {"email": "novo@example.com", "senha_atual": senha})
    assert resposta.status_code == 400
    with app.app_context():
        usuario = Usuario.buscar_por_id(1)
        assert usuario.email == "local@example.com" and usuario.ativo


@pytest.mark.parametrize("operacao", ["PUT", "DELETE"])
def test_conta_local_aceita_senha_correta(app, operacao):
    resposta = enviar(cliente(app), operacao, "/usuarios/1", {"email": "novo@example.com", "senha_atual": "Original.123"})
    assert resposta.status_code == (200 if operacao == "PUT" else 204)


def test_edicao_nome_ou_mesmo_email_nao_exige_senha(app):
    resposta = enviar(cliente(app), "PUT", "/usuarios/1", {"nome": "Novo nome", "email": "local@example.com"})
    assert resposta.status_code == 200


@pytest.mark.parametrize("senha", ["", " ", 123, True])
def test_senha_vazia_ou_invalida_nao_inutiliza_login(app, senha):
    client = cliente(app)
    assert enviar(client, "PUT", "/usuarios/1", {"senha": senha}).status_code == 400
    with app.app_context():
        assert db.session.get(Usuario, 1).versao_sessao == 1


def test_vincular_exige_login_csrf_e_senha_atual(app):
    assert app.test_client().post("/auth/google/vincular").status_code == 403
    client = cliente(app)
    assert client.post("/auth/google/vincular").status_code == 403
    assert enviar(client, "POST", "/auth/google/vincular").status_code == 400
    assert enviar(client, "POST", "/auth/google/vincular", {"senha_atual": "errada"}).status_code == 400


def iniciar_vinculo(client):
    with patch("controllers.auth_controller.oauth.google.authorize_redirect",
               return_value=redirect("https://accounts.google.com/o/oauth2/v2/auth?state=vinculo-teste")):
        assert enviar(client, "POST", "/auth/google/vincular", {"senha_atual": "Original.123"}).status_code == 200


def test_vinculo_explicito_preserva_email_senha_builds_e_revoga_sessoes_antigas(app):
    client, antiga = cliente(app), cliente(app)
    iniciar_vinculo(client)
    with patch("controllers.auth_controller.oauth.google.authorize_access_token",return_value={
        "userinfo":{"sub":"novo-google","email":"outra-identidade@example.com","email_verified":True}}):
        resposta=client.get("/auth/google/entrar?state=vinculo-teste")
    assert resposta.location.endswith("/pages/configuracoes.html?google=vinculado")
    assert antiga.get("/auth/me").json["auth"] is False
    dados=client.get("/auth/me").json["usuario"]
    assert dados["google_vinculado"] is True and dados["possui_senha"] is True
    assert dados["email"]=="local@example.com" and "google_sub" not in dados and "senha" not in dados
    with app.app_context():
        assert db.session.get(Usuario,1).google_sub=="novo-google"


@pytest.mark.parametrize("falha",["state","expirado","sessao","ocupado","nao_verificado"])
def test_vinculo_falho_nao_mescla_contas_nem_troca_usuario(app,falha):
    client=cliente(app);iniciar_vinculo(client)
    with client.session_transaction() as sessao:
        if falha=="expirado":sessao["vinculo_google_pendente"]={**sessao["vinculo_google_pendente"],"instante":time.time()-301}
        if falha=="sessao":sessao["vinculo_google_pendente"]={**sessao["vinculo_google_pendente"],"sessao":"2:1"}
    with patch("controllers.auth_controller.oauth.google.authorize_access_token",return_value={"userinfo":{
        "sub":"google-123" if falha=="ocupado" else "novo-google","email":"local@example.com","email_verified":falha!="nao_verificado"}}):
        resposta=client.get("/auth/google/entrar?state="+("errado" if falha=="state" else "vinculo-teste"))
    assert "google_erro=" in resposta.location
    assert client.get("/auth/me").json["usuario"]["id"]==1
    with app.app_context():
        assert db.session.get(Usuario,1).google_sub is None
        assert db.session.get(Usuario,2).google_sub=="google-123"


def test_conta_google_pode_criar_senha_so_com_confirmacao_recente(app):
    client=cliente(app,2)
    dados={"senha":"SenhaNova.123"}
    assert enviar(client,"PUT","/usuarios/2",dados).status_code==400
    with client.session_transaction() as sessao:
        sessao["confirmacao_google"]={"sessao":"2:1","sub":"google-123","instante":time.time()}
    assert enviar(client,"PUT","/usuarios/2",dados).status_code==200
    with app.app_context():
        usuario=db.session.get(Usuario,2)
        assert usuario.senha and usuario.google_sub=="google-123" and usuario.versao_sessao==2


@pytest.mark.parametrize("operacao", ["PUT", "DELETE"])
def test_google_sem_confirmacao_e_sem_csrf_recusados(app, operacao):
    client = cliente(app, 2)
    assert enviar(client, operacao, "/usuarios/2", {"email": "novo@example.com"}).status_code == 400
    assert client.post("/auth/google/confirmar").status_code == 403


def iniciar_google(client):
    with patch("controllers.auth_controller.oauth.google.authorize_redirect",
               return_value=redirect("https://accounts.google.com/o/oauth2/v2/auth?state=state-teste")):
        assert enviar(client, "POST", "/auth/google/confirmar").status_code == 200


@pytest.mark.parametrize("operacao", ["PUT", "DELETE"])
def test_google_confirma_mesma_conta_antes_da_acao(app, operacao):
    client = cliente(app, 2)
    iniciar_google(client)
    with patch("controllers.auth_controller.oauth.google.authorize_access_token", return_value={
        "userinfo": {"sub": "google-123", "email_verified": True}
    }):
        resposta = client.get("/auth/google/entrar?state=state-teste")
    assert resposta.location.endswith("/pages/configuracoes.html")
    assert enviar(client, operacao, "/usuarios/2", {"email": "novo@example.com"}).status_code == (200 if operacao == "PUT" else 204)


@pytest.mark.parametrize("falha", ["sub", "state", "expirado", "sessao"])
def test_callback_google_nao_confirma_identidade_errada(app, falha):
    client = cliente(app, 2)
    iniciar_google(client)
    if falha in ("expirado", "sessao"):
        with client.session_transaction() as sessao:
            pendente = sessao["confirmacao_google_pendente"]
            if falha == "expirado":
                pendente["instante"] = time.time() - 301
            else:
                pendente["sessao"] = "1:1"
            sessao["confirmacao_google_pendente"] = pendente
    with patch("controllers.auth_controller.oauth.google.authorize_access_token", return_value={
        "userinfo": {"sub": "outra-conta" if falha == "sub" else "google-123", "email_verified": True}
    }):
        client.get("/auth/google/entrar?state=" + ("errado" if falha == "state" else "state-teste"))
    with client.session_transaction() as sessao:
        assert "confirmacao_google" not in sessao
        assert sessao["_user_id"] == "2:1"


def test_confirmacao_google_expira_e_nao_substitui_senha_local(app):
    for usuario_id, instante in [(2, time.time() - 301), (1, time.time())]:
        client = cliente(app, usuario_id)
        with client.session_transaction() as sessao:
            sessao["confirmacao_google"] = {"sessao": f"{usuario_id}:1", "sub": "google-123", "instante": instante}
        assert enviar(client, "DELETE", f"/usuarios/{usuario_id}").status_code == 400


def test_google_cancelado_nao_libera_acao(app):
    client = cliente(app, 2)
    iniciar_google(client)
    with patch("controllers.auth_controller.oauth.google.authorize_access_token", side_effect=OAuthError("access_denied")):
        assert client.get("/auth/google/entrar?state=state-teste").status_code == 302
    assert enviar(client, "DELETE", "/usuarios/2").status_code == 400
