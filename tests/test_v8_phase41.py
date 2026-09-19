# ========== tests/test_v8_phase41.py ==========
# Phase 41 — Supabase Auth Migration Test Suite
# Comprehensive 30 Unit & Integration Tests covering:
# - Supabase JWT verification & claims decoding
# - Profile synchronization & zero backend password storage
# - Input validation & rate limiting
# - PostgreSQL RLS migration & multi-tenant isolation
# - Bearer token HTTP endpoints & session decoupling

import os
import shutil
import tempfile
import unittest
import asyncio
import json
import time

from core.v8.account_device import (
    MikasaUser,
    MikasaProfile,
    AccountDeviceManager,
)
from core.v8.account_auth import (
    SupabaseAuthManager,
    AccountAuthManager,
    SupabaseSessionClaims,
    AuthRateLimiter,
    validate_username,
    validate_email,
)
from core.v8.telegram_identity import TelegramIdentityManager
from core.v8.auth_session import RemoteAuthSession
from core.api_server import (
    handle_auth_register,
    handle_auth_login,
    handle_auth_me,
    handle_auth_verify_email,
    handle_auth_forgot_password,
    handle_auth_reset_password,
    handle_auth_change_password,
    handle_devices_list,
    _get_request_user_id,
)


class MockRequest:
    """Mock aiohttp request for endpoint testing."""
    def __init__(self, method="GET", query=None, headers=None, body=None, match_info=None, remote="127.0.0.1"):
        self.method = method
        self.query = query or {}
        self.headers = headers or {}
        self._body = body or {}
        self.match_info = match_info or {}
        self.remote = remote

    async def json(self):
        return self._body


class TestSupabaseJWTVerification(unittest.TestCase):
    """Scenarios 1-6: Supabase JWT Verification & Claims Decoding"""

    def setUp(self):
        self.secret = "test-super-secret-jwt-signing-key-32ch!"
        self.auth_mgr = SupabaseAuthManager(supabase_jwt_secret=self.secret)

    def test_01_supabase_jwt_valid_signature_and_claims(self):
        """Scenario 1: Valid HS256 JWT signature verification and claims extraction."""
        token = self.auth_mgr.create_mock_jwt(
            user_id="user-uuid-001",
            email="developer@mikasa.ai",
            username="mikasadev",
            display_name="Mikasa Developer",
            role="authenticated",
            exp_seconds=1800,
            secret=self.secret
        )
        ok, msg, claims = self.auth_mgr.verify_supabase_jwt(token)
        self.assertTrue(ok)
        self.assertEqual(msg, "OK")
        self.assertIsNotNone(claims)
        self.assertEqual(claims.user_id, "user-uuid-001")
        self.assertEqual(claims.email, "developer@mikasa.ai")
        self.assertEqual(claims.username, "mikasadev")
        self.assertEqual(claims.display_name, "Mikasa Developer")
        self.assertEqual(claims.role, "authenticated")
        self.assertTrue(claims.is_valid)

    def test_02_supabase_jwt_expired_token_rejected(self):
        """Scenario 2: Token with expired timestamp is rejected."""
        token = self.auth_mgr.create_mock_jwt(
            user_id="user-uuid-expired",
            email="expired@mikasa.ai",
            exp_seconds=-60,
            secret=self.secret
        )
        ok, msg, claims = self.auth_mgr.verify_supabase_jwt(token)
        self.assertFalse(ok)
        self.assertIn("expired", msg.lower())
        self.assertIsNone(claims)

    def test_03_supabase_jwt_invalid_signature_rejected(self):
        """Scenario 3: Token signed with a different key is rejected for invalid signature."""
        token = self.auth_mgr.create_mock_jwt(
            user_id="user-uuid-tampered",
            email="tampered@mikasa.ai",
            secret="different-unauthorized-secret-key!"
        )
        ok, msg, claims = self.auth_mgr.verify_supabase_jwt(token)
        self.assertFalse(ok)
        self.assertIn("imzo", msg.lower())
        self.assertIsNone(claims)

    def test_04_supabase_jwt_malformed_tokens_rejected(self):
        """Scenario 4: Malformed, empty, or unparseable tokens are safely rejected without crash."""
        cases = [
            "",
            None,
            "just-a-plain-string",
            "part1.part2",
            "part1.part2.part3.part4",
            "notbase64.notbase64.notbase64",
        ]
        for bad_tok in cases:
            ok, msg, claims = self.auth_mgr.verify_supabase_jwt(bad_tok)
            self.assertFalse(ok)
            self.assertIsNone(claims)

    def test_05_supabase_jwt_claims_dataclass(self):
        """Scenario 5: SupabaseSessionClaims properties, valid checks, and dict export."""
        now = time.time()
        claims = SupabaseSessionClaims(
            user_id="sub-uuid-123",
            email="alice@example.com",
            role="authenticated",
            exp=now + 3600,
            iat=now,
            username="alice",
            display_name="Alice Smith"
        )
        self.assertEqual(claims.id, "sub-uuid-123")
        self.assertTrue(claims.is_valid)

        d = claims.to_dict()
        self.assertEqual(d["user_id"], "sub-uuid-123")
        self.assertEqual(d["email"], "alice@example.com")
        self.assertEqual(d["username"], "alice")
        self.assertTrue(d["is_valid"])

        expired_claims = SupabaseSessionClaims(user_id="sub-123", exp=now - 10)
        self.assertFalse(expired_claims.is_valid)

    def test_06_supabase_jwt_unverified_dev_fallback(self):
        """Scenario 6: Fail-closed security - when secret is unconfigured and JWKS unavailable, unverified token is rejected."""
        dev_mgr = SupabaseAuthManager(supabase_jwt_secret="")
        token = self.auth_mgr.create_mock_jwt(
            user_id="dev-user-01",
            email="dev@example.com",
            username="devuser",
            secret=self.secret
        )
        ok, msg, claims = dev_mgr.verify_supabase_jwt(token)
        self.assertFalse(ok)
        self.assertIsNone(claims)
        self.assertIn("UNCONFIGURED_KEY", msg)


class TestProfileAndZeroPasswordStorage(unittest.TestCase):
    """Scenarios 7-12: Public Profile Sync & Zero Backend Password Storage"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_test_profile_")
        self.storage_file = os.path.join(self.test_dir, "accounts.json")
        self.device_mgr = AccountDeviceManager(storage_path=self.storage_file)
        self.auth_mgr = SupabaseAuthManager(
            account_device_mgr=self.device_mgr,
            supabase_jwt_secret="test-secret"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_07_zero_password_storage_in_mikasa_user(self):
        """Scenario 7: Assert MikasaUser and MikasaProfile have ZERO password storage attributes."""
        user = MikasaUser(id="uuid-test-01", username="testuser", email="test@example.com")
        self.assertFalse(hasattr(user, "password_hash"))
        self.assertFalse(hasattr(user, "password_salt"))
        self.assertFalse(hasattr(user, "password"))

        data = user.to_dict()
        self.assertNotIn("password_hash", data)
        self.assertNotIn("password_salt", data)
        self.assertNotIn("password", data)
        self.assertIs(MikasaProfile, MikasaUser)

    def test_08_upsert_profile_from_supabase_new_user(self):
        """Scenario 8: upsert_profile_from_supabase creates new MikasaUser with Supabase UUID."""
        profile = self.device_mgr.upsert_profile_from_supabase(
            user_id="auth-users-uuid-101",
            email="newuser@example.com",
            username="newuser",
            display_name="New User",
            avatar_url="https://example.com/avatar.png",
            is_verified=True
        )
        self.assertEqual(profile.id, "auth-users-uuid-101")
        self.assertEqual(profile.email, "newuser@example.com")
        self.assertEqual(profile.username, "newuser")
        self.assertEqual(profile.display_name, "New User")
        self.assertTrue(profile.is_verified)

        fetched = self.device_mgr.get_user("auth-users-uuid-101")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, "auth-users-uuid-101")

    def test_09_upsert_profile_from_supabase_existing_user(self):
        """Scenario 9: upsert_profile_from_supabase updates existing profile in-place without duplicate."""
        self.device_mgr.upsert_profile_from_supabase(
            user_id="auth-users-uuid-102",
            email="user102@example.com",
            username="user102",
            display_name="Original Name"
        )
        updated = self.device_mgr.upsert_profile_from_supabase(
            user_id="auth-users-uuid-102",
            email="user102_updated@example.com",
            display_name="Updated Name",
            avatar_url="https://example.com/new_avatar.png"
        )
        self.assertEqual(updated.id, "auth-users-uuid-102")
        self.assertEqual(updated.email, "user102_updated@example.com")
        self.assertEqual(updated.display_name, "Updated Name")
        self.assertEqual(updated.avatar_url, "https://example.com/new_avatar.png")

        all_users = self.device_mgr.list_users()
        matching = [u for u in all_users if u.id == "auth-users-uuid-102"]
        self.assertEqual(len(matching), 1)

    def test_10_authenticate_token_flow(self):
        """Scenario 10: authenticate_token verifies JWT and automatically synchronizes profile."""
        token = self.auth_mgr.create_mock_jwt(
            user_id="supabase-auth-uuid-201",
            email="tokenuser@example.com",
            username="tokenuser",
            display_name="Token User"
        )
        claims, profile = self.auth_mgr.authenticate_token(token)
        self.assertIsNotNone(claims)
        self.assertIsNotNone(profile)
        self.assertEqual(claims.user_id, "supabase-auth-uuid-201")
        self.assertEqual(profile.id, "supabase-auth-uuid-201")
        self.assertEqual(profile.email, "tokenuser@example.com")
        self.assertEqual(profile.username, "tokenuser")

    def test_11_profile_username_fallback_generation(self):
        """Scenario 11: Falls back to email prefix or user_id when username metadata is missing."""
        token = self.auth_mgr.create_mock_jwt(
            user_id="uuid-no-username",
            email="johndoe@example.com",
            username="",
            display_name=""
        )
        claims, profile = self.auth_mgr.authenticate_token(token)
        self.assertEqual(profile.username, "johndoe")

        # Without email
        token_no_email = self.auth_mgr.create_mock_jwt(
            user_id="uuid-plain-only",
            email="",
            username=""
        )
        claims2, profile2 = self.auth_mgr.authenticate_token(token_no_email)
        self.assertEqual(profile2.username, "uuid-plain-only")

    def test_12_mikasa_user_json_serialization(self):
        """Scenario 12: MikasaUser serialization roundtrip maintains structure without password leaks."""
        user = MikasaUser(
            id="uuid-ser-1",
            username="serial_user",
            email="ser@example.com",
            display_name="Serial User",
            status="ACTIVE",
            is_verified=True
        )
        d = user.to_dict()
        self.assertNotIn("password", d)
        self.assertNotIn("password_hash", d)

        roundtrip = MikasaUser.from_dict(d)
        self.assertEqual(roundtrip.id, user.id)
        self.assertEqual(roundtrip.username, user.username)
        self.assertEqual(roundtrip.email, user.email)
        self.assertEqual(roundtrip.status, user.status)


class TestInputValidationAndRateLimiter(unittest.TestCase):
    """Scenarios 13-18: Input Validation & Rate Limiter Security"""

    def test_13_validate_username_valid(self):
        """Scenario 13: Valid usernames conform to length and character set."""
        valid_cases = ["john_doe", "alice-99", "admin_user", "MikasaAI", "dev-v8"]
        for u in valid_cases:
            valid, clean = validate_username(u)
            self.assertTrue(valid, f"Should be valid: {u}")
            self.assertEqual(clean, u)

    def test_14_validate_username_invalid_chars(self):
        """Scenario 14: Invalid characters in username are rejected."""
        invalid_cases = ["user name", "user@email", "bad!char", "slash/name", "hash#tag", "dollar$name"]
        for u in invalid_cases:
            valid, msg = validate_username(u)
            self.assertFalse(valid, f"Should be invalid: {u}")
            self.assertIn("Username 3-32 belgidan", msg)

    def test_15_validate_username_length_boundaries(self):
        """Scenario 15: Usernames shorter than 3 or longer than 32 characters are rejected."""
        self.assertFalse(validate_username("ab")[0])
        self.assertTrue(validate_username("abc")[0])
        self.assertTrue(validate_username("a" * 32)[0])
        self.assertFalse(validate_username("a" * 33)[0])
        self.assertFalse(validate_username("")[0])
        self.assertFalse(validate_username(None)[0])

    def test_16_validate_email_formats(self):
        """Scenario 16: Canonical email formatting, case normalization, and invalid pattern rejection."""
        valid, clean = validate_email("  Test.User@Example.COM  ")
        self.assertTrue(valid)
        self.assertEqual(clean, "test.user@example.com")

        valid_empty, clean_empty = validate_email("", allow_empty=True)
        self.assertTrue(valid_empty)
        self.assertEqual(clean_empty, "")

        invalid_empty, _ = validate_email("", allow_empty=False)
        self.assertFalse(invalid_empty)

        invalid_emails = ["notanemail", "@missinguser.com", "user@.com", "user name@example.com"]
        for em in invalid_emails:
            valid, _ = validate_email(em)
            self.assertFalse(valid, f"Should be invalid: {em}")

    def test_17_auth_rate_limiter_allows_under_limit(self):
        """Scenario 17: Rate limiter permits requests under the max attempt threshold."""
        limiter = AuthRateLimiter()
        ip = "192.168.1.100"
        for _ in range(4):
            limiter.record_failure(ip)
            limited, wait = limiter.is_rate_limited(ip)
            self.assertFalse(limited)
            self.assertEqual(wait, 0.0)

    def test_18_auth_rate_limiter_blocks_and_resets(self):
        """Scenario 18: Exceeding max attempts triggers rate limit cooldown, and success resets it."""
        limiter = AuthRateLimiter()
        ip = "192.168.1.101"
        for _ in range(5):
            limiter.record_failure(ip)

        limited, wait = limiter.is_rate_limited(ip)
        self.assertTrue(limited)
        self.assertGreater(wait, 0.0)

        # Successful attempt resets counter
        limiter.record_success(ip)
        limited_after, wait_after = limiter.is_rate_limited(ip)
        self.assertFalse(limited_after)
        self.assertEqual(wait_after, 0.0)


class TestRLSMigrationAndTenantIsolation(unittest.TestCase):
    """Scenarios 19-24: PostgreSQL RLS Migration & Multi-Tenant Isolation"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_test_rls_")
        self.device_file = os.path.join(self.test_dir, "devices.json")
        self.account_mgr = AccountDeviceManager(storage_path=self.device_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_19_sql_migration_file_exists(self):
        """Scenario 19: PostgreSQL migration file exists and defines all 4 required schema tables."""
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "supabase", "migrations", "20260918_phase41_supabase_auth.sql"
        )
        self.assertTrue(os.path.exists(migration_path), f"Migration not found at {migration_path}")
        with open(migration_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("CREATE TABLE IF NOT EXISTS public.profiles", content)
        self.assertIn("CREATE TABLE IF NOT EXISTS public.devices", content)
        self.assertIn("CREATE TABLE IF NOT EXISTS public.telegram_links", content)
        self.assertIn("CREATE TABLE IF NOT EXISTS public.permissions", content)

    def test_20_sql_migration_rls_enabled(self):
        """Scenario 20: Row Level Security is explicitly enabled on all 4 tables."""
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "supabase", "migrations", "20260918_phase41_supabase_auth.sql"
        )
        with open(migration_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY", content)
        self.assertIn("ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY", content)
        self.assertIn("ALTER TABLE public.telegram_links ENABLE ROW LEVEL SECURITY", content)
        self.assertIn("ALTER TABLE public.permissions ENABLE ROW LEVEL SECURITY", content)

    def test_21_sql_migration_auth_uid_policies(self):
        """Scenario 21: Policies use auth.uid() check to enforce strict tenant data boundaries."""
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "supabase", "migrations", "20260918_phase41_supabase_auth.sql"
        )
        with open(migration_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("id = auth.uid()", content)
        self.assertIn("user_id = auth.uid()", content)
        self.assertIn("CREATE POLICY", content)

    def test_22_sql_migration_new_user_trigger(self):
        """Scenario 22: Automatic profile creation trigger on auth.users insert."""
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "supabase", "migrations", "20260918_phase41_supabase_auth.sql"
        )
        with open(migration_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("CREATE OR REPLACE FUNCTION public.handle_new_user()", content)
        self.assertIn("CREATE TRIGGER on_auth_user_created", content)
        self.assertIn("AFTER INSERT", content)
        self.assertIn("ON auth.users", content)

    def test_23_multi_tenant_device_isolation(self):
        """Scenario 23: Devices of User A cannot be accessed, listed, or renamed by User B."""
        user_a = self.account_mgr.upsert_profile_from_supabase(user_id="user-uuid-A", username="alice")
        user_b = self.account_mgr.upsert_profile_from_supabase(user_id="user-uuid-B", username="bob")

        dev_a = self.account_mgr.register_device(user_id=user_a.id, device_id="laptop-a", name="Alice Laptop")
        dev_b = self.account_mgr.register_device(user_id=user_b.id, device_id="pc-b", name="Bob Desktop")

        # User A list
        devices_a = self.account_mgr.get_devices_for_user(user_a.id)
        self.assertEqual(len(devices_a), 1)
        self.assertEqual(devices_a[0].device_id, "laptop-a")

        # User B list
        devices_b = self.account_mgr.get_devices_for_user(user_b.id)
        self.assertEqual(len(devices_b), 1)
        self.assertEqual(devices_b[0].device_id, "pc-b")

        # User A attempts to rename User B's device -> fails
        self.assertEqual(dev_a.name, "Alice Laptop")
        ok, msg, _ = self.account_mgr.rename_device("pc-b", user_id=user_a.id, new_name="Hacked Device")
        self.assertFalse(ok)
        self.assertEqual(dev_b.name, "Bob Desktop")

    def test_24_multi_tenant_telegram_link_isolation(self):
        """Scenario 24: Telegram identities linked to User A cannot be unlinked or accessed by User B."""
        tg_mgr = TelegramIdentityManager(storage_path=os.path.join(self.test_dir, "tg.json"))
        user_a = self.account_mgr.upsert_profile_from_supabase(user_id="user-uuid-A2", username="alice2")
        user_b = self.account_mgr.upsert_profile_from_supabase(user_id="user-uuid-B2", username="bob2")

        # Link telegram for User A
        req, otp, deep_link, err = tg_mgr.create_link_request(mikasa_user_id=user_a.id)
        tg_mgr.verify_otp(otp=otp, telegram_user_id=987654321, username="alice_tg")

        # Verify link belongs to User A
        link_a = tg_mgr.get_link_by_mikasa_user(user_a.id)
        self.assertIsNotNone(link_a)
        self.assertEqual(link_a.telegram_user_id, 987654321)

        # User B has no link
        link_b = tg_mgr.get_link_by_mikasa_user(user_b.id)
        self.assertIsNone(link_b)

        # User B cannot unlink User A's telegram link
        self.assertEqual(tg_mgr.count_active_links(), 1)
        ok = tg_mgr.unlink(telegram_user_id=111222333)
        self.assertFalse(ok)
        self.assertIsNotNone(tg_mgr.get_link_by_mikasa_user(user_a.id))


class TestAPISupabaseAuthAndSessionDecoupling(unittest.TestCase):
    """Scenarios 25-30: Bearer Token API Endpoints & Session Separation"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_test_api_")
        self.storage_file = os.path.join(self.test_dir, "accounts.json")
        self.account_mgr = AccountDeviceManager(storage_path=self.storage_file)
        self.auth_mgr = SupabaseAuthManager(
            account_device_mgr=self.account_mgr,
            supabase_jwt_secret="api-test-jwt-secret-key-32chars!!"
        )
        AccountDeviceManager._instance = self.account_mgr
        AccountDeviceManager._default_instance = self.account_mgr
        AccountAuthManager._instance = self.auth_mgr
        AccountAuthManager._default_instance = self.auth_mgr

    def tearDown(self):
        AccountDeviceManager._instance = None
        AccountDeviceManager._default_instance = None
        AccountAuthManager._instance = None
        AccountAuthManager._default_instance = None
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_25_api_me_authenticated_with_bearer_token(self):
        """Scenario 25: GET /api/auth/me returns 200 and user profile when Bearer JWT is valid."""
        async def _run():
            token = self.auth_mgr.create_mock_jwt(
                user_id="user-uuid-api-me",
                email="me@mikasa.ai",
                username="meperson",
                display_name="Me Person",
                secret=self.auth_mgr.supabase_jwt_secret
            )
            req = MockRequest(headers={"Authorization": f"Bearer {token}"})
            resp = await handle_auth_me(req)
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.text)
            self.assertTrue(data["ok"])
            self.assertTrue(data["authenticated"])
            self.assertEqual(data["user"]["id"], "user-uuid-api-me")
            self.assertEqual(data["user"]["username"], "meperson")
            self.assertEqual(data["user"]["email"], "me@mikasa.ai")
            self.assertNotIn("password", data["user"])

        asyncio.run(_run())

    def test_26_api_me_unauthenticated_returns_401(self):
        """Scenario 26: GET /api/auth/me returns 401 Unauthorized when Bearer token is missing or invalid."""
        async def _run():
            # Missing Authorization header
            req1 = MockRequest()
            resp1 = await handle_auth_me(req1)
            self.assertEqual(resp1.status, 401)
            data1 = json.loads(resp1.text)
            self.assertFalse(data1["authenticated"])

            # Invalid token
            req2 = MockRequest(headers={"Authorization": "Bearer invalid.jwt.token"})
            resp2 = await handle_auth_me(req2)
            self.assertEqual(resp2.status, 401)
            data2 = json.loads(resp2.text)
            self.assertFalse(data2["authenticated"])

        asyncio.run(_run())

    def test_27_api_devices_authenticated_with_bearer_token(self):
        """Scenario 27: GET /api/devices uses Bearer token to isolate user's registered devices."""
        async def _run():
            uid_a = "user-uuid-api-dev-a"
            uid_b = "user-uuid-api-dev-b"
            self.account_mgr.register_device(user_id=uid_a, device_id="dev-a1", name="Device A")
            self.account_mgr.register_device(user_id=uid_b, device_id="dev-b1", name="Device B")

            token_a = self.auth_mgr.create_mock_jwt(
                user_id=uid_a,
                email="a@example.com",
                secret=self.auth_mgr.supabase_jwt_secret
            )
            req_a = MockRequest(headers={"Authorization": f"Bearer {token_a}"})
            extracted_uid = _get_request_user_id(req_a)
            self.assertEqual(extracted_uid, uid_a)

            resp = await handle_devices_list(req_a)
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.text)
            self.assertTrue(data["ok"])
            self.assertEqual(data["user_id"], uid_a)
            device_ids = [d["device_id"] for d in data["devices"]]
            self.assertIn("dev-a1", device_ids)
            self.assertNotIn("dev-b1", device_ids)

        asyncio.run(_run())

    def test_28_api_direct_auth_notices(self):
        """Scenario 28: Direct auth endpoints inform clients to use Supabase Auth client SDK."""
        async def _run():
            dummy = MockRequest()
            handlers = [
                (handle_auth_register, "POST /api/auth/register"),
                (handle_auth_login, "POST /api/auth/login"),
                (handle_auth_verify_email, "POST /api/auth/verify-email"),
                (handle_auth_forgot_password, "POST /api/auth/forgot-password"),
                (handle_auth_reset_password, "POST /api/auth/reset-password"),
                (handle_auth_change_password, "POST /api/auth/change-password"),
            ]
            for handler, name in handlers:
                resp = await handler(dummy)
                self.assertEqual(resp.status, 200, f"Failed on {name}")
                data = json.loads(resp.text)
                self.assertTrue(data["ok"])
                self.assertEqual(data.get("provider"), "supabase_auth")

        asyncio.run(_run())

    def test_29_separation_of_supabase_auth_and_remote_auth_session(self):
        """Scenario 29: SupabaseSessionClaims and RemoteAuthSession are strictly decoupled."""
        # Supabase Session: identity, email, exp, role
        supa_session = SupabaseSessionClaims(
            user_id="user-uuid-sep",
            email="sep@example.com",
            role="authenticated",
            exp=time.time() + 3600
        )
        # RemoteAuthSession: hardware device_id, challenge-response, agent permissions
        remote_session = RemoteAuthSession(
            user_id="user-uuid-sep",
            device_id="hardware-pc-id",
            expires_at=time.time() + 900,
            permissions=["screen.read", "terminal.execute"]
        )

        self.assertFalse(hasattr(supa_session, "device_id"))
        self.assertTrue(hasattr(remote_session, "device_id"))
        self.assertFalse(hasattr(supa_session, "permissions"))
        self.assertTrue(hasattr(remote_session, "permissions"))
        self.assertEqual(remote_session.device_id, "hardware-pc-id")
        self.assertIn("screen.read", remote_session.permissions)

    def test_30_env_configuration_security(self):
        """Scenario 30: Frontend .env never contains service role or JWT secrets, root .env does."""
        root_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.example")
        frontend_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mikasa-7", ".env.example")

        self.assertTrue(os.path.exists(root_env_path))
        self.assertTrue(os.path.exists(frontend_env_path))

        with open(root_env_path, "r", encoding="utf-8") as f:
            root_env = f.read()
        with open(frontend_env_path, "r", encoding="utf-8") as f:
            fe_env = f.read()

        # Root backend config
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY", root_env)
        self.assertIn("SUPABASE_JWT_SECRET", root_env)

        # Frontend config MUST NOT contain service role key or JWT secret assignments
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY=", fe_env)
        self.assertNotIn("SUPABASE_JWT_SECRET=", fe_env)
        self.assertIn("VITE_SUPABASE_URL=", fe_env)
        self.assertIn("VITE_SUPABASE_ANON_KEY=", fe_env)


if __name__ == "__main__":
    unittest.main()
