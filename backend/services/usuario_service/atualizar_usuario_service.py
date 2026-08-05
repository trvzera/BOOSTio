from models import Usuario

class AtualizarUsuarioService:
  def executar(usuario_id,dados):
    usuario = Usuario.buscar_por_id(usuario_id)
    if usuario is None:
      return None

    novo_email = dados.get("email")
    if novo_email:
      usuario_existente = Usuario.buscar_por_email(novo_email)

      if usuario_existente:
        raise ValueError("Já existe um usuario com esse email")
    
    usuario.atualizar_dados(
      dados.get("usuario"),
      dados.get("email"),
      dados.get("senha"),
    )
    
    return usuario.to_dict()

    