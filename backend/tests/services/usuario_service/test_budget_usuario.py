from decimal import Decimal

import pytest
from flask import Flask

from models import Usuario, db, lm
from controllers.usuario_controller import usuario_bp
from controllers.auth_controller import auth_bp
from services.usuario_service.atualizar_budget_usuario_service import AtualizarBudgetUsuarioService


@pytest.mark.parametrize("dados", [
    None, [], {}, {"budget": 100}, {"usar_budget": False},
    {"budget": 100, "usar_budget": True, "usuario_id": 2},
    *({"budget": valor, "usar_budget": False} for valor in [True, "100", -1, 1000000.01, 1.001, float("nan"), float("inf"), {}, []]),
    *({"budget": 100, "usar_budget": valor} for valor in [None, "false", 0, 1]),
    {"budget": None, "usar_budget": True}, {"budget": 0, "usar_budget": True},
])
def test_rejeita_budget_invalido_sem_alterar_usuario(dados, mocker):
    buscar = mocker.patch.object(Usuario, "buscar_por_id")
    with pytest.raises(ValueError):
        AtualizarBudgetUsuarioService().executar(1, dados)
    buscar.assert_not_called()


def test_usuario_inexistente(mocker):
    mocker.patch.object(Usuario, "buscar_por_id", return_value=None)
    assert AtualizarBudgetUsuarioService().executar(99, {"budget": 10, "usar_budget": False}) is None


@pytest.fixture
def app_budget(tmp_path):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="apenas-testes-budget", SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'contas.db'}")
    db.init_app(app)
    lm.init_app(app)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(auth_bp)
    with app.app_context():
        db.create_all()
        db.session.add_all([Usuario(nome="A", email="a@example.test"), Usuario(nome="B", email="b@example.test")])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def autenticar(cliente, usuario_id):
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = f"{usuario_id}:1"
        sessao["_fresh"] = True


def test_sessao_e_propriedade_sao_obrigatorias(app_budget):
    cliente = app_budget.test_client()
    assert cliente.put("/usuarios/1/budget", json={"budget": 5000, "usar_budget": True}).status_code == 401
    autenticar(cliente, 2)
    resposta = cliente.put("/usuarios/1/budget", json={"budget": 5000, "usar_budget": True})
    assert resposta.status_code == 403
    assert cliente.get("/auth/me").json["usuario"]["budget"] is None
    assert all("budget" not in usuario and "usar_budget" not in usuario for usuario in cliente.get("/usuarios/").json["usuarios"])


def test_persiste_centavos_entre_sessoes_sem_alterar_outra_conta(app_budget):
    cliente = app_budget.test_client()
    autenticar(cliente, 1)
    resposta = cliente.put("/usuarios/1/budget", json={"budget": 5432.10, "usar_budget": True})
    assert resposta.status_code == 200
    assert resposta.json["usuario"]["budget"] == 5432.1
    assert resposta.headers["Cache-Control"] == "no-store"
    outro_navegador = app_budget.test_client()
    autenticar(outro_navegador, 1)
    perfil = outro_navegador.get("/auth/me")
    assert perfil.json["usuario"]["budget"] == 5432.1
    assert perfil.json["usuario"]["usar_budget"] is True
    assert perfil.headers["Cache-Control"] == "no-store"
    autenticar(outro_navegador, 2)
    assert outro_navegador.get("/auth/me").json["usuario"]["budget"] is None
    with app_budget.app_context():
        assert db.session.get(Usuario, 1).budget == Decimal("5432.10")


@pytest.mark.parametrize("budget,usar", [(None, False), (0, False), (1000000, True), (0.01, True)])
def test_limites_e_remocao(app_budget, budget, usar):
    cliente = app_budget.test_client()
    autenticar(cliente, 1)
    resposta = cliente.put("/usuarios/1/budget", json={"budget": budget, "usar_budget": usar})
    assert resposta.status_code == 200
    assert resposta.json["usuario"]["budget"] == budget
    assert resposta.json["usuario"]["usar_budget"] == usar


def test_entrada_invalida_nao_apaga_valor_salvo(app_budget):
    cliente = app_budget.test_client()
    autenticar(cliente, 1)
    cliente.put("/usuarios/1/budget", json={"budget": 5000, "usar_budget": True})
    for dados in [{}, [], {"budget": -1, "usar_budget": True}, {"budget": None, "usar_budget": True}]:
        assert cliente.put("/usuarios/1/budget", json=dados).status_code == 400
    assert cliente.put("/usuarios/1/budget", data="{bad", content_type="application/json").status_code == 400
    assert cliente.get("/auth/me").json["usuario"]["budget"] == 5000


def test_falha_de_banco_nao_retorna_sucesso(app_budget, mocker):
    from sqlalchemy.exc import SQLAlchemyError
    cliente = app_budget.test_client()
    autenticar(cliente, 1)
    mocker.patch.object(Usuario, "atualizar_budget", side_effect=SQLAlchemyError("teste"))
    resposta = cliente.put("/usuarios/1/budget", json={"budget": 100, "usar_budget": False})
    assert resposta.status_code == 500
    assert cliente.get("/auth/me").json["usuario"]["budget"] is None
