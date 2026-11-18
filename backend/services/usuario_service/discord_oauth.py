import base64
import hashlib
import re
from urllib.parse import urlencode

import requests
from flask import current_app

ISSUER = "https://discord.com"
API_DISCORD = ISSUER + "/api/v10"


def discord_configurado():
    return bool(current_app.config.get("DISCORD_CLIENT_ID") and current_app.config.get("DISCORD_CLIENT_SECRET"))


def uri_retorno_discord():
    api = current_app.config.get("API_PUBLIC_URL") or "http://127.0.0.1:5000"
    return api.rstrip("/") + "/auth/discord/callback"


def url_autorizacao_discord(state, verificador):
    digest = hashlib.sha256(verificador.encode("ascii")).digest()
    desafio = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return ISSUER + "/oauth2/authorize?" + urlencode({
        "client_id": current_app.config["DISCORD_CLIENT_ID"],
        "redirect_uri": uri_retorno_discord(),
        "response_type": "code",
        "scope": "identify",
        "state": state,
        "code_challenge": desafio,
        "code_challenge_method": "S256",
        "prompt": "consent",
    })


def buscar_identidade_discord(code, verificador):
    resposta = requests.post(
        API_DISCORD + "/oauth2/token",
        auth=(current_app.config["DISCORD_CLIENT_ID"], current_app.config["DISCORD_CLIENT_SECRET"]),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": uri_retorno_discord(),
            "code_verifier": verificador,
        },
        timeout=8,
        allow_redirects=False,
    )
    resposta.raise_for_status()
    dados_token = resposta.json() if resposta.status_code == 200 else None
    token = dados_token.get("access_token") if isinstance(dados_token, dict) else None
    if not isinstance(token, str) or not re.fullmatch(r"[!-~]{1,2048}", token):
        raise ValueError("Resposta de autorização inválida.")
    resposta = requests.get(
        API_DISCORD + "/users/@me",
        headers={"Authorization": "Bearer " + token},
        timeout=8,
        allow_redirects=False,
    )
    resposta.raise_for_status()
    dados = resposta.json() if resposta.status_code == 200 else None
    if not isinstance(dados, dict):
        raise ValueError("Perfil do Discord inválido.")
    identificador, nome = dados.get("id"), dados.get("username")
    if (not isinstance(identificador, str) or not re.fullmatch(r"[1-9][0-9]{0,19}", identificador)
            or not isinstance(nome, str) or not nome.strip() or len(nome) > 80):
        raise ValueError("Perfil do Discord inválido.")
    return identificador, nome
