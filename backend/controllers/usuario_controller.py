from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from smtplib import SMTPException, SMTPAuthenticationError, SMTPRecipientsRefused
from email_validator import EmailNotValidError
from utils.decorators import apenas_proprio_usuario


from services.usuario_service.criar_usuario_service import CriarUsuarioService
from services.usuario_service.deletar_usuario_service import DeletarUsuarioService
from services.usuario_service.listar_usuarios_service import ListarUsuariosService
from services.usuario_service.listar_usuario_id_service import ListarUsuarioIdService
from services.usuario_service.atualizar_usuario_service import AtualizarUsuarioService
from services.usuario_service.redefinir_senha_service import RedefinirSenhaService
from services.email_service.enviar_codigo_email_service import EnviarEmailService
from services.email_service.enviar_email_recuperar_service import EnviarEmailRecuperarService


usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuarios")

#Faltando buscar por Email e finalizar criar usuario na service.

@usuario_bp.post("/")
def criar_usuario():
    try:
        dados = request.get_json() or {}
        service = CriarUsuarioService()
        usuario = service.executar(dados)
        
        if usuario:
            login_user(usuario)

        return jsonify({
            "mensagem": "Usuario cadastrado com sucesso",
            "usuario": usuario.to_dict()
            }
        ),201
        
    except ValueError as erro:
        return jsonify({f"erro": f"{str(erro)}"}),400
    
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar o usuario no banco de dados."}), 500

@usuario_bp.delete("/<int:usuario_id>")
@login_required
@apenas_proprio_usuario
def excluir_usuario(usuario_id):
    try:
        service = DeletarUsuarioService()
        usuario = service.executar(usuario_id)

        if usuario is False:
            return jsonify({"erro": "Usuario não encontrado."}), 404

        logout_user()
        
        return jsonify(""),204

    except SQLAlchemyError as e:
        db.session.rollback()
        print(e)
        return jsonify({"erro":"Erro ao excluir o usuario do banco de dados"}),500

@usuario_bp.get("/")
@login_required
def listar_usuarios():
    service = ListarUsuariosService()
    usuarios = service.executar()

    return jsonify({
        "mensagem": "usuarios listados com sucesso",
        "usuarios": usuarios
        }),200

@usuario_bp.get("/<int:usuario_id>")
@login_required
@apenas_proprio_usuario
def listar_usuario_id(usuario_id):
    try:
        service = ListarUsuarioIdService()
        usuario = service.buscar_por_id(usuario_id)

        return jsonify({
            "mensagem":"Usuario encontrado com sucesso",
            "usuario": usuario,
            }),200

    except ValueError as erro:
        return jsonify({"erro":f"{str(erro)}"}),404

@usuario_bp.put("/<int:usuario_id>")
@login_required
@apenas_proprio_usuario
def atualizar_usuario(usuario_id):
    try:
        dados = request.get_json() or {}
        service = AtualizarUsuarioService()
        usuario = service.executar(usuario_id,dados)

        if usuario is None:
            return jsonify({"erro":"Usuario não encontrado"}),404

        return jsonify({"mensagem":"Usuario atualizado com sucesso"}),200

    except EmailNotValidError:
        return jsonify({"erro": "Email inexistente"}), 400
    
    except ValueError as erro:
        return jsonify({"erro":f"{str(erro)}"}),400
    
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro":"Erro ao atualizar o usuario no banco de dados"})

@usuario_bp.post("/esqueci-senha")
def esqueci_senha():
    try:
        dados = request.get_json() or {}
        usuario = Usuario.buscar_por_email(dados.get("email"))

        #Só envia o email se o usuario existir, mas a resposta é sempre a mesma
        #pra não revelar se aquele email está cadastrado (evita enumeração de usuarios).
        if usuario:
            service = EnviarEmailRecuperarService()
            service.executar(usuario)

        return jsonify({
            "mensagem": "Se esse email estiver cadastrado, um link de recuperação foi enviado."
        }),200

    except SMTPAuthenticationError:
        return jsonify({"mensagem":'Falha na autenticação do servidor de email'}),400

    except SMTPRecipientsRefused:
        return jsonify({"mensagem": 'Endereço de email do destinatário foi recusado'}),400

    except SMTPException as erro:
        return jsonify({"mensagem": f'Erro ao enviar email {str(erro)}'}),400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao processar a solicitação."}), 500

@usuario_bp.post("/redefinir-senha")
def redefinir_senha():
    try:
        dados = request.get_json() or {}
        service = RedefinirSenhaService()
        usuario = service.executar(dados)

        return jsonify({
            "mensagem": "Senha redefinida com sucesso",
            "usuario": usuario
        }),200

    except ValueError as erro:
        return jsonify({"erro": str(erro)}),400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao redefinir a senha."}), 500
