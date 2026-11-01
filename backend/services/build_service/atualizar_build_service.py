from models import BuildSalva
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService


class AtualizarBuildService:
    def executar(self, usuario_id, identificador, dados):
        if not usuario_id or not identificador:
            raise ValueError("Build não encontrada")

        if not isinstance(dados, dict):
            raise ValueError("Envie uma build válida")

        build = BuildSalva.buscar(usuario_id, identificador)
        if build is None:
            raise ValueError("Build não encontrada")
        build.salvar_estado(dados)
        return AvaliarCompatibilidadeService().para_resposta(build, incluir_links=True)
