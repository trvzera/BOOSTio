from models import BuildSalva, Usuario
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService


class CriarBuildManualService:
    def executar(self, usuario_id, dados):
        if not isinstance(dados, dict):
            raise ValueError("Envie uma build válida")

        dados = self._aplicar_budget(usuario_id, dados)
        estado = BuildSalva.validar_estado(dados)
        build = BuildSalva.criar_limitada(usuario_id, estado)

        return AvaliarCompatibilidadeService().para_resposta(build, incluir_links=True)

    @staticmethod
    def _aplicar_budget(usuario_id, dados):
        if "orcamento" not in dados:
            usuario = Usuario.buscar_por_id(usuario_id)
            budget = usuario.budget if usuario and usuario.usar_budget and usuario.budget is not None else None
            dados = {**dados, "orcamento": float(budget) if budget is not None and budget > 0 else None}
        return dados
