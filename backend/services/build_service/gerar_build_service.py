from requests.exceptions import HTTPError, Timeout, ConnectionError

from .fluxo_geracao_service import FluxoGeracaoService
from services.llm_service.bloquear_geracao_service import BloquearGeracaoService


class GerarBuildService:
    """Entrada da geração: impede gerações simultâneas do mesmo usuário e, se o provedor da IA falhar,
    tenta uma vez com o modelo de reserva, sem rodada de correção."""
    def executar(self, usuario_id, dados):
        with BloquearGeracaoService().executar(usuario_id):
            try:
                return FluxoGeracaoService().executar(usuario_id, dados)
            except HTTPError as erro:
                if erro.response is None or erro.response.status_code not in (429, 500, 502, 503, 504):
                    raise
                return self._fallback(usuario_id, dados)
            except (Timeout, ConnectionError):
                return self._fallback(usuario_id, dados)

    @staticmethod
    def _fallback(usuario_id, dados):
        return FluxoGeracaoService().executar(
            usuario_id, dados, modelo="gemini-flash-lite-latest", tentativas_correcao=0,
        )
