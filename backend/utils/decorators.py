from functools import wraps
from flask import current_app, jsonify
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError


def usuario_atual_e_administrador():
    return bool(getattr(current_user, "administrador", False))


def exceto_administrador(func):
    """Pula a função (e devolve None) quando o usuário logado é administrador."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if usuario_atual_e_administrador():
            return None
        return func(*args, **kwargs)
    return wrapper


def apenas_proprio_usuario(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.id != kwargs.get('usuario_id'):
            return jsonify({"erro": "Sem autorização"}), 403
        return func(*args, **kwargs)
    return wrapper      


def apenas_administrador(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(current_user, "administrador", False):
            return jsonify({"erro": "Acesso restrito a administradores", "codigo": "sem-permissao"}), 403
        return func(*args, **kwargs)
    return wrapper


def tratar_erros(mensagem_banco=None, status_valor=400, status_banco=500, mensagem_inesperada=None, repassar=()):
    """Resposta padrão de erro para a rota.

    ValueError vira `status_valor` com a mensagem do erro. Falha de banco desfaz a transação e devolve
    `mensagem_banco` (sem ela, a falha de banco segue adiante). `mensagem_inesperada` captura o resto como 500.
    Os erros em `repassar` seguem para os errorhandlers do blueprint.
    """
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from models import db
            try:
                return func(*args, **kwargs)
            except repassar:
                raise
            except ValueError as erro:
                return jsonify({"erro": str(erro)}), status_valor
            except SQLAlchemyError:
                db.session.rollback()
                if mensagem_banco is None:
                    raise
                current_app.logger.exception("Falha no banco em %s", func.__name__)
                return jsonify({"erro": mensagem_banco}), status_banco
            except Exception:
                if mensagem_inesperada is None:
                    raise
                current_app.logger.exception("Erro inesperado em %s", func.__name__)
                return jsonify({"erro": mensagem_inesperada}), 500
        return wrapper
    return decorador
