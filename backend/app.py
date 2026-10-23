from dotenv import load_dotenv
from configs import ambientes,configurar_oauth #Antes por esta com secret_key(IMPORTANTE)
from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from services.configuracao_service.configurar_acesso_service import ConfigurarAcessoService
from services.configuracao_service.validar_producao_service import ValidarProducaoService
from models import db,lm,mail 
from commands.precos import registrar_comandos_precos
import os

from controllers.usuario_controller import usuario_bp
from controllers.auth_controller import auth_bp
from controllers.email_controller import email_bp
from controllers.benchmark_controller import benchmark_bp
from controllers.build_controller import build_bp
from controllers.saude_controller import saude_bp
from migrations.budget_usuario import registrar_migracao_budget
from commands.banco import registrar_comandos_banco
from utils.csrf import configurar_csrf
from utils.limite_requisicoes import configurar_limites

load_dotenv()


#Inicio o app e passo as configurações do app.
#O instance_path é fixado ao lado do app.py: sem isso o flask usa a pasta atual (cwd) e o caminho relativo do sqlite (URL_DATABASE) quebra dependendo de onde o app é executado.
app = Flask(__name__, instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__))))

@app.errorhandler(RequestEntityTooLarge)
def requisicao_grande(_erro):
    return jsonify({"erro": "Requisição muito grande", "codigo": "requisicao-grande"}), 413

ambiente = os.getenv('APP_ENV', 'desenvolvimento')
app.config.from_object(ambientes[ambiente])

if ambiente == 'producao':
    ValidarProducaoService().executar(app)
ConfigurarAcessoService().executar(app, producao=ambiente == 'producao')

configurar_csrf(app)
configurar_limites(app, producao=ambiente == 'producao')
#Iniciar o login manager e passar o app como parametro
lm.init_app(app)
db.init_app(app)
mail.init_app(app)
configurar_oauth(app)

app.register_blueprint(usuario_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(email_bp)
app.register_blueprint(benchmark_bp)
app.register_blueprint(build_bp)
app.register_blueprint(saude_bp)
registrar_migracao_budget(app, db)

registrar_comandos_banco(app)
registrar_comandos_precos(app)

if __name__ == '__main__':
    if ambiente == 'producao':
        raise RuntimeError("Em produção, inicie pelo servidor WSGI: gunicorn -c gunicorn.conf.py wsgi:app")
    app.run(debug=True)
