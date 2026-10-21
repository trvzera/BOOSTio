from models import BuildSalva
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService


class AtualizarBuildService:
    def executar(self, usuario_id, identificador, dados):
        build = BuildSalva.buscar(usuario_id, identificador)
        if build is None:
            raise ValueError("Build não encontrada")
        build.salvar_estado(dados)
        return AvaliarCompatibilidadeService().para_resposta(build, incluir_links=True)
