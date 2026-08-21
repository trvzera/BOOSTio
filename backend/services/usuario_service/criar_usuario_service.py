from models import Usuario
from werkzeug.security import generate_password_hash
from email_validator import validate_email
from utils.validacoes import validacao_campos,validar_senha_forte

class CriarUsuarioService:
  def executar(self, dados: dict) -> Usuario:

    validacao_campos(dados,campos_obrigatorios = ["nome","email","senha"])

    email_tratado = self._validar_email(dados['email']).lower()

    usuario_existente = Usuario.buscar_por_email(email_tratado)

    if usuario_existente:
      raise ValueError("Esse Usuario já existe,experimente fazer login")

    validar_senha_forte(dados["senha"])

    senha_protegida = generate_password_hash(dados["senha"])

    usuario = Usuario(
      nome = dados['nome'],
      email = email_tratado,
      senha = senha_protegida,
    )

    usuario.salvar()

    return usuario

  @staticmethod
  def _validar_email(email:str) -> str:
    return validate_email(email,check_deliverability=False).normalized