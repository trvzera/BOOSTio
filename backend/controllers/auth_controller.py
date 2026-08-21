from flask import Blueprint,request,jsonify,redirect,url_for
from flask_login import LoginManager, UserMixin, login_user,logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from models import lm
from configs import oauth
from services.usuario_service.entrar_usuario_service import EntrarUsuarioService
from services.usuario_service.entrar_google_usuario_service import EntrarGoogleService

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
@auth_bp.post("/sair")
@login_required
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


@auth_bp.get("/google/redirecionar")
def redirecionar_google():
    redirect_uri = url_for('auth.callback_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.get("/google/entrar")
def callback_google():
    try:
        token = oauth.google.authorize_access_token()
        dados_usuario = token.get('userinfo')

        usuario = EntrarGoogleService().executar(dados_usuario)
        login_user(usuario)

        return redirect('http://localhost:5500/pages/index.html') #Redirect obrigatorio, o google espera um retorno desse tipo
    except ValueError as erro:
        return redirect(f'http://localhost:5500/pages/login.html?erro={str(erro)}')