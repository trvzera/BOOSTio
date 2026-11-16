import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord

from main import Botio
from setups import react_to_setup

CHANNEL = 1570588343807516733


class SetupReactionTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self, *, content_type="image/png", filename="setup.png"):
        client = SimpleNamespace(guild_id=1, setups_channel_id=CHANNEL)
        message = SimpleNamespace(guild=SimpleNamespace(id=1), channel=SimpleNamespace(id=CHANNEL),
                                  author=SimpleNamespace(bot=False),
                                  attachments=[SimpleNamespace(content_type=content_type, filename=filename)],
                                  add_reaction=AsyncMock())
        return client, message

    async def test_images_get_exactly_one_fire_even_with_multiple_attachments(self):
        client, message = self.fixture()
        message.attachments *= 3
        self.assertTrue(await react_to_setup(client, message))
        message.add_reaction.assert_awaited_once_with("🔥")

    async def test_missing_mime_uses_image_filename(self):
        client, message = self.fixture(content_type=None, filename="MEU-SETUP.JPG")
        self.assertTrue(await react_to_setup(client, message))

    async def test_non_images_and_text_do_not_get_reactions(self):
        for mime, filename in [("video/mp4", "setup.mp4"), ("application/pdf", "setup.pdf"), ("text/plain", "setup.png")]:
            with self.subTest(mime=mime):
                client, message = self.fixture(content_type=mime, filename=filename)
                self.assertFalse(await react_to_setup(client, message))
                message.add_reaction.assert_not_awaited()
        client, message = self.fixture()
        message.attachments = []
        self.assertFalse(await react_to_setup(client, message))
        message.add_reaction.assert_not_awaited()

    async def test_only_humans_in_configured_guild_and_channel(self):
        for alter in (lambda c,m:setattr(m.author,"bot",True),
                      lambda c,m:setattr(m,"guild",None),
                      lambda c,m:setattr(m.guild,"id",2),
                      lambda c,m:setattr(m.channel,"id",CHANNEL+1),
                      lambda c,m:setattr(c,"setups_channel_id",None)):
            client, message = self.fixture()
            alter(client,message)
            self.assertFalse(await react_to_setup(client, message))
            message.add_reaction.assert_not_awaited()

    async def test_missing_permissions_and_deleted_messages_do_not_crash(self):
        for cls, status in [(discord.Forbidden,403),(discord.NotFound,404),(discord.HTTPException,500)]:
            client, message = self.fixture()
            message.add_reaction.side_effect = cls(SimpleNamespace(status=status,reason="Teste"),"Teste")
            self.assertFalse(await react_to_setup(client,message))
            message.add_reaction.assert_awaited_once()

    async def test_gateway_handler_and_intents_work_without_message_logging(self):
        bot = Botio(1, 2, welcome_store=Mock(), setups_channel_id=CHANNEL)
        self.addAsyncCleanup(bot.close)
        self.assertTrue(bot.intents.guild_messages)
        self.assertTrue(bot.intents.message_content)
        _, message = self.fixture()
        await bot.on_message(message)
        message.add_reaction.assert_awaited_once_with("🔥")
