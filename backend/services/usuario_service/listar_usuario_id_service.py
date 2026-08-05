from models import Usuario

class ListarUsuarioIdService:
  def executar(usuario_id):
    if not isinstance(usuario_id,int):
      raise ValueError("Digite um id válido")
      
    usuario = Usuario.buscar_por_id(usuario_id)
    
    if usuario_buscado is None:
      raise ValueError("Esse usuario não existe")
    
    return usuario.to_dict()
