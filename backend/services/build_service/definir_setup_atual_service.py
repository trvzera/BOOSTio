from models import BuildSalva


class DefinirSetupAtualService:
    def executar(self, usuario_id, identificador):
        BuildSalva.definir_setup_atual(usuario_id, identificador)
