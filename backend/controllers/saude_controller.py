from flask import Blueprint, jsonify
from redis import RedisError
from sqlalchemy.exc import SQLAlchemyError

from services.configuracao_service.verificar_saude_service import VerificarSaudeService


saude_bp = Blueprint("saude", __name__)


@saude_bp.get("/health")
def verificar_saude():
  try:
    VerificarSaudeService().executar()
    return jsonify({"status": "ok"}), 200
  except (SQLAlchemyError, RedisError, OSError):
    return jsonify({"status": "indisponivel"}), 503
