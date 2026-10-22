import secrets

from flask import jsonify, request, session


def token_csrf():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def configurar_csrf(app):
    @app.before_request
    def verificar_csrf():
        if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return None

        token_esperado = session.get("csrf_token")
        token_recebido = request.headers.get("X-CSRF-Token", "")
        if not token_esperado or not secrets.compare_digest(token_esperado, token_recebido):
            return jsonify({"erro": "Token CSRF inválido. Atualize a página e tente novamente.", "codigo": "csrf-invalido"}), 403

        return None
