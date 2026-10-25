from flask import Blueprint,request,jsonify
from flask_login import login_required
from models import db
from sqlalchemy.exc import SQLAlchemyError
from smtplib import SMTPException, SMTPAuthenticationError, SMTPRecipientsRefused
from email_validator import EmailNotValidError
from utils.decorators import apenas_proprio_usuario
from utils.limite_requisicoes import limiter, chave_usuario

from services.email_service.enviar_codigo_email_service import EnviarEmailService
from services.email_service.verificar_codigo_email_service import VerificarCodigoEmail

email_bp = Blueprint("email",__name__,url_prefix='/email')


class EmailController:
    """Controller HTTP do recurso; métodos estáticos não compartilham estado de requisição."""

    @staticmethod
    @email_bp.post("/verificar/enviar/<int:usuario_id>")
    @limiter.limit("20 per hour")
    @limiter.limit("5 per hour", key_func=chave_usuario)
    @login_required
    @apenas_proprio_usuario
    def enviar_email(usuario_id):
      try:
        service = EnviarEmailService()
        resposta = service.executar_para_usuario(usuario_id)

        return jsonify({
          "mensagem":"email enviado com sucesso",
          "enviado": resposta
        }),200


      except SMTPAuthenticationError:
        return jsonify({"erro": "Não foi possível enviar o código agora. Tente novamente mais tarde."}),503
    
      except SMTPRecipientsRefused:
        return jsonify({"erro": "Não foi possível entregar o código neste endereço. Confira seu e-mail."}),400
    
      except (SMTPException, OSError):
        return jsonify({"erro": "Não foi possível enviar o código agora. Tente novamente mais tarde."}),503

      except EmailNotValidError as e:
        return jsonify({"erro": "Email inexistente"}), 400
    
      except ValueError as e:
        return jsonify({"erro":str(e)}),400
  
      except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar o codigo no banco de dados."}), 500


    @staticmethod
    @email_bp.post("/verificar/conferir/<int:usuario_id>")
    @limiter.limit("60 per hour")
    @limiter.limit("25 per hour", key_func=chave_usuario)
    @login_required
    @apenas_proprio_usuario
    def conferir_email(usuario_id):
      try:
        dados = request.get_json() or {}
        service = VerificarCodigoEmail()
        usuario = service.executar_para_usuario(usuario_id,dados)
        return jsonify({
          "mensagem":"Email verificado com sucesso",
          "usuario": usuario
        }),200

      except ValueError as e:
        return jsonify({"erro": str(e)}),400
