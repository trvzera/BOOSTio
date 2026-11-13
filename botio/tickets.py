"""Atendimento privado; o próprio canal guarda a identificação do ticket."""

import asyncio
import logging
import re
import time

import discord

log = logging.getLogger("botio.tickets")


class TicketError(Exception):
    pass


def ticket_overwrites(guild, owner, staff):
    conversation = dict(view_channel=True, send_messages=True, read_message_history=True,
                        attach_files=True, embed_links=True)
    return {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        staff: discord.PermissionOverwrite(**conversation),
        owner: discord.PermissionOverwrite(**conversation),
        guild.me: discord.PermissionOverwrite(**conversation, manage_channels=True),
    }


class TicketManager:
    def __init__(self, client, category_id=None, support_role_id=None):
        self.client = client
        self.category_id = category_id
        self.support_role_id = support_role_id
        self.lock = asyncio.Lock()
        self.last_open = {}

    def owner_id(self, channel):
        if not isinstance(channel, discord.TextChannel) or channel.category_id != self.category_id:
            return None
        match = re.fullmatch(r"BOTio ticket owner=(\d+)", channel.topic or "")
        return int(match[1]) if match else None

    def check_server(self, interaction):
        if interaction.guild_id != self.client.guild_id or interaction.guild is None:
            raise TicketError("Use este atendimento no servidor da BOOSTio.")
        if not self.category_id or not self.support_role_id:
            raise TicketError("O atendimento ainda não está disponível. Procure a equipe do servidor.")

    def can_close(self, member, owner_id):
        return (member.id == owner_id or member.guild_permissions.manage_guild
                or any(role.id == self.support_role_id for role in member.roles))

    async def open(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            self.check_server(interaction)
            async with self.lock:
                guild = interaction.guild
                owner = await guild.fetch_member(interaction.user.id)
                if owner.bot or owner.pending is not False:
                    raise TicketError("Conclua o aceite das regras antes de abrir um ticket.")
                if (not any(role.id == self.client.role_id for role in owner.roles)
                        and not owner.guild_permissions.manage_guild):
                    raise TicketError("Aguarde a liberação do cargo Membro antes de abrir um ticket.")
                staff = guild.get_role(self.support_role_id)
                category = await guild.fetch_channel(self.category_id)
                if (not isinstance(category, discord.CategoryChannel) or staff is None
                        or staff.is_default() or staff.managed or staff.id == self.client.role_id):
                    raise TicketError("O atendimento está indisponível. Procure a equipe do servidor.")
                # Busca no Discord para também recuperar tickets após reinícios.
                channels = await guild.fetch_channels()
                existing = next((channel for channel in channels if self.owner_id(channel) == owner.id), None)
                if existing is not None:
                    await interaction.followup.send(f"Você já tem um ticket aberto: {existing.mention}",
                                                    ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                    return
                if guild.me is None:
                    raise TicketError("O atendimento está indisponível. Tente novamente em instantes.")
                permissions = category.permissions_for(guild.me)
                if not (permissions.view_channel and permissions.manage_channels and permissions.manage_roles):
                    log.warning("Tickets: BOTio precisa de Ver canal, Gerenciar canais e Gerenciar permissões na categoria.")
                    raise TicketError("A equipe precisa ajustar as permissões do atendimento.")
                now = time.monotonic()
                self.last_open = {key: value for key, value in self.last_open.items() if now - value < 60}
                if owner.id in self.last_open:
                    raise TicketError("Aguarde um minuto antes de abrir outro ticket.")
                # Mantém o intervalo mesmo se a resposta à criação for incerta.
                self.last_open[owner.id] = now
                channel = await guild.create_text_channel(
                    name=f"ticket-{owner.id}", category=category,
                    topic=f"BOTio ticket owner={owner.id}",
                    overwrites=ticket_overwrites(guild, owner, staff),
                    reason="BOTio: atendimento solicitado pelo próprio membro",
                )
                embed = discord.Embed(
                    title="Atendimento BOOSTio",
                    description=(f"{owner.mention}, conte como podemos ajudar.\n\n"
                                 "Este canal é reservado a você e à equipe. Cargos com Administrador também têm acesso.\n\n"
                                 "Ao encerrar, o canal e suas mensagens serão apagados, sem cópia pelo BOTio."),
                    color=0x0088FF,
                )
                try:
                    await channel.send(embed=embed, view=TicketCloseView(self),
                                       allowed_mentions=discord.AllowedMentions.none())
                except discord.HTTPException as error:
                    # O canal já existe; /fechar-ticket funciona mesmo sem botão.
                    log.warning("Ticket criado sem mensagem inicial: status=%s", error.status)
                await interaction.followup.send(f"Seu atendimento foi aberto: {channel.mention}. "
                                                "Envie sua solicitação nesse canal. Use /fechar-ticket para encerrar.",
                                                ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                log.info("Ticket privado aberto.")
        except TicketError as error:
            await interaction.followup.send(str(error), ephemeral=True)
        except discord.HTTPException as error:
            log.warning("Abertura de ticket não confirmada: status=%s", error.status)
            await interaction.followup.send("Não foi possível confirmar a abertura. Aguarde um minuto e use /ticket "
                                            "para localizar um atendimento que já tenha sido criado.", ephemeral=True)

    async def validated_close(self, interaction, channel_id):
        self.check_server(interaction)
        channel = await interaction.guild.fetch_channel(channel_id)
        owner_id = self.owner_id(channel)
        if owner_id is None:
            raise TicketError("Use esta opção dentro de um ticket do BOTio.")
        member = await interaction.guild.fetch_member(interaction.user.id)
        if not self.can_close(member, owner_id):
            raise TicketError("Somente o solicitante e a equipe podem encerrar este ticket.")
        return channel

    async def request_close(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            channel = await self.validated_close(interaction, interaction.channel_id)
        except TicketError as error:
            await interaction.followup.send(str(error), ephemeral=True)
        except discord.HTTPException as error:
            log.warning("Validação de encerramento indisponível: status=%s", error.status)
            await interaction.followup.send("Não foi possível verificar o ticket. Tente novamente.", ephemeral=True)
        else:
            await interaction.followup.send("Encerrar este atendimento? O canal e todas as suas mensagens "
                                            "serão apagados. Essa ação não pode ser desfeita.",
                                            view=ConfirmTicketClose(self, interaction.user.id, channel.id), ephemeral=True)


class TicketOpenView(discord.ui.View):
    def __init__(self, manager):
        super().__init__(timeout=None)
        self.manager = manager

    @discord.ui.button(label="Abrir atendimento", style=discord.ButtonStyle.primary, custom_id="botio:ticket:open")
    async def open_ticket(self, interaction, button):
        await self.manager.open(interaction)


class TicketCloseView(discord.ui.View):
    def __init__(self, manager):
        super().__init__(timeout=None)
        self.manager = manager

    @discord.ui.button(label="Encerrar atendimento", style=discord.ButtonStyle.secondary, custom_id="botio:ticket:close")
    async def close_ticket(self, interaction, button):
        await self.manager.request_close(interaction)


class ConfirmTicketClose(discord.ui.View):
    def __init__(self, manager, author_id, channel_id):
        super().__init__(timeout=60)
        self.manager = manager
        self.author_id = author_id
        self.channel_id = channel_id
        self.used = False

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Esta confirmação pertence a outra pessoa.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirmar encerramento", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        await interaction.response.defer()
        async with self.manager.lock:
            if self.used:
                await interaction.edit_original_response(content="Esta confirmação já foi finalizada.", view=None)
                return
            try:
                channel = await self.manager.validated_close(interaction, self.channel_id)
                self.used = True
                await interaction.edit_original_response(content="Encerrando o atendimento…", view=None)
                await channel.delete(reason="BOTio: encerramento confirmado pelo solicitante ou equipe")
            except TicketError as error:
                await interaction.edit_original_response(content=str(error), view=None)
            except discord.HTTPException as error:
                log.warning("Encerramento de ticket não confirmado: status=%s", error.status)
                await interaction.edit_original_response(content="Não foi possível confirmar o encerramento. "
                                                         "Confira se o canal ainda existe antes de tentar novamente.", view=None)
            else:
                log.info("Ticket privado encerrado.")
            self.stop()

    @discord.ui.button(label="Manter aberto", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        async with self.manager.lock:
            if self.used:
                await interaction.response.send_message("Esta confirmação já foi finalizada.", ephemeral=True)
                return
            self.used = True
            self.stop()
            await interaction.response.edit_message(content="Ticket mantido aberto.", view=None)
