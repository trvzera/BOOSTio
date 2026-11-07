from models import ProdutoPendente
from services.marketplace_service.processar_fila_service import LOJAS
from services.peca_service.modelos_pecas import MODELOS_PECAS
from .apresentar_pendencia_service import apresentar_pendencia

STATUS = ("em_revisao", "pendente", "rejeitado", "importado")


class ListarPendenciasService:
    def executar(self, *, status="em_revisao", loja=None, categoria=None, depois_id=0, limite=20):
        if status not in STATUS:
            raise ValueError("Situação inválida")
        if loja is not None and loja not in LOJAS:
            raise ValueError("Loja inválida")
        if categoria is not None and categoria not in {m.__tablename__ for m in MODELOS_PECAS}:
            raise ValueError("Categoria inválida")
        if type(depois_id) is not int or depois_id < 0 or type(limite) is not int or not 1 <= limite <= 100:
            raise ValueError("Paginação inválida")
        pendencias, total = ProdutoPendente.listar_para_admin(
            status=status, loja=loja, categoria=categoria, depois_id=depois_id, limite=limite)
        return {
            "pendencias": [apresentar_pendencia(p) for p in pendencias],
            "total": total,
            "proximo": pendencias[-1].id if len(pendencias) == limite else None,
            "por_status": ProdutoPendente.contar_por_status(),
            "lojas": list(LOJAS),
            "categorias": [m.__tablename__ for m in MODELOS_PECAS],
        }
