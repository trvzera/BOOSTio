from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user,logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from smtplib import SMTPException, SMTPAuthenticationError, SMTPRecipientsRefused
from email_validator import EmailNotValidError
from utils.decorators import apenas_proprio_usuario

from services.email_service.enviar_codigo_email_service import EnviarEmailService
from services.email_service.verificar_codigo_email_service import VerificarCodigoEmail

email_bp = Blueprint("email",__name__,url_prefix='/email')


@email_bp.post("/verificar/enviar/<int:usuario_id>")
@login_required
@apenas_proprio_usuario
def enviar_email(usuario_id):
  try:
    usuario_buscado = Usuario.buscar_por_id(usuario_id)
    
    service = EnviarEmailService()
    resposta = service.executar(usuario_buscado)

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


@email_bp.post("/verificar/conferir/<int:usuario_id>")
@login_required
@apenas_proprio_usuario
def conferir_email(usuario_id):
  try:
    dados = request.get_json() or {}
    usuario_buscado = Usuario.buscar_por_id(usuario_id)

    service = VerificarCodigoEmail()
    usuario = service.executar(dados,usuario_buscado)
    return jsonify({
      "mensagem":"Email verificado com sucesso",
      "usuario": usuario
    }),200

  except ValueError as e:
    return jsonify({"erro": str(e)}),400


@email.post("/recuperar/enviar")
def enviar_email_recuperar():
  try:
    dados = request.get_json() or {}
    usuario_buscado = Usuario.buscar_por_email(dados.get("email"))

    service = EnviarEmailService()
    resposta = service.executar(usuario_buscado)

    return jsonify({
      "mensagem":"Email enviado com sucesso",
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


@email_bp.post("/recuperar/conferir")
def conferir_email():
  try:
    dados = request.get_json() or {}
    usuario_buscado = Usuario.buscar_por_email(dados.get("email"))

    service = VerificarCodigoEmail()
    usuario = service.executar(dados,usuario_buscado)

    return jsonify({
      "mensagem":"Email verificado com sucesso",
      "usuario": usuario
    }),200

  except ValueError as e:
    return jsonify({"erro": str(e)}),400