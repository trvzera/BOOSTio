from flask import Blueprint,request,jsonify
from flask_login import LoginManager, UserMixin, login_user,logout_user, login_required, current_user
from models import db,Usuario
from sqlalchemy.exc import SQLAlchemyError
from models import lm


from services.email_service.enviar_codigo_email_service import EnviarEmailService

email_bp = Blueprint("auth",__name__,url_prefix='/email')

@email_bp.post("/check")
def conferir_email():
    