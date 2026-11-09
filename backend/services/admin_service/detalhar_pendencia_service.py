from models import ProdutoPendente
from .apresentar_pendencia_service import apresentar_pendencia


class DetalharPendenciaService:
    def executar(self, pendencia_id):
        pendencia = ProdutoPendente.buscar_por_id(pendencia_id)
        if pendencia is None:
            raise LookupError("Pendência não encontrada")
        return apresentar_pendencia(pendencia, detalhado=True)
