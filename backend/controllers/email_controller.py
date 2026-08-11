from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user,logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from models import lm
from smtplib import SMTPException, SMTPAuthenticationError, SMTPRecipientsRefused

from services.email_service.enviar_codigo_email_service import EnviarEmailService

email_bp = Blueprint("auth",__name__,url_prefix='/email')

@email_bp.post("/enviar")
def enviar_codigo():
    try:
        dados = request.get_json()

        service = EnviarEmailService()
        resposta = service.executar(dados)

        return jsonify({
            "mensagem": resposta
        }),200
    

    except SMTPAuthenticationError:
        return jsonify({
            "mensagem":'Falha na autenticação do servidor de email'
            }),400
    
    except SMTPRecipientsRefused:
        return jsonify({"mensagem": 'Endereço de email do destinatário foi recusado'}),400
    
    except SMTPException as erro:
        return jsonify({"mensagem": f'Erro ao enviar email {str(erro)}'}),400