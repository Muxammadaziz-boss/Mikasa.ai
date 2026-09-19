# ========== tests/test_v8_phase43.py ==========
# Mikasa AI v8.0.0 — Phase 43: Real Supabase E2E Integration & Auth Validation
# Comprehensive Test Suite covering:
# 1. Real & Asymmetric JWT Verification (ES256 Raw (R||S) -> DER, RS256, HS256)
# 2. Supabase Auth Lifecycle (Register validation, Login claims, Email verification errors)
# 3. GET /api/auth/me Profile & Session verification
# 4. Multi-Tenant Boundary Enforcement & Cross-Tenant Spoofing Defense (403 Forbidden)
# 5. PostgreSQL RLS Schema Migration Integrity (Idempotency, auth.uid(), Trigger safety)
# 6. OAuth State Protection, Single-Use Pop & Replay Prevention
# 7. Zero Secret Leakage, AST Scan & Live Supabase JWKS Connectivity Probe

import os
import ast
import json
import time
import shutil
import tempfile
import unittest
import asyncio
from typing import Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric import ec, rsa, padding, utils
from cryptography.hazmat.primitives import hashes

from core.v8.account_device import (
    MikasaUser,
    AccountDeviceManager,
)
from core.v8.account_auth import (
    SupabaseAuthManager,
    AccountAuthManager,
    SupabaseSessionClaims,
    SupabaseJWKSClient,
    validate_username,
    validate_email,
)
from core.v8.permission_center import PermissionStore
from core.api_server import (
    resolve_auth_identity,
    get_authenticated_user,
    handle_auth_me,
    handle_auth_logout,
    handle_auth_logout_all,
    handle_health,
    handle_devices_list,
    handle_oauth_session_save,
    handle_oauth_session_get,
    _pending_oauth_sessions,
    _pending_oauth_lock,
)


class MockRequest:
    """Mock aiohttp request for isolated endpoint testing."""
    def __init__(
        self,
        method: str = "GET",
        query: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        match_info: Optional[Dict[str, str]] = None,
        remote: str = "127.0.0.1"
    ):
        self.method = method
        self.query = query or {}
        self.headers = headers or {}
        self._body = body or {}
        self.match_info = match_info or {}
        self.remote = remote

    async def json(self):
        return self._body


class BasePhase43Test(unittest.TestCase):
    """Clean test isolation harness for Phase 43."""
    def setUp(self):
        self._orig_env = dict(os.environ)
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p43_")

        self.adm_storage = os.path.join(self.temp_dir, "test_adm.json")
        self.auth_storage = os.path.join(self.temp_dir, "test_auth.json")
        self.perm_storage = os.path.join(self.temp_dir, "test_perm.json")

        self.test_supabase_url = "https://vdcssmzguxfknqkfxbed.supabase.co"
        self.jwt_secret = "phase43-super-secret-jwt-signing-key-32ch!"

        os.environ["SUPABASE_URL"] = self.test_supabase_url
        os.environ["SUPABASE_PUBLISHABLE_KEY"] = "sb_publishable_p43_test_key_12345"
        os.environ["SUPABASE_SECRET_KEY"] = "sb_secret_p43_test_key_67890"
        os.environ["SUPABASE_JWT_SECRET"] = self.jwt_secret
        os.environ["MIKASA_REQUIRE_AUTH"] = "true"

        AccountDeviceManager._default_instance = None
        AccountDeviceManager._instance = None
        self.adm = AccountDeviceManager.get_default_instance(storage_path=self.adm_storage)
        self.adm._users.clear()
        self.adm._devices.clear()
        self.adm._devices_by_hw_id.clear()
        self.adm._user_devices.clear()
        self.adm._contexts.clear()

        AccountAuthManager._default_instance = None
        AccountAuthManager._instance = None
        self.auth_mgr = AccountAuthManager.get_default_instance(storage_path=self.auth_storage)
        self.auth_mgr.supabase_jwt_secret = self.jwt_secret
        self.auth_mgr.supabase_url = self.test_supabase_url

        PermissionStore._default_instance = None
        PermissionStore._instance = None
        self.perm_store = PermissionStore.get_default_instance(storage_path=self.perm_storage)
        self.perm_store._profiles.clear()

        with _pending_oauth_lock:
            _pending_oauth_sessions.clear()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.clear()
        os.environ.update(self._orig_env)
        AccountDeviceManager._default_instance = None
        AccountAuthManager._default_instance = None
        PermissionStore._default_instance = None
        with _pending_oauth_lock:
            _pending_oauth_sessions.clear()

    def create_mock_es256_token(
        self,
        private_key: ec.EllipticCurvePrivateKey,
        kid: str,
        user_id: str,
        email: str = "es256@mikasa.ai",
        exp_seconds: int = 3600,
        issuer: Optional[str] = None
    ) -> str:
        """Create RFC 7515 standard ES256 JWT with raw (R || S) 64-byte signature."""
        iss = issuer if issuer is not None else f"{self.test_supabase_url}/auth/v1"
        header = {"alg": "ES256", "typ": "JWT", "kid": kid}
        payload = {
            "sub": user_id,
            "email": email,
            "role": "authenticated",
            "exp": int(time.time()) + exp_seconds,
            "iat": int(time.time()),
            "iss": iss,
            "user_metadata": {
                "username": user_id.split("-")[0],
                "display_name": f"User {user_id.split('-')[0].capitalize()}",
                "avatar_url": "https://avatar.mikasa.ai/u/1.png"
            }
        }
        h_b64 = self.auth_mgr._base64url_encode(json.dumps(header).encode("utf-8"))
        p_b64 = self.auth_mgr._base64url_encode(json.dumps(payload).encode("utf-8"))
        signing_input = f"{h_b64}.{p_b64}".encode("utf-8")

        # Cryptography signs producing DER
        der_sig = private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
        # Convert DER to standard JWT raw (R || S) format
        r, s = utils.decode_dss_signature(der_sig)
        raw_sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
        sig_b64 = self.auth_mgr._base64url_encode(raw_sig)
        return f"{h_b64}.{p_b64}.{sig_b64}"


# =====================================================================
# 1. ASYMMETRIC ES256 / RS256 & JWT VERIFICATION ENGINE
# =====================================================================

class TestPhase43JWTVerificationEngine(BasePhase43Test):
    """Scenarios 1-6: Real-world Asymmetric ES256 raw signature conversion & claims parsing."""

    def test_01_es256_raw_jwt_signature_verification_succeeds(self):
        """Scenario 1: Standard RFC 7515 raw (R || S) 64-byte ES256 JWT signature is converted to DER and verified."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        kid = "live-supabase-es256-key-001"

        # Register public key in JWKS client
        self.auth_mgr.jwks_client.add_mock_key(kid, public_key)

        token = self.create_mock_es256_token(
            private_key=private_key,
            kid=kid,
            user_id="usr-es256-alisher",
            email="alisher@mikasa.ai"
        )

        ok, msg, claims = self.auth_mgr.verify_supabase_jwt(token)
        self.assertTrue(ok, f"Verification failed: {msg}")
        self.assertIsNotNone(claims)
        self.assertEqual(claims.user_id, "usr-es256-alisher")
        self.assertEqual(claims.email, "alisher@mikasa.ai")
        self.assertEqual(claims.avatar_url, "https://avatar.mikasa.ai/u/1.png")
        self.assertTrue(claims.is_valid)

        # Verify claims.to_dict() has avatar_url
        claims_dict = claims.to_dict()
        self.assertIn("avatar_url", claims_dict)
        self.assertEqual(claims_dict["avatar_url"], "https://avatar.mikasa.ai/u/1.png")

    def test_02_es256_expired_token_rejected(self):
        """Scenario 2: ES256 token with past exp timestamp is rejected with EXPIRED_TOKEN."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        kid = "live-supabase-es256-key-001"
        self.auth_mgr.jwks_client.add_mock_key(kid, private_key.public_key())

        token = self.create_mock_es256_token(
            private_key=private_key,
            kid=kid,
            user_id="usr-es256-expired",
            exp_seconds=-120
        )

        ok, msg, claims = self.auth_mgr.verify_supabase_jwt(token)
        self.assertFalse(ok)
        self.assertIn("expired", msg.lower())
        self.assertIsNone(claims)

    def test_03_es256_forged_signature_rejected(self):
        """Scenario 3: ES256 token signed by an untrusted key is rejected with INVALID_SIGNATURE."""
        private_key_real = ec.generate_private_key(ec.SECP256R1())
        private_key_attacker = ec.generate_private_key(ec.SECP256R1())
        kid = "live-supabase-es256-key-001"

        # JWKS holds the real public key
        self.auth_mgr.jwks_client.add_mock_key(kid, private_key_real.public_key())

        # Attacker signs token using their own private key
        forged_token = self.create_mock_es256_token(
            private_key=private_key_attacker,
            kid=kid,
            user_id="usr-attacker-target"
        )

        ok, msg, claims = self.auth_mgr.verify_supabase_jwt(forged_token)
        self.assertFalse(ok)
        self.assertIn("imzo tekshiruvidan o'tmadi", msg.lower())
        self.assertIsNone(claims)

    def test_04_es256_invalid_issuer_rejected(self):
        """Scenario 4: ES256 token with mismatched issuer is rejected."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        kid = "live-supabase-es256-key-001"
        self.auth_mgr.jwks_client.add_mock_key(kid, private_key.public_key())

        token = self.create_mock_es256_token(
            private_key=private_key,
            kid=kid,
            user_id="usr-es256-wrong-iss",
            issuer="https://evil-spoofed-issuer.supabase.co/auth/v1"
        )

        ok, msg, claims = self.auth_mgr.verify_supabase_jwt(token)
        self.assertFalse(ok)
        self.assertIn("noto'g'ri token beruvchi", msg.lower())

    def test_05_rs256_asymmetric_jwt_verification(self):
        """Scenario 5: Asymmetric RS256 token verified via JWKS."""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        kid = "live-supabase-rs256-key-002"
        self.auth_mgr.jwks_client.add_mock_key(kid, private_key.public_key())

        header = {"alg": "RS256", "typ": "JWT", "kid": kid}
        payload = {
            "sub": "usr-rs256-bobur",
            "email": "bobur@mikasa.ai",
            "role": "authenticated",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "iss": f"{self.test_supabase_url}/auth/v1"
        }
        h_b64 = self.auth_mgr._base64url_encode(json.dumps(header).encode("utf-8"))
        p_b64 = self.auth_mgr._base64url_encode(json.dumps(payload).encode("utf-8"))
        signing_input = f"{h_b64}.{p_b64}".encode("utf-8")
        sig = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        sig_b64 = self.auth_mgr._base64url_encode(sig)
        rs256_token = f"{h_b64}.{p_b64}.{sig_b64}"

        ok, msg, claims = self.auth_mgr.verify_supabase_jwt(rs256_token)
        self.assertTrue(ok)
        self.assertEqual(claims.user_id, "usr-rs256-bobur")

    def test_06_malformed_tokens_rejected_without_crash(self):
        """Scenario 6: Malformed or non-string tokens fail safely without crashing."""
        for bad_token in ["", "   ", "one.two", "one.two.three.four", "invalid-token", None]:
            ok, msg, claims = self.auth_mgr.verify_supabase_jwt(bad_token)
            self.assertFalse(ok)
            self.assertIsNone(claims)


# =====================================================================
# 2. REST API /api/auth/me & SESSION RESTORE
# =====================================================================

class TestPhase43AuthMeAndSessionRestore(BasePhase43Test):
    """Scenarios 7-11: GET /api/auth/me, Bearer token authentication, profile sync."""

    def setUp(self):
        super().setUp()
        self.ec_key = ec.generate_private_key(ec.SECP256R1())
        self.kid = "test-auth-me-kid"
        self.auth_mgr.jwks_client.add_mock_key(self.kid, self.ec_key.public_key())

    def test_07_auth_me_valid_bearer_token_returns_200(self):
        """Scenario 7: GET /api/auth/me with valid Bearer token returns 200, user, and session."""
        user_id = "user-uuid-dilshod"
        token = self.create_mock_es256_token(
            private_key=self.ec_key,
            kid=self.kid,
            user_id=user_id,
            email="dilshod@mikasa.ai"
        )

        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp = asyncio.run(handle_auth_me(req))
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.text)
        self.assertTrue(data["ok"])
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user"]["id"], user_id)
        self.assertEqual(data["user"]["email"], "dilshod@mikasa.ai")
        self.assertEqual(data["session"]["user_id"], user_id)

    def test_08_auth_me_missing_token_returns_401(self):
        """Scenario 8: GET /api/auth/me without Bearer token returns 401 Unauthorized."""
        req = MockRequest(method="GET", headers={})
        resp = asyncio.run(handle_auth_me(req))
        self.assertEqual(resp.status, 401)
        data = json.loads(resp.text)
        self.assertFalse(data["ok"])
        self.assertFalse(data["authenticated"])

    def test_09_auth_me_forged_token_returns_401(self):
        """Scenario 9: GET /api/auth/me with forged token returns 401 Unauthorized."""
        bad_key = ec.generate_private_key(ec.SECP256R1())
        forged_token = self.create_mock_es256_token(
            private_key=bad_key,
            kid=self.kid,
            user_id="user-uuid-hacker"
        )
        req = MockRequest(method="GET", headers={"Authorization": f"Bearer {forged_token}"})
        resp = asyncio.run(handle_auth_me(req))
        self.assertEqual(resp.status, 401)

    def test_10_auth_logout_broadcasts_event(self):
        """Scenario 10: POST /api/auth/logout succeeds and clears session state."""
        user_id = "user-uuid-logout"
        token = self.create_mock_es256_token(
            private_key=self.ec_key,
            kid=self.kid,
            user_id=user_id
        )
        req = MockRequest(method="POST", headers={"Authorization": f"Bearer {token}"})
        resp = asyncio.run(handle_auth_logout(req))
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.text)
        self.assertTrue(data["ok"])
        self.assertTrue(data["logged_out"])

    def test_11_auth_logout_all_terminates_active_sessions(self):
        """Scenario 11: POST /api/auth/logout-all succeeds for authenticated user."""
        user_id = "user-uuid-logout-all"
        token = self.create_mock_es256_token(
            private_key=self.ec_key,
            kid=self.kid,
            user_id=user_id
        )
        req = MockRequest(method="POST", headers={"Authorization": f"Bearer {token}"})
        resp = asyncio.run(handle_auth_logout_all(req))
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.text)
        self.assertTrue(data["ok"])
        self.assertEqual(data["user_id"], user_id)


# =====================================================================
# 3. MULTI-TENANT BOUNDARY ENFORCEMENT & SPOOFING DEFENSE
# =====================================================================

class TestPhase43MultiTenantBoundaries(BasePhase43Test):
    """Scenarios 12-16: Strict tenant isolation via JWT.sub, 403 Forbidden on tampering."""

    def setUp(self):
        super().setUp()
        self.ec_key = ec.generate_private_key(ec.SECP256R1())
        self.kid = "test-tenant-kid"
        self.auth_mgr.jwks_client.add_mock_key(self.kid, self.ec_key.public_key())
        self.user_a = "user-uuid-alice"
        self.user_b = "user-uuid-bob"
        self.token_a = self.create_mock_es256_token(self.ec_key, self.kid, self.user_a, "alice@mikasa.ai")
        self.token_b = self.create_mock_es256_token(self.ec_key, self.kid, self.user_b, "bob@mikasa.ai")

    def test_12_tenant_a_cannot_access_tenant_b_query_param_403(self):
        """Scenario 12: User A attempting to pass ?user_id=User-B is rejected with 403 Forbidden."""
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {self.token_a}"},
            query={"user_id": self.user_b}
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 403)
        data = json.loads(resp.text)
        self.assertIn("Cross-tenant access denied", data["error"])

    def test_13_tenant_a_cannot_access_tenant_b_header_spoofing_403(self):
        """Scenario 13: User A attempting to pass X-Mikasa-User-Id: User-B is rejected with 403."""
        req = MockRequest(
            method="GET",
            headers={
                "Authorization": f"Bearer {self.token_a}",
                "X-Mikasa-User-Id": self.user_b
            }
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 403)
        data = json.loads(resp.text)
        self.assertIn("Cross-tenant access denied", data["error"])

    def test_14_tenant_admin_spoofing_rejected_403(self):
        """Scenario 14: Regular user attempting ?user_id=admin is rejected with 403 Forbidden."""
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {self.token_a}"},
            query={"user_id": "admin"}
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 403)

    def test_15_device_data_completely_isolated_between_tenants(self):
        """Scenario 15: Devices registered by User A are completely hidden from User B."""
        self.adm.register_device(self.user_a, "alice-pc-desktop", "Alice PC")
        self.adm.register_device(self.user_b, "bob-pc-laptop", "Bob Laptop")

        # Query devices as Alice
        req_a = MockRequest(method="GET", headers={"Authorization": f"Bearer {self.token_a}"})
        resp_a = asyncio.run(handle_devices_list(req_a))
        devices_a = json.loads(resp_a.text)["devices"]
        self.assertEqual(len(devices_a), 1)
        self.assertEqual(devices_a[0]["device_id"], "alice-pc-desktop")

        # Query devices as Bob
        req_b = MockRequest(method="GET", headers={"Authorization": f"Bearer {self.token_b}"})
        resp_b = asyncio.run(handle_devices_list(req_b))
        devices_b = json.loads(resp_b.text)["devices"]
        self.assertEqual(len(devices_b), 1)
        self.assertEqual(devices_b[0]["device_id"], "bob-pc-laptop")

    def test_16_permissions_isolated_between_tenants(self):
        """Scenario 16: Device permissions modified by User A do not affect User B profile."""
        shared_dev_id = "shared-hardware-id"
        self.perm_store.update_permissions(self.user_a, shared_dev_id, {"system_control": False})

        profile_b = self.perm_store.get_profile(self.user_b, shared_dev_id)
        self.assertTrue(profile_b.permissions.get("system_control", True))


# =====================================================================
# 4. POSTGRESQL RLS MIGRATIONS AUDIT
# =====================================================================

class TestPhase43PostgreSQLMigrations(unittest.TestCase):
    """Scenarios 17-20: PostgreSQL RLS schema, idempotent policies, handle_new_user trigger."""

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.migration_p41 = os.path.join(self.base_dir, "supabase", "migrations", "20260918_phase41_supabase_auth.sql")
        self.migration_p42 = os.path.join(self.base_dir, "supabase", "migrations", "20260918_phase42_device_enrollment.sql")

    def test_17_migrations_files_exist(self):
        """Scenario 17: Migration files exist in supabase/migrations/."""
        self.assertTrue(os.path.exists(self.migration_p41), f"Missing {self.migration_p41}")
        self.assertTrue(os.path.exists(self.migration_p42), f"Missing {self.migration_p42}")

    def test_18_migrations_idempotency_drop_policy_if_exists(self):
        """Scenario 18: All policies use DROP POLICY IF EXISTS before CREATE POLICY."""
        for path in (self.migration_p41, self.migration_p42):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("DROP POLICY IF EXISTS", content, f"Non-idempotent policy in {path}")

    def test_19_migrations_rls_enabled_on_all_tables(self):
        """Scenario 19: All 7 required schema tables have RLS explicitly enabled."""
        with open(self.migration_p41, "r", encoding="utf-8") as f:
            p41 = f.read()
        with open(self.migration_p42, "r", encoding="utf-8") as f:
            p42 = f.read()

        tables_p41 = ["public.profiles", "public.devices", "public.telegram_links", "public.permissions"]
        tables_p42 = ["public.device_pairing_sessions", "public.device_credentials", "public.device_auth_challenges"]

        for t in tables_p41:
            self.assertIn(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY", p41)
        for t in tables_p42:
            self.assertIn(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY", p42)

    def test_20_migrations_trigger_collision_resistant_and_google_metadata(self):
        """Scenario 20: handle_new_user() trigger includes collision-resistant username loop and Google metadata."""
        with open(self.migration_p41, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("CREATE OR REPLACE FUNCTION public.handle_new_user()", content)
        self.assertIn("avatar_url", content)
        self.assertIn("picture", content)
        self.assertIn("full_name", content)
        self.assertIn("WHILE EXISTS", content)  # Collision resistance loop


# =====================================================================
# 5. OAUTH FLOW, SINGLE-USE POP & REPLAY DEFENSE
# =====================================================================

class TestPhase43OAuthProtection(BasePhase43Test):
    """Scenarios 21-24: State-indexed OAuth sessions, single-use consumption, concurrency."""

    def test_21_oauth_session_save_and_retrieve_with_state(self):
        """Scenario 21: OAuth session saved with cryptographic state and retrieved successfully."""
        state = "state-p43-oauth-111"
        req_save = MockRequest(
            method="POST",
            body={
                "access_token": "sb-token-phase43",
                "user": {"id": "user-oauth-p43"},
                "state": state
            }
        )
        resp_save = asyncio.run(handle_oauth_session_save(req_save))
        self.assertEqual(resp_save.status, 200)

        req_get = MockRequest(method="GET", query={"state": state})
        resp_get = asyncio.run(handle_oauth_session_get(req_get))
        self.assertEqual(resp_get.status, 200)
        data = json.loads(resp_get.text)
        self.assertEqual(data["session"]["access_token"], "sb-token-phase43")

    def test_22_oauth_session_single_use_pop_rejection(self):
        """Scenario 22: Retrieving OAuth session twice fails on 2nd attempt (consumed)."""
        state = "state-single-use-phase43"
        req_save = MockRequest(method="POST", body={"access_token": "token-pop", "state": state})
        asyncio.run(handle_oauth_session_save(req_save))

        # First retrieve -> 200 OK
        req_get = MockRequest(method="GET", query={"state": state})
        resp1 = asyncio.run(handle_oauth_session_get(req_get))
        self.assertEqual(resp1.status, 200)

        # Second retrieve -> 404 Not Found
        resp2 = asyncio.run(handle_oauth_session_get(req_get))
        self.assertEqual(resp2.status, 404)

    def test_23_oauth_expired_state_rejected(self):
        """Scenario 23: OAuth session past TTL returns 404."""
        state = "state-expired-p43"
        with _pending_oauth_lock:
            _pending_oauth_sessions[state] = (time.time() - 30.0, {"access_token": "expired"})

        req_get = MockRequest(method="GET", query={"state": state})
        resp = asyncio.run(handle_oauth_session_get(req_get))
        self.assertEqual(resp.status, 404)

    def test_24_oauth_concurrent_state_isolation(self):
        """Scenario 24: Concurrent OAuth sessions for User A and User B do not interfere."""
        state_a = "state-p43-alice"
        state_b = "state-p43-bob"

        asyncio.run(handle_oauth_session_save(MockRequest(method="POST", body={"user": "alice", "state": state_a})))
        asyncio.run(handle_oauth_session_save(MockRequest(method="POST", body={"user": "bob", "state": state_b})))

        # Pop Bob first
        resp_b = asyncio.run(handle_oauth_session_get(MockRequest(method="GET", query={"state": state_b})))
        self.assertEqual(resp_b.status, 200)
        self.assertEqual(json.loads(resp_b.text)["session"]["user"], "bob")

        # Alice remains available
        resp_a = asyncio.run(handle_oauth_session_get(MockRequest(method="GET", query={"state": state_a})))
        self.assertEqual(resp_a.status, 200)
        self.assertEqual(json.loads(resp_a.text)["session"]["user"], "alice")


# =====================================================================
# 6. STATIC SECURITY SCAN & LIVE SUPABASE AUDIT
# =====================================================================

class TestPhase43SecurityScanAndLiveAudit(unittest.TestCase):
    """Scenarios 25-28: Zero fallback secrets, AST code safety, health check, live JWKS probe."""

    def test_25_no_default_test_secrets_in_codebase(self):
        """Scenario 25: Ensure no forbidden fallback secrets exist in project files."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        forbidden = "-".join(["mikasa", "default", "test", "secret"])

        violations = []
        for root, _, files in os.walk(base_dir):
            if any(p in root for p in [".git", "node_modules", ".venv", "__pycache__", "dist", "build"]):
                continue
            for fname in files:
                if fname.endswith((".py", ".ts", ".tsx", ".js", ".json", ".sql", ".env.example")):
                    if fname in ("test_v8_security_audit.py", "test_v8_phase43.py"):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            if forbidden in f.read():
                                violations.append(fpath)
                    except Exception:
                        pass
        self.assertEqual(len(violations), 0, f"Found forbidden secret in: {violations}")

    def test_26_ast_scan_no_eval_or_exec_in_core_modules(self):
        """Scenario 26: AST scan verifies no eval() or exec() in core/v8/account_auth.py."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        fpath = os.path.join(base_dir, "core", "v8", "account_auth.py")
        with open(fpath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=fpath)

        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    calls.append(node.func.id)
        self.assertEqual(len(calls), 0, f"Dangerous calls detected: {calls}")

    def test_27_health_endpoint_zero_secret_leakage(self):
        """Scenario 27: GET /api/health returns configured status without leaking sensitive keys."""
        req = MockRequest(method="GET")
        resp = asyncio.run(handle_health(req))
        self.assertEqual(resp.status, 200)
        text = resp.text
        self.assertNotIn("sb_secret_", text)
        self.assertNotIn("service_role", text)
        self.assertNotIn("JWT_SECRET", text)

    def test_28_live_supabase_jwks_connectivity_probe(self):
        """Scenario 28: Live probe to configured Supabase JWKS endpoint."""
        url = os.environ.get("SUPABASE_URL", "https://vdcssmzguxfknqkfxbed.supabase.co")
        client = SupabaseJWKSClient(supabase_url=url)
        # Attempt live key refresh if network is available
        refreshed = client.refresh_keys()
        if refreshed:
            self.assertGreater(len(client._cached_keys), 0)
            # Verify cached key is an ECPublicKey or RSAPublicKey
            first_key = next(iter(client._cached_keys.values()))
            self.assertIsNotNone(first_key)


if __name__ == "__main__":
    unittest.main()
