from models import Usuario

class ListarUsuarioIdService:
  def executar(usuario_id: int) -> dict:
    if not usuario_id:
      raise ValueError("Esse usuario não existe")
      
    usuario = Usuario.buscar_por_id(usuario_id)
    
    if usuario is None:
      raise ValueError("Esse usuario não existe")
    
    return usuario.to_dict()
