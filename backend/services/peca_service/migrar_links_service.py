from repositories.migracao_links_repository import MigracaoLinksRepository
from .modelos_pecas import MODELOS_PECAS


class MigrarLinksService:
    """Migração incremental do SQLite: mantém registros e transfere links antigos."""

    def executar(self):
        return MigracaoLinksRepository().executar(MODELOS_PECAS)
