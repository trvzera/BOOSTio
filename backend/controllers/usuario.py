from flask import Blueprint, redirect, render_template, request, url_for
from services.usuario_service import UsuarioService

usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuario", template_folder='../../frontend/templates')

@usuario_bp.route("/criar", methods=['GET','POST'])
def criar_usuario():
    if request.method == 'GET':
        return render_template('index.html')
 
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    repo = UsuarioService()
    usuario = repo.criar_usuario(nome, email, senha)
    print(usuario)
    return redirect(url_for('usuario.listar_usuarios'))

@usuario_bp.route("/listar", methods=['GET'])
def listar_usuarios():
    repo = UsuarioService()
    lista_de_usuarios = repo.listar_usuarios()
    return render_template('lista.html', usuarios=lista_de_usuarios)


@usuario_bp.route("/excluir/<int:usuario_id>", methods=['POST']) 
def excluir_usuario(usuario_id):
    repo = UsuarioService()
    repo.excluir_usuario(usuario_id)
    return redirect(url_for('usuario.listar_usuarios'))


@usuario_bp.route("/alterar/<int:usuario_id>", methods=['GET', 'POST'])
def alterar_usuario(usuario_id):
    repo = UsuarioService()
    
    if request.method == 'GET':
        usuario = repo.obter_usuario(usuario_id)
        if not usuario:
            return redirect(url_for('usuario.listar_usuarios'))
        
        return render_template('editar.html', usuario=usuario)
    
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    repo.alterar_usuario(usuario_id, nome, email, senha)
    
    return redirect(url_for('usuario.listar_usuarios'))