from models import TokenRecuperacao,Usuario
from utils.validacoes import validacao_campos,validar_senha_forte
from werkzeug.security import generate_password_hash

class RedefinirSenhaService:
  def executar(self,dados:dict) -> dict:
    validacao_campos(dados,["token","senha"])

    token_recuperacao = TokenRecuperacao.buscar_por_token(dados["token"])

    if not token_recuperacao:
      raise ValueError("Link inválido ou expirado")

    usuario = Usuario.buscar_por_id(token_recuperacao.usuario_id)

    if not usuario:
      raise ValueError("Link inválido ou expirado")

    validar_senha_forte(dados["senha"])

    usuario.atualizar_dados(senha = generate_password_hash(dados["senha"]))
    token_recuperacao.marcar_como_usado()

    return usuario.to_dict()
