from models import BuildSalva,Usuario

class ListarBuildService:
  def executar(self, usuario_id: int):
    if not Usuario.buscar_por_id(usuario_id):
      raise ValueError("Usuario não encontrado")
    return [build.to_dict() for build in BuildSalva.listar_por_usuario(usuario_id)]
