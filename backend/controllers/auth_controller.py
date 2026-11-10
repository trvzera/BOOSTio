from services.usuario_service.validar_retorno_google_service import validar_vinculo, validar_confirmacao
import time
from urllib.parse import urlencode
from flask import session
from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint,request,jsonify,redirect,url_for,current_app
from flask_login import login_user,logout_user, login_required, current_user
from configs import oauth
from services.usuario_service.entrar_usuario_service import EntrarUsuarioService
from services.usuario_service.estado_oauth_service import estado_da_autorizacao
from services.usuario_service.entrar_google_usuario_service import EntrarGoogleService
from services.usuario_service.vincular_google_service import VincularGoogleService
from services.usuario_service.confirmar_identidade_service import ConfirmarIdentidadeService
from utils.csrf import token_csrf
from utils.limite_requisicoes import limiter, chave_email, chave_usuario

auth_bp = Blueprint("auth",__name__,url_prefix='/auth')


@auth_bp.get("/csrf")
def obter_csrf():
    return jsonify({"csrf_token": token_csrf()}), 200


@auth_bp.after_request
def nao_armazenar_sessao(resposta):
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@auth_bp.post("/entrar")
@limiter.limit("20 per minute")
@limiter.limit("10 per 15 minutes", key_func=chave_email)
def entrar_usuario():
    try:
        dados = request.get_json()

        service = EntrarUsuarioService()
        usuario = service.executar(dados)

        session.pop("confirmacao_google", None)
        session.pop("confirmacao_google_pendente", None)
        session.pop("vinculo_google_pendente", None)
        login_user(usuario)

        return jsonify({
            "mensagem":"Usuario logado com sucesso",
            "usuario": usuario.to_dict()
        }),200

    except ValueError as erro:
        return jsonify({"erro":f"{str(erro)}"}),400


@auth_bp.post("/sair")
@login_required
def sair_usuario():
    session.pop("confirmacao_google", None)
    session.pop("confirmacao_google_pendente", None)
    session.pop("vinculo_google_pendente", None)
    logout_user()
    return jsonify({
        "mensagem":"Usuario deslogado com sucesso"
    }),200


@auth_bp.get("/me")
def teste_logado():
    if current_user.is_authenticated:
        return jsonify({
            "auth":True,
            "usuario":current_user.to_dict(incluir_budget=True, incluir_preferencias=True)
        }),200

    return jsonify({
                "auth":False,
                "usuario":None
            }),200


@auth_bp.get("/google/redirecionar")
@limiter.limit("20 per hour")
def redirecionar_google():
    session.pop("confirmacao_google_pendente", None)
    session.pop("vinculo_google_pendente", None)
    redirect_uri = _url_callback_google()
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.post("/google/confirmar")
@login_required
@limiter.limit("5 per minute")
def confirmar_google():
    if not current_user.google_sub:
        return jsonify({"erro": "Entre pelo Google novamente para identificar sua conta."}), 400
    session.pop("confirmacao_google", None)
    session.pop("vinculo_google_pendente", None)
    resposta = oauth.google.authorize_redirect(
        _url_callback_google(),
        prompt="select_account consent", login_hint=current_user.google_sub,
    )
    session["confirmacao_google_pendente"] = {
        "sessao": current_user.get_id(), "sub": current_user.google_sub,
        "instante": time.time(),
        "state": estado_da_autorizacao(resposta.location),
    }
    return jsonify({"url": resposta.location})


@auth_bp.post("/google/vincular")
@login_required
@limiter.limit("5 per minute", key_func=chave_usuario)
def vincular_google():
    if current_user.google_sub:
        return jsonify({"erro": "Sua conta já está vinculada ao Google"}),409
    try:
        ConfirmarIdentidadeService().executar(current_user, request.get_json(silent=True))
    except ValueError as erro:
        return jsonify({"erro": str(erro)}),400
    session.pop("confirmacao_google_pendente", None)
    session.pop("confirmacao_google", None)
    resposta = oauth.google.authorize_redirect(_url_callback_google(), prompt="select_account consent")
    session["vinculo_google_pendente"] = {
        "sessao": current_user.get_id(), "email": current_user.email, "instante": time.time(),
        "state": estado_da_autorizacao(resposta.location),
    }
    return jsonify({"url": resposta.location})


def _url_callback_google():
    return current_app.config.get("GOOGLE_REDIRECT_URI") or url_for('auth.callback_google', _external=True)


@auth_bp.get("/google/entrar")
def callback_google():
    vinculando = "vinculo_google_pendente" in session
    try:
        token = oauth.google.authorize_access_token()
        dados_usuario = token.get('userinfo')

        vinculo = session.pop("vinculo_google_pendente", None)
        if vinculo:
            validar_vinculo(current_user, vinculo, request.args.get("state"), time.time())
            usuario = VincularGoogleService().executar(current_user._get_current_object(), dados_usuario)
            login_user(usuario)
            base_url = current_app.config['FRONTEND_URL'].rstrip('/')
            return redirect(f'{base_url}/pages/configuracoes.html?google=vinculado')

        pendente = session.pop("confirmacao_google_pendente", None)
        if pendente:
            validar_confirmacao(current_user, pendente, dados_usuario, request.args.get("state"), time.time())
            session["confirmacao_google"] = {
                "sessao": current_user.get_id(), "sub": pendente["sub"], "instante": time.time(),
            }
            base_url = current_app.config['FRONTEND_URL'].rstrip('/')
            return redirect(f'{base_url}/pages/configuracoes.html')

        usuario = EntrarGoogleService().executar(dados_usuario)
        session.pop("confirmacao_google", None)
        login_user(usuario)

        base_url = current_app.config['FRONTEND_URL'].rstrip('/')
        return redirect(f'{base_url}/pages/index.html') #Redirect obrigatorio, o google espera um retorno desse tipo
    except ValueError as erro:
        base_url = current_app.config['FRONTEND_URL'].rstrip('/')
        if vinculando:
            return redirect(f'{base_url}/pages/configuracoes.html?{urlencode({"google_erro": str(erro)})}')
        return redirect(f'{base_url}/pages/login.html?{urlencode({"erro": str(erro)})}')
    except OAuthError:
        session.pop("vinculo_google_pendente", None)
        session.pop("confirmacao_google_pendente", None)
        session.pop("confirmacao_google", None)
        base_url = current_app.config['FRONTEND_URL'].rstrip('/')
        if vinculando:
            return redirect(f'{base_url}/pages/configuracoes.html?{urlencode({"google_erro": "Não foi possível confirmar com o Google. Tente novamente."})}')
        return redirect(f'{base_url}/pages/login.html?{urlencode({"erro": "Não foi possível confirmar com o Google. Tente novamente."})}')
