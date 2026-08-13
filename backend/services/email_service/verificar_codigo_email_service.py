from flask_mail import Message
from models import Codigo,Usuario
from datetime import datetime
from utils.validacoes import validacao_campos

class VerificarCodigoEmail:
  def executar(self,dados:dict,usuario_id:int):
    validacao_campos(dados,["codigo"])
    
    if not usuario_id:
      raise ValueError("Id do usuario invalido")
    
    usuario = Usuario.buscar_por_id(usuario_id)
    
    if not usuario:
      raise ValueError("Nenhum usuario encontrado")
    
    codigo_informado = dados["codigo"]
      
    codigo_recente = Codigo.buscar_codigo_recente(usuario.id)

    if codigo_recente.codigo != codigo_informado:
      raise ValueError("O codigo digitado esta errado")
    
    if codigo_recente.esta_expirado():
      raise ValueError("Esse codigo expirou")

    codigo_recente.marcar_como_usado()
    usuario.verificado = True
    usuario.salvar()

    return usuario.to_dict()

    
    
      