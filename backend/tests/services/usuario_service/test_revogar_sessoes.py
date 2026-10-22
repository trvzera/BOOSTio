import pytest
from flask import Flask, request
from flask_login import login_user, login_required
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from models import db, lm, Usuario, TokenRecuperacao
from migrations.sessao_usuario import migrar_sessao_usuario
from services.usuario_service.entrar_usuario_service import EntrarUsuarioService
from services.usuario_service.deletar_usuario_service import DeletarUsuarioService
from services.usuario_service.redefinir_senha_service import RedefinirSenhaService


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="apenas-testes", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    db.init_app(app)
    lm.init_app(app)

    @app.post("/login")
    def entrar():
        usuario = EntrarUsuarioService().executar(request.json)
        assert login_user(usuario, remember=True)
        return "ok"

    @app.get("/privado")
    @login_required
    def privado():
        return "ok"

    with app.app_context():
        db.create_all()
        Usuario(nome="Teste", email="teste@example.com", senha=generate_password_hash("Original.123")).salvar()
        Usuario(nome="Outro", email="outro@example.com", senha=generate_password_hash("Original.123")).salvar()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def entrar(cliente, email="teste@example.com", senha="Original.123"):
    assert cliente.post("/login", json={"email": email, "senha": senha}).status_code == 200
    assert cliente.get("/privado").status_code == 200


@pytest.mark.parametrize("operacao", ["recuperar", "excluir", "alterar"])
def test_revoga_dois_dispositivos_e_cookie_remember_sem_afetar_outro_usuario(app, operacao):
    primeiro, segundo, outro = [app.test_client() for _ in range(3)]
    entrar(primeiro)
    entrar(segundo)
    entrar(outro, email="outro@example.com")
    # Simula o segundo dispositivo dependendo apenas do cookie de lembrar login.
    segundo.delete_cookie(app.config["SESSION_COOKIE_NAME"])
    with app.app_context():
        usuario = Usuario.buscar_por_id(1)
        if operacao == "excluir":
            DeletarUsuarioService().executar(usuario.id, {"senha_atual": "Original.123"})
        elif operacao == "alterar":
            usuario.atualizar_dados(senha=generate_password_hash("NovaSenha.123"))
        else:
            TokenRecuperacao(usuario_id=usuario.id, token_hash=generate_password_hash("token-teste")).salvar()
            RedefinirSenhaService().executar({"token": "token-teste", "senha": "NovaSenha.123"})
    assert primeiro.get("/privado").status_code == 401
    assert segundo.get("/privado").status_code == 401
    assert outro.get("/privado").status_code == 200
    if operacao != "excluir":
        entrar(primeiro, senha="NovaSenha.123")


@pytest.mark.parametrize("identificador", ["1", "", "1:0", "1:abc", "1:1:1", "9" * 100 + ":1"])
def test_recusa_sessao_antiga_ou_invalida(app, identificador):
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = identificador
    assert cliente.get("/privado").status_code == 401


def test_conta_inativa_nao_autentica_nem_recupera_senha(app):
    with app.app_context():
        usuario = Usuario.buscar_por_id(1)
        usuario.atualizar_dados(ativo=False)
        with app.test_request_context():
            assert not login_user(usuario)
        with pytest.raises(ValueError):
            EntrarUsuarioService().executar({"email": usuario.email, "senha": "Original.123"})
        TokenRecuperacao(usuario_id=usuario.id, token_hash=generate_password_hash("token-teste")).salvar()
        with pytest.raises(ValueError, match="inválido"):
            RedefinirSenhaService().executar({"token": "token-teste", "senha": "NovaSenha.123"})
        assert Usuario.buscar_por_sessao(usuario.get_id()) is None


def test_migracao_preserva_usuario_e_e_idempotente():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        with db.engine.begin() as conexao:
            conexao.execute(text("CREATE TABLE usuario (id INTEGER PRIMARY KEY, nome TEXT)"))
            conexao.execute(text("INSERT INTO usuario VALUES (1, 'Teste')"))
        migrar_sessao_usuario()
        migrar_sessao_usuario()
        with db.engine.begin() as conexao:
            assert tuple(conexao.execute(text("SELECT * FROM usuario")).one()) == (1, "Teste", 1)
        db.engine.dispose()
