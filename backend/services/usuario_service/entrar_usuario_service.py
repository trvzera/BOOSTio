from models import Usuario
from werkzeug.security import check_password_hash

class EntrarUsuarioService:
  def executar(self,dados):
    campos_obrigatorios = ["email","senha"]

    for campo in campos_obrigatorios:
      if dados.get(campo) is None:
        raise ValueError(f"O campo {campo} e obrigatorio")

    usuario = Usuario.buscar_por_email(dados["email"])
    
    if not usuario or not check_password_hash(usuario.senha,dados["senha"]):
      raise ValueError(f"Senha ou email invalidos")

    return usuario



