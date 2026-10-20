from models import BuildSalva


class BuscarBuildPublicaService:
    def executar(self, identificador):
        build = BuildSalva.buscar_publica(identificador)
        if build is None:
            raise ValueError("Build não encontrada")
        return build.to_dict(incluir_links=True)
