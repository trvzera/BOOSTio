from models import BuildSalva


class BuscarBuildService:
    def executar(self, usuario_id: int, build_id: str) -> dict:
        build = BuildSalva.buscar(usuario_id, build_id)
        if build is None:
            raise ValueError("Build não encontrada")
        return build.to_dict(incluir_links=True)
