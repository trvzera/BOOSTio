from models import BuildSalva,Usuario
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService

class ListarBuildService:
  def executar(self, usuario_id: int):
    if not Usuario.buscar_por_id(usuario_id):
      raise ValueError("Usuario não encontrado")
    return [AvaliarCompatibilidadeService().para_resposta(build) for build in BuildSalva.listar_por_usuario(usuario_id)]
