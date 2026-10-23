from models import Usuario
from utils.validacoes import validar_senha_forte
from werkzeug.security import generate_password_hash,check_password_hash
from email_validator import validate_email, ValidatedEmail
from .confirmar_identidade_service import ConfirmarIdentidadeService

class AtualizarUsuarioService:
  def executar(self, usuario_id: int, dados: dict) -> dict | None:
    if not usuario_id:
      return None
    if not isinstance(dados, dict):
      raise ValueError("Envie um objeto JSON válido")
    nome = dados.get("nome")
    if nome is not None and (not isinstance(nome, str) or not 0 < len(nome.strip()) <= 30):
      raise ValueError("Informe um nome de até 30 caracteres")
    if dados.get("senha") is not None and (not isinstance(dados["senha"], str) or len(dados["senha"]) > 1024):
      raise ValueError("Senha inválida")

    usuario = Usuario.buscar_por_id(usuario_id)
    
    if usuario is None:
      return None
    
    novo_email = dados.get("email")
    
    email_tratado: str | None = None

    if novo_email:
      if not isinstance(novo_email, str) or len(novo_email) > 150:
        raise ValueError("Informe um email válido")
      email_tratado = self._validar_email(novo_email).normalized.lower()
      usuario_existente = Usuario.buscar_por_email(email_tratado)

      if usuario_existente and usuario_existente.id != usuario.id:
        raise ValueError("Já existe um usuario com esse email")
      if email_tratado != usuario.email:
        ConfirmarIdentidadeService().executar(usuario, dados)

      
    senha = dados.get("senha")

    if senha:
      verificacao = self._confirma_senha(dados,usuario.senha)
      if verificacao:
        validar_senha_forte(senha)
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
  def _validar_email(email: str) -> ValidatedEmail:
    return  validate_email(email,check_deliverability=False)
