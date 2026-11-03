import secrets
from flask import Blueprint, jsonify, request, session, render_template, g
from sqlalchemy.exc import SQLAlchemyError
from services.mercadolivre_service.autorizar_conta_service import AutorizarContaMercadoLivreService
from utils.limite_requisicoes import limiter

mercadolivre_auth_bp = Blueprint('mercadolivre_auth', __name__, url_prefix='/auth/mercadolivre')


@mercadolivre_auth_bp.after_request
def proteger_resposta(resposta):
    resposta.headers['Cache-Control'] = 'no-store'
    resposta.headers['Referrer-Policy'] = 'no-referrer'
    resposta.headers['X-Content-Type-Options'] = 'nosniff'
    resposta.headers['X-Frame-Options'] = 'DENY'
    nonce = getattr(g, 'ml_nonce', '')
    resposta.headers['Content-Security-Policy'] = f"default-src 'none'; script-src 'nonce-{nonce}'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return resposta


@mercadolivre_auth_bp.get('/conectar')
def pagina():
    g.ml_nonce = secrets.token_urlsafe(24)
    return render_template('mercadolivre/conectar.html', nonce=g.ml_nonce)


@mercadolivre_auth_bp.post('/conectar')
@limiter.limit('10 per minute')
def conectar():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or set(dados) != {'convite'}:
        return jsonify(erro='Informe o convite administrativo'), 400
    try:
        navegador = secrets.token_urlsafe(32)
        url = AutorizarContaMercadoLivreService().iniciar(dados['convite'], navegador)
        session['ml_oauth_navegador'] = navegador
        return jsonify(url=url)
    except ValueError as erro:
        return jsonify(erro=str(erro)), 400
    except SQLAlchemyError:
        return jsonify(erro='Banco indisponível para autorização; confira a migração'), 503


@mercadolivre_auth_bp.get('/callback')
@limiter.limit('20 per minute')
def callback():
    # Parâmetros repetidos não podem selecionar um código ou state arbitrariamente.
    if any(len(request.args.getlist(k)) > 1 for k in ('state', 'code', 'error')):
        return 'Retorno de autorização inválido. Gere outro convite no terminal.', 400
    navegador = session.get('ml_oauth_navegador')
    try:
        AutorizarContaMercadoLivreService().concluir(request.args.get('state'), navegador,
            request.args.get('code'), recusado='error' in request.args)
        session.pop('ml_oauth_navegador', None)
        return 'Mercado Livre conectado com sucesso. Tokens salvos no servidor. Você pode fechar esta página.', 200
    except ValueError as erro:
        return str(erro), 400
    except SQLAlchemyError:
        return 'Não foi possível salvar a autorização. Gere outro convite; não reutilize o código.', 503
