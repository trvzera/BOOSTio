from unittest.mock import patch

import pytest
from flask import Flask, jsonify, request, session, redirect

from controllers.auth_controller import auth_bp
from services.configuracao_service.configurar_acesso_service import ConfigurarAcessoService
from services.configuracao_service.gerar_configuracao_frontend_service import GerarConfiguracaoFrontendService


def criar_app(**alteracoes):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="apenas-testes", FRONTEND_URL="https://www.example.com/frontend",
                      API_PUBLIC_URL="https://api.example.com", SESSION_COOKIE_SAMESITE="Lax",
                      SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True)
    app.config.update(alteracoes)
    ConfigurarAcessoService().executar(app, producao=True)
    app.register_blueprint(auth_bp)

    @app.get("/verificar")
    def verificar():
        session["teste"] = True
        return jsonify(https=request.is_secure, ip=request.remote_addr)
    return app


def test_cors_cookies_e_preflight_csrf():
    client = criar_app().test_client()
    resposta = client.get("/verificar", base_url="https://api.example.com", headers={"Origin": "https://www.example.com"})
    assert resposta.headers["Access-Control-Allow-Origin"] == "https://www.example.com"
    assert resposta.headers["Access-Control-Allow-Credentials"] == "true"
    for atributo in ("Secure", "HttpOnly", "SameSite=Lax"):
        assert atributo in resposta.headers["Set-Cookie"]
    preflight = client.options("/verificar", base_url="https://api.example.com", headers={
        "Origin": "https://www.example.com", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "X-CSRF-Token,Content-Type",
    })
    assert "X-CSRF-Token" in preflight.headers["Access-Control-Allow-Headers"]
    resposta = client.get("/verificar", base_url="https://api.example.com", headers={"Origin": "https://intruso.example"})
    assert "Access-Control-Allow-Origin" not in resposta.headers


@pytest.mark.parametrize("confiar", [0, 1])
def test_proxy_respeita_apenas_cabecalhos_configurados(confiar):
    client = criar_app(TRUSTED_PROXY_HOPS=confiar, TRUSTED_PROXY_PROTO_HOPS=confiar).test_client()
    resposta = client.get("/verificar", base_url="http://api.example.com", headers={
        "X-Forwarded-For": "203.0.113.8", "X-Forwarded-Proto": "https", "X-Forwarded-Host": "intruso.example",
    })
    assert resposta.json["https"] == bool(confiar)
    assert resposta.json["ip"] == ("203.0.113.8" if confiar else "127.0.0.1")


def test_callback_fixo_mesmo_com_conexao_interna_http():
    client = criar_app(API_PUBLIC_URL="https://api.example.com/api").test_client()
    with patch("controllers.auth_controller.oauth") as oauth:
        oauth.google.authorize_redirect.return_value = redirect("https://accounts.google.com")
        assert client.get("/auth/google/redirecionar", base_url="http://api.example.com").status_code == 302
        oauth.google.authorize_redirect.assert_called_once_with("https://api.example.com/api/auth/google/entrar")
    assert client.get("/verificar", base_url="https://intruso.example").status_code == 400


@pytest.mark.parametrize("alteracoes", [
    {"FRONTEND_URL": None}, {"API_PUBLIC_URL": None}, {"API_PUBLIC_URL": "http://api.example.com"},
    {"FRONTEND_URL": "https://localhost"}, {"CORS_ORIGINS": "*"},
    {"CORS_ORIGINS": "https://www.example.com/frontend"}, {"TRUSTED_PROXY_HOPS": -1},
    {"TRUSTED_PROXY_PROTO_HOPS": -1}, {"API_PUBLIC_URL": "https://user:senha@api.example.com"},
])
def test_configuracao_invalida_recusada(alteracoes):
    with pytest.raises(ValueError):
        criar_app(**alteracoes)


def test_geracao_frontend_exporta_somente_endereco_publico(tmp_path):
    destino = tmp_path / "config-publica.js"
    GerarConfiguracaoFrontendService().executar({
        "FRONTEND_URL": "https://www.example.com", "API_PUBLIC_URL": "https://api.example.com/",
        "SESSION_COOKIE_SAMESITE": "Lax", "SECRET_KEY": "segredo-nao-exportar", "MAIL_PASSWORD": "senha-nao-exportar",
    }, destino, producao=True)
    texto = destino.read_text(encoding="utf-8")
    assert 'export const API_PUBLICA = "https://api.example.com";' in texto
    assert "nao-exportar" not in texto
