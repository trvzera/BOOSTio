from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from services.benchmark_service.consultar_benchmark_service import ConsultarBenchmarkService
from services.benchmark_service.buscar_jogos_benchmark_service import BuscarJogosBenchmarkService
from services.benchmark_service.consultar_requisitos_service import ConsultarRequisitosService
from services.benchmark_service.consultar_requisitos_build_service import ConsultarRequisitosBuildService
from services.benchmark_service.fpshq_service import ErroBenchmark
from services.benchmark_service.blender_service import cliente_blender

benchmark_bp = Blueprint("benchmark", __name__, url_prefix="/benchmark")


@benchmark_bp.after_request
def resposta_privada(resposta):
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@benchmark_bp.errorhandler(401)
def sessao_necessaria(_erro):
    return jsonify({"erro": "Entre na sua conta para consultar o desempenho.", "codigo": "nao-autenticado"}), 401


def executar_consulta(service, campos, chave):
    try:
        if any(campo not in campos or len(request.args.getlist(campo)) != 1 for campo in request.args):
            raise ValueError("Parâmetros de benchmark inválidos.")
        resultado = service.executar(request.args, current_user.id)
        resposta = jsonify({chave: resultado})
        return resposta, 200
    except ValueError as erro:
        return jsonify({"erro": str(erro), "codigo": "entrada"}), 400
    except ErroBenchmark as erro:
        resposta = jsonify({"erro": str(erro), "codigo": erro.codigo, "espera": erro.espera})
        if erro.espera:
            resposta.headers["Retry-After"] = str(erro.espera)
        return resposta, erro.status


@benchmark_bp.get("/fps")
@login_required
def consultar_benchmark():
    return executar_consulta(ConsultarBenchmarkService(), ("game", "cpu", "gpu", "res", "preset"), "resultado")


@benchmark_bp.get("/jogos")
@login_required
def buscar_jogos():
    return executar_consulta(BuscarJogosBenchmarkService(), ("q",), "resultado")


@benchmark_bp.get("/blender")
@login_required
def consultar_blender():
    return executar_consulta(cliente_blender, ("dispositivo", "tipo"), "resultado")


@benchmark_bp.get("/requisitos")
@login_required
def consultar_requisitos():
    return executar_consulta(ConsultarRequisitosService(), ("game", "ram_gb"), "resultado")


@benchmark_bp.get("/requisitos-build")
@login_required
def consultar_requisitos_build():
    return executar_consulta(ConsultarRequisitosBuildService(), ("game", "build_id"), "resultado")
