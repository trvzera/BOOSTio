import secrets
import time

from flask import Blueprint, current_app, jsonify, redirect, request, session
from flask_login import current_user, login_required
from requests import RequestException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import Usuario, db
from services.usuario_service.discord_oauth import (
    ISSUER, buscar_identidade_discord, discord_configurado, url_autorizacao_discord,
)
from utils.limite_requisicoes import chave_usuario, limiter

discord_bp = Blueprint("discord", __name__, url_prefix="/auth/discord")
PENDENTE = "vinculo_discord_pendente"


@discord_bp.after_request
def proteger_resposta(resposta):
    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["Referrer-Policy"] = "no-referrer"
    return resposta


@discord_bp.get("")
@login_required
def consultar_vinculo():
    return jsonify(disponivel=discord_configurado(), nome=current_user.discord_username)


@discord_bp.post("/vincular")
@limiter.limit("5 per minute", key_func=chave_usuario)
@login_required
def vincular_discord():
    if current_user.discord_id is not None:
        return jsonify(erro="Desconecte a conta atual antes de conectar outra."), 409
    if not discord_configurado():
        return jsonify(erro="A conexão com o Discord está indisponível."), 503
    state, verificador = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    session[PENDENTE] = {
        "state": state, "verificador": verificador, "sessao": current_user.get_id(),
        "expira": time.time() + 300,
    }
    return jsonify(url=url_autorizacao_discord(state, verificador))


def _voltar(estado):
    frontend = current_app.config["FRONTEND_URL"].rstrip("/")
    return redirect(f"{frontend}/pages/configuracoes.html?discord={estado}#discord-settings")


@discord_bp.get("/callback")
@limiter.limit("20 per minute")
def callback_discord():
    pendente = session.get(PENDENTE)
    state = request.args.get("state", "")
    if (not pendente or not current_user.is_authenticated or current_user.get_id() != pendente["sessao"]
            or pendente["expira"] <= time.time() or not state.isascii()
            or not secrets.compare_digest(state, pendente["state"])):
        return _voltar("expirado")
    session.pop(PENDENTE)
    if request.args.get("error") == "access_denied":
        return _voltar("cancelado")
    code = request.args.get("code")
    if not code or len(code) > 2048 or request.args.get("iss", ISSUER) != ISSUER or not discord_configurado():
        return _voltar("erro")
    try:
        identificador, nome = buscar_identidade_discord(code, pendente["verificador"])
    except (RequestException, ValueError):
        return _voltar("erro")
    try:
        alteradas = Usuario.query.filter_by(
            id=current_user.id, ativo=True, versao_sessao=current_user.versao_sessao, discord_id=None,
        ).update({Usuario.discord_id: identificador, Usuario.discord_username: nome}, synchronize_session=False)
        db.session.commit()
        return _voltar("conectado" if alteradas else "conflito")
    except IntegrityError:
        db.session.rollback()
        return _voltar("conflito")
    except SQLAlchemyError:
        db.session.rollback()
        return _voltar("erro")


@discord_bp.delete("")
@limiter.limit("5 per minute", key_func=chave_usuario)
@login_required
def desvincular_discord():
    session.pop(PENDENTE, None)
    try:
        Usuario.query.filter_by(id=current_user.id, ativo=True, versao_sessao=current_user.versao_sessao).update(
            {Usuario.discord_id: None, Usuario.discord_username: None}, synchronize_session=False)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(erro="Não foi possível desconectar o Discord agora."), 503
    return "", 204
