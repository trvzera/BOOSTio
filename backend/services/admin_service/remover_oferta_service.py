from models import Oferta
from services.build_service.listar_catalogo_build_service import ListarCatalogoBuildService


class RemoverOfertaService:
    def executar(self, oferta_id):
        oferta = Oferta.retirar_do_catalogo(oferta_id)
        if oferta is None:
            raise LookupError("Oferta não encontrada")
        ListarCatalogoBuildService.limpar_cache()
        return {"id": oferta.id, "loja": oferta.loja, "produto_id_loja": oferta.produto_id_loja, "ativa": oferta.ativa}
