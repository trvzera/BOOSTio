from flask import Blueprint,request,jsonify
from flask_login import login_required
from utils.decorators import apenas_proprio_usuario
from models import db,Build
from sqlalchemy.exc import SQLAlchemyError

from services.build_service.listar_builds_service import ListarBuildService

build_bp = Blueprint("build",__name__,url_prefix='/build')


@build_bp.get("/<int:usuario_id>")
@login_required
@apenas_proprio_usuario
def mostrar_builds(usuario_id):
  try:
    service = ListarBuildService()
    builds = service.executar(usuario_id)

    if builds is None:
      return jsonify({"erro":"Usuario não encontrado"}),404

    return jsonify({"mensagem":"Builds listadas com sucesso","builds":builds})
  
  except ValueError as e:
    return jsonify({
      "erro":e
    })

# @build_bp.post("/")
# def criar_build():
    