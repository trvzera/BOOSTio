from models import Usuario
from werkzeug.security import generate_password_hash

class AtualizarUsuarioService:
  def executar(self,usuario_id,dados):
    usuario = Usuario.buscar_por_id(usuario_id)
    if usuario is None:
      return None

    novo_email = dados.get("email")
    if novo_email:
      usuario_existente = Usuario.buscar_por_email(novo_email)

      if usuario_existente:
        raise ValueError("Já existe um usuario com esse email")
    
    senha = dados.get("senha")

    if senha:
      senha = generate_password_hash(senha)

    usuario.atualizar_dados(
      dados.get("usuario"),
      dados.get("email"),
      senha,
    )
    
    return usuario.to_dict()

    