import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord
from movement import send_movement


class MovementTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self, public=False):
        channel = Mock(spec=discord.TextChannel)
        channel.permissions_for.return_value = discord.Permissions(view_channel=public)
        channel.send = AsyncMock()
        guild = SimpleNamespace(default_role=object(), get_role=lambda _: object(), get_channel=lambda _: channel)
        member = SimpleNamespace(guild=guild, mention="<@42>", id=42,
                                 display_avatar=SimpleNamespace(url="https://cdn.discordapp.com/embed/avatars/0.png"),
                                 created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
        client = SimpleNamespace(movement_channel_id=10, role_id=2)
        return client, member, channel

    async def test_private_log_has_identity_avatar_time_without_notification(self):
        client, member, channel = self.fixture()
        await send_movement(client, member, joined=True)
        channel.send.assert_awaited_once()
        args = channel.send.call_args.kwargs
        embed = args['embed']
        self.assertIn("<@42>", embed.description)
        self.assertEqual(embed.thumbnail.url, member.display_avatar.url)
        self.assertEqual(embed.fields[1].value, "42")
        self.assertIsNotNone(embed.timestamp)
        self.assertEqual(args['allowed_mentions'].to_dict()['parse'], [])

    async def test_public_channel_is_rejected(self):
        client, member, channel = self.fixture(public=True)
        await send_movement(client, member, joined=True)
        channel.send.assert_not_awaited()

    async def test_no_config_does_not_post_anywhere(self):
        client, member, channel = self.fixture()
        client.movement_channel_id = None
        await send_movement(client, member, joined=True)
        channel.send.assert_not_awaited()

    async def test_join_tracks_and_departure_erases_records(self):
        from main import Botio
        store = Mock()
        bot = Botio(1, 2, welcome_store=store)
        self.addAsyncCleanup(bot.close)
        client, member, channel = self.fixture()
        member.guild.id = 1
        member.bot = False
        bot.grant_member = AsyncMock()
        await bot.on_member_join(member)
        store.track.assert_called_once_with(member)
        bot.grant_member.assert_awaited_once_with(member)
        await bot.on_member_remove(member)
        store.forget.assert_called_once_with(1, 42)
