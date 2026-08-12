from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user,logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from models import lm


from services.email_service.verificar_codigo_email_service import VerificarCodigoEmail

email_bp = Blueprint("auth",__name__,url_prefix='/email')

@email_bp.post("/check")
def conferir_email():
  try:
    dados = request.get_json()
    service = VerificarCodigoEmail()
    usuario = service.executar(dados)
    return jsonify({
      "mensagem":"Email verificado com sucesso",
      "usuario": usuario
    }),200
  except ValueError:
    jsonify({"erro"})


    