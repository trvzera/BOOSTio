import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord

from tickets import TicketManager, TicketOpenView, TicketCloseView


class TicketTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.default = Mock(spec=discord.Role)
        self.default.id = 1
        self.member_role = Mock(spec=discord.Role)
        self.member_role.id = 2
        self.staff = Mock(spec=discord.Role)
        self.staff.id = 3
        self.staff.is_default.return_value = False
        self.staff.managed = False
        self.owner = Mock(spec=discord.Member)
        self.owner.id = 42
        self.owner.bot = False
        self.owner.pending = False
        self.owner.roles = [self.member_role]
        self.owner.guild_permissions = discord.Permissions.none()
        self.owner.mention = "<@42>"
        self.category = Mock(spec=discord.CategoryChannel)
        self.category.id = 10
        self.category.permissions_for.return_value = discord.Permissions(
            view_channel=True, manage_channels=True, manage_roles=True)
        self.channel = Mock(spec=discord.TextChannel)
        self.channel.id = 100
        self.channel.category_id = 10
        self.channel.topic = "BOTio ticket owner=42"
        self.channel.mention = "<#100>"
        self.channel.send = AsyncMock()
        self.channel.delete = AsyncMock()
        self.channels = []

        async def create(**kwargs):
            self.channels.append(self.channel)
            return self.channel

        self.guild = SimpleNamespace(
            id=1, default_role=self.default, me=Mock(spec=discord.Member),
            get_role=Mock(return_value=self.staff), fetch_member=AsyncMock(return_value=self.owner),
            fetch_channel=AsyncMock(side_effect=lambda channel_id: self.category if channel_id == 10 else self.channel),
            fetch_channels=AsyncMock(side_effect=lambda: list(self.channels)),
            create_text_channel=AsyncMock(side_effect=create),
        )
        self.client = SimpleNamespace(guild_id=1, role_id=2)
        self.manager = TicketManager(self.client, 10, 3)

    def interaction(self):
        return SimpleNamespace(
            guild=self.guild, guild_id=1, channel_id=100, user=self.owner,
            response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock(), edit_message=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()), edit_original_response=AsyncMock(),
        )

    async def test_open_denies_everyone_and_grants_only_requester_staff_and_bot(self):
        interaction = self.interaction()
        await self.manager.open(interaction)
        self.guild.create_text_channel.assert_awaited_once()
        kwargs = self.guild.create_text_channel.call_args.kwargs
        overwrites = kwargs["overwrites"]
        self.assertFalse(overwrites[self.default].view_channel)
        self.assertNotIn(self.member_role, overwrites)
        self.assertEqual(set(overwrites), {self.default, self.staff, self.owner, self.guild.me})
        self.assertTrue(overwrites[self.owner].view_channel)
        self.assertTrue(overwrites[self.staff].view_channel)
        self.assertIsNone(overwrites[self.owner].manage_channels)
        self.assertIsNone(overwrites[self.owner].manage_roles)
        self.assertEqual(kwargs["category"], self.category)
        self.assertEqual(kwargs["topic"], "BOTio ticket owner=42")
        self.assertEqual(self.channel.send.call_args.kwargs["allowed_mentions"].to_dict()["parse"], [])
        self.assertTrue(interaction.followup.send.call_args.kwargs["ephemeral"])

    async def test_simultaneous_requests_create_only_one_ticket(self):
        await asyncio.gather(self.manager.open(self.interaction()), self.manager.open(self.interaction()))
        self.guild.create_text_channel.assert_awaited_once()

    async def test_existing_ticket_is_recovered_after_restart(self):
        self.channels.append(self.channel)
        restarted = TicketManager(self.client, 10, 3)
        interaction = self.interaction()
        await restarted.open(interaction)
        self.guild.create_text_channel.assert_not_awaited()
        self.assertIn("<#100>", interaction.followup.send.call_args.args[0])

    async def test_pending_or_unreleased_member_cannot_open_ticket(self):
        for pending, roles in ((True, [self.member_role]), (None, [self.member_role]), (False, [])):
            with self.subTest(pending=pending, roles=bool(roles)):
                self.owner.pending, self.owner.roles = pending, roles
                await self.manager.open(self.interaction())
        self.guild.create_text_channel.assert_not_awaited()

    async def test_other_server_and_missing_configuration_are_rejected(self):
        interaction = self.interaction()
        interaction.guild_id = 99
        await self.manager.open(interaction)
        await TicketManager(self.client).open(self.interaction())
        self.guild.fetch_member.assert_not_awaited()
        self.guild.create_text_channel.assert_not_awaited()

    async def test_public_member_role_cannot_be_used_as_support(self):
        self.staff.id = self.client.role_id
        await self.manager.open(self.interaction())
        self.guild.create_text_channel.assert_not_awaited()

    async def test_missing_category_permissions_cannot_create_ticket(self):
        self.category.permissions_for.return_value = discord.Permissions(view_channel=True)
        await self.manager.open(self.interaction())
        self.guild.create_text_channel.assert_not_awaited()

    async def test_ticket_survives_failure_to_send_first_message(self):
        self.channel.send.side_effect = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "No send")
        await self.manager.open(self.interaction())
        await self.manager.open(self.interaction())
        self.guild.create_text_channel.assert_awaited_once()
        self.channel.delete.assert_not_awaited()

    async def test_creation_timeout_is_recovered_instead_of_creating_duplicate(self):
        async def uncertain_create(**kwargs):
            self.channels.append(self.channel)
            raise discord.HTTPException(SimpleNamespace(status=500, reason="Internal error"), "Unknown outcome")
        self.guild.create_text_channel.side_effect = uncertain_create
        await self.manager.open(self.interaction())
        await self.manager.open(self.interaction())
        self.guild.create_text_channel.assert_awaited_once()

    async def test_reopening_just_closed_ticket_is_throttled(self):
        await self.manager.open(self.interaction())
        self.channels.clear()
        interaction = self.interaction()
        await self.manager.open(interaction)
        self.guild.create_text_channel.assert_awaited_once()
        self.assertIn("Aguarde um minuto", interaction.followup.send.call_args.args[0])

    async def confirmation(self):
        interaction = self.interaction()
        await self.manager.request_close(interaction)
        return interaction.followup.send.call_args.kwargs["view"]

    async def test_closure_requires_explicit_confirmation_and_can_be_cancelled(self):
        view = await self.confirmation()
        self.channel.delete.assert_not_awaited()
        await view.cancel.callback(self.interaction())
        self.channel.delete.assert_not_awaited()
        await view.confirm.callback(self.interaction())
        self.channel.delete.assert_not_awaited()

    async def test_owner_can_confirm_deletion_only_once(self):
        view = await self.confirmation()
        await view.confirm.callback(self.interaction())
        await view.confirm.callback(self.interaction())
        self.channel.delete.assert_awaited_once()

    async def test_another_user_cannot_confirm_requesters_deletion(self):
        view = await self.confirmation()
        interaction = self.interaction()
        interaction.user = SimpleNamespace(id=77)
        await view.confirm.callback(interaction)
        self.channel.delete.assert_not_awaited()

    async def test_unrelated_channel_is_never_deleted(self):
        self.channel.category_id = 999
        await self.manager.request_close(self.interaction())
        self.channel.delete.assert_not_awaited()
        self.channel.category_id = 10
        self.channel.topic = "Canal de avisos"
        await self.manager.request_close(self.interaction())
        self.channel.delete.assert_not_awaited()

    async def test_staff_permission_is_rechecked_at_confirmation(self):
        self.channel.topic = "BOTio ticket owner=999"
        self.owner.roles.append(self.staff)
        view = await self.confirmation()
        self.owner.roles = [self.member_role]
        await view.confirm.callback(self.interaction())
        self.channel.delete.assert_not_awaited()

    async def test_persistent_buttons_work_after_restart(self):
        self.assertTrue(TicketOpenView(self.manager).is_persistent())
        self.assertTrue(TicketCloseView(self.manager).is_persistent())
