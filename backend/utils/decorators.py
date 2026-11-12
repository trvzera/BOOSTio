from functools import wraps
from flask import jsonify
from flask_login import current_user


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
