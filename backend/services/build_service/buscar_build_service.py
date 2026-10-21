from models import BuildSalva
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService


class BuscarBuildService:
    def executar(self, usuario_id: int, build_id: str) -> dict:
        build = BuildSalva.buscar(usuario_id, build_id)
        if build is None:
            raise ValueError("Build não encontrada")
        return AvaliarCompatibilidadeService().para_resposta(build, incluir_links=True)
