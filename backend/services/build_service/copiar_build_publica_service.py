from copy import deepcopy

from models import BuildSalva
from .criar_build_manual_service import CriarBuildManualService


class CopiarBuildPublicaService:
    def executar(self, usuario_id, identificador):
        original = BuildSalva.buscar_publica(identificador)
        if original is None:
            raise ValueError("Build não encontrada")
        # Copia componentes, não informações pessoais, budget, tranca ou setup atual.
        estado = {campo: deepcopy(original.estado[campo]) for campo in (
            "titulo", "descricao", "componentes", "incluirPerifericos", "incluirRede", "substituirFansWaterCooler"
        ) if campo in original.estado}
        estado.update(visibilidade="privado", travada=False)
        return CriarBuildManualService().executar(usuario_id, estado)
