from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user,logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from utils.decorators import apenas_proprio_usuario
from services.peca_service.mostrar_pecas_service import MostrarPecasService

peca_bp = Blueprint("peca",__name__,url_prefix='/pecas')

@peca_bp.get("/")
def mostrar_pecas():
    try:
        mostrar_pecas_service = MostrarPecasService()
        pecas = mostrar_pecas_service.executar()
        return jsonify({"Mensagem": "Peças buscadas com sucesso",
            "Pecas": pecas}), 200

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except Exception as e:
        return jsonify({"erro": "Ocorreu um erro ao buscar as peças.", "detalhes": str(e)}), 500
