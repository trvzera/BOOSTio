from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user,logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from models import lm

from services.usuario_service.entrar_usuario_service import EntrarUsuarioService

auth_bp = Blueprint("auth",__name__,url_prefix='/auth')

#Rota de login
@auth_bp.post("/entrar")
def entrar_usuario():
    try:
        dados = request.get_json()

        service = EntrarUsuarioService()
        usuario = service.executar(dados)

        login_user(usuario)

        return jsonify({
            "mensagem":"Usuario logado com sucesso",
            "usuario": usuario.to_dict()
        }),200
    
    except ValueError as erro:
        return jsonify({"erro":f"{str(erro)}"}),400

#Rota de logout
@login_required
@auth_bp.post("/sair")
def sair_usuario():
    logout_user()
    return jsonify({
        "mensagem":"Usuario deslogado com sucesso"
    }),200

#Rota para teste do front se esta logado
@auth_bp.get("/me")
def teste_logado():
    if current_user.is_authenticated:
        return jsonify({
            "auth":True,
            "usuario":current_user.to_dict()
        }),200

    return jsonify({
                "auth":False,
                "usuario":None
            }),200