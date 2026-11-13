"""Condições para liberar o cargo de comunidade."""


def can_grant(*, bot, pending, has_role, screening_enabled):
    # pending=False significa verificação concluída OU dispensada pelo Discord.
    return screening_enabled and not bot and pending is False and not has_role
