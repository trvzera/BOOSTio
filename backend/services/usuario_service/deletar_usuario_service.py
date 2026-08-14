from models import Usuario,Codigo,db

class DeletarUsuarioService:
  def executar(self, usuario_id: int) -> bool:   
    if not usuario_id:
      return False

    usuario = Usuario.buscar_por_id(usuario_id)

    if not usuario:
      return False
    
    Codigo.deletar_codigos_usuario(usuario.id)

    usuario.desativar()
    
    return True