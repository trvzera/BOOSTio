from models import Usuario
from werkzeug.security import check_password_hash
from utils.validacoes import validacao_campos

class EntrarUsuarioService:
  def executar(self, dados: dict) -> Usuario:
    validacao_campos(dados,["email","senha"])

    usuario = Usuario.buscar_por_email(dados["email"].lower())

    if usuario and usuario.senha is None:
      raise ValueError(f"Experimente fazer login com o Google")
    
    if not usuario or not check_password_hash(usuario.senha,dados["senha"]):
      raise ValueError(f"Senha ou email inválidos")

    return usuario



