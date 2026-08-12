from functools import wraps
from flask import jsonify
from flask_login import current_user


def apenas_proprio_usuario(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.id != args[0]:
            return jsonify({"erro": "Sem autorização"}), 403
        return func(*args, **kwargs)
    return wrapper      