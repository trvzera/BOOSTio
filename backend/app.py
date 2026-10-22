from dotenv import load_dotenv
from configs import ambientes,configurar_oauth #Antes por esta com secret_key(IMPORTANTE)
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db,lm,mail 
import os

from controllers.usuario_controller import usuario_bp
from controllers.auth_controller import auth_bp
from controllers.email_controller import email_bp
from controllers.benchmark_controller import benchmark_bp
from controllers.build_controller import build_bp
from services.peca_service.popular_pecas_service import PopularPecasService
from migrations.budget_usuario import registrar_migracao_budget
from migrations.imagens_pecas import migrar_imagens_pecas
from migrations.rede_build import migrar_rede_build
from migrations.codigos_email import migrar_codigos_email
from migrations.google_usuario import migrar_google_usuario
from migrations.sessao_usuario import migrar_sessao_usuario
from utils.csrf import configurar_csrf
from utils.limite_requisicoes import configurar_limites

load_dotenv()


#Inicio o app e passo as configurações do app.
#O instance_path é fixado ao lado do app.py: sem isso o flask usa a pasta atual (cwd) e o caminho relativo do sqlite (URL_DATABASE) quebra dependendo de onde o app é executado.
app = Flask(__name__, instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__))))

ambiente = os.getenv('APP_ENV', 'desenvolvimento')
app.config.from_object(ambientes[ambiente])

if app.config['TRUSTED_PROXY_HOPS'] < 0:
    raise ValueError('TRUSTED_PROXY_HOPS não pode ser negativo')

if app.config['TRUSTED_PROXY_HOPS']:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config['TRUSTED_PROXY_HOPS'])

configurar_csrf(app)
configurar_limites(app, producao=ambiente == 'producao')
#Iniciar o login manager e passar o app como parametro
lm.init_app(app)
db.init_app(app)
mail.init_app(app)
configurar_oauth(app)

#flask cors permite o fornt consumir a api do back, e salvar os cookies, quando o front estiver nessas urls
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5500", "http://127.0.0.1:5500",
    "http://localhost:5501", "http://127.0.0.1:5501",
])

app.register_blueprint(usuario_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(email_bp)
app.register_blueprint(benchmark_bp)
app.register_blueprint(build_bp)
registrar_migracao_budget(app, db)

with app.app_context():
    db.create_all()
    migrar_google_usuario()
    migrar_sessao_usuario()
    migrar_imagens_pecas()
    migrar_rede_build()
    migrar_codigos_email()

from commands.precos import registrar_comandos_precos
registrar_comandos_precos(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        PopularPecasService().executar(atualizar_precos=True)
    app.run(debug=True)
