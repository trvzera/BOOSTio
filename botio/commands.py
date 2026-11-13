"""Comandos restritos ao servidor configurado. Nenhuma execução de shell."""

import asyncio
import logging

import discord
from discord import app_commands
from welcome import SITE_URL, INSTAGRAM_URL

log = logging.getLogger("botio.commands")

PRIVACY_TEXT = (
    "**Privacidade do BOTio**\n\n"
    "A equipe BOOSTio utiliza o bot para liberar o acesso após a verificação do Discord, "
    "enviar uma saudação privada e publicar atualizações aprovadas.\n\n"
    "**Dados:** IDs do servidor e do membro, data de entrada e situação da tentativa de boas-vindas. "
    "Nome e ícone são usados para apresentar a saudação, sem gravação no banco do bot. "
    "Não lemos nem arquivamos conversas; conteúdo de mensagens e presença estão desativados.\n\n"
    "**Armazenamento:** banco local no equipamento que executa o bot; quando hospedado, na VPS. "
    "Não há envio a serviços de anúncios ou IA. Mensagens e comandos também são processados pelo Discord.\n\n"
    "**Retenção:** os registros de boas-vindas permanecem durante sua participação para evitar duplicação. "
    "São removidos ao sair, ou na próxima sincronização completa se o bot estava desligado.\n\n"
    "**Movimentação:** se configurado, o canal privado da equipe recebe entrada/saída, menção, "
    "avatar, ID e datas. Esses registros ficam no Discord até exclusão pela equipe e não são apagados "
    "pelo comando de exclusão local. Para solicitar sua remoção, procure a equipe.\n\n"
    "**Seus direitos:** use /apagar-meus-dados para excluir o registro local. "
    "Isso não remove cargos nem mensagens já entregues no Discord. "
    "Para acesso, correção, dúvidas ou outras solicitações: **contato@boostio.com.br** ou equipe do servidor."
)


def can_announce(interaction, guild_id):
    return (interaction.guild_id == guild_id
            and isinstance(interaction.user, discord.Member)
            and interaction.user.guild_permissions.manage_guild)


def help_message(guild):
    embed = discord.Embed(
        title="Como podemos ajudar?",
        description=(
            "**Monte seu PC**\nUse /montar ou abra o site pelo botão abaixo.\n\n"
            "**Sua privacidade**\nUse /privacidade para consultar os dados utilizados pelo BOTio "
            "e /apagar-meus-dados para excluir seu registro local de boas-vindas."
        ),
        color=0x0088FF,
    )
    embed.set_footer(text="BOOSTio · Menos dúvidas, mais desempenho.")
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Montar meu PC", url=SITE_URL))
    view.add_item(discord.ui.Button(label="Instagram", url=INSTAGRAM_URL))
    if guild.rules_channel is not None:
        view.add_item(discord.ui.Button(label="Regras do servidor", url=guild.rules_channel.jump_url))
    return embed, view


class AnnouncePreview(discord.ui.View):
    def __init__(self, client, author_id, channel_id, embed):
        super().__init__(timeout=180)
        self.client = client
        self.author_id = author_id
        self.channel_id = channel_id
        self.embed = embed
        self.used = False
        self.lock = asyncio.Lock()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id or not can_announce(interaction, self.client.guild_id):
            await interaction.response.send_message("Esta prévia é restrita ao responsável pelo anúncio.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Publicar atualização", style=discord.ButtonStyle.primary)
    async def publish(self, interaction, button):
        async with self.lock:
            if self.used:
                await interaction.response.send_message("Esta prévia já foi finalizada.", ephemeral=True)
                return
            # Revalida a permissão em tempo real, inclusive após mudanças de cargos.
            try:
                member = await interaction.guild.fetch_member(self.author_id)
            except discord.HTTPException:
                await interaction.response.send_message("Não foi possível validar sua permissão. Tente novamente.", ephemeral=True)
                return
            if not member.guild_permissions.manage_guild:
                await interaction.response.send_message("Você precisa de Gerenciar servidor para publicar.", ephemeral=True)
                return
            channel = interaction.guild.get_channel(self.channel_id)
            if (self.client.announcements_channel_id != self.channel_id
                    or not isinstance(channel, discord.TextChannel)):
                await interaction.response.send_message("Canal de anúncios indisponível ou alterado.", ephemeral=True)
                return
            self.used = True
            await interaction.response.defer(ephemeral=True)
            try:
                message = await channel.send(embed=self.embed, allowed_mentions=discord.AllowedMentions.none())
            except discord.HTTPException:
                # Não tenta novamente automaticamente: um timeout pode ocultar sucesso.
                await interaction.edit_original_response(content="Não foi possível confirmar a publicação. Confira o canal antes de tentar novamente.", embed=None, view=None)
                log.warning("Não foi possível confirmar publicação de anúncio.")
            else:
                await interaction.edit_original_response(content=f"Atualização publicada: {message.jump_url}", embed=None, view=None)
                log.info("Atualização publicada no canal configurado.")
            self.stop()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        async with self.lock:
            if self.used:
                await interaction.response.send_message("Esta prévia já foi finalizada.", ephemeral=True)
                return
            self.used = True
            self.stop()
            await interaction.response.edit_message(content="Publicação cancelada.", embed=None, view=None)


def register_commands(client):
    tree = app_commands.CommandTree(client)
    guild = discord.Object(id=client.guild_id)

    @tree.command(name="ajuda", description="Veja os links e comandos úteis da BOOSTio.", guild=guild)
    async def help_command(interaction: discord.Interaction):
        embed, view = help_message(interaction.guild)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True,
                                                allowed_mentions=discord.AllowedMentions.none())

    @tree.command(name="montar", description="Abra o site da BOOSTio para montar seu PC.", guild=guild)
    async def build_link(interaction: discord.Interaction):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Montar meu PC", url=SITE_URL))
        await interaction.response.send_message(f"Monte seu PC no site da BOOSTio: {SITE_URL}",
                                                view=view, ephemeral=True)

    @tree.command(name="privacidade", description="Veja quais dados o BOTio utiliza.", guild=guild)
    async def privacy(interaction: discord.Interaction):
        await interaction.response.send_message(PRIVACY_TEXT, ephemeral=True)

    @tree.command(name="apagar-meus-dados", description="Exclua seu registro local de boas-vindas do BOTio.", guild=guild)
    async def erase(interaction: discord.Interaction):
        client.welcome_store.forget(client.guild_id, interaction.user.id)
        await interaction.response.send_message("Seu registro local de boas-vindas foi excluído. Seu cargo e acesso foram mantidos. Uma nova entrada no servidor gera um novo registro.", ephemeral=True)

    @tree.command(name="testar-boas-vindas", description="Equipe: teste a mensagem privada na sua própria conta.", guild=guild)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.cooldown(1, 60, key=lambda interaction: interaction.user.id)
    async def test_welcome(interaction: discord.Interaction):
        if not can_announce(interaction, client.guild_id):
            await interaction.response.send_message("Restrito à equipe com Gerenciar servidor.", ephemeral=True)
            return
        from welcome import welcome_message
        await interaction.response.defer(ephemeral=True)
        embed, view = welcome_message(interaction.user)
        try:
            await interaction.user.send(embed=embed, view=view, allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            result = "O Discord bloqueou a DM. Confira as configurações de mensagens privadas desta conta."
        except discord.HTTPException as error:
            result = f"Falha de envio (HTTP {error.status}). Confira o terminal."
        else:
            result = "Mensagem de teste enviada no seu privado."
        await interaction.followup.send(result, ephemeral=True)

    @tree.command(name="anunciar", description="Prepare uma atualização com prévia antes de publicar.", guild=guild)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.cooldown(1, 30, key=lambda interaction: interaction.user.id)
    async def announce(interaction: discord.Interaction, titulo: app_commands.Range[str, 1, 180],
                       texto: app_commands.Range[str, 1, 3000]):
        if not can_announce(interaction, client.guild_id):
            await interaction.response.send_message("Você precisa de Gerenciar servidor para anunciar.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(client.announcements_channel_id or 0)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Configure DISCORD_ANNOUNCEMENTS_CHANNEL_ID com o canal público de novidades.", ephemeral=True)
            return
        embed = discord.Embed(title=titulo, description=texto, color=0x0088FF)
        embed.set_footer(text="BOOSTio · Menos dúvidas, mais desempenho.")
        await interaction.response.send_message(content=f"Prévia — destino: {channel.mention}. Só será publicado ao confirmar.",
                                                embed=embed, view=AnnouncePreview(client, interaction.user.id, channel.id, embed),
                                                ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @tree.error
    async def command_error(interaction, error):
        text = "Aguarde alguns segundos antes de tentar novamente." if isinstance(error, app_commands.CommandOnCooldown) else "Não foi possível concluir. Tente novamente ou procure a equipe."
        log.warning("Comando não concluído: %s", type(error).__name__)
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    return tree
