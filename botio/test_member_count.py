import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import discord

from main import Botio
from member_count import sync_member_count


class MemberCountTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self, *, count=12, name="Contador", allowed=True):
        channel = Mock(spec=discord.VoiceChannel)
        channel.name = name
        channel.edit = AsyncMock()
        channel.permissions_for.return_value = discord.Permissions(view_channel=True, manage_channels=allowed)
        guild = SimpleNamespace(member_count=count, members=[SimpleNamespace(bot=False)],
                                me=object(), get_channel=Mock(return_value=channel))
        return guild, channel

    async def test_total_uses_server_count_including_bots_and_uncached_members(self):
        guild, channel = self.fixture()
        self.assertTrue(await sync_member_count(guild, 10))
        channel.edit.assert_awaited_once()
        self.assertEqual(channel.edit.call_args.kwargs["name"], "👥 Membros: 12")

    async def test_no_edit_when_total_is_unchanged(self):
        guild, channel = self.fixture(name="👥 Membros: 12")
        self.assertFalse(await sync_member_count(guild, 10))
        channel.edit.assert_not_awaited()

    async def test_missing_configuration_leaves_channels_untouched(self):
        guild, channel = self.fixture()
        await sync_member_count(guild, None)
        guild.get_channel.assert_not_called()
        channel.edit.assert_not_awaited()

    async def test_text_channel_cannot_be_renamed(self):
        guild, _ = self.fixture()
        channel = Mock(spec=discord.TextChannel)
        channel.edit = AsyncMock()
        guild.get_channel.return_value = channel
        await sync_member_count(guild, 10)
        channel.edit.assert_not_awaited()

    async def test_missing_permission_leaves_channel_untouched(self):
        guild, channel = self.fixture(allowed=False)
        await sync_member_count(guild, 10)
        channel.edit.assert_not_awaited()

    async def test_unknown_count_does_not_publish_partial_cache_count(self):
        guild, channel = self.fixture(count=None)
        await sync_member_count(guild, 10)
        channel.edit.assert_not_awaited()

    async def test_http_failure_can_retry_with_latest_total(self):
        guild, channel = self.fixture()
        channel.edit.side_effect = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "Missing permission")
        self.assertFalse(await sync_member_count(guild, 10))
        channel.edit.side_effect = None
        guild.member_count = 11
        self.assertTrue(await sync_member_count(guild, 10))
        self.assertEqual(channel.edit.call_args.kwargs["name"], "👥 Membros: 11")

    async def test_periodic_update_uses_only_configured_server(self):
        guild, channel = self.fixture()
        bot = Botio(1, 2, welcome_store=Mock(), member_count_channel_id=10)
        self.addAsyncCleanup(bot.close)
        with patch.object(bot, "get_guild", return_value=guild) as get_guild:
            await bot.refresh_member_count()
        get_guild.assert_called_once_with(1)
        guild.get_channel.assert_called_once_with(10)
        channel.edit.assert_awaited_once()
