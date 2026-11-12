from flask_login import current_user


def usuario_atual_e_administrador():
    return bool(getattr(current_user, "administrador", False))
