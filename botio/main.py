import asyncio
import logging
import os
import ssl
from pathlib import Path

import discord
import aiohttp
import certifi
from discord.ext import tasks
from dotenv import load_dotenv

from policy import can_grant
from welcome import WelcomeStore, send_welcome
from commands import register_commands
from movement import send_movement
from member_count import sync_member_count
from tickets import TicketManager, TicketOpenView, TicketCloseView

log = logging.getLogger("botio")


class Botio(discord.Client):
    def __init__(self, guild_id, role_id, *, connector=None, welcome_store=None,
                 announcements_channel_id=None, movement_channel_id=None, member_count_channel_id=None,
                 tickets_category_id=None, support_role_id=None):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents, connector=connector, allowed_mentions=discord.AllowedMentions.none())
        self.guild_id = guild_id
        self.role_id = role_id
        self.grant_lock = asyncio.Lock()
        self.welcome_store = welcome_store or WelcomeStore(Path(os.getenv("BOTIO_STATE_PATH", str(Path(__file__).with_name("state.sqlite3")))))
        self.announcements_channel_id = announcements_channel_id
        self.movement_channel_id = movement_channel_id
        self.member_count_channel_id = member_count_channel_id
        self.tickets = TicketManager(self, tickets_category_id, support_role_id)
        self.tree = register_commands(self)

    async def setup_hook(self):
        self.add_view(TicketOpenView(self.tickets))
        self.add_view(TicketCloseView(self.tickets))
        try:
            await self.tree.sync(guild=discord.Object(id=self.guild_id))
        except discord.HTTPException as error:
            log.warning("Registro de comandos indisponível (status=%s); entrada e cargos continuam ativos.", error.status)
        self.reconcile.start()
        if self.member_count_channel_id:
            self.refresh_member_count.start()

    async def close(self):
        self.reconcile.cancel()
        self.refresh_member_count.cancel()
        await super().close()

    def configured_role(self, guild):
        if guild.id != self.guild_id:
            return None
        if "MEMBER_VERIFICATION_GATE_ENABLED" not in guild.features:
            log.error("Ative o aceite nativo das regras; concessão de cargos pausada.")
            return None
        role = guild.get_role(self.role_id)
        if role is None or role.is_default() or role.managed:
            log.error("Configure um cargo Membro válido e não gerenciado.")
            return None
        me = guild.me
        if me is None or not me.guild_permissions.manage_roles or role >= me.top_role:
            log.error("BOTio precisa de Gerenciar cargos e de um cargo acima de Membro.")
            return None
        elevated = (
            "administrator", "manage_roles", "manage_guild", "manage_channels",
            "manage_webhooks", "kick_members", "ban_members", "moderate_members",
            "manage_messages", "manage_threads", "mention_everyone",
        )
        if any(getattr(role.permissions, permission, False) for permission in elevated):
            log.error("O cargo Membro não deve ter permissões administrativas, de moderação ou menções gerais.")
            return None
        return role

    async def grant_member(self, member):
        if member.guild.id != self.guild_id:
            return
        async with self.grant_lock:
            role = self.configured_role(member.guild)
            if role is None or member.bot:
                return
            try:
                # Reconsulta antes de conceder para evitar usar pending desatualizado.
                current = await member.guild.fetch_member(member.id)
                if current.pending is not False:
                    log.info("Entrada observada; aguardando aceite nativo antes do cargo e da DM.")
                    return
                if role in current.roles:
                    await send_welcome(current, self.welcome_store, log)
                    return
                if not can_grant(
                    bot=current.bot,
                    pending=current.pending,
                    has_role=role in current.roles,
                    screening_enabled=True,
                ):
                    return
                await current.add_roles(role, reason="Verificação nativa concluída; BOTio")
                log.info("Cargo Membro atribuído.")
                await send_welcome(current, self.welcome_store, log)
            except discord.NotFound:
                pass  # O membro pode ter saído durante a sincronização.
            except discord.HTTPException as error:
                log.warning("Não foi possível atribuir cargo: status=%s", error.status)

    async def on_ready(self):
        log.info("BOTio 0.4 conectado. Servidor configurado: %s; boas-vindas privadas ativas.", self.guild_id)
        log.info("Canal de movimentação: %s", self.movement_channel_id or "não configurado")
        log.info("Canal contador de membros: %s", self.member_count_channel_id or "não configurado")
        log.info("Categoria de tickets: %s; cargo de atendimento: %s",
                 self.tickets.category_id or "não configurada", self.tickets.support_role_id or "não configurado")
        if self.get_guild(self.guild_id) is None:
            log.error("BOTio não encontrou o servidor configurado; confira o convite e o ID.")

    async def on_member_join(self, member):
        if member.guild.id != self.guild_id:
            return
        if not member.bot:
            self.welcome_store.track(member)
        await self.grant_member(member)
        await send_movement(self, member, joined=True)

    async def on_member_update(self, before, after):
        if before.pending and after.pending is False:
            if after.guild.id == self.guild_id and not after.bot:
                log.info("Conclusão da verificação recebida; verificando cargo e DM.")
                self.welcome_store.track(after)
            await self.grant_member(after)

    async def on_member_remove(self, member):
        if member.guild.id == self.guild_id:
            self.welcome_store.forget(self.guild_id, member.id)
            await send_movement(self, member, joined=False)

    @tasks.loop(minutes=10)
    async def reconcile(self):
        # Recupera aceites feitos durante desligamentos e falhas temporárias.
        guild = self.get_guild(self.guild_id)
        if guild is None:
            return
        role = self.configured_role(guild)
        if role is None:
            return
        try:
            active_ids = set()
            async for member in guild.fetch_members(limit=None):
                active_ids.add(member.id)
                if member.bot:
                    continue
                if member.pending is not False:
                    if member.pending is True:
                        self.welcome_store.track(member)
                    continue
                if role in member.roles:
                    await send_welcome(member, self.welcome_store, log)
                    continue
                if can_grant(bot=member.bot, pending=member.pending,
                             has_role=role in member.roles, screening_enabled=True):
                    await self.grant_member(member)
            self.welcome_store.prune(self.guild_id, active_ids)
        except discord.HTTPException as error:
            log.warning("Sincronização indisponível; nova tentativa em 10 min. status=%s", error.status)

    @reconcile.before_loop
    async def before_reconcile(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=5)
    async def refresh_member_count(self):
        guild = self.get_guild(self.guild_id)
        if guild is not None:
            await sync_member_count(guild, self.member_count_channel_id)

    @refresh_member_count.before_loop
    async def before_refresh_member_count(self):
        await self.wait_until_ready()


async def run_bot(token, guild_id, role_id, announcements_channel_id=None, movement_channel_id=None,
                  member_count_channel_id=None, tickets_category_id=None, support_role_id=None):
    # Acrescenta as autoridades confiáveis do certifi às do sistema.
    # Mantém a verificação do certificado e do hostname habilitada.
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=context)
    async with Botio(guild_id, role_id, connector=connector, announcements_channel_id=announcements_channel_id,
                     movement_channel_id=movement_channel_id, member_count_channel_id=member_count_channel_id,
                     tickets_category_id=tickets_category_id, support_role_id=support_role_id) as bot:
        await bot.start(token)


def main():
    os.umask(0o077)
    load_dotenv(Path(__file__).with_name(".env"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    token_file = os.getenv("DISCORD_BOT_TOKEN_FILE")
    if token_file:
        token = Path(token_file).read_text().strip()
    if not token:
        raise SystemExit("Preencha DISCORD_BOT_TOKEN em botio/.env (não compartilhe o token).")
    try:
        guild_id = int(os.environ["DISCORD_GUILD_ID"])
        role_id = int(os.environ["DISCORD_MEMBER_ROLE_ID"])
        announcements_id = int(os.getenv("DISCORD_ANNOUNCEMENTS_CHANNEL_ID") or "0") or None
        movement_id = int(os.getenv("DISCORD_MOVEMENT_CHANNEL_ID") or "0") or None
        member_count_id = int(os.getenv("DISCORD_MEMBER_COUNT_CHANNEL_ID") or "0") or None
        tickets_category_id = int(os.getenv("DISCORD_TICKETS_CATEGORY_ID") or "0") or None
        support_role_id = int(os.getenv("DISCORD_SUPPORT_ROLE_ID") or "0") or None
        if any(value is not None and value <= 0 for value in (guild_id, role_id, announcements_id, movement_id,
                                                             member_count_id, tickets_category_id, support_role_id)):
            raise ValueError
    except (KeyError, ValueError):
        raise SystemExit("Preencha os IDs de servidor, cargo e canais com números positivos válidos.") from None
    try:
        asyncio.run(run_bot(token, guild_id, role_id, announcements_id, movement_id, member_count_id,
                            tickets_category_id, support_role_id))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
