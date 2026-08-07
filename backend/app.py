from flask import Flask, render_template
from flask_cors import CORS
from models import db 
from models import lm
from controllers.usuario_controller import usuario_bp
import os
from dotenv import load_dotenv
from configs import ambientes

#Mais para frente fazer um arquivo configs.py para colocar as configurações do flask em um arquivo separado.

#Carrega as variaveis de ambiente
load_dotenv()

app = Flask(__name__,)
app.config.from_object(ambientes[os.getenv('APP_ENV')])

#Necessario para o flask-login
#Puxo das variaveis de ambiente

#Iniciar o login manager e passar o app como parametro
lm.init_app(app)

#flask cors permite o fornt consumir a api do back
CORS(app)


db.init_app(app)
app.register_blueprint(usuario_bp)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)