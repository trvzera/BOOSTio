from flask import Flask, jsonify

from controllers.auth_controller import auth_bp
from utils.csrf import configurar_csrf


def criar_app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="segredo-somente-para-testes")
    configurar_csrf(app)
    app.register_blueprint(auth_bp)

    @app.post("/alterar")
    def alterar():
        return jsonify({"alterado": True})

    return app


def test_requisicoes_que_alteram_dados_exigem_token_csrf():
    app = criar_app()
    cliente = app.test_client()

    assert cliente.post("/alterar").status_code == 403

    resposta_token = cliente.get("/auth/csrf")
    assert resposta_token.status_code == 200
    assert resposta_token.headers["Cache-Control"] == "no-store"
    token = resposta_token.json["csrf_token"]

    assert cliente.post("/alterar", headers={"X-CSRF-Token": "invalido"}).status_code == 403
    assert cliente.post("/alterar", headers={"X-CSRF-Token": token}).json == {"alterado": True}
    assert cliente.get("/auth/csrf").json["csrf_token"] == token


def test_token_de_outra_sessao_nao_funciona():
    app = criar_app()
    primeiro = app.test_client()
    segundo = app.test_client()

    token = primeiro.get("/auth/csrf").json["csrf_token"]
    segundo.get("/auth/csrf")

    resposta = segundo.post("/alterar", headers={"X-CSRF-Token": token})
    assert resposta.status_code == 403
    assert resposta.json["codigo"] == "csrf-invalido"
