from models import Usuario
from services.email_service.enviar_email_recuperar_service import EnviarEmailRecuperarService


class SolicitarRecuperacaoSenhaService:
    """Localiza a conta e solicita envio sem revelar se o e-mail existe."""

    def executar(self, dados):
        email = dados.get("email") if isinstance(dados, dict) else None
        if not isinstance(email, str) or len(email) > 150:
            return
        usuario = Usuario.buscar_por_email(email.strip().lower())
        if usuario and usuario.ativo:
            EnviarEmailRecuperarService().executar(usuario)
