from services.peca_service.modelos_pecas import MODELOS_PECAS


class ListarCatalogoBuildService:
    def executar(self):
        return [peca.to_catalogo() for modelo in MODELOS_PECAS for peca in modelo.mostrar_pecas()]
