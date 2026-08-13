from models import Usuario,Codigo,db

class DeletarUsuarioService:
  def executar(self, usuario_id: int) -> bool:   
    if not usuario_id:
      return False

    usuario = Usuario.buscar_por_id(usuario_id)

    if not usuario:
      return False
    
    Codigo.query.filter_by(usuario_id=usuario_id).delete()
    usuario.ativo = False
    
    db.session.commit()
    return True