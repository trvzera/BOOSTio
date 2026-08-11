from models import Usuario

class ListarUsuariosService:
  def executar(self) -> list[dict]:
    usuarios = Usuario.listar_todos()

    return [usuario.to_dict() for usuario in usuarios]