from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user,logout_user, login_required, current_user
from models import db
from sqlalchemy.exc import SQLAlchemyError
from smtplib import SMTPException, SMTPAuthenticationError, SMTPRecipientsRefused
from email_validator import EmailNotValidError

from services.email_service.enviar_codigo_email_service import EnviarEmailService
from services.email_service.verificar_codigo_email_service import VerificarCodigoEmail

email_bp = Blueprint("email",__name__,url_prefix='/email')

@email_bp.post("/enviar")
def enviar_email():
  try:
    service = EnviarEmailService()
    resposta = service.executar(current_user)

    return jsonify({
      "mensagem":"email enviado com sucesso",
      "enviado": resposta
    }),200


  except SMTPAuthenticationError:
    return jsonify({"mensagem":'Falha na autenticação do servidor de email'}),400
    
  except SMTPRecipientsRefused:
    return jsonify({"mensagem": 'Endereço de email do destinatário foi recusado'}),400
    
  except SMTPException as erro:
    return jsonify({"mensagem": f'Erro ao enviar email {str(erro)}'}),400

  except EmailNotValidError as e:
    return jsonify({"erro": "Email inexistente"}), 400
    
  except ValueError as e:
    return jsonify({"erro":str(e)})
  
  except SQLAlchemyError:
    db.session.rollback()
    return jsonify({"erro": "Erro ao salvar o codigo no banco de dados."}), 500

@email_bp.post("/verificar")
def conferir_email():
  try:
    dados = request.get_json() or {}
    service = VerificarCodigoEmail()
    usuario = service.executar(dados,current_user)
    return jsonify({
      "mensagem":"Email verificado com sucesso",
      "usuario": usuario
    }),200

  except ValueError as e:
    return jsonify({"erro": str(e)}),400


    