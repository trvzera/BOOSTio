from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from smtplib import SMTPAuthenticationError
from unittest.mock import patch

import pytest
from flask import Flask
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, lm, mail, Usuario, TokenRecuperacao
from controllers.usuario_controller import usuario_bp
from migrations.tokens_recuperacao import migrar_tokens_recuperacao
from services.email_service.enviar_email_recuperar_service import EnviarEmailRecuperarService
from services.usuario_service.redefinir_senha_service import RedefinirSenhaService


@pytest.fixture
def app(tmp_path):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="apenas-testes", FRONTEND_URL="https://boostio.example",
                      SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'teste.db'}")
    db.init_app(app)
    lm.init_app(app)
    mail.init_app(app)
    app.register_blueprint(usuario_bp)
    with app.app_context():
        db.create_all()
        Usuario(nome="Teste", email="teste@example.com", senha=generate_password_hash("Original.123")).salvar()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def emitir():
    usuario = Usuario.buscar_por_id(1)
    return TokenRecuperacao.emitir(usuario, "token-teste")


def redefinir():
    return RedefinirSenhaService().executar({"token": "token-teste", "senha": "NovaSenha.123"})


def test_envio_guarda_so_hash_indexado_e_link_funciona(app):
    with app.app_context(), patch("services.email_service.enviar_email_recuperar_service.mail.send") as enviar:
        with patch.object(EnviarEmailRecuperarService, "_gerar_token", return_value="token-teste"):
            EnviarEmailRecuperarService().executar(Usuario.buscar_por_id(1))
        assert "token=token-teste" in enviar.call_args.args[0].body
        token = TokenRecuperacao.buscar_por_token("token-teste")
        assert len(token.token_hash) == 64 and "token-teste" not in token.token_hash
        assert any(i["column_names"] == ["token_hash"] for i in inspect(db.engine).get_indexes("token_recuperacao"))
        assert TokenRecuperacao.buscar_por_token("errado") is None
        redefinir()
        assert check_password_hash(Usuario.buscar_por_id(1).senha, "NovaSenha.123")
        assert Usuario.buscar_por_id(1).versao_sessao == 2
        with pytest.raises(ValueError):
            redefinir()


@pytest.mark.parametrize("alteracao", ["email", "senha", "inativo", "expirado", "reenviado"])
def test_links_invalidos_nao_alteram_senha(app, alteracao):
    with app.app_context():
        token = emitir()
        usuario = Usuario.buscar_por_id(1)
        if alteracao == "email":
            usuario.atualizar_dados(email="novo@example.com")
        elif alteracao == "senha":
            usuario.atualizar_dados(senha=generate_password_hash("OutraSenha.123"))
        elif alteracao == "inativo":
            usuario.atualizar_dados(ativo=False)
        elif alteracao == "expirado":
            token.data_expiracao = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.session.commit()
        else:
            TokenRecuperacao.emitir(usuario, "token-novo")
        senha_anterior = usuario.senha
        with pytest.raises(ValueError):
            redefinir()
        assert Usuario.buscar_por_id(1).senha == senha_anterior


def test_falha_commit_reverte_senha_token_e_sessao(app):
    with app.app_context():
        emitir()
        senha_anterior = Usuario.buscar_por_id(1).senha
        with patch.object(db.session, "commit", side_effect=SQLAlchemyError("falha simulada")):
            with pytest.raises(SQLAlchemyError):
                redefinir()
        assert Usuario.buscar_por_id(1).senha == senha_anterior
        assert Usuario.buscar_por_id(1).versao_sessao == 1
        assert TokenRecuperacao.buscar_por_token("token-teste") is not None


@pytest.mark.parametrize("senha", [123, "fraca", "x" * 1025])
def test_senha_invalida_nao_consumome_link(app, senha):
    with app.app_context():
        emitir()
        with pytest.raises(ValueError):
            RedefinirSenhaService().executar({"token": "token-teste", "senha": senha})
        assert TokenRecuperacao.buscar_por_token("token-teste") is not None


def test_duas_requisicoes_so_consumem_token_uma_vez(app):
    with app.app_context():
        emitir()
    def executar():
        with app.app_context():
            try:
                redefinir()
                return "ok"
            except ValueError:
                return "recusado"
    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(lambda _: executar(), range(2)))
    assert sorted(resultados) == ["ok", "recusado"]
    with app.app_context():
        assert Usuario.buscar_por_id(1).versao_sessao == 2


@pytest.mark.parametrize("fuso", [None, timezone.utc, timezone(timedelta(hours=-3))])
def test_expiracao_com_e_sem_fuso(fuso):
    agora = datetime.now(timezone.utc)
    expiracao = agora - timedelta(seconds=1)
    expiracao = expiracao.replace(tzinfo=None) if fuso is None else expiracao.astimezone(fuso)
    assert TokenRecuperacao(data_expiracao=expiracao).esta_expirado()


def test_resposta_publica_igual_com_email_inexistente_inativo_e_falha_smtp(app):
    client = app.test_client()
    inexistente = client.post("/usuarios/esqueci-senha", json={"email": "ninguem@example.com"})
    with patch("services.email_service.enviar_email_recuperar_service.mail.send", side_effect=SMTPAuthenticationError(535, b"segredo-smtp")):
        falha = client.post("/usuarios/esqueci-senha", json={"email": " TESTE@example.com "})
    with app.app_context():
        Usuario.buscar_por_id(1).atualizar_dados(ativo=False)
    with patch("services.email_service.enviar_email_recuperar_service.mail.send") as enviar:
        inativo = client.post("/usuarios/esqueci-senha", json={"email": "teste@example.com"})
        enviar.assert_not_called()
    assert inexistente.status_code == falha.status_code == inativo.status_code == 200
    assert inexistente.json == falha.json == inativo.json
    assert "segredo-smtp" not in falha.get_data(as_text=True)


def test_migracao_invalida_legado_e_preserva_tokens_novos():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        with db.engine.begin() as conexao:
            conexao.execute(text("CREATE TABLE token_recuperacao (id INTEGER PRIMARY KEY, token_hash TEXT, usado BOOLEAN)"))
            conexao.execute(text("INSERT INTO token_recuperacao VALUES (1, 'hash-legado', 0)"))
        migrar_tokens_recuperacao()
        with db.engine.begin() as conexao:
            assert conexao.execute(text("SELECT usado FROM token_recuperacao WHERE id=1")).scalar() == 1
            conexao.execute(text("INSERT INTO token_recuperacao VALUES (2, 'hash-novo', 0, 'teste@example.com', 1)"))
        migrar_tokens_recuperacao()
        with db.engine.begin() as conexao:
            assert conexao.execute(text("SELECT usado FROM token_recuperacao WHERE id=2")).scalar() == 0
        db.engine.dispose()
