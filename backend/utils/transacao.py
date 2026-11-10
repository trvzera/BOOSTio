from models import db


def desfazer_transacao_quebrada(_erro):
    """Se a requisição terminou com a transação quebrada, ela é desfeita aqui.

    Por isso os controllers não precisam chamar rollback."""
    if not db.session.is_active:
        db.session.rollback()


def configurar_transacao(app):
    app.teardown_request(desfazer_transacao_quebrada)
