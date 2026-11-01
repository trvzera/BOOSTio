from models import BuildSalva


class ExcluirBuildService:
    def executar(self, usuario_id, identificador):
        if not usuario_id or not identificador:
            raise ValueError("Build não encontrada")

        build = BuildSalva.buscar(usuario_id, identificador)
        if build is None:
            raise ValueError("Build não encontrada")
        if build.estado.get("travada"):
            raise ValueError("Destranque a build para excluir")
        build.excluir_com_original()
