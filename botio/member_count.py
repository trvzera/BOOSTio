"""Contagem total do servidor, incluindo bots, no nome de um canal de voz."""

import logging

import discord

log = logging.getLogger("botio.member_count")


async def sync_member_count(guild, channel_id):
    if not channel_id:
        return False
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.VoiceChannel):
        log.warning("Contador: configure um canal de voz válido no servidor.")
        return False
    # member_count vem do Gateway e inclui bots e membros fora do cache local.
    count = guild.member_count
    if count is None or count < 0:
        log.warning("Contador: total de membros ainda indisponível.")
        return False
    name = f"👥 Membros: {count}"
    if channel.name == name:
        return False
    me = guild.me
    if me is None:
        return False
    permissions = channel.permissions_for(me)
    if not permissions.view_channel or not permissions.manage_channels:
        log.warning("Contador: BOTio precisa de Ver canal e Gerenciar canais no canal de voz.")
        return False
    try:
        await channel.edit(name=name, reason="BOTio: total de membros, incluindo bots")
    except discord.HTTPException as error:
        log.warning("Contador não atualizado: status=%s; nova tentativa em 5 min.", error.status)
        return False
    log.info("Contador atualizado: %s membros, incluindo bots.", count)
    return True
