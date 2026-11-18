from urllib.parse import parse_qs, urlsplit

import pytest
from flask import Flask
from sqlalchemy import inspect, text

from controllers.discord_controller import PENDENTE, discord_bp
from migrations.discord_usuario import preparar_discord_usuario
from models import Usuario, db, lm
from utils.csrf import configurar_csrf, token_csrf


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="teste", SQLALCHEMY_DATABASE_URI="sqlite://",
                      DISCORD_CLIENT_ID="123", DISCORD_CLIENT_SECRET="teste",
                      API_PUBLIC_URL="https://api.example.test", FRONTEND_URL="https://example.test")
    db.init_app(app)
    lm.init_app(app)
    configurar_csrf(app)
    app.register_blueprint(discord_bp)
    app.add_url_rule("/csrf", view_func=lambda: {"csrf_token": token_csrf()}, methods=["GET"])
    with app.app_context():
        db.create_all()
        db.session.add_all([Usuario(nome="A", email="a@example.test"), Usuario(nome="B", email="b@example.test")])
        db.session.commit()
    return app


def sessao(cliente, id_conta):
    with cliente.session_transaction() as dados:
        dados["_user_id"] = f"{id_conta}:1"


def cabecalho_csrf(cliente):
    return {"X-CSRF-Token": cliente.get("/csrf").json["csrf_token"]}


def iniciar(cliente):
    resposta = cliente.post("/auth/discord/vincular", headers=cabecalho_csrf(cliente))
    assert resposta.status_code == 200
    url = urlsplit(resposta.json["url"])
    assert url.netloc == "discord.com" and url.path == "/oauth2/authorize"
    parametros = parse_qs(url.query)
    assert parametros["scope"] == ["identify"]
    assert parametros["redirect_uri"] == ["https://api.example.test/auth/discord/callback"]
    assert parametros["code_challenge_method"] == ["S256"]
    return parametros["state"][0]


def retornar(cliente, state, **parametros):
    return cliente.get("/auth/discord/callback", query_string={"state": state, **parametros})


def test_vinculo_exige_login_e_csrf(app):
    cliente = app.test_client()
    assert cliente.get("/auth/discord").status_code == 401
    assert cliente.post("/auth/discord/vincular", headers=cabecalho_csrf(cliente)).status_code == 401
    sessao(cliente, 1)
    assert cliente.post("/auth/discord/vincular").status_code == 403
    assert cliente.delete("/auth/discord").status_code == 403


def test_vincula_uma_conta_e_permite_desconectar(app, mocker):
    consultar = mocker.patch("controllers.discord_controller.buscar_identidade_discord",
                             return_value=("123456789012345678", "discord_teste"))
    cliente = app.test_client()
    sessao(cliente, 1)
    state = iniciar(cliente)
    resposta = retornar(cliente, state, code="codigo-teste", iss="https://discord.com")
    assert resposta.location == "https://example.test/pages/configuracoes.html?discord=conectado#discord-settings"
    assert resposta.headers["Referrer-Policy"] == "no-referrer"
    assert cliente.get("/auth/discord").json == {"nome": "discord_teste", "disponivel": True}
    assert cliente.post("/auth/discord/vincular", headers=cabecalho_csrf(cliente)).status_code == 409
    assert "discord=expirado" in retornar(cliente, state, code="codigo-teste").location
    assert consultar.call_count == 1

    outra = app.test_client()
    sessao(outra, 2)
    assert "discord=conflito" in retornar(outra, iniciar(outra), code="codigo-teste").location
    assert outra.get("/auth/discord").json["nome"] is None

    assert cliente.delete("/auth/discord", headers=cabecalho_csrf(cliente)).status_code == 204
    assert cliente.get("/auth/discord").json["nome"] is None
    assert "discord=conectado" in retornar(outra, iniciar(outra), code="novo-codigo").location
    with app.app_context():
        conta = db.session.get(Usuario, 2)
        conta.desativar()
        assert conta.discord_id is None and conta.discord_username is None


def test_callback_recusa_estado_sessao_emissor_e_prazo_incorretos(app, mocker):
    consultar = mocker.patch("controllers.discord_controller.buscar_identidade_discord")
    cliente = app.test_client()
    sessao(cliente, 1)
    state = iniciar(cliente)
    assert "discord=expirado" in retornar(cliente, "outro-state", code="teste").location
    sessao(cliente, 2)
    assert "discord=expirado" in retornar(cliente, state, code="teste").location
    sessao(cliente, 1)
    assert "discord=erro" in retornar(cliente, state, code="teste", iss="https://example.test").location
    state = iniciar(cliente)
    assert "discord=cancelado" in retornar(cliente, state, error="access_denied").location
    state = iniciar(cliente)
    with cliente.session_transaction() as dados:
        dados[PENDENTE] = {**dados[PENDENTE], "expira": 0}
    assert "discord=expirado" in retornar(cliente, state, code="teste").location
    consultar.assert_not_called()


def test_migracao_preserva_conta_antiga_e_pode_ser_repetida(tmp_path):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path / 'legado.db'}"
    db.init_app(app)
    with app.app_context():
        with db.engine.begin() as conexao:
            conexao.execute(text("CREATE TABLE usuario (id INTEGER PRIMARY KEY, nome VARCHAR(30))"))
            conexao.execute(text("INSERT INTO usuario (id, nome) VALUES (1, 'Conta antiga')"))
        assert preparar_discord_usuario() == ["discord_id", "discord_username"]
        assert preparar_discord_usuario() == []
        with db.engine.connect() as conexao:
            assert conexao.execute(text("SELECT nome, discord_id, discord_username FROM usuario")).one() == (
                "Conta antiga", None, None)
        indices = inspect(db.engine).get_indexes("usuario")
        assert any(i["column_names"] == ["discord_id"] and i["unique"] for i in indices)
