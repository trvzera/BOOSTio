"""Confere identidade e prazo do retorno Google; sessão e HTTP ficam no controller."""

def validar_vinculo(usuario, vinculo, state, agora):
    if (not usuario.is_authenticated or usuario.get_id() != vinculo.get("sessao")
        or usuario.email != vinculo.get("email") or state != vinculo.get("state")
        or not 0 <= agora - vinculo.get("instante", 0) <= 300):
        raise ValueError("A vinculação expirou ou a conta mudou. Inicie novamente pelo perfil.")


def validar_confirmacao(usuario, pendente, dados_usuario, state, agora):
    if (not usuario.is_authenticated or usuario.get_id() != pendente["sessao"]
        or state != pendente["state"]
        or not 0 <= agora - pendente["instante"] <= 300
        or not dados_usuario or dados_usuario.get("sub") != pendente["sub"]
        or dados_usuario.get("email_verified") is not True):
        raise ValueError("Confirme com a mesma conta Google. A solicitação pode ter expirado.")
