from flask import Blueprint, jsonify
from redis import RedisError
from sqlalchemy.exc import SQLAlchemyError

from services.configuracao_service.verificar_saude_service import VerificarSaudeService


saude_bp = Blueprint("saude", __name__)


class SaudeController:
    """Controller HTTP do recurso; métodos estáticos não compartilham estado de requisição."""

    @staticmethod
    @saude_bp.get("/health")
    def verificar_saude():
      try:
        VerificarSaudeService().executar()
        return jsonify({"status": "ok"}), 200
      except (SQLAlchemyError, RedisError, OSError):
        return jsonify({"status": "indisponivel"}), 503
