# ========== tests/test_v8_production_integration.py ==========
# Phase 46 & Production Integration Regression Tests
# Tests production CORS, remote IP handling, auth resolution, Telegram sync, and Supabase security

import os
import sys
import json
import time
import unittest
import asyncio
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from core.api_server import (
    create_app,
    cors_middleware,
    is_production_or_remote_enabled,
    resolve_auth_identity,
)
from core.v8.telegram_identity import (
    TelegramIdentityManager,
    UserTelegramLink,
    TelegramIdentity,
)


class TestCORSProductionIntegration(unittest.TestCase):
    """Test production vs development CORS and remote IP security middleware."""

    def setUp(self):
        self._orig_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_is_production_or_remote_enabled_default_dev(self):
        os.environ["ENVIRONMENT"] = "development"
        os.environ.pop("RAILWAY_ENVIRONMENT", None)
        os.environ.pop("MIKASA_ALLOW_REMOTE_API", None)
        self.assertFalse(is_production_or_remote_enabled())

    def test_is_production_or_remote_enabled_railway(self):
        os.environ["RAILWAY_ENVIRONMENT"] = "production"
        self.assertTrue(is_production_or_remote_enabled())

    def test_is_production_or_remote_enabled_explicit_flag(self):
        os.environ["MIKASA_ALLOW_REMOTE_API"] = "true"
        self.assertTrue(is_production_or_remote_enabled())

    def test_is_production_or_remote_enabled_env_production(self):
        os.environ["ENVIRONMENT"] = "production"
        self.assertTrue(is_production_or_remote_enabled())


class TestProductionAPIServerIntegration(AioHTTPTestCase):
    """Integration test suite for aiohttp API Server with production middleware."""

    async def get_application(self):
        os.environ["ENVIRONMENT"] = "production"
        os.environ["RAILWAY_ENVIRONMENT"] = "production"
        os.environ["MIKASA_ALLOW_REMOTE_API"] = "true"
        return create_app()

    @unittest_run_loop
    async def test_health_endpoint_200(self):
        resp = await self.client.request("GET", "/health")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data.get("status"), "ok")

    @unittest_run_loop
    async def test_options_preflight_returns_204_with_cors_headers(self):
        headers = {
            "Origin": "https://mikasa-v8-api-production.up.railway.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        }
        resp = await self.client.request("OPTIONS", "/api/telegram/status", headers=headers)
        self.assertEqual(resp.status, 204)
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "https://mikasa-v8-api-production.up.railway.app")
        self.assertIn("GET", resp.headers.get("Access-Control-Allow-Methods", ""))
        self.assertIn("Authorization", resp.headers.get("Access-Control-Allow-Headers", ""))

    @unittest_run_loop
    async def test_telegram_status_allowed_in_production(self):
        headers = {
            "Origin": "https://mikasa-v8-api-production.up.railway.app",
        }
        resp = await self.client.request("GET", "/api/telegram/status", headers=headers)
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "https://mikasa-v8-api-production.up.railway.app")


class TestResolveAuthIdentityProduction(unittest.TestCase):
    """Test identity resolution, token validation, and cross-tenant protection."""

    def setUp(self):
        self._orig_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_legacy_admin_param_mapped_to_authenticated_user(self):
        fake_user = MagicMock()
        fake_user.id = "44444444-4444-4444-4444-444444444444"
        fake_session = MagicMock()

        req = MagicMock()
        req.headers = {
            "Authorization": "Bearer fake-token-123",
            "X-Mikasa-User-Id": "admin"
        }
        req.query = {"mikasa_user_id": "admin"}

        with patch("core.v8.AccountAuthManager.get_default_instance") as mock_auth_cls:
            mock_mgr = MagicMock()
            mock_mgr.authenticate_token.return_value = (fake_session, fake_user)
            mock_auth_cls.return_value = mock_mgr

            user_id, user, session, err = resolve_auth_identity(req, required=True)
            self.assertIsNone(err)
            self.assertEqual(user_id, "44444444-4444-4444-4444-444444444444")

    def test_cross_tenant_foreign_uuid_rejected(self):
        fake_user = MagicMock()
        fake_user.id = "44444444-4444-4444-4444-444444444444"
        fake_session = MagicMock()

        req = MagicMock()
        req.headers = {
            "Authorization": "Bearer fake-token-123",
            "X-Mikasa-User-Id": "99999999-9999-9999-9999-999999999999"
        }
        req.query = {}

        with patch("core.v8.AccountAuthManager.get_default_instance") as mock_auth_cls:
            mock_mgr = MagicMock()
            mock_mgr.authenticate_token.return_value = (fake_session, fake_user)
            mock_auth_cls.return_value = mock_mgr

            user_id, user, session, err = resolve_auth_identity(req, required=True)
            self.assertIsNotNone(err)
            self.assertEqual(err.status, 403)

    def test_missing_token_when_auth_enforced_returns_401(self):
        os.environ["MIKASA_REQUIRE_AUTH"] = "true"
        req = MagicMock()
        req.headers = {}
        req.query = {}

        with patch("core.v8.AccountAuthManager.get_default_instance") as mock_auth_cls:
            mock_mgr = MagicMock()
            mock_mgr.is_configured.return_value = True
            mock_auth_cls.return_value = mock_mgr

            user_id, user, session, err = resolve_auth_identity(req, required=True)
            self.assertIsNotNone(err)
            self.assertEqual(err.status, 401)


class TestTelegramIdentitySupabaseSync(unittest.TestCase):
    """Test Supabase persistence synchronization for TelegramIdentityManager."""

    def setUp(self):
        self._orig_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        TelegramIdentityManager._default_instance = None

    def test_supabase_config_parsing(self):
        os.environ["SUPABASE_URL"] = "https://vdcssmzguxfknqkfxbed.supabase.co/"
        os.environ["SUPABASE_PUBLISHABLE_KEY"] = "sb_publishable_test"
        os.environ["SUPABASE_SECRET_KEY"] = "sb_secret_test"

        mgr = TelegramIdentityManager.get_default_instance()
        url, anon, secret = mgr._get_supabase_config()
        self.assertEqual(url, "https://vdcssmzguxfknqkfxbed.supabase.co")
        self.assertEqual(anon, "sb_publishable_test")
        self.assertEqual(secret, "sb_secret_test")

    def test_sync_link_to_supabase_with_uuid(self):
        os.environ["SUPABASE_URL"] = "https://example.supabase.co"
        os.environ["SUPABASE_SECRET_KEY"] = "test-secret"

        mgr = TelegramIdentityManager.get_default_instance()
        test_uuid = "12345678-1234-5678-1234-567812345678"
        link = UserTelegramLink(
            mikasa_user_id=test_uuid,
            telegram_user_id=123456789,
            metadata={"username": "testuser", "first_name": "Test"}
        )

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 201
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            mgr.sync_link_to_supabase(link)
            self.assertTrue(mock_urlopen.called)

    def test_delete_link_from_supabase(self):
        os.environ["SUPABASE_URL"] = "https://example.supabase.co"
        os.environ["SUPABASE_SECRET_KEY"] = "test-secret"

        mgr = TelegramIdentityManager.get_default_instance()

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 204
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            mgr.delete_link_from_supabase(123456789)
            self.assertTrue(mock_urlopen.called)


if __name__ == "__main__":
    unittest.main()
