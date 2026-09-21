# ========== tests/test_v8_telegram_production.py ==========
# Phase 46 — Telegram Production Webhook, Security, Railway readiness tests

import os
import asyncio
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from core.v8.telegram_gateway import MockTelegramTransport
from core.v8.telegram_identity import TelegramIdentityManager
from core.v8.account_device import AccountDeviceManager
from core.v8.auth_session import SessionManager
from core.v8.universal_bot import UniversalTelegramBot
from core.v8.telegram_webhook import (
    UpdateIdempotencyStore,
    TelegramWebhookService,
    register_telegram_routes,
    build_telegram_webhook_service,
)
from core.api_server import create_app, handle_health


class TestTelegramBotCommandsProduction(unittest.TestCase):
    """Core bot commands including /session and /logout."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_tg_prod_")
        self.tg_storage = os.path.join(self.temp_dir, "tg.json")
        self.adm_storage = os.path.join(self.temp_dir, "adm.json")
        self.identity_mgr = TelegramIdentityManager(storage_path=self.tg_storage)
        self.adm = AccountDeviceManager(storage_path=self.adm_storage)
        self.transport = MockTelegramTransport()
        self.bot = UniversalTelegramBot(
            identity_manager=self.identity_mgr,
            account_device_manager=self.adm,
            transport=self.transport,
        )
        req, otp, _, _ = self.identity_mgr.create_link_request("user_a")
        self.identity_mgr.verify_otp(otp, telegram_user_id=111222, username="user_a")
        self.adm.register_device("user_a", "pc-1", "Uy PC", status="online")
        self.adm.select_device("user_a", "pc-1")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        SessionManager._default_instance = None

    def _msg(self, tg_id, text):
        return {
            "message": {
                "message_id": 1,
                "chat": {"id": tg_id},
                "from": {"id": tg_id, "username": "u"},
                "text": text,
            }
        }

    def test_start_help_link_account_devices_select(self):
        for cmd in ("/start", "/help", "/account", "/devices"):
            asyncio.run(self.bot.process_update(self._msg(111222, cmd)))
        texts = " ".join(m["text"] for m in self.transport.sent_messages)
        self.assertIn("/link", texts)
        self.assertIn("Uy PC", texts)

    def test_status_shows_device_state(self):
        asyncio.run(self.bot.process_update(self._msg(111222, "/status")))
        text = self.transport.sent_messages[-1]["text"]
        self.assertIn("ONLINE", text)
        self.assertIn("Uy PC", text)

    def test_session_and_logout_flow(self):
        sm = SessionManager.get_default_instance()
        sm.create_session("user_a", "pc-1", ttl=900.0)

        asyncio.run(self.bot.process_update(self._msg(111222, "/session")))
        self.assertIn("Faol", self.transport.sent_messages[-1]["text"])
        self.assertNotIn("session_id", self.transport.sent_messages[-1]["text"].lower())

        asyncio.run(self.bot.process_update(self._msg(111222, "/logout")))
        self.assertIn("yopildi", self.transport.sent_messages[-1]["text"].lower())

        asyncio.run(self.bot.process_update(self._msg(111222, "/session")))
        self.assertIn("Faol emas", self.transport.sent_messages[-1]["text"])


class TestTelegramWebhookSecurity(unittest.TestCase):
    def setUp(self):
        self.transport = MockTelegramTransport()
        self.bot = UniversalTelegramBot(transport=self.transport)
        self.svc = TelegramWebhookService(
            bot=self.bot,
            transport=self.transport,
            webhook_secret="test-webhook-secret-xyz",
            bot_token="123456789:AAFakeTokenForTestsOnly",
        )

    def test_idempotency_duplicate_update(self):
        store = UpdateIdempotencyStore()
        self.assertTrue(store.claim(100))
        self.assertFalse(store.claim(100))
        self.assertTrue(store.claim(101))

    def test_invalid_secret_rejected(self):
        async def _run():
            req = MagicMock()
            req.match_info = {"secret": "wrong-secret"}
            req.headers = {}
            req.path = "/telegram/webhook/wrong-secret"
            resp = await self.svc.handle_webhook(req)
            self.assertEqual(resp.status, 403)

        asyncio.run(_run())


class TestTelegramWebhookIntegration(AioHTTPTestCase):
    def setUp(self):
        super().setUp()
        self._env_patch = patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "123456789:AAFakeTokenForTestsOnly",
                "TELEGRAM_WEBHOOK_SECRET": "integration-secret-abc",
                "TELEGRAM_USE_WEBHOOK": "true",
                "TELEGRAM_BOT_USERNAME": "TestBot",
            },
            clear=False,
        )
        self._env_patch.start()
        self.transport = MockTelegramTransport()
        self.bot = UniversalTelegramBot(transport=self.transport)
        self.svc = TelegramWebhookService(
            bot=self.bot,
            transport=self.transport,
            webhook_secret="integration-secret-abc",
            bot_token="123456789:AAFakeTokenForTestsOnly",
        )

    def tearDown(self):
        self._env_patch.stop()
        super().tearDown()

    async def get_application(self):
        app = web.Application()
        register_telegram_routes(app, self.svc)
        return app

    async def test_valid_webhook_secret_accepts_update(self):
        update = {
            "update_id": 42,
            "message": {
                "message_id": 1,
                "chat": {"id": 999},
                "from": {"id": 999},
                "text": "/help",
            },
        }
        path = self.svc.webhook_path()
        resp = await self.client.post(
            path,
            json=update,
            headers={"X-Telegram-Bot-Api-Secret-Token": "integration-secret-abc"},
        )
        self.assertEqual(resp.status, 200)
        await asyncio.sleep(0.05)
        self.assertTrue(len(self.transport.sent_messages) >= 1)

    async def test_duplicate_update_idempotent(self):
        update = {
            "update_id": 77,
            "message": {
                "message_id": 2,
                "chat": {"id": 888},
                "from": {"id": 888},
                "text": "/start",
            },
        }
        path = self.svc.webhook_path()
        headers = {"X-Telegram-Bot-Api-Secret-Token": "integration-secret-abc"}
        r1 = await self.client.post(path, json=update, headers=headers)
        r2 = await self.client.post(path, json=update, headers=headers)
        self.assertEqual(r1.status, 200)
        self.assertEqual(r2.status, 200)
        await asyncio.sleep(0.05)
        self.assertEqual(len(self.transport.sent_messages), 1)

    async def test_invalid_webhook_secret_forbidden(self):
        resp = await self.client.post(
            "/telegram/webhook/wrong",
            json={"update_id": 1, "message": {"text": "/start"}},
        )
        self.assertEqual(resp.status, 403)

    async def test_malformed_payload_rejected(self):
        path = self.svc.webhook_path()
        resp = await self.client.post(path, data=b"not-json")
        self.assertIn(resp.status, (400, 415))

    async def test_oversized_payload_rejected_413(self):
        path = self.svc.webhook_path()
        huge_payload = b"x" * (256 * 1024 + 10)
        resp = await self.client.post(path, data=huge_payload, headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status, 413)

    async def test_ready_endpoint(self):
        resp = await self.client.get("/ready")
        self.assertIn(resp.status, (200, 503))
        data = await resp.json()
        self.assertIn("checks", data)
        self.assertIn("telegram_bot", data["checks"])

    async def test_shutdown_rejects_new_updates(self):
        await self.svc.begin_shutdown()
        path = self.svc.webhook_path()
        resp = await self.client.post(
            path,
            json={"update_id": 999},
            headers={"X-Telegram-Bot-Api-Secret-Token": "integration-secret-abc"},
        )
        self.assertEqual(resp.status, 503)


class TestMultiTenantIsolationTelegram(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_tg_isolation_")
        self.tg_storage = os.path.join(self.temp_dir, "tg.json")
        self.adm_storage = os.path.join(self.temp_dir, "adm.json")
        self.identity_mgr = TelegramIdentityManager(storage_path=self.tg_storage)
        self.adm = AccountDeviceManager(storage_path=self.adm_storage)
        self.transport = MockTelegramTransport()
        self.bot = UniversalTelegramBot(
            identity_manager=self.identity_mgr,
            account_device_manager=self.adm,
            transport=self.transport,
        )
        req_a, otp_a, _, _ = self.identity_mgr.create_link_request("user_a")
        req_b, otp_b, _, _ = self.identity_mgr.create_link_request("user_b")
        self.identity_mgr.verify_otp(otp_a, telegram_user_id=1001)
        self.identity_mgr.verify_otp(otp_b, telegram_user_id=2002)
        self.adm.register_device("user_a", "dev-a", "A PC", status="online")
        self.adm.register_device("user_b", "dev-b", "B PC", status="online")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cross_user_device_access_denied(self):
        async def _run():
            await self.bot.process_update({
                "message": {
                    "chat": {"id": 1001},
                    "from": {"id": 1001},
                    "text": "/select dev-b",
                }
            })
            text = self.transport.sent_messages[-1]["text"]
            self.assertNotIn("B PC", text)
            self.assertTrue("Xatolik" in text or "topilmadi" in text.lower())

        asyncio.run(_run())


class TestRailwayHealthEndpoints(unittest.TestCase):
    def test_health_liveness_no_secrets(self):
        async def _run():
            req = MagicMock()
            resp = await handle_health(req)
            body = resp.body
            import json
            data = json.loads(body.decode())
            self.assertEqual(data.get("status"), "ok")
            for forbidden in (
                "TELEGRAM_BOT_TOKEN",
                "SUPABASE_SECRET",
                "service_role",
                "access_token",
            ):
                self.assertNotIn(forbidden, body.decode())

        asyncio.run(_run())

    @patch.dict(
        os.environ,
        {
            "TELEGRAM_BOT_TOKEN": "123:ABC",
            "TELEGRAM_WEBHOOK_SECRET": "sec",
            "TELEGRAM_USE_WEBHOOK": "true",
        },
    )
    def test_build_webhook_service_configured(self):
        svc = build_telegram_webhook_service()
        self.assertIsNotNone(svc)
        self.assertIn("/telegram/webhook/", svc.webhook_path())


if __name__ == "__main__":
    unittest.main()
