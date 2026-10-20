from models import BuildSalva


class CriarBuildManualService:
    def executar(self, usuario_id, dados):
        build = BuildSalva(usuario_id=usuario_id, estado=BuildSalva.validar_estado(dados))
        build.salvar()
        return build.to_dict(incluir_links=True)
