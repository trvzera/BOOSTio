from models import Usuario

class DeletarUsuarioService():
  def executar(self,id):

    usuario = Usuario.buscar_por_id(id)

    if not usuario:
      raise ValueError("Esse usuario não existe")

    usuario.deletar()
    return True