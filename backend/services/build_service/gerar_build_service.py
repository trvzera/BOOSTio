from requests.exceptions import HTTPError, Timeout, ConnectionError

from .criar_build_service import CriarBuildService
from services.llm_service.bloquear_geracao_service import BloquearGeracaoService


class GerarBuildService:
    """Coordena uma geração e seu fallback, mantendo a mesma trava e cota."""

    def executar(self, usuario_id, dados):
        with BloquearGeracaoService().executar(usuario_id):
            try:
                return CriarBuildService().executar(usuario_id, dados)
            except HTTPError as erro:
                if erro.response is None or erro.response.status_code not in (429, 500, 502, 503, 504):
                    raise
                return self._fallback(usuario_id, dados)
            except (Timeout, ConnectionError):
                return self._fallback(usuario_id, dados)

    @staticmethod
    def _fallback(usuario_id, dados):
        return CriarBuildService().executar(
            usuario_id, dados, modelo="gemini-3.8-flash", tentativas_correcao=0,
        )
