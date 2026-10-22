from models import Usuario,Codigo,db
from .confirmar_identidade_service import ConfirmarIdentidadeService

class DeletarUsuarioService:
  def executar(self, usuario_id: int, dados=None) -> bool:
    if not usuario_id:
      return False

    usuario = Usuario.buscar_por_id(usuario_id)

    if not usuario:
      return False
    
    ConfirmarIdentidadeService().executar(usuario, dados)
    Codigo.deletar_codigos_usuario(usuario.id)

    usuario.desativar()
    
    return True
