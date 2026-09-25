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


class TestGoogleOAuthRedirectAndSecurity(AioHTTPTestCase):
    """Tests for Google OAuth redirect chain, environment separation, state validation, and token security."""

    async def get_application(self):
        os.environ["ENVIRONMENT"] = "production"
        os.environ["MIKASA_ALLOW_REMOTE_API"] = "true"
        return create_app()

    @unittest_run_loop
    async def test_oauth_callback_html_scrubs_tokens_and_sets_no_store_headers(self):
        resp = await self.client.request("GET", "/api/auth/callback?state=test_state_123")
        self.assertEqual(resp.status, 200)
        self.assertIn("no-store", resp.headers.get("Cache-Control", ""))
        self.assertEqual(resp.headers.get("Referrer-Policy"), "no-referrer")
        text = await resp.text()
        self.assertIn("window.history.replaceState", text)
        self.assertIn("/api/auth/callback/session", text)
        self.assertNotIn("localhost:140", text)

    @unittest_run_loop
    async def test_oauth_session_save_and_one_time_retrieve(self):
        state = "oauth_state_valid_987654"
        save_resp = await self.client.request(
            "POST",
            "/api/auth/callback/session",
            json={
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20ifQ.sig123",
                "refresh_token": "refresh_tok_abc",
                "state": state,
            },
        )
        self.assertEqual(save_resp.status, 200)
        self.assertIn("no-store", save_resp.headers.get("Cache-Control", ""))
        save_data = await save_resp.json()
        self.assertTrue(save_data.get("ok"))
        self.assertEqual(save_data.get("state"), state)

        # Wrong state must NOT retrieve the session
        wrong_resp = await self.client.request("GET", "/api/auth/callback/session?state=wrong_state_000")
        self.assertEqual(wrong_resp.status, 404)

        # Omitted state must NOT leak a state-bound session
        no_state_resp = await self.client.request("GET", "/api/auth/callback/session")
        self.assertEqual(no_state_resp.status, 404)

        # Correct state retrieves the session once
        get_resp = await self.client.request("GET", f"/api/auth/callback/session?state={state}")
        self.assertEqual(get_resp.status, 200)
        get_data = await get_resp.json()
        self.assertTrue(get_data.get("ok"))
        self.assertEqual(get_data["session"]["refresh_token"], "refresh_tok_abc")

        # Second request with the same state must be rejected (one-time session)
        replay_resp = await self.client.request("GET", f"/api/auth/callback/session?state={state}")
        self.assertEqual(replay_resp.status, 404)

    @unittest_run_loop
    async def test_oauth_invalid_or_expired_state_rejected(self):
        from core.api_server import _pending_oauth_sessions, _pending_oauth_lock

        # 1. Invalid state characters rejected with 400 on POST
        bad_post = await self.client.request(
            "POST",
            "/api/auth/callback/session",
            json={"access_token": "tok_123", "state": "bad state <script>alert(1)</script>"},
        )
        self.assertEqual(bad_post.status, 400)

        # 2. Invalid state characters rejected with 400 on GET
        bad_get = await self.client.request(
            "GET",
            "/api/auth/callback/session?state=invalid%20state%20with%20spaces",
        )
        self.assertEqual(bad_get.status, 400)

        # 3. Empty token/code payload rejected with 400
        empty_post = await self.client.request(
            "POST",
            "/api/auth/callback/session",
            json={"state": "valid_state_empty"},
        )
        self.assertEqual(empty_post.status, 400)

        # 4. Expired state rejected with 404
        expired_state = "expired_state_111"
        with _pending_oauth_lock:
            _pending_oauth_sessions[expired_state] = (time.time() - 10.0, {"access_token": "tok_exp"})

        exp_get = await self.client.request("GET", f"/api/auth/callback/session?state={expired_state}")
        self.assertEqual(exp_get.status, 404)

    @unittest_run_loop
    async def test_oauth_tokens_never_leaked_in_errors_or_audit_logs(self):
        from core.api_server import _redact_oauth_secrets
        from core.v8.events import RemoteAuditLogger

        raw = "Failed at http://localhost:140/#access_token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abcde&refresh_token=sec_ref_99"
        redacted = _redact_oauth_secrets(raw)
        self.assertNotIn("eyJhbGciOiJIUzI1NiJ9", redacted)
        self.assertNotIn("sec_ref_99", redacted)
        self.assertIn("[REDACTED]", redacted)

        # Save an OAuth error containing a token and verify GET redacts it
        err_state = "err_state_test_555"
        await self.client.request(
            "POST",
            "/api/auth/callback/session",
            json={
                "state": err_state,
                "error": "access_denied: access_token=leaked_tok_999",
            },
        )
        err_get = await self.client.request("GET", f"/api/auth/callback/session?state={err_state}")
        self.assertEqual(err_get.status, 400)
        err_body = await err_get.text()
        self.assertNotIn("leaked_tok_999", err_body)

        # Verify audit log does not contain tokens
        audit_events = [e.to_dict() for e in RemoteAuditLogger.get_instance().get_history(limit=10)]
        serialized_audit = json.dumps(audit_events)
        self.assertNotIn("leaked_tok_999", serialized_audit)
        self.assertNotIn("refresh_tok_abc", serialized_audit)

    def test_frontend_environment_separation_blocks_localhost_140_and_preserves_tauri(self):
        backend_service_path = os.path.join(
            BASE_DIR, "mikasa-7", "src", "services", "backendService.ts"
        )
        with open(backend_service_path, "r", encoding="utf-8") as f:
            ts_code = f.read()

        # Verify required functions and protections exist in backendService.ts
        self.assertIn("FORBIDDEN_FRONTEND_PORTS = new Set([\"140\", \"1420\", \"1421\", \"5173\"])", ts_code)
        self.assertIn("export function isTauriRuntime", ts_code)
        self.assertIn("__TAURI_INTERNALS__", ts_code)
        self.assertIn("tauri.localhost", ts_code)
        self.assertIn("export function isProductionWebRuntime", ts_code)
        self.assertIn("export function resolveOAuthCallbackBase", ts_code)
        self.assertIn("export function resolveOAuthRedirectUrl", ts_code)
        self.assertIn("export function scrubUrlOAuthTokens", ts_code)
        self.assertIn("export function redactSensitiveTokens", ts_code)


if __name__ == "__main__":
    unittest.main()

