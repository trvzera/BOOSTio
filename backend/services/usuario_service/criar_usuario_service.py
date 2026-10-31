from models import Usuario, PreferenciasUso
from werkzeug.security import generate_password_hash
from email_validator import validate_email
from utils.validacoes import validacao_campos,validar_senha_forte

class CriarUsuarioService:
  def executar(self, dados: dict) -> Usuario:

    validacao_campos(dados,campos_obrigatorios = ["nome","email","senha"])
    if not isinstance(dados["nome"], str) or not 0 < len(dados["nome"].strip()) <= 30:
      raise ValueError("Informe um nome de até 30 caracteres")
    if not isinstance(dados["email"], str) or len(dados["email"]) > 150:
      raise ValueError("Informe um email válido")
    if not isinstance(dados["senha"], str) or len(dados["senha"]) > 1024:
      raise ValueError("Senha inválida")

    email_tratado = self._validar_email(dados['email']).lower()

    usuario_existente = Usuario.buscar_por_email(email_tratado)

    usuario_existente2 = Usuario.buscar_por_email(dados['email'].lower())
  
    if usuario_existente or usuario_existente2:
      raise ValueError("Esse Usuario já existe,experimente fazer login")

    validar_senha_forte(dados["senha"])

    senha_protegida = generate_password_hash(dados["senha"])

    usuario = Usuario(
      nome = dados['nome'],
      email = email_tratado,
      senha = senha_protegida,
    )

    usuario.preferencias_uso = PreferenciasUso(tutorial="pendente")
    usuario.salvar()

    return usuario

  @staticmethod
  def _validar_email(email:str) -> str:
    return validate_email(email,check_deliverability=False).normalized
