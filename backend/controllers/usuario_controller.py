from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from models import lm

from services.usuario_service.criar_usuario_service import CriarUsuarioService
from services.usuario_service.entrar_usuario_service import EntrarUsuarioService
from services.usuario_service.deletar_usuario_service import DeletarUsuarioService
from services.usuario_service.listar_usuarios_service import ListarUsuariosService
from services.usuario_service.listar_usuario_id_service import ListarUsuarioIdService
from services.usuario_service.atualizar_usuario_service import AtualizarUsuarioService


usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuarios")

#Funcão obrigatória para o login buscar informações do usuario pelo id
@lm.user_loader
def user_loader(id):
    usuario = Usuario.buscar_por_id(id)
    return usuario

#Faltando buscar por Email e finalizar criar usuario na service.

@usuario_bp.post("/")
def criar_usuario():
    try:
        dados = request.get_json() or {}
        service = CriarUsuarioService()
        usuario = service.executar(dados)
        
        if usuario:
            #Se o usuario existir,logo ele na aplicação
            login_user(usuario)

        return jsonify({
            "mensagem": "Usuario cadastrado com sucesso",
            "usuario": usuario.to_dict()
            }
        ),201
    
    #Capturo erros
    except ValueError as erro:
        return jsonify({f"erro": f"Erro: {str(erro)}"}),400

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar o usuario no banco de dados."}), 500


@usuario_bp.delete("/<int:usuario_id>") 
def excluir_usuario(usuario_id):
    try:
        service = DeletarUsuarioService()
        usuario = service.executar(usuario_id)

        if usuario is False:
            return jsonify({"erro": "Usuario não encontrado."}), 404

        return jsonify({"mensagem":"Usuario excluido com sucesso"}),204

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro":"Erro ao excluir o usuario do banco de dados"}),500


@usuario_bp.get("/")
def listar_usuarios():
    service = ListarUsuariosService()
    usuarios = service.executar()

    return jsonify({
        "mensagem": "usuarios listados com sucesso",
        "usuarios": usuarios
        }),200


@usuario_bp.get("/<int:usuario_id>")
def listar_usuario_id(usuario_id):
    try:
        service = ListarUsuarioIdService()
        usuario = service.buscar_por_id(usuario_id)

        return jsonify({
            "mensagem":"Usuario encontrado com sucesso",
            "usuario": usuario,
            }),200

    except ValueError as erro:
        return jsonify({"erro":f"Erro: {str(erro)}"}),404


@usuario_bp.put("/<int:usuario_id>")
def atualizar_usuario(usuario_id):
    try:
        dados = request.get_json() or {}
        service = AtualizarUsuarioService()
        usuario = service.executar(usuario_id,dados)

        if usuario is None:
            return jsonify({"erro":"Usuario não encontrado"}),404

        return jsonify({"mensagem":"Usuario atualizado com sucesso"}),200

    except ValueError as erro:
        db.session.rollback()
        return jsonify({"erro":f"Erro: {str(erro)}"}),400
    
    except SQLAlchemyError:
        return jsonify({"erro":"Erro ao atualizar o usuario no banco de dados"})


@usuario_bp.post("/entrar")
def entrar_usuario():
    try:
        dados = request.get_json()

        service = EntrarUsuarioService()
        usuario = service.executar(dados)

        return jsonify({
            "mensagem":"Usuario logado com sucesso",
            "usuario": usuario
        }),200
    
    except ValueError as erro:
        return jsonify({"erro":f"Erro: {str(erro)}"}),400
