from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math


class FalhaMarketplace(ValueError):
    def __init__(self, status=None, retry_after=None, *, temporaria=False):
        self.status = status
        self.temporaria = temporaria or status in (429, 500, 502, 503, 504)
        self.autenticacao = status in (401, 403)
        self.espera = _retry_after(retry_after)
        super().__init__(f'Consulta de marketplace não concluída (HTTP {status or "rede"})')


def _retry_after(valor):
    try:
        espera = float(valor)
    except (TypeError, ValueError):
        try:
            espera = (parsedate_to_datetime(valor) - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return 0
    return max(0, espera) if math.isfinite(espera) else 0


class FilaAguardando(ValueError):
    pass
