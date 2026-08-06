from flask import Flask, render_template
from models import db 
from controllers.usuario_controller import usuario_bp
from flask import Flask
from flask_cors import CORS

#flask cors permite o fornt consumir a api do back
app = Flask(__name__,)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/banco.db'


db.init_app(app)
app.register_blueprint(usuario_bp)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)