from models.usuario import Usuario
from models import db

class UsuarioService:
    def criar_usuario(self, nome, email, senha):
        usuario = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(usuario)
        db.session.commit()
        return usuario
  
    def excluir_usuario(self, usuario_id):
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return None
        
        db.session.delete(usuario)
        db.session.commit()
        return True
  
    def listar_usuarios(self):
        return Usuario.query.all()
    
    def obter_usuario(self, usuario_id):
        return Usuario.query.get(usuario_id)

    def alterar_usuario(self, usuario_id, nome, email, senha):
        usuario = self.obter_usuario(usuario_id)
        
        if not usuario:
            return None
            
        usuario.nome = nome
        usuario.email = email
        
        if senha: 
            usuario.senha = senha
            
        db.session.commit()
        return usuario