from models import BuildSalva
from services.build_service.criar_build_manual_service import CriarBuildManualService


class DuplicarBuildService:
    def executar(self, usuario_id, identificador):
        original = BuildSalva.buscar(usuario_id, identificador)
        if original is None:
            raise ValueError("Build não encontrada")
        estado = {**original.estado, "titulo": (original.estado["titulo"] + " (cópia)")[:100],
                  "travada": False, "visibilidade": "privado"}
        return CriarBuildManualService().executar(usuario_id, estado)
