from flask_mail import Message
from models import Codigo,Usuario
from datetime import datetime


class verificarCodigoEmail:
  def executar(self,dados):
    usuario = Usuario.buscar_por_id(dados.get(dados))

    codigo_recente = usuario.codigo[-1]
    
    if codigo_recente.data_expiracao < datetime.now():
      raise ValueError("")
    if not codigo_recente:
      raise ValueError("Esse usuario não tem um codigo")
    
    
      