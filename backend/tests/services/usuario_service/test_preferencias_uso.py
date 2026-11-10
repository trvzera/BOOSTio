from flask import Flask
import pytest
from sqlalchemy.exc import SQLAlchemyError

from models import db, lm, Usuario, PreferenciasUso
from controllers.usuario_controller import usuario_bp
from controllers.auth_controller import auth_bp
from commands.banco import registrar_comandos_banco
from services.usuario_service.atualizar_preferencias_uso_service import AtualizarPreferenciasUsoService
from services.usuario_service.criar_usuario_service import CriarUsuarioService
from services.usuario_service.entrar_google_usuario_service import EntrarGoogleService
from utils.csrf import configurar_csrf


@pytest.fixture
def app_experiencia(tmp_path):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="testes-preferencias", SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'experiencia.db'}")
    db.init_app(app); lm.init_app(app)
    app.register_blueprint(usuario_bp); app.register_blueprint(auth_bp)
    registrar_comandos_banco(app)
    with app.app_context():
        db.create_all()
        Usuario(nome="Antigo", email="antigo@example.com", budget=5000, usar_budget=True).salvar()
        Usuario(nome="Outro", email="outro@example.com").salvar()
    yield app
    with app.app_context():
        db.session.remove(); db.engine.dispose()


def autenticar(cliente, id=1):
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = f"{id}:1"; sessao["_fresh"] = True


@pytest.mark.parametrize("dados", [None, [], {}, {"nivel_hardware": "avancado"},
    {"nivel_hardware": True}, {"nivel_hardware": []}, {"usuario_id": 2},
    {"tutorial": "pendente"}, {"tutorial": "nao-oferecido"}, {"tutorial": None},
    {"tutorial": []}, {"versao_tutorial": 100}, {"nivel_hardware": "iniciante", "budget": 1}])
def test_rejeita_entrada_sem_consultar_ou_alterar_conta(dados, mocker):
    busca = mocker.patch.object(Usuario, "buscar_por_id")
    with pytest.raises(ValueError): AtualizarPreferenciasUsoService().executar(1, dados)
    busca.assert_not_called()


def test_apenas_proprio_usuario_autenticado_altera_preferencias(app_experiencia):
    c = app_experiencia.test_client()
    url = "/usuarios/1/preferencias-uso"
    assert c.put(url, json={"nivel_hardware": "iniciante"}).status_code == 401
    autenticar(c, 2)
    assert c.put(url, json={"nivel_hardware": "iniciante"}).status_code == 403
    assert c.get("/auth/me").json["usuario"]["preferencias_uso"]["tutorial"] == "nao-oferecido"


def test_contas_antigas_nao_recebem_tutorial_automatico_e_persistem_preferencia(app_experiencia):
    c = app_experiencia.test_client(); autenticar(c)
    assert c.get("/auth/me").json["usuario"]["preferencias_uso"] == {
        "nivel_hardware": None, "tutorial": "nao-oferecido", "versao_tutorial": 1}
    resposta = c.put("/usuarios/1/preferencias-uso", json={"nivel_hardware": "iniciante", "tutorial": "concluido"})
    assert resposta.status_code == 200 and resposta.headers["Cache-Control"] == "no-store"
    outro = app_experiencia.test_client(); autenticar(outro)
    usuario = outro.get("/auth/me").json["usuario"]
    assert usuario["preferencias_uso"]["nivel_hardware"] == "iniciante"
    assert usuario["preferencias_uso"]["tutorial"] == "concluido"
    assert usuario["budget"] == 5000 and usuario["usar_budget"]
    outro.put("/usuarios/1/preferencias-uso", json={"nivel_hardware": None})
    assert outro.get("/auth/me").json["usuario"]["preferencias_uso"]["tutorial"] == "concluido"
    with app_experiencia.app_context():
        assert "preferencias_uso" not in db.session.get(Usuario, 1).to_dict()
        assert db.session.get(Usuario, 2).preferencias_uso is None


def test_cadastro_normal_e_google_oferecem_tutorial_sem_reiniciar_no_login(app_experiencia):
    with app_experiencia.app_context():
        normal = CriarUsuarioService().executar({"nome": "Novo", "email": "novo@example.com", "senha": "Senha.000"})
        assert normal.preferencias_uso.tutorial == "pendente"
        google = EntrarGoogleService().executar({"sub": "google-novo", "email_verified": True, "email": "google@example.com"})
        assert google.preferencias_uso.tutorial == "pendente"
        AtualizarPreferenciasUsoService().executar(google.id, {"tutorial": "pulado"})
        repetido = EntrarGoogleService().executar({"sub": "google-novo", "email_verified": True, "email": "google@example.com"})
        assert repetido.preferencias_uso.tutorial == "pulado"


def test_csrf_e_necessario_sem_restringir_consulta(app_experiencia):
    configurar_csrf(app_experiencia)
    c = app_experiencia.test_client(); autenticar(c)
    assert c.put("/usuarios/1/preferencias-uso", json={"tutorial": "pulado"}).status_code == 403
    token = c.get("/auth/csrf").json["csrf_token"]
    assert c.put("/usuarios/1/preferencias-uso", json={"tutorial": "pulado"}, headers={"X-CSRF-Token": token}).status_code == 200


def test_falha_de_gravacao_nao_mente_sobre_conclusao(app_experiencia, mocker):
    c = app_experiencia.test_client(); autenticar(c)
    mocker.patch.object(db.session, "commit", side_effect=SQLAlchemyError("erro interno"))
    r = c.put("/usuarios/1/preferencias-uso", json={"tutorial": "concluido"})
    assert r.status_code == 500 and "erro interno" not in r.text
    mocker.stopall()
    assert c.get("/auth/me").json["usuario"]["preferencias_uso"]["tutorial"] == "nao-oferecido"


def test_preparacao_cria_so_tabela_nova_sem_alterar_usuarios(app_experiencia):
    with app_experiencia.app_context():
        PreferenciasUso.__table__.drop(db.engine)
    runner = app_experiencia.test_cli_runner()
    for _ in range(2): assert runner.invoke(args=["preferencias-preparar"]).exit_code == 0
    with app_experiencia.app_context():
        assert Usuario.query.count() == 2
        assert db.session.get(Usuario, 1).nome == "Antigo"
        assert PreferenciasUso.query.count() == 0
