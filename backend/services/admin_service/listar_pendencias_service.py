from models import ProdutoPendente
from services.marketplace_service.processar_fila_service import LOJAS
from models.modelos_pecas import MODELOS_PECAS
from .apresentar_pendencia_service import apresentar_pendencia
from .pendencias_acionaveis import ABERTAS, contar_acionaveis, ids_acionaveis

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
        ids = ids_acionaveis(status, loja, categoria) if status in ABERTAS else None
        pendencias, total = ProdutoPendente.listar_para_admin(
            status=status, loja=loja, categoria=categoria, depois_id=depois_id, limite=limite, ids=ids)
        return {
            "pendencias": [apresentar_pendencia(p) for p in pendencias],
            "total": total,
            "proximo": pendencias[-1].id if len(pendencias) == limite else None,
            "por_status": _contagens(),
            "lojas": list(LOJAS),
            "categorias": [m.__tablename__ for m in MODELOS_PECAS],
        }


def _contagens():
    contagens = {s: n for s, n in ProdutoPendente.contar_por_status().items() if s not in ABERTAS}
    return {**contagens, **contar_acionaveis()}
