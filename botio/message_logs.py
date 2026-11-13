"""Registros privados de alterações em mensagens da comunidade, sem banco local."""

import logging

import discord

log = logging.getLogger("botio.message_logs")
UNAVAILABLE = "Texto indisponível: mensagem fora do cache ou recebida com o bot desligado."


def context(client, payload):
    destination_id = client.message_log_channel_id
    if not destination_id or payload.guild_id != client.guild_id or payload.channel_id == destination_id:
        return None
    guild = client.get_guild(client.guild_id)
    if guild is None:
        return None
    source = guild.get_channel_or_thread(payload.channel_id)
    if not isinstance(source, (discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel)):
        return None
    if isinstance(source, discord.Thread) and source.is_private():
        return None
    parent = source.parent if isinstance(source, discord.Thread) else source
    if parent is None:
        return None
    if client.tickets.category_id and parent.category_id == client.tickets.category_id:
        return None
    roles = [guild.default_role, guild.get_role(client.role_id)]
    # Não copia mensagens da equipe ou de outros canais privados para o log.
    if not any(role is not None and source.permissions_for(role).view_channel for role in roles):
        return None
    destination = guild.get_channel(destination_id)
    if not isinstance(destination, discord.TextChannel):
        log.warning("Mensagens: canal de registros não encontrado.")
        return None
    if any(role is not None and destination.permissions_for(role).view_channel for role in roles):
        log.error("Mensagens: registros bloqueados porque o canal de destino não é privado.")
        return None
    return destination, source


def text_excerpt(value, limit=1024):
    value = discord.utils.escape_mentions(discord.utils.escape_markdown(value or "(sem texto)"))
    return value if len(value) <= limit else value[:limit - 1] + "…"


def author_text(message, data=None):
    if message is not None:
        return f"{text_excerpt(message.author.name)}\nID: {message.author.id}"
    author = (data or {}).get("author", {})
    if author.get("id"):
        return f"{text_excerpt(author.get('username', 'Usuário'))}\nID: {author['id']}"
    return "Autor indisponível no cache."


async def send(destination, embed):
    try:
        await destination.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException as error:
        log.warning("Registro de mensagem não enviado: status=%s", error.status)
        return False
    return True


async def log_edit(client, payload):
    channels = context(client, payload)
    if channels is None:
        return False
    before = payload.cached_message
    data = payload.data
    if (before is not None and before.author.bot) or data.get("author", {}).get("bot", False):
        return False
    content_changed = "content" in data and (before is None or before.content != data["content"])
    attachment_changed = "attachments" in data and (
        before is None or {item.id for item in before.attachments} != {int(item["id"]) for item in data["attachments"]})
    if not content_changed and not attachment_changed:
        return False  # Mudanças automáticas de embeds não são edições de texto.
    destination, source = channels
    embed = discord.Embed(title="✏️ Mensagem editada", color=0xF5A623, timestamp=discord.utils.utcnow(),
                          description=f"Canal: {source.mention}\nID da mensagem: {payload.message_id}\n"
                                      f"[Abrir mensagem](https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id})")
    embed.add_field(name="Autor", value=author_text(before, data), inline=False)
    embed.add_field(name="Antes", value=text_excerpt(before.content) if before else UNAVAILABLE, inline=False)
    after = data.get("content", before.content if before else None)
    embed.add_field(name="Depois", value=text_excerpt(after) if after is not None else "Texto não informado pelo Discord.", inline=False)
    if attachment_changed:
        previous = len(before.attachments) if before else "indisponível"
        embed.add_field(name="Quantidade de anexos", value=f"Antes: {previous} · Depois: {len(data['attachments'])}", inline=False)
    return await send(destination, embed)


async def log_delete(client, payload):
    channels = context(client, payload)
    if channels is None:
        return False
    message = payload.cached_message
    if message is not None and message.author.bot:
        return False
    destination, source = channels
    embed = discord.Embed(title="🗑️ Mensagem excluída", color=0xE74C3C, timestamp=discord.utils.utcnow(),
                          description=f"Canal: {source.mention}\nID da mensagem: {payload.message_id}")
    embed.add_field(name="Autor", value=author_text(message), inline=False)
    embed.add_field(name="Texto excluído", value=text_excerpt(message.content) if message else UNAVAILABLE, inline=False)
    return await send(destination, embed)


async def log_bulk_delete(client, payload):
    channels = context(client, payload)
    if channels is None:
        return False
    destination, source = channels
    embed = discord.Embed(title="🗑️ Mensagens excluídas em lote", color=0xE74C3C, timestamp=discord.utils.utcnow(),
                          description=f"Canal: {source.mention}\nTotal excluído: {len(payload.message_ids)}")
    ids = sorted(payload.message_ids)
    embed.add_field(name="IDs das mensagens (até 20)", value=", ".join(map(str, ids[:20])) or "Não informado", inline=False)
    cached = sorted((message for message in payload.cached_messages if not message.author.bot), key=lambda message: message.id)
    for message in cached[:5]:
        embed.add_field(name=f"Mensagem {message.id}", value=text_excerpt(f"{message.author.name} (ID {message.author.id})\n{message.content}", 800), inline=False)
    embed.set_footer(text="Até 5 trechos disponíveis no cache. Mensagens fora do cache não podem ser recuperadas.")
    return await send(destination, embed)
