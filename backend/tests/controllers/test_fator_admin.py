import secrets
import time

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.twofactor.totp import TOTP
from flask import Flask
from werkzeug.security import generate_password_hash

from controllers.auth_controller import auth_bp
from controllers.admin_controller import admin_bp
from models import db, lm, Usuario, FatorAdmin
from utils.csrf import configurar_csrf


@pytest.fixture
def ambiente():
    app = Flask(__name__)
    chave = Fernet.generate_key()
    app.config.update(SECRET_KEY="teste", SQLALCHEMY_DATABASE_URI="sqlite://", ADMIN_2FA_CHAVE=chave,
                      RATELIMIT_STORAGE_URI="memory://")
    db.init_app(app)
    lm.init_app(app)
    configurar_csrf(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    segredo = secrets.token_bytes(20)
    with app.app_context():
        db.create_all()
        usuario = Usuario(nome="Admin", email="admin@example.test", verificado=True, administrador=True,
                          senha=generate_password_hash("teste"), google_sub="google-admin")
        db.session.add(usuario)
        db.session.flush()
        db.session.add(FatorAdmin(usuario_id=usuario.id, segredo_cifrado=Fernet(chave).encrypt(segredo), ultimo_intervalo=0))
        db.session.commit()
    return app.test_client(), TOTP(segredo, 6, SHA1(), 30)


def enviar(cliente, caminho, **dados):
    csrf = cliente.get("/auth/csrf").json["csrf_token"]
    return cliente.post(caminho, json=dados, headers={"X-CSRF-Token": csrf})


def senha(cliente):
    return enviar(cliente, "/auth/entrar", email="admin@example.test", senha="teste")


def test_admin_exige_segundo_fator_e_revoga_no_logout(ambiente):
    cliente, autenticador = ambiente
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = "1:1"
    assert cliente.get("/admin/pendencias").status_code == 401
    assert senha(cliente).status_code == 202
    assert cliente.get("/auth/me").json == {"auth": False, "usuario": None}
    assert enviar(cliente, "/admin/pendencias/1/rejeitar").status_code == 401
    assert enviar(cliente, "/auth/admin/confirmar", codigo="abc").status_code == 403
    codigo = autenticador.generate(int(time.time())).decode()
    assert enviar(cliente, "/auth/admin/confirmar", codigo=codigo).status_code == 200
    assert cliente.get("/admin/pendencias").status_code == 200
    cookie = cliente.get_cookie("session").value
    assert enviar(cliente, "/auth/sair").status_code == 200
    cliente.set_cookie("session", cookie)
    assert cliente.get("/admin/pendencias").status_code == 401
    assert senha(cliente).status_code == 202
    assert enviar(cliente, "/auth/admin/confirmar", codigo=codigo).status_code == 403


def test_google_admin_exige_codigo_e_desafio_expira(ambiente, mocker):
    cliente, _ = ambiente
    mocker.patch("controllers.auth_controller.oauth.google", create=True).authorize_access_token.return_value = {
        "userinfo": {"sub": "google-admin", "email": "admin@example.test", "email_verified": True}}
    cliente.application.config["FRONTEND_URL"] = "https://example.test"
    assert cliente.get("/auth/google/entrar").location.endswith("?etapa=autenticador")
    assert cliente.get("/admin/pendencias").status_code == 401
    with cliente.session_transaction() as sessao:
        sessao["desafio_admin"] = {"conta": "1:1", "expira": 0}
    assert enviar(cliente, "/auth/admin/confirmar", codigo="123456").status_code == 401


def test_cadastro_no_console_confirma_aparelho_antes_de_trocar(ambiente, mocker):
    from commands.usuarios import registrar_comandos_usuarios

    cliente, _ = ambiente
    app = cliente.application
    registrar_comandos_usuarios(app)
    runner = app.test_cli_runner()
    comando = ["admin-2fa-configurar", "--email", "admin@example.test"]
    with app.app_context():
        anterior = db.session.get(FatorAdmin, 1).segredo_cifrado
    assert runner.invoke(args=comando, input="invalido\n").exit_code != 0
    with app.app_context():
        assert db.session.get(FatorAdmin, 1).segredo_cifrado == anterior
    segredo = b"a" * 20
    mocker.patch("commands.usuarios.secrets.token_bytes", return_value=segredo)
    codigo = TOTP(segredo, 6, SHA1(), 30).generate(int(time.time())).decode()
    assert runner.invoke(args=comando, input=codigo + "\n").exit_code == 0
    with app.app_context():
        fator = db.session.get(FatorAdmin, 1)
        assert Fernet(app.config["ADMIN_2FA_CHAVE"]).decrypt(fator.segredo_cifrado) == segredo
        assert db.session.get(Usuario, 1).versao_sessao == 2
