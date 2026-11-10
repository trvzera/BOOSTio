from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from services.admin_service.aceitar_pendencia_service import AceitarPendenciaService, ConflitoPendencia
from services.admin_service.descartar_candidato_service import DescartarCandidatoService
from services.admin_service.detalhar_pendencia_service import DetalharPendenciaService
from services.admin_service.listar_pendencias_service import ListarPendenciasService
from services.admin_service.rejeitar_pendencia_service import RejeitarPendenciaService
from services.admin_service.sugerir_pendencia_service import EnviarPendenciasParaIAService, listar_ids_para_ia
from services.mercadolivre_service.controle_requisicoes_service import ErroMercadoLivre, OrcamentoRequisicoesEsgotado
from utils.decorators import apenas_administrador

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _responder(funcao):
    """Traduz os erros dos services para HTTP; nenhuma mensagem de banco chega ao navegador."""
    try:
        resposta = jsonify(funcao())
        resposta.headers["Cache-Control"] = "no-store"
        return resposta, 200
    except (ErroMercadoLivre, OrcamentoRequisicoesEsgotado):
        # Antes de ValueError, de que ambos herdam: é falha da loja, não da entrada do administrador.
        return jsonify({"erro": "O Mercado Livre não respondeu agora. Tente novamente em instantes.", "codigo": "loja-indisponivel"}), 502
    except ConflitoPendencia as erro:
        return jsonify({"erro": str(erro), "codigo": "conflito"}), 409
    except ValueError as erro:
        return jsonify({"erro": str(erro), "codigo": "entrada"}), 400
    except LookupError as erro:
        return jsonify({"erro": str(erro), "codigo": "nao-encontrada"}), 404
    except SQLAlchemyError:
        return jsonify({"erro": "Painel indisponível no momento", "codigo": "indisponivel"}), 503


@admin_bp.get("/pendencias")
@login_required
@apenas_administrador
def listar_pendencias():
    def listar():
        argumentos = request.args
        return ListarPendenciasService().executar(
            status=argumentos.get("status", "em_revisao"), loja=argumentos.get("loja") or None,
            categoria=argumentos.get("categoria") or None,
            depois_id=_inteiro(argumentos.get("depois_id", "0")), limite=_inteiro(argumentos.get("limite", "20")))
    return _responder(listar)


@admin_bp.get("/pendencias/<int:pendencia_id>")
@login_required
@apenas_administrador
def detalhar_pendencia(pendencia_id):
    return _responder(lambda: DetalharPendenciaService().executar(pendencia_id))


@admin_bp.post("/pendencias/<int:pendencia_id>/aceitar")
@login_required
@apenas_administrador
def aceitar_pendencia(pendencia_id):
    corpo = request.get_json(silent=True) or {}
    return _responder(lambda: AceitarPendenciaService().executar(
        pendencia_id, current_user.id, corpo.get("peca") if isinstance(corpo.get("peca"), str) else ""))


@admin_bp.post("/pendencias/<int:pendencia_id>/candidatos/descartar")
@login_required
@apenas_administrador
def descartar_candidato(pendencia_id):
    corpo = request.get_json(silent=True) or {}
    return _responder(lambda: DescartarCandidatoService().executar(
        pendencia_id, current_user.id, corpo.get("peca")))


@admin_bp.get("/pendencias/ids-para-ia")
@login_required
@apenas_administrador
def ids_para_ia():
    argumentos = request.args
    return _responder(lambda: listar_ids_para_ia(
        status=argumentos.get("status", "em_revisao"), loja=argumentos.get("loja") or None,
        categoria=argumentos.get("categoria") or None))


@admin_bp.post("/pendencias/enviar-ia")
@login_required
@apenas_administrador
def enviar_pendencias_para_ia():
    corpo = request.get_json(silent=True) or {}
    return _responder(lambda: EnviarPendenciasParaIAService().executar(
        corpo.get("ids"), decidir=corpo.get("decidir") is True, refazer=corpo.get("refazer") is not False))


@admin_bp.post("/pendencias/<int:pendencia_id>/rejeitar")
@login_required
@apenas_administrador
def rejeitar_pendencia(pendencia_id):
    corpo = request.get_json(silent=True) or {}
    motivo = corpo.get("motivo") if isinstance(corpo.get("motivo"), str) else None
    return _responder(lambda: RejeitarPendenciaService().executar(pendencia_id, current_user.id, motivo))


def _inteiro(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError("Parâmetro numérico inválido") from None
