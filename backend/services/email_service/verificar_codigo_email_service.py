import re
import secrets

from models import Codigo,Usuario
from utils.validacoes import validacao_campos

class VerificarCodigoEmail:
  def executar(self,dados:dict,usuario:Usuario):
    validacao_campos(dados,["codigo"])
    
    if not usuario:
      raise ValueError("Nenhum usuario encontrado")
    
    codigo_informado = dados["codigo"]
    if not isinstance(codigo_informado, str) or not re.fullmatch(r"[0-9]{6}", codigo_informado):
      raise ValueError("Informe o código de seis dígitos")

    codigo_recente = Codigo.buscar_codigo_recente(usuario.id)

    if (not codigo_recente or codigo_recente.usado or codigo_recente.esta_expirado()
        or not codigo_recente.email_destino or codigo_recente.email_destino != usuario.email):
      raise ValueError("Código inválido ou expirado. Solicite outro código")

    if not codigo_recente.registrar_tentativa():
      raise ValueError("Limite de tentativas atingido. Solicite outro código")

    if not secrets.compare_digest(codigo_recente.codigo, codigo_informado):
      raise ValueError("O código digitado está errado")

    codigo_recente.confirmar_email()

    return usuario.to_dict()
