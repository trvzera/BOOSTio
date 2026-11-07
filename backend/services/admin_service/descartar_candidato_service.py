from datetime import datetime, timezone

from models import ProdutoPendente
from .apresentar_pendencia_service import apresentar_pendencia


class DescartarCandidatoService:
    def executar(self, pendencia_id, administrador_id, referencia_peca):
        if not isinstance(referencia_peca, str) or not referencia_peca:
            raise ValueError("Informe a peça a tirar da lista")
        revisao = {"acao": "descartar_candidato", "administrador_id": administrador_id,
                   "em": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}
        pendencia = ProdutoPendente.descartar_candidato(pendencia_id, referencia_peca, revisao)
        return apresentar_pendencia(pendencia, detalhado=True)
