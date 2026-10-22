from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from flask import Flask
from sqlalchemy import text

from models import db, mail, Codigo, Usuario
from migrations.codigos_email import migrar_codigos_email
from services.email_service.enviar_codigo_email_service import EnviarEmailService
from services.email_service.verificar_codigo_email_service import VerificarCodigoEmail


@pytest.fixture
def usuario():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    db.init_app(app)
    mail.init_app(app)
    with app.app_context():
        db.create_all()
        usuario = Usuario(nome="Teste", email="antigo@example.com")
        usuario.salvar()
        yield usuario
        db.session.remove()
        db.drop_all()


def emitir(usuario, codigo="123456"):
    with patch.object(EnviarEmailService, "_gerar_codigo", return_value=codigo), patch(
        "services.email_service.enviar_codigo_email_service.mail.send"
    ) as envio:
        EnviarEmailService().executar(usuario)
        assert envio.call_args.args[0].recipients == [usuario.email]
    return Codigo.buscar_codigo_recente(usuario.id)


def conferir(usuario, codigo):
    return VerificarCodigoEmail().executar({"codigo": codigo}, usuario)


def test_codigo_confirma_apenas_uma_vez_o_email_destinatario(usuario):
    codigo = emitir(usuario)
    assert codigo.email_destino == usuario.email
    assert conferir(usuario, "123456")["verificado"]
    with pytest.raises(ValueError):
        conferir(usuario, "123456")


def test_troca_de_email_invalida_codigo_e_exige_novo(usuario):
    antigo = emitir(usuario)
    usuario.atualizar_dados(email="novo@example.com")
    db.session.refresh(antigo)
    assert antigo.usado
    assert not usuario.verificado
    with pytest.raises(ValueError):
        conferir(usuario, "123456")
    antigo.criado_em = datetime.now(timezone.utc) - timedelta(seconds=31)
    db.session.commit()
    novo = emitir(usuario, "654321")
    assert novo.email_destino == "novo@example.com"
    assert conferir(usuario, "654321")["verificado"]


def test_reenvio_nao_ressuscita_codigo_antigo(usuario):
    antigo = emitir(usuario)
    antigo.criado_em = datetime.now(timezone.utc) - timedelta(seconds=31)
    db.session.commit()
    novo = emitir(usuario, "654321")
    db.session.refresh(antigo)
    assert antigo.usado
    with pytest.raises(ValueError):
        conferir(usuario, "123456")
    conferir(usuario, "654321")
    assert Codigo.buscar_codigo_recente(usuario.id).id == novo.id
    with pytest.raises(ValueError):
        conferir(usuario, "123456")


def test_confirmacao_carregada_antes_da_troca_nao_confirma_email_novo(usuario):
    codigo = emitir(usuario)
    usuario.atualizar_dados(email="novo@example.com")
    with pytest.raises(ValueError):
        codigo.confirmar_email()
    db.session.refresh(usuario)
    assert not usuario.verificado


def test_email_igual_preserva_confirmacao(usuario):
    emitir(usuario)
    conferir(usuario, "123456")
    usuario.atualizar_dados(email=usuario.email)
    assert usuario.verificado


def test_codigo_sem_destinatario_nao_confirma(usuario):
    Codigo(usuario_id=usuario.id, codigo="123456").salvar()
    with pytest.raises(ValueError):
        conferir(usuario, "123456")
    assert not usuario.verificado


def test_limite_de_tentativas_preservado(usuario):
    emitir(usuario)
    for _ in range(5):
        with pytest.raises(ValueError):
            conferir(usuario, "000000")
    with pytest.raises(ValueError, match="Limite"):
        conferir(usuario, "123456")
    assert not usuario.verificado


def test_codigo_expirado_nao_confirma(usuario):
    codigo = emitir(usuario)
    codigo.data_expiracao = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.session.commit()
    with pytest.raises(ValueError):
        conferir(usuario, "123456")


def test_migracao_invalida_legado_sem_invalidar_codigos_novos():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        with db.engine.begin() as conexao:
            conexao.execute(text("CREATE TABLE codigo (id INTEGER PRIMARY KEY, codigo TEXT, usado BOOLEAN)"))
            conexao.execute(text("INSERT INTO codigo VALUES (1, '123456', 0)"))
        migrar_codigos_email()
        with db.engine.begin() as conexao:
            assert conexao.execute(text("SELECT usado FROM codigo WHERE id=1")).scalar() == 1
            conexao.execute(text("INSERT INTO codigo (id,codigo,usado,email_destino) VALUES (2,'654321',0,'novo@example.com')"))
        migrar_codigos_email()
        with db.engine.begin() as conexao:
            assert conexao.execute(text("SELECT usado FROM codigo WHERE id=2")).scalar() == 0
        db.engine.dispose()
