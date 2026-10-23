import os


class ValidarProducaoService:
  def executar(self, app):
    chave = app.config.get("SECRET_KEY")
    if not isinstance(chave, str) or len(chave) < 32:
      raise RuntimeError("Configure SECRET_KEY com pelo menos 32 caracteres em produção")

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
      raise RuntimeError("Configure URL_DATABASE em produção")

    obrigatorias = (
      "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GEMINI_API_KEY",
      "MAIL_USERNAME", "MAIL_PASSWORD",
    )
    ausentes = [nome for nome in obrigatorias if not os.getenv(nome, "").strip()]
    if ausentes:
      raise RuntimeError("Configure as variáveis de produção: " + ", ".join(ausentes))
