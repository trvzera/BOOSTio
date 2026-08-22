from models import Usuario
from utils.validacoes import validacao_campos

class EntrarGoogleService:
  def executar(self,dados_google:dict):
    if not dados_google.get("email_verified"):
      raise ValueError("Email do Google não verificado")

    email = dados_google.get("email")    
    usuario = Usuario.buscar_por_email(email)

    if usuario: 
      return usuario

    usuario = Usuario(
      nome=dados_google.get("name"),
      email=email,
      senha=None,
      login_google=True,
      verificado=True
    )

    usuario.salvar()

    return usuario