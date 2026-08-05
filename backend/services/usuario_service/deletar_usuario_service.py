from models import Usuario

class DeletarUsuarioService:
  def executar(self,id):

    usuario = Usuario.buscar_por_id(id)

    if not usuario:
      return False

    usuario.deletar()
    return True