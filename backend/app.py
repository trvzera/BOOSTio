from flask import Flask, render_template
from models import db 
from controllers.usuario import usuario_bp 

app = Flask(__name__, template_folder='../../frontend/templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///text.db'


db.init_app(app)
app.register_blueprint(usuario_bp)

@app.route("/")
def home():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)