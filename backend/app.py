from dotenv import load_dotenv
from configs import ambientes #Antes por esta com secret_key(IMPORTANTE)
from flask import Flask, render_template
from flask_cors import CORS
from models import db 
from models import lm
from controllers.usuario_controller import usuario_bp
import os


load_dotenv()


#Inicio o app e passo as configurações do app.
app = Flask(__name__,)
app.config.from_object(ambientes[os.getenv('APP_ENV')])

#Iniciar o login manager e passar o app como parametro
lm.init_app(app)
db.init_app(app)

#flask cors permite o fornt consumir a api do back
CORS(app)

app.register_blueprint(usuario_bp)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)