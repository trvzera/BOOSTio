from dotenv import load_dotenv
from configs import ambientes #Antes por esta com secret_key(IMPORTANTE)
from flask import Flask, render_template
from flask_cors import CORS
from flask_mail import Mail, Message
from models import db,lm,mail 
import os

from controllers.usuario_controller import usuario_bp
from controllers.auth_controller import auth_bp
from controllers.email_controller import email_bp

load_dotenv()


#Inicio o app e passo as configurações do app.
app = Flask(__name__,)
app.config.from_object(ambientes[os.getenv('APP_ENV', 'desenvolvimento')])
#Iniciar o login manager e passar o app como parametro
lm.init_app(app)
db.init_app(app)
mail.init_app(app)

#flask cors permite o fornt consumir a api do back, e salvar os cookies, quando o front estiver nessas urls
CORS(app, supports_credentials=True, origins=["http://localhost:5500", "http://127.0.0.1:5500"])

app.register_blueprint(usuario_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(email_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)