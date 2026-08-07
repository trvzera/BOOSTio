from models import Usuario
#Biblioteca para passar e verificar senha hash(segurança)
from werkzeug.security import generate_password_hash


class CriarUsuarioService:
  #Adicionar verificação de senha sendo menor que 8 caracteres e etc...
  #Adicionar verificação do formato do email
  
  def executar(self,dados):
    campos_obrigatorios = ["nome","email","senha"]
    campos_obrigatorios_resp = []

    #Verificar se os campos obrigatorios estão preenchidos
    for campo in campos_obrigatorios:
      if not dados.get(campo):
        campos_obrigatorios_resp.append(campo)

    if len(campos_obrigatorios_resp) > 0:
      raise ValueError(f"O(s) campos '{"','".join(campos_obrigatorios_resp)}'")


    usuario_existente = Usuario.buscar_por_email(dados['email'])

    if usuario_existente:
      raise ValueError("Esse Usuario já existe,experimente fazer login")


    
    senha_protegida = generate_password_hash(dados["senha"])

    usuario = Usuario(
      nome = dados['nome'],
      email = dados['email'],
      senha = senha_protegida,
    )

    usuario.salvar()

    #Retornar a instancia pois irei usar o flask-login no controller    
    return usuario

  #any percorre todos e se um for true, retorna true
  def validar_senha(self,senha):
    if len(senha) < 8:
      raise ValueError("A senha deve ter no minimo oito caracteres")

    if not any(c.isupper for c in senha):
      raise ValueError("A senha deve ter no minimo uma letra maiuscula")

    if not any(c.islower for c in senha):
      raise ValueError("A senha deve ter no minimo uma letra minuscula")
    
    if not any(c.isdigit() for c in senha):
      raise ValueError("A senha deve conter ao menos um numero")
    
    if not any(senha.isalnum()):
      raise ValueError("A senha deve conter ao menos um caractere especial")
