from models import Build,Usuario

class ListarBuildService:
  def executar(usuario_id:int):
    usuario_requisicao = Usuario.buscar_por_id(usuario_id)
    
    if not usuario_requisicao:
      return None

    builds = Build.listar_por_usuario(usuario_id)
    
    builds_totais_formatadas = [build.to_dict for build in builds]
    
    return builds_totais_formatadas