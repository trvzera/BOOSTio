import logging
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import discord

from main import Botio
from welcome import WelcomeStore, send_welcome, SITE_URL, INSTAGRAM_URL


class WelcomeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "state.sqlite3"
        self.store = WelcomeStore(self.path)
        self.member = SimpleNamespace(
            id=42, guild=SimpleNamespace(id=1, icon=None),
            joined_at=datetime.now(timezone.utc), display_name="Pessoa",
            send=AsyncMock(), pending=False, bot=False, roles=[], add_roles=AsyncMock(),
        )
        self.logger = logging.getLogger("test.botio")

    async def test_new_member_gets_links_once_even_after_restart(self):
        self.store.track(self.member)
        await send_welcome(self.member, self.store, self.logger)
        await send_welcome(self.member, WelcomeStore(self.path), self.logger)
        self.member.send.assert_awaited_once()
        message = self.member.send.call_args.kwargs
        urls = [item.url for item in message["view"].children]
        self.assertIn(SITE_URL, urls)
        self.assertIn(INSTAGRAM_URL, urls)
        self.assertIn("Menos dúvidas, mais desempenho.", message["embed"].footer.text)

    async def test_existing_member_is_not_contacted_on_sync(self):
        await send_welcome(self.member, self.store, self.logger)
        self.member.send.assert_not_awaited()

    async def test_gateway_and_rest_precision_refer_to_same_entry(self):
        self.member.joined_at = datetime(2026, 11, 13, 1, 37, 43, 679047, tzinfo=timezone.utc)
        self.store.track(self.member)
        fetched = SimpleNamespace(**vars(self.member))
        fetched.joined_at = self.member.joined_at.replace(microsecond=679000)
        bot = Botio(1, 2, welcome_store=self.store)
        self.addAsyncCleanup(bot.close)
        self.member.guild.fetch_member = AsyncMock(return_value=fetched)
        with patch.object(bot, "configured_role", return_value=SimpleNamespace(id=2)):
            await bot.grant_member(self.member)
            self.store.track(self.member)
            await bot.grant_member(self.member)
        self.member.send.assert_awaited_once()

    def legacy_record(self, joined_at, status):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO welcomes VALUES (?, ?, ?, ?)",
                       ("1", "42", joined_at, status))
            db.execute("PRAGMA user_version=0")

    async def test_migration_recovers_waiting_welcome_with_original_precision(self):
        self.member.joined_at = datetime(2026, 11, 13, 1, 37, 43, 679000, tzinfo=timezone.utc)
        self.legacy_record("2026-11-13T01:37:43.679047+00:00", "waiting")
        await send_welcome(self.member, WelcomeStore(self.path), self.logger)
        await send_welcome(self.member, WelcomeStore(self.path), self.logger)
        self.member.send.assert_awaited_once()

    async def test_migration_preserves_all_attempted_welcomes(self):
        self.member.joined_at = datetime(2026, 11, 13, 1, 37, 43, 679000, tzinfo=timezone.utc)
        for status in ("sent", "blocked", "failed", "claimed"):
            with self.subTest(status=status):
                self.store.forget(1, 42)
                self.legacy_record("2026-11-13T01:37:43.679047+00:00", status)
                store = WelcomeStore(self.path)
                store.track(self.member)
                await send_welcome(self.member, store, self.logger)
                with closing(sqlite3.connect(self.path)) as db:
                    statuses = db.execute("SELECT status FROM welcomes").fetchall()
                self.assertEqual(statuses, [(status,)])
        self.member.send.assert_not_awaited()

    async def test_migration_merges_precision_variants_without_resetting_delivery(self):
        self.member.joined_at = datetime(2026, 11, 13, 1, 37, 43, 679000, tzinfo=timezone.utc)
        self.legacy_record("2026-11-13T01:37:43.679047+00:00", "sent")
        self.legacy_record("2026-11-13T01:37:43.679+00:00", "waiting")
        store = WelcomeStore(self.path)
        self.assertFalse(store.claim(self.member))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT status FROM welcomes").fetchall(), [("sent",)])

    async def test_blocked_dm_is_not_retried(self):
        self.store.track(self.member)
        self.member.send.side_effect = discord.Forbidden(
            SimpleNamespace(status=403, reason="Forbidden"), "Blocked")
        await send_welcome(self.member, self.store, self.logger)
        await send_welcome(self.member, self.store, self.logger)
        self.member.send.assert_awaited_once()

    async def test_rejoin_can_receive_new_welcome(self):
        self.store.track(self.member)
        await send_welcome(self.member, self.store, self.logger)
        self.member.joined_at += timedelta(days=1)
        self.store.track(self.member)
        await send_welcome(self.member, self.store, self.logger)
        self.assertEqual(self.member.send.await_count, 2)

    async def test_erasure_and_departure_cleanup(self):
        self.store.track(self.member)
        self.store.forget(1, self.member.id)
        self.assertFalse(self.store.claim(self.member))
        self.store.track(self.member)
        self.store.prune(1, {self.member.id})
        self.assertTrue(self.store.claim(self.member))
        self.store.prune(1, set())
        self.assertFalse(self.store.claim(self.member))

    async def test_pending_waits_and_role_is_added_before_dm(self):
        bot = Botio(1, 2, welcome_store=self.store)
        self.addAsyncCleanup(bot.close)
        role = SimpleNamespace(id=2)
        self.member.guild.fetch_member = AsyncMock(return_value=self.member)
        self.store.track(self.member)
        self.member.pending = True
        with patch.object(bot, "configured_role", return_value=role):
            await bot.grant_member(self.member)
            self.member.send.assert_not_awaited()
            self.member.add_roles.assert_not_awaited()
            self.member.pending = False
            async def check_role_first(**kwargs):
                self.member.add_roles.assert_awaited_once()
            self.member.send.side_effect = check_role_first
            await bot.grant_member(self.member)
            self.member.send.assert_awaited_once()

    async def test_failed_role_does_not_send_welcome(self):
        bot = Botio(1, 2, welcome_store=self.store)
        self.addAsyncCleanup(bot.close)
        self.member.guild.fetch_member = AsyncMock(return_value=self.member)
        self.member.add_roles.side_effect = discord.Forbidden(
            SimpleNamespace(status=403, reason="Forbidden"), "Missing permissions")
        self.store.track(self.member)
        with patch.object(bot, "configured_role", return_value=SimpleNamespace(id=2)):
            await bot.grant_member(self.member)
        self.member.send.assert_not_awaited()

    async def test_acceptance_event_grants_role_and_sends_only_one_dm(self):
        bot = Botio(1, 2, welcome_store=self.store)
        self.addAsyncCleanup(bot.close)
        self.member.guild.fetch_member = AsyncMock(return_value=self.member)
        with patch.object(bot, "configured_role", return_value=SimpleNamespace(id=2)):
            await bot.on_member_update(SimpleNamespace(pending=True), self.member)
            await bot.on_member_update(SimpleNamespace(pending=True), self.member)
        self.member.send.assert_awaited_once()

    async def test_sync_never_sends_dm_with_unknown_screening_state(self):
        bot = Botio(1, 2, welcome_store=self.store)
        self.addAsyncCleanup(bot.close)
        role = SimpleNamespace(id=2)
        self.member.roles = [role]
        self.member.pending = None
        self.store.track(self.member)

        async def members(**kwargs):
            yield self.member

        self.member.guild.fetch_members = members
        with patch.object(bot, "get_guild", return_value=self.member.guild), \
                patch.object(bot, "configured_role", return_value=role):
            await bot.reconcile()
        self.member.send.assert_not_awaited()

    async def test_sync_recovers_waiting_dm_after_acceptance_while_offline(self):
        self.store.track(self.member)
        bot = Botio(1, 2, welcome_store=WelcomeStore(self.path))
        self.addAsyncCleanup(bot.close)
        role = SimpleNamespace(id=2)
        self.member.roles = [role]

        async def members(**kwargs):
            yield self.member

        self.member.guild.fetch_members = members
        with patch.object(bot, "get_guild", return_value=self.member.guild), \
                patch.object(bot, "configured_role", return_value=role):
            await bot.reconcile()
            await bot.reconcile()
        self.member.send.assert_awaited_once()
