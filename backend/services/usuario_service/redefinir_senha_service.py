from models import TokenRecuperacao,Usuario
from utils.validacoes import validacao_campos,validar_senha_forte
from werkzeug.security import generate_password_hash

class RedefinirSenhaService:
  def executar(self,dados:dict) -> dict:
    if not isinstance(dados, dict):
      raise ValueError("Informe o token e a nova senha")
    validacao_campos(dados,["token","senha"])
    if not isinstance(dados["senha"], str) or len(dados["senha"]) > 1024:
      raise ValueError("Senha inválida")

    token_recuperacao = TokenRecuperacao.buscar_por_token(dados["token"])

    if not token_recuperacao:
      raise ValueError("Link inválido ou expirado")

    usuario = Usuario.buscar_por_id(token_recuperacao.usuario_id)

    if not usuario or not usuario.ativo:
      raise ValueError("Link inválido ou expirado")

    validar_senha_forte(dados["senha"])

    token_recuperacao.redefinir_senha(generate_password_hash(dados["senha"]))

    return usuario.to_dict()
