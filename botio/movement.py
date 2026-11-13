"""Registros de entrada e saída destinados somente à equipe."""

import logging
import discord

log = logging.getLogger("botio.movement")


async def send_movement(client, member, *, joined):
    if not client.movement_channel_id:
        log.info("Registro de movimentação desativado: configure DISCORD_MOVEMENT_CHANNEL_ID.")
        return
    channel = member.guild.get_channel(client.movement_channel_id)
    if not isinstance(channel, discord.TextChannel):
        log.warning("Canal de movimentação não encontrado.")
        return
    public_roles = [member.guild.default_role, member.guild.get_role(client.role_id)]
    if any(role is not None and channel.permissions_for(role).view_channel for role in public_roles):
        log.error("Registro de movimentação bloqueado: o canal deve estar oculto para @everyone e Membro.")
        return
    now = discord.utils.utcnow()
    action = "entrou no servidor" if joined else "saiu do servidor"
    embed = discord.Embed(title="Membro entrou" if joined else "Membro saiu",
                          description=f"{member.mention} {action}.",
                          color=0x0088FF if joined else 0x747F8D, timestamp=now)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Usuário", value=discord.utils.escape_markdown(str(member)), inline=True)
    embed.add_field(name="ID do usuário", value=str(member.id), inline=True)
    embed.add_field(name="Data e hora", value=f"<t:{int(now.timestamp())}:F>", inline=False)
    embed.add_field(name="Conta criada", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=False)
    embed.set_footer(text="BOTio · Registro privado da equipe")
    try:
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException as error:
        log.warning("Não foi possível registrar movimentação: status=%s", error.status)
