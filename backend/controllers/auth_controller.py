from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from models import lm

from services.usuario_service.entrar_usuario_service import EntrarUsuarioService

auth_bp = Blueprint("auth",__name__,url_prefix='/auth')

@auth_bp.post("/entrar")
def entrar_usuario():
    try:
        dados = request.get_json()

        service = EntrarUsuarioService()
        usuario = service.executar(dados)

        return jsonify({
            "mensagem":"Usuario logado com sucesso",
            "usuario": usuario
        }),200
    
    except ValueError as erro:
        return jsonify({"erro":f"Erro: {str(erro)}"}),400