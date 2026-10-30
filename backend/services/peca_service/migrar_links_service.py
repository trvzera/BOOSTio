from repositories.migracao_links_repository import MigracaoLinksRepository
from .modelos_pecas import MODELOS_PECAS


class MigrarLinksService:
    def executar(self):
        return MigracaoLinksRepository().executar(MODELOS_PECAS)
