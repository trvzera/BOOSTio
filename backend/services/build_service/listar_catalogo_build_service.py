from models import Oferta
from models.modelos_pecas import MODELOS_PECAS


class ListarCatalogoBuildService:
    def executar(self):
        return Oferta.anexar_a_catalogo([peca.to_catalogo() for modelo in MODELOS_PECAS for peca in modelo.listar_publicadas()])
