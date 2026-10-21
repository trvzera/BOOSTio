from models import BuildSalva, Usuario, db
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService


class CriarBuildManualService:
    def executar(self, usuario_id, dados):
        # Ausência usa a preferência da conta; null explícito preserva importações/cópias sem teto.
        if isinstance(dados, dict) and "orcamento" not in dados:
            usuario = db.session.get(Usuario, usuario_id)
            budget = usuario.budget if usuario and usuario.usar_budget and usuario.budget is not None else None
            dados = {**dados, "orcamento": float(budget) if budget is not None and budget > 0 else None}
        build = BuildSalva.criar_limitada(usuario_id, BuildSalva.validar_estado(dados))
        return AvaliarCompatibilidadeService().para_resposta(build, incluir_links=True)
