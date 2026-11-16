"""Reação às fotos de setups no canal configurado, sem baixar as imagens."""

import logging

import discord

log = logging.getLogger("botio.setups")


def has_image(message):
    for attachment in message.attachments:
        content_type = attachment.content_type
        if content_type and content_type.lower().startswith("image/"):
            return True
        if not content_type and attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".heic")):
            return True
    return False


async def react_to_setup(client, message):
    if (not client.setups_channel_id or message.guild is None
            or message.guild.id != client.guild_id
            or message.channel.id != client.setups_channel_id
            or message.author.bot or not has_image(message)):
        return False
    try:
        await message.add_reaction("🔥")
    except discord.HTTPException as error:
        log.warning("Não foi possível reagir ao setup: status=%s", error.status)
        return False
    return True
