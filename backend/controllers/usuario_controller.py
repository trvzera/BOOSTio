from flask import Blueprint,request,jsonify,current_app
from flask_login import login_user, logout_user, login_required
from models import db
from sqlalchemy.exc import SQLAlchemyError
from smtplib import SMTPException
from email_validator import EmailNotValidError
from utils.decorators import apenas_proprio_usuario, tratar_erros
from utils.limite_requisicoes import limiter, chave_email, chave_usuario


from services.usuario_service.criar_usuario_service import CriarUsuarioService
from services.usuario_service.deletar_usuario_service import DeletarUsuarioService
from services.usuario_service.listar_usuario_id_service import ListarUsuarioIdService
from services.usuario_service.atualizar_usuario_service import AtualizarUsuarioService
from services.usuario_service.atualizar_budget_usuario_service import AtualizarBudgetUsuarioService
from services.usuario_service.atualizar_preferencias_uso_service import AtualizarPreferenciasUsoService
from services.usuario_service.redefinir_senha_service import RedefinirSenhaService
from services.usuario_service.solicitar_recuperacao_senha_service import SolicitarRecuperacaoSenhaService


usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuarios")

@usuario_bp.errorhandler(401)
def sessao_necessaria(_erro):
    return jsonify({"erro": "Entre na sua conta para continuar."}), 401


@usuario_bp.put("/<int:usuario_id>/preferencias-uso")
@login_required
@apenas_proprio_usuario
@limiter.limit("30 per minute", key_func=chave_usuario)
@tratar_erros("Não foi possível salvar suas preferências. Tente novamente.")
def atualizar_preferencias_uso(usuario_id):
    usuario = AtualizarPreferenciasUsoService().executar(usuario_id, request.get_json(silent=True))
    if usuario is None:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    resposta = jsonify({"mensagem": "Preferências salvas na sua conta.", "usuario": usuario})
    resposta.headers["Cache-Control"] = "no-store"
    return resposta, 200


@usuario_bp.put("/<int:usuario_id>/budget")
@login_required
@apenas_proprio_usuario
@tratar_erros("Não foi possível salvar o budget. Tente novamente.")
def atualizar_budget(usuario_id):
    usuario = AtualizarBudgetUsuarioService().executar(usuario_id, request.get_json(silent=True))
    if usuario is None:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    resposta = jsonify({"mensagem": "Budget atualizado com sucesso", "usuario": usuario})
    resposta.headers["Cache-Control"] = "no-store"
    return resposta, 200


@usuario_bp.post("/")
@limiter.limit("5 per hour")
@limiter.limit("3 per hour", key_func=chave_email)
@tratar_erros("Erro ao salvar o usuario no banco de dados.")
def criar_usuario():
    usuario = CriarUsuarioService().executar(request.get_json() or {})

    if usuario:
        login_user(usuario)

    return jsonify({"mensagem": "Usuario cadastrado com sucesso", "usuario": usuario.to_dict()}), 201


@usuario_bp.delete("/<int:usuario_id>")
@limiter.limit("5 per minute", key_func=chave_usuario)
@login_required
@apenas_proprio_usuario
@tratar_erros("Erro ao excluir o usuario do banco de dados")
def excluir_usuario(usuario_id):
    usuario = DeletarUsuarioService().executar(usuario_id, request.get_json(silent=True))

    if usuario is False:
        return jsonify({"erro": "Usuario não encontrado."}), 404

    logout_user()

    return jsonify(""), 204


@usuario_bp.get("/<int:usuario_id>")
@login_required
@apenas_proprio_usuario
@tratar_erros(status_valor=404)
def listar_usuario_id(usuario_id):
    usuario = ListarUsuarioIdService().executar(usuario_id)
    return jsonify({"mensagem": "Usuario encontrado com sucesso", "usuario": usuario}), 200


@usuario_bp.put("/<int:usuario_id>")
@limiter.limit("5 per minute", key_func=chave_usuario)
@login_required
@apenas_proprio_usuario
@tratar_erros("Erro ao atualizar o usuario no banco de dados")
def atualizar_usuario(usuario_id):
    try:
        usuario = AtualizarUsuarioService().executar(usuario_id, request.get_json() or {})
    except EmailNotValidError:
        return jsonify({"erro": "Email inexistente"}), 400

    if usuario is None:
        return jsonify({"erro": "Usuario não encontrado"}), 404

    return jsonify({"mensagem": "Usuario atualizado com sucesso"}), 200


@usuario_bp.post("/esqueci-senha")
@limiter.limit("10 per hour")
@limiter.limit("3 per hour", key_func=chave_email)
def esqueci_senha():
    try:
        SolicitarRecuperacaoSenhaService().executar(request.get_json(silent=True))

    except (SMTPException, OSError):
        current_app.logger.warning("Falha no envio de email de recuperação de senha")
    except ValueError:
        db.session.rollback()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("Falha no banco durante solicitação de recuperação de senha")

    return jsonify({
        "mensagem": "Se esse email estiver cadastrado, um link de recuperação foi enviado."
    }),200


@usuario_bp.post("/redefinir-senha")
@limiter.limit("20 per hour")
@tratar_erros("Erro ao redefinir a senha.")
def redefinir_senha():
    usuario = RedefinirSenhaService().executar(request.get_json() or {})
    return jsonify({"mensagem": "Senha redefinida com sucesso", "usuario": usuario}), 200
