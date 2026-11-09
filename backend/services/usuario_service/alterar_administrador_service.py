from models import Usuario


class AlterarAdministradorService:
    def executar(self, email: str, administrador: bool) -> dict:
        usuario = Usuario.buscar_por_email((email or "").strip())
        if usuario is None or not usuario.ativo:
            raise ValueError("Conta não encontrada")
        if administrador and not usuario.verificado:
            raise ValueError("Só contas com e-mail verificado podem ser administradoras")
        if bool(usuario.administrador) == administrador:
            return {"email": usuario.email, "administrador": administrador, "alterada": False}
        if not Usuario.alterar_administrador(usuario.id, administrador):
            raise ValueError("Não foi possível alterar a conta; confira se ela continua ativa e verificada")
        return {"email": usuario.email, "administrador": administrador, "alterada": True}
