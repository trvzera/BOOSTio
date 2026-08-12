from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError


from services.usuario_service.criar_usuario_service import CriarUsuarioService
from services.usuario_service.deletar_usuario_service import DeletarUsuarioService
from services.usuario_service.listar_usuarios_service import ListarUsuariosService
from services.usuario_service.listar_usuario_id_service import ListarUsuarioIdService
from services.usuario_service.atualizar_usuario_service import AtualizarUsuarioService
from services.email_service.enviar_codigo_email_service import EnviarEmailService


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
def excluir_usuario(usuario_id):
    try:
        service = DeletarUsuarioService()
        usuario = service.executar(usuario_id)

        if usuario is False:
            return jsonify({"erro": "Usuario não encontrado."}), 404

        return jsonify({"mensagem":"Usuario excluído com sucesso"}),204

    except SQLAlchemyError:
        db.session.rollback()
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
def atualizar_usuario(usuario_id):
    try:
        dados = request.get_json() or {}
        service = AtualizarUsuarioService()
        usuario = service.executar(usuario_id,dados)

        if usuario is None:
            return jsonify({"erro":"Usuario não encontrado"}),404

        return jsonify({"mensagem":"Usuario atualizado com sucesso"}),200

    except EmailNotValidError as e:
        return jsonify({"erro": "Email inexistente"}), 400
    
    except ValueError as erro:
        return jsonify({"erro":f"{str(erro)}"}),400
    
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro":"Erro ao atualizar o usuario no banco de dados"})
