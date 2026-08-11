from models import Usuario
from werkzeug.security import generate_password_hash,check_password_hash
from email_validator import validate_email

class AtualizarUsuarioService:
  def executar(self,usuario_id,dados):
    usuario = Usuario.buscar_por_id(usuario_id)
    if usuario is None:
      return None

    novo_email = dados.get("email")
    if novo_email:
      email_tratado = self._validar_email(novo_email).lower()
      usuario_existente = Usuario.buscar_por_email(email_tratado)

      if usuario_existente and usuario_existente.id != usuario.id:
        raise ValueError("Já existe um usuario com esse email")

    senha = dados.get("senha")

    if senha:
      verificacao = self._confirma_senha(dados,usuario.senha)
      if verificacao:
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
  def _confirma_senha(dados,senha_atual_hash):
    senha_atual_informada = dados.get("senha_atual")

    if not senha_atual_informada:
      return False

    return check_password_hash(senha_atual_hash,senha_atual_informada)

  @staticmethod
  def _validar_email(email):
    return  validate_email(email,check_deliverability=False)