from models import Usuario

class EntrarGoogleService:
  def executar(self, dados_google: dict):
    # O controller fornece as informações do ID token validado pelo Authlib.
    self._validar_identidade(dados_google)
    google_sub = dados_google["sub"]
    usuario = Usuario.buscar_por_google_sub(google_sub)
    if usuario:
      self._validar_ativo(usuario)
      return usuario

    email = dados_google["email"].strip().lower()
    usuario = Usuario.buscar_por_email(email)
    if usuario:
      self._validar_ativo(usuario)
      if (usuario.google_sub is None and usuario.login_google
          and usuario.verificado and usuario.senha is None):
        usuario.vincular_google_legado(google_sub)
        return usuario
      raise ValueError(
        "Este email já possui uma conta. Entre pelo método original; "
        "a vinculação automática com o Google não é permitida."
      )

    nome = dados_google.get("name")
    usuario = Usuario(
      nome=nome[:30] if isinstance(nome, str) and nome.strip() else "Usuário Google",
      email=email,
      senha=None,
      google_sub=google_sub,
      login_google=True,
      verificado=True
    )

    usuario.salvar()

    return usuario

  def _validar_identidade(self, dados):
    if not isinstance(dados, dict) or dados.get("email_verified") is not True:
      raise ValueError("Email do Google não verificado")
    sub = dados.get("sub")
    email = dados.get("email")
    if not isinstance(sub, str) or not sub.strip() or len(sub) > 255:
      raise ValueError("Identificador do Google inválido")
    if (not isinstance(email, str) or not email.strip()
        or "@" not in email or len(email.strip()) > 150):
      raise ValueError("Email do Google inválido")

  def _validar_ativo(self, usuario):
    if not usuario.ativo:
      raise ValueError("Esta conta está desativada")
