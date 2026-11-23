from flask import current_app
from itsdangerous import BadData, URLSafeTimedSerializer

from models import Codigo, db


class LinkVerificacaoEmailService:
    _INVALIDO = "Este link é inválido, já foi usado ou expirou. Solicite outro e-mail de verificação."

    @staticmethod
    def _assinador():
        return URLSafeTimedSerializer(current_app.secret_key, salt="boostio-verificacao-email")

    def montar_link(self, codigo):
        token = self._assinador().dumps([codigo.id, codigo.criado_em.isoformat()])
        frontend = current_app.config["FRONTEND_URL"].rstrip("/")
        return f"{frontend}/pages/verificar-email.html#token={token}"

    def confirmar(self, token):
        if not isinstance(token, str) or not 1 <= len(token) <= 512:
            raise ValueError(self._INVALIDO)
        try:
            codigo_id, criado_em = self._assinador().loads(token, max_age=300)
        except (BadData, TypeError, ValueError):
            raise ValueError(self._INVALIDO) from None

        codigo = db.session.get(Codigo, codigo_id)
        if (not codigo or codigo.usado or codigo.esta_expirado()
                or codigo.criado_em.isoformat() != criado_em):
            raise ValueError(self._INVALIDO)

        try:
            codigo.confirmar_email()
        except ValueError:
            raise ValueError(self._INVALIDO) from None
