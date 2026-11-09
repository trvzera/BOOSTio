from functools import wraps
from flask import jsonify
from flask_login import current_user


def apenas_proprio_usuario(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.id != kwargs.get('usuario_id'):
            return jsonify({"erro": "Sem autorização"}), 403
        return func(*args, **kwargs)
    return wrapper      


def apenas_administrador(func):
    """Usar depois de @login_required: quem não é administrador recebe 403, mesmo que digite a rota."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(current_user, "administrador", False):
            return jsonify({"erro": "Acesso restrito a administradores", "codigo": "sem-permissao"}), 403
        return func(*args, **kwargs)
    return wrapper
