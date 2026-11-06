from services.validacoes_service.validar_estado_build_service import validar_estado
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
        atualizar_estado(build, dados)
        return AvaliarCompatibilidadeService().para_resposta(build, incluir_links=True)


def atualizar_estado(build, dados):
    if build.estado.get("travada"):
        if dados != {"travada": False}:
            raise ValueError("Destranque a build para alterar")
        build.gravar_estado({**build.estado, "travada": False})
        return
    build.gravar_estado({**validar_estado(dados), "setupAtual": bool(build.estado.get("setupAtual", False))})
