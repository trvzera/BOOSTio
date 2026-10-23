from models import Usuario
from werkzeug.security import check_password_hash
from utils.validacoes import validacao_campos

class EntrarUsuarioService:
  def executar(self, dados: dict) -> Usuario:
    validacao_campos(dados,["email","senha"])
    if (not isinstance(dados["email"], str) or len(dados["email"]) > 150
        or not isinstance(dados["senha"], str) or len(dados["senha"]) > 1024):
      raise ValueError("Senha ou email inválidos")

    usuario = Usuario.buscar_por_email(dados["email"].lower())

    if usuario and not usuario.ativo:
      raise ValueError("Senha ou email inválidos")

    if usuario and usuario.senha is None:
      raise ValueError(f"Experimente fazer login com o Google")
    
    if not usuario or not check_password_hash(usuario.senha,dados["senha"]):
      raise ValueError(f"Senha ou email inválidos")

    return usuario



