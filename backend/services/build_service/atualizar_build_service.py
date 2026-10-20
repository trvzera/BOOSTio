from models import BuildSalva


class AtualizarBuildService:
    def executar(self, usuario_id, identificador, dados):
        build = BuildSalva.buscar(usuario_id, identificador)
        if build is None:
            raise ValueError("Build não encontrada")
        build.salvar_estado(dados)
        return build.to_dict(incluir_links=True)
