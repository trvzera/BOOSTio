from models import Usuario
#Biblioteca para passar e verificar senha hash(segurança)
from werkzeug.security import generate_password_hash, check_password_hash


class CriarUsuarioService:
  #Adicionar verificação de senha sendo menor que 8 caracteres e etc...
  #Adicionar verificação do formato do email
  #Após cadastrar, logar o usuario direto? Ou exigir login
  
  def executar(self,dados):
    campos_obrigatorios = ["nome","email","senha"]

    #Verificar se os campos obrigatorios estão preenchidos
    for campo in campos_obrigatorios:
      if not dados.get(campo):
        raise ValueError(f"O campo '{campo}' é obrigatório.")
    

    usuario_existente = Usuario.buscar_por_email(dados['email'])

    if usuario_existente:
      raise ValueError("Esse Usuario já existe,experimente fazer login")

    senha_protegida = generate_password_hash(dados["senha"])

    usuario = Usuario(
      nome = dados['nome'],
      email = dados['email'],
      senha = senha_protegida,
    )

    Usuario.salvar(usuario)

    return usuario.to_dict()