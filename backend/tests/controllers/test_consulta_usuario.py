import pytest
from flask import Flask

from controllers.usuario_controller import usuario_bp
from models import Usuario, db, lm
from services.usuario_service.listar_usuario_id_service import ListarUsuarioIdService


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="apenas-testes", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    db.init_app(app)
    lm.init_app(app)
    app.register_blueprint(usuario_bp)
    with app.app_context():
        db.create_all()
        Usuario(nome="Teste", email="teste@example.com", senha="hash-privado").salvar()
        Usuario(nome="Outro", email="outro@example.com").salvar()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_consulta_propria_conta_sem_expor_credenciais(app):
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = "1:1"
    resposta = cliente.get("/usuarios/1")
    assert resposta.status_code == 200
    assert resposta.json["usuario"]["id"] == 1
    assert resposta.json["usuario"]["email"] == "teste@example.com"
    assert not {"senha", "google_sub", "versao_sessao"} & resposta.json["usuario"].keys()


def test_consulta_exige_login_e_nao_permite_outra_conta(app):
    cliente = app.test_client()
    assert cliente.get("/usuarios/1").status_code == 401
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = "1:1"
    assert cliente.get("/usuarios/2").status_code == 403
    assert cliente.get("/usuarios/999").status_code == 403


def test_service_recusa_usuario_inexistente(app):
    with app.app_context(), pytest.raises(ValueError, match="não existe"):
        ListarUsuarioIdService().executar(999)
