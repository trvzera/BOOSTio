from models import BuildSalva
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService


class BuscarBuildPublicaService:
    def executar(self, identificador):
        build = BuildSalva.buscar_publica(identificador)
        if build is None:
            raise ValueError("Build não encontrada")
        return AvaliarCompatibilidadeService().para_resposta(build, incluir_links=True)
