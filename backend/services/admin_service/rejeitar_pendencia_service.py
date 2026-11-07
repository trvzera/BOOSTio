from datetime import datetime, timezone

from models import ProdutoPendente
from .apresentar_pendencia_service import apresentar_pendencia

MOTIVO_PADRAO = "Rejeitada por um administrador"


class RejeitarPendenciaService:
    def executar(self, pendencia_id, administrador_id, motivo=None, *, origem="administrador"):
        motivo = (motivo or "").strip() or MOTIVO_PADRAO
        if len(motivo) > 200:
            raise ValueError("O motivo deve ter até 200 caracteres")
        revisao = {"acao": "rejeitar", "administrador_id": administrador_id, "origem": origem,
                   "em": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}
        pendencia = ProdutoPendente.rejeitar(pendencia_id, motivo, revisao)
        return apresentar_pendencia(pendencia)
