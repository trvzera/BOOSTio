from flask_mail import Message
from models import Codigo,Usuario
from datetime import datetime


class VerificarCodigoEmail:
  def executar(self,dados):
    usuario = Usuario.buscar_por_id(dados.get(dados))
    codigo_recente = usuario.codigo[-1]

    if codigo_recente.codigo != dados.get("codigo"):
      raise ValueError("O codigo digitado esta errado")
    
    if codigo_recente.esta_expirado():
      raise ValueError("Esse codigo expirou")

    codigo_recente.marcar_como_usado()

    return usuario.to_dict()

    
    
      