import pytest
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from controllers.saude_controller import saude_bp
from models import db


@pytest.fixture
def app_saude():
    app=Flask(__name__)
    app.config.update(TESTING=True,SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    db.init_app(app)
    app.register_blueprint(saude_bp)
    yield app
    with app.app_context():
        db.session.remove();db.engine.dispose()


def test_health_consulta_repository_sem_criar_registros_ou_commit(app_saude,mocker):
    commit=mocker.patch.object(db.session,"commit",side_effect=AssertionError("commit indevido"))
    resposta=app_saude.test_client().get("/health")
    assert resposta.status_code==200 and resposta.json=={"status":"ok"}
    commit.assert_not_called()


def test_health_falha_controlada_preserva_status_http(app_saude,mocker):
    mocker.patch("repositories.saude_repository.SaudeRepository.verificar_conexao",side_effect=SQLAlchemyError("falha de teste"))
    resposta=app_saude.test_client().get("/health")
    assert resposta.status_code==503 and resposta.json=={"status":"indisponivel"}
