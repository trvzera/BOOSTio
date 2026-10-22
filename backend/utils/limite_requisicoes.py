import hashlib

from flask import jsonify, request
from flask_login import current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def resposta_limite(_limite):
    resposta = jsonify({
        "erro": "Muitas tentativas. Aguarde antes de tentar novamente.",
        "codigo": "limite-requisicoes",
    })
    resposta.status_code = 429
    return resposta


limiter = Limiter(
    key_func=get_remote_address,
    headers_enabled=True,
    retry_after="delta-seconds",
    on_breach=resposta_limite,
)


def configurar_limites(app, producao=False):
    armazenamento = app.config.get("RATELIMIT_STORAGE_URI") or ""
    if producao and not armazenamento.startswith(("redis://", "rediss://")):
        raise RuntimeError("Configure RATELIMIT_STORAGE_URI com uma URL Redis em produção")
    limiter.init_app(app)


def chave_email():
    dados = request.get_json(silent=True)
    email = dados.get("email") if isinstance(dados, dict) else None
    if not isinstance(email, str) or not email.strip():
        return f"ip:{get_remote_address()}"
    normalizado = email.strip().casefold()
    return "email:" + hashlib.sha256(normalizado.encode("utf-8")).hexdigest()


def chave_usuario():
    if current_user.is_authenticated:
        return f"usuario:{current_user.id}"
    return f"ip:{get_remote_address()}"
