import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord

from main import Botio
from message_logs import log_edit, log_delete, log_bulk_delete, UNAVAILABLE


class MessageLogTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.source = Mock(spec=discord.TextChannel)
        self.source.category_id = 20
        self.source.mention = "<#10>"
        self.source.permissions_for.return_value = discord.Permissions(view_channel=True)
        self.destination = Mock(spec=discord.TextChannel)
        self.destination.permissions_for.return_value = discord.Permissions.none()
        self.destination.send = AsyncMock()
        self.guild = SimpleNamespace(default_role=object(), get_role=Mock(return_value=object()),
                                     get_channel_or_thread=Mock(return_value=self.source),
                                     get_channel=Mock(return_value=self.destination))
        self.client = SimpleNamespace(guild_id=1, role_id=2, message_log_channel_id=99,
                                      get_guild=Mock(return_value=self.guild))
        self.message = SimpleNamespace(id=100, content="Texto original", attachments=[],
                                       author=SimpleNamespace(name="pessoa", id=42, bot=False))
        self.payload = SimpleNamespace(guild_id=1, channel_id=10, message_id=100,
                                       cached_message=self.message, data={"content": "Texto alterado"})

    async def test_edit_logs_before_and_after_without_notifications(self):
        self.assertTrue(await log_edit(self.client, self.payload))
        kwargs = self.destination.send.call_args.kwargs
        embed = kwargs["embed"]
        self.assertEqual(embed.title, "✏️ Mensagem editada")
        fields = {field.name: field.value for field in embed.fields}
        self.assertEqual(fields["Antes"], "Texto original")
        self.assertEqual(fields["Depois"], "Texto alterado")
        self.assertIn("42", fields["Autor"])
        self.assertEqual(kwargs["allowed_mentions"].to_dict()["parse"], [])

    async def test_deleted_message_uses_cache(self):
        self.assertTrue(await log_delete(self.client, self.payload))
        embed = self.destination.send.call_args.kwargs["embed"]
        self.assertEqual(embed.title, "🗑️ Mensagem excluída")
        self.assertEqual(embed.fields[-1].value, "Texto original")

    async def test_uncached_deletion_explicitly_reports_missing_content(self):
        self.payload.cached_message = None
        await log_delete(self.client, self.payload)
        embed = self.destination.send.call_args.kwargs["embed"]
        self.assertEqual(embed.fields[-1].value, UNAVAILABLE)
        self.assertIn("indisponível", embed.fields[0].value)

    async def test_uncached_edit_can_log_new_text_without_inventing_old_text(self):
        self.payload.cached_message = None
        self.payload.data["author"] = {"id": "42", "username": "pessoa"}
        await log_edit(self.client, self.payload)
        fields = self.destination.send.call_args.kwargs["embed"].fields
        self.assertEqual(fields[1].value, UNAVAILABLE)
        self.assertEqual(fields[2].value, "Texto alterado")

    async def test_embed_only_and_unchanged_edits_are_ignored(self):
        for data in ({"embeds": []}, {"content": "Texto original", "attachments": []}):
            self.payload.data = data
            await log_edit(self.client, self.payload)
        self.destination.send.assert_not_awaited()

    async def test_attachment_changes_are_logged_without_copying_files(self):
        self.payload.data = {"attachments": [{"id": "123", "url": "https://example.com/private.png"}]}
        await log_edit(self.client, self.payload)
        embed = self.destination.send.call_args.kwargs["embed"]
        self.assertEqual(embed.fields[-1].value, "Antes: 0 · Depois: 1")
        self.assertNotIn("private.png", str(embed.to_dict()))

    async def test_private_channels_are_excluded(self):
        self.source.permissions_for.return_value = discord.Permissions.none()
        await log_edit(self.client, self.payload)
        await log_delete(self.client, self.payload)
        self.destination.send.assert_not_awaited()

    async def test_private_threads_are_excluded_even_with_public_parent(self):
        source = Mock(spec=discord.Thread)
        source.is_private.return_value = True
        self.guild.get_channel_or_thread.return_value = source
        await log_delete(self.client, self.payload)
        self.destination.send.assert_not_awaited()

    async def test_public_threads_can_be_logged(self):
        source = Mock(spec=discord.Thread)
        source.is_private.return_value = False
        source.parent = self.source
        source.mention = "<#10>"
        source.permissions_for.return_value = discord.Permissions(view_channel=True)
        self.guild.get_channel_or_thread.return_value = source
        self.assertTrue(await log_delete(self.client, self.payload))

    async def test_public_log_destination_is_rejected(self):
        self.destination.permissions_for.return_value = discord.Permissions(view_channel=True)
        await log_delete(self.client, self.payload)
        self.destination.send.assert_not_awaited()

    async def test_wrong_server_direct_messages_and_log_channel_are_ignored(self):
        for guild_id, channel_id in ((999, 10), (None, 10), (1, 99)):
            self.payload.guild_id, self.payload.channel_id = guild_id, channel_id
            await log_edit(self.client, self.payload)
            await log_delete(self.client, self.payload)
        self.guild.get_channel_or_thread.assert_not_called()
        self.destination.send.assert_not_awaited()

    async def test_bot_messages_are_ignored(self):
        self.message.author.bot = True
        await log_edit(self.client, self.payload)
        await log_delete(self.client, self.payload)
        self.payload.cached_message = None
        self.payload.data["author"] = {"id": "9", "bot": True}
        await log_edit(self.client, self.payload)
        self.destination.send.assert_not_awaited()

    async def test_long_content_and_mentions_fit_discord_limits(self):
        self.message.content = "@everyone " + "*" * 2000
        self.payload.data["content"] = "@here " + "x" * 2000
        await log_edit(self.client, self.payload)
        embed = self.destination.send.call_args.kwargs["embed"]
        self.assertLessEqual(len(embed), 6000)
        self.assertTrue(all(len(field.value) <= 1024 for field in embed.fields))
        self.assertNotIn("@everyone", embed.fields[1].value)
        self.assertNotIn("@here", embed.fields[2].value)

    async def test_bulk_deletion_sends_one_bounded_summary(self):
        messages = [SimpleNamespace(id=100+i, author=self.message.author, content="x"*2000) for i in range(100)]
        payload = SimpleNamespace(guild_id=1, channel_id=10, message_ids={message.id for message in messages},
                                  cached_messages=messages)
        self.assertTrue(await log_bulk_delete(self.client, payload))
        self.destination.send.assert_awaited_once()
        embed = self.destination.send.call_args.kwargs["embed"]
        self.assertLessEqual(len(embed), 6000)
        self.assertEqual(len(embed.fields), 6)
        self.assertIn("Total excluído: 100", embed.description)

    async def test_send_failure_does_not_break_other_handlers(self):
        self.destination.send.side_effect = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "No send")
        self.assertFalse(await log_delete(self.client, self.payload))

    async def test_only_configured_monitoring_enables_server_message_intents(self):
        for destination_id in (None, 99):
            bot = Botio(1, 2, welcome_store=Mock(), message_log_channel_id=destination_id)
            self.addAsyncCleanup(bot.close)
            self.assertEqual(bot.intents.message_content, bool(destination_id))
            self.assertEqual(bot.intents.guild_messages, bool(destination_id))
            self.assertFalse(bot.intents.dm_messages)
