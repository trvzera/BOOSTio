from flask_mail import Message
from models import Codigo,Usuario
from datetime import datetime
from utils.validacoes import validacao_campos

class VerificarCodigoEmail:
  def executar(self,dados:dict,usuario:Usuario):
    validacao_campos(dados,["codigo"])

    codigo_informado = dados["codigo"]

    if not usuario:
      raise ValueError("Nenhum usuario logado")
      
    codigo_recente = Codigo.buscar_codigo_recente(usuario.id)

    if codigo_recente.codigo != codigo_informado:
      raise ValueError("O codigo digitado esta errado")
    
    if codigo_recente.esta_expirado():
      raise ValueError("Esse codigo expirou")

    codigo_recente.marcar_como_usado()
    usuario.verificado = True

    return usuario.to_dict()

    
    
      