from email import message_from_bytes

import pytest
from flask import Flask
from flask_mail import Message

from models import mail
from services.email_service.enviar_codigo_email_service import EnviarEmailService


@pytest.fixture
def app_email():
    app = Flask(__name__)
    app.config.update(TESTING=True, MAIL_SUPPRESS_SEND=True, MAIL_DEFAULT_SENDER=("BOOSTio", "seguranca@example.test"))
    mail.init_app(app)
    return app


def test_mensagem_multipart_tem_codigo_expiracao_e_instrucao_sem_rastreamento(app_email):
    with app_email.app_context():
        msg = Message(subject="Seu código de verificação — BOOSTio", recipients=["qa@example.test"])
        EnviarEmailService._monta_mensagem(msg, "001234", "Giovanni")
        mime = message_from_bytes(msg.as_bytes())
    # Flask-Mail envolve as alternativas em multipart/mixed, mesmo sem anexos.
    assert {parte.get_content_type() for parte in mime.walk()} >= {"multipart/alternative", "text/plain", "text/html"}
    for corpo in (msg.body, msg.html):
        assert "001234" in corpo and "5 minutos" in corpo and "Giovanni" in corpo
        assert "não solicitou" in corpo and "Não compartilhe" in corpo
        assert "mais recente" in corpo
    assert 'lang="pt-BR"' in msg.html
    assert "<img" not in msg.html and "<script" not in msg.html and "https://" not in msg.html


def test_nome_e_escapado_e_codigo_nunca_aceita_html(app_email):
    with app_email.app_context():
        msg = Message()
        EnviarEmailService._monta_mensagem(msg, "123456", '<img src=x onerror="alert(1)">')
        assert "<img" not in msg.html
        assert "&lt;img" in msg.html
        for codigo in ("<script>", "12345", "1234567", "١٢٣٤٥٦", 123456, None):
            with pytest.raises(ValueError, match="Código"):
                EnviarEmailService._monta_mensagem(msg, codigo)
