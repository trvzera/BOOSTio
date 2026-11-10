import pytest
from flask import Flask
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models import db, Usuario
from migrations.google_usuario import migrar_google_usuario
from services.usuario_service.entrar_google_usuario_service import EntrarGoogleService


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def identidade(**alteracoes):
    return dict(sub="google-123", email="pessoa@example.com", email_verified=True,
                name="Pessoa") | alteracoes


def criar_usuario(**alteracoes):
    usuario = Usuario(**(dict(nome="Pessoa", email="pessoa@example.com", senha=None,
                             login_google=False, verificado=False, ativo=True) | alteracoes))
    usuario.salvar()
    return usuario


def test_cria_conta_e_reutiliza_sub_mesmo_com_email_google_alterado(banco):
    service = EntrarGoogleService()
    usuario = service.executar(identidade())
    assert usuario.google_sub == "google-123"
    assert usuario.verificado and usuario.login_google and usuario.senha is None
    assert service.executar(identidade(email="novo@example.com")).id == usuario.id
    assert Usuario.query.count() == 1
    assert usuario.email == "pessoa@example.com"


@pytest.mark.parametrize("verificado", [False, True])
def test_nao_vincula_conta_local_nem_altera_senha(banco, verificado):
    usuario = criar_usuario(senha="hash-original", verificado=verificado)
    with pytest.raises(ValueError, match="método original"):
        EntrarGoogleService().executar(identidade())
    db.session.refresh(usuario)
    assert usuario.google_sub is None
    assert usuario.senha == "hash-original"
    assert usuario.verificado == verificado
    assert not usuario.login_google


def test_migra_conta_google_legada_sem_senha(banco):
    usuario = criar_usuario(login_google=True, verificado=True)
    assert EntrarGoogleService().executar(identidade()).id == usuario.id
    db.session.refresh(usuario)
    assert usuario.google_sub == "google-123"


@pytest.mark.parametrize("alteracoes", [
    {"senha": "hash-original"}, {"verificado": False}, {"google_sub": "outro-sub"},
])
def test_nao_vincula_legado_ambiguo_ou_outro_sub(banco, alteracoes):
    criar_usuario(**(dict(login_google=True, verificado=True) | alteracoes))
    with pytest.raises(ValueError, match="método original"):
        EntrarGoogleService().executar(identidade())


@pytest.mark.parametrize("sub", [None, "google-123"])
def test_recusa_conta_desativada(banco, sub):
    criar_usuario(login_google=True, verificado=True, google_sub=sub, ativo=False)
    with pytest.raises(ValueError, match="desativada"):
        EntrarGoogleService().executar(identidade())


@pytest.mark.parametrize("dados", [None, {}, identidade(sub=None), identidade(sub=""),
    identidade(email=None), identidade(email_verified=False), identidade(email_verified="true")])
def test_recusa_identidade_incompleta_ou_nao_verificada(banco, dados):
    with pytest.raises(ValueError):
        EntrarGoogleService().executar(dados)
    assert Usuario.query.count() == 0


def test_sub_tem_unicidade_no_banco(banco):
    criar_usuario(google_sub="google-123")
    with pytest.raises(IntegrityError):
        criar_usuario(email="outra@example.com", google_sub="google-123")
    db.session.rollback()


def test_migracao_preserva_cadastro_antigo_e_pode_repetir():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        with db.engine.begin() as conexao:
            conexao.execute(text("CREATE TABLE usuario (id INTEGER PRIMARY KEY, email TEXT, senha TEXT)"))
            conexao.execute(text("INSERT INTO usuario VALUES (1, 'pessoa@example.com', 'hash-original')"))
        migrar_google_usuario()
        migrar_google_usuario()
        with db.engine.begin() as conexao:
            assert tuple(conexao.execute(text("SELECT * FROM usuario")).one()) == (
                1, "pessoa@example.com", "hash-original", None)
            conexao.execute(text("UPDATE usuario SET google_sub = 'google-123'"))
        with pytest.raises(IntegrityError):
            with db.engine.begin() as conexao:
                conexao.execute(text("INSERT INTO usuario VALUES (2, 'outra@example.com', NULL, 'google-123')"))
        db.session.remove()
        db.engine.dispose()
