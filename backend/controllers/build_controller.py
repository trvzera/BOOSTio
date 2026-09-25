from flask import Blueprint,request,jsonify
from flask_login import login_required,current_user
from utils.decorators import apenas_proprio_usuario
from models import db,Build
from sqlalchemy.exc import SQLAlchemyError

from services.build_service.listar_builds_service import ListarBuildService
from services.build_service.criar_build_service import CriarBuildService

build_bp = Blueprint("build",__name__,url_prefix='/build')


@build_bp.get("/")
@login_required
def mostrar_builds():
  try:
    usuario_id = current_user.id
    service = ListarBuildService()
    builds = service.executar(usuario_id)

    if builds is None:
      return jsonify({"erro":"Usuario não encontrado"}),404

    return jsonify({"mensagem":"Builds listadas com sucesso","builds":builds})
  
  except ValueError as e:
    return jsonify({
      "erro":str(e)
    })

@build_bp.post("/")
def criar_build():
  try:
    dados = request.get_json()
    usuario_id = current_user.id
    service = CriarBuildService()
    build = service.executar(usuario_id, dados)
    return jsonify({"mensagem":"Build criada com sucesso","build":build.to_dict()})
  
  except SQLAlchemyError as e:
    db.session.rollback()
    return jsonify({"erro":"Erro ao criar build"}),500
  
  except Exception as e:
    return jsonify({"erro":str(e)}),400
    