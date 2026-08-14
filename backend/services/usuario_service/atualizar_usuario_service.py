from models import Usuario
from werkzeug.security import generate_password_hash,check_password_hash
from email_validator import validate_email, ValidatedEmail

class AtualizarUsuarioService:
  def executar(self, usuario_id: int, dados: dict) -> dict | None:
    if not usuario_id:
      return None

    usuario = Usuario.buscar_por_id(usuario_id)
    
    if usuario is None:
      return None
    
    novo_email = dados.get("email")
    
    email_tratado: str | None = None

    if novo_email:
      email_tratado = self._validar_email(novo_email).normalized.lower()
      usuario_existente = Usuario.buscar_por_email(email_tratado)

      if usuario_existente and usuario_existente.id != usuario.id:
        raise ValueError("Já existe um usuario com esse email")

      usuario.verificado = False
      
    senha = dados.get("senha")

    if senha:
      verificacao = self._confirma_senha(dados,usuario.senha)
      if verificacao:
        self._validar_senha(senha)
        senha = generate_password_hash(senha)
      else:
        raise ValueError("Digite a senha atual correta")

    usuario.atualizar_dados(
      dados.get("nome"),
      email_tratado,
      senha,
    )

    return usuario.to_dict()

  @staticmethod
  def _confirma_senha(dados: dict, senha_atual_hash: str) -> bool:
    senha_atual_informada = dados.get("senha_atual")

    if not senha_atual_informada:
      return False

    return check_password_hash(senha_atual_hash,senha_atual_informada)

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
  def _validar_email(email: str) -> ValidatedEmail:
    return  validate_email(email,check_deliverability=False)