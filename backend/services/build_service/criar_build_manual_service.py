from models import BuildSalva


class CriarBuildManualService:
    def executar(self, usuario_id, dados):
        build = BuildSalva.criar_limitada(usuario_id, BuildSalva.validar_estado(dados))
        return build.to_dict(incluir_links=True)
