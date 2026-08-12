from models import Usuario
from werkzeug.security import generate_password_hash
from email_validator import validate_email
from utils.validacoes import validacao_campos 

class CriarUsuarioService:
  def executar(self, dados: dict) -> Usuario:

    validacao_campos(dados,campos_obrigatorios = ["nome","email","senha"])

    email_tratado = self._validar_email(dados['email']).lower()
    
    usuario_existente = Usuario.buscar_por_email(email_tratado)

    if usuario_existente:
      raise ValueError("Esse Usuario já existe,experimente fazer login")

    self._validar_senha(dados["senha"])
    
    senha_protegida = generate_password_hash(dados["senha"])

    usuario = Usuario(
      nome = dados['nome'],
      email = email_tratado,
      senha = senha_protegida,
    )

    usuario.salvar()

    return usuario

  @staticmethod
  def _validar_senha(senha:str) -> None:
    if len(senha) < 8:
        raise ValueError("A senha deve ter no minimo oito caracteres")

    if not any(c.isupper() for c in senha):
        raise ValueError("A senha deve ter no minimo uma letra maiuscula")

    if not any(c.islower() for c in senha):
        raise ValueError("A senha deve ter no minimo uma letra minuscula")

    if not any(c.isdigit() for c in senha):
        raise ValueError("A senha deve conter ao menos um numero")

    if not any(not c.isalnum() for c in senha):
        raise ValueError("A senha deve conter ao menos um caractere especial")

  @staticmethod
  def _validar_email(email:str) -> str:
    return validate_email(email,check_deliverability=False).normalized