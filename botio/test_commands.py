from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import unittest

import discord

from commands import AnnouncePreview, can_announce


class AnnouncementTests(unittest.IsolatedAsyncioTestCase):
    def interaction(self, *, author=42, allowed=True, guild_id=1):
        user = Mock(spec=discord.Member)
        user.id = author
        user.guild_permissions = discord.Permissions(manage_guild=allowed)
        channel = Mock(spec=discord.TextChannel)
        channel.send = AsyncMock(return_value=SimpleNamespace(jump_url="https://discord.com/channels/1/2/3"))
        guild = SimpleNamespace(get_channel=lambda channel_id: channel,
                                fetch_member=AsyncMock(return_value=user))
        return SimpleNamespace(user=user, guild_id=guild_id, guild=guild,
                               response=SimpleNamespace(send_message=AsyncMock(), defer=AsyncMock(), edit_message=AsyncMock()),
                               edit_original_response=AsyncMock()), channel

    async def test_authorization_requires_server_and_permission(self):
        interaction, _ = self.interaction()
        self.assertTrue(can_announce(interaction, 1))
        self.assertFalse(can_announce(interaction, 2))
        interaction.user.guild_permissions = discord.Permissions.none()
        self.assertFalse(can_announce(interaction, 1))

    async def test_other_staff_cannot_confirm_someone_elses_preview(self):
        interaction, channel = self.interaction(author=99)
        view = AnnouncePreview(SimpleNamespace(guild_id=1), 42, 2, discord.Embed(title="Teste"))
        self.assertFalse(await view.interaction_check(interaction))
        channel.send.assert_not_awaited()

    async def test_publish_once_and_disable_mentions(self):
        interaction, channel = self.interaction()
        client = SimpleNamespace(guild_id=1, announcements_channel_id=2)
        view = AnnouncePreview(client, 42, 2, discord.Embed(title="Teste", description="@everyone"))
        await view.publish.callback(interaction)
        await view.publish.callback(interaction)
        channel.send.assert_awaited_once()
        self.assertEqual(channel.send.call_args.kwargs['allowed_mentions'].to_dict()['parse'], [])

    async def test_revoked_permission_blocks_publication(self):
        interaction, channel = self.interaction()
        revoked = Mock(spec=discord.Member)
        revoked.guild_permissions = discord.Permissions.none()
        interaction.guild.fetch_member.return_value = revoked
        view = AnnouncePreview(SimpleNamespace(guild_id=1, announcements_channel_id=2), 42, 2, discord.Embed())
        await view.publish.callback(interaction)
        channel.send.assert_not_awaited()

    async def test_changed_destination_blocks_publication(self):
        interaction, channel = self.interaction()
        view = AnnouncePreview(SimpleNamespace(guild_id=1, announcements_channel_id=99), 42, 2, discord.Embed())
        await view.publish.callback(interaction)
        channel.send.assert_not_awaited()
