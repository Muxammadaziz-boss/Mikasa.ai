# ========== tests/test_v8_security_audit.py ==========
# Mikasa AI v8.0.0 — Comprehensive Security Audit Test Suite
# Hardened Multi-Tenant, Supabase JWT, OAuth & Cryptographic Device Security
#
# Sections Covered:
# 1. AUTH: Valid/Invalid JWT, Expiration, Missing Token, Malformed Token, RS256 JWKS
# 2. TENANT: Cross-tenant parameter tampering (403 Forbidden), Header Spoofing, Admin Escapes
# 3. DEVICE: Owner access, Non-owner rejection (404/403), Revoked status enforcement
# 4. PAIRING: Valid code, Invalid code, Max 5 attempts lockout, TTL expiry, Single-use replay prevention
# 5. OAUTH: State-bound session storage, Single-use consumption (pop), Expired session, Multi-user concurrency
# 6. REMOTE: Scoped permissions, Isolated user profile boundaries
# 7. STATIC SCAN: Secret leaks check, Zero default secrets, Safe AST verification

import os
import ast
import json
import time
import shutil
import tempfile
import unittest
import asyncio
from typing import Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

from core.v8.account_device import (
    MikasaUser,
    Device,
    AccountDeviceManager,
)
from core.v8.account_auth import (
    SupabaseAuthManager,
    AccountAuthManager,
    SupabaseSessionClaims,
    SupabaseJWKSClient,
)
from core.v8.device_pairing import DevicePairingManager
from core.v8.permission_center import PermissionStore
from core.api_server import (
    resolve_auth_identity,
    handle_devices_list,
    handle_device_detail,
    handle_device_rename,
    handle_device_select,
    handle_device_revoke,
    handle_device_pairing_start,
    handle_device_pairing_cancel,
    handle_oauth_session_save,
    handle_oauth_session_get,
    handle_remote_permissions_get,
    handle_remote_permissions_put,
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


class BaseSecurityAuditTest(unittest.TestCase):
    """Base test class providing clean environment isolation."""
    def setUp(self):
        self._orig_env = dict(os.environ)
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_sec_audit_")

        # Isolated storage paths
        self.adm_storage = os.path.join(self.temp_dir, "test_adm.json")
        self.auth_storage = os.path.join(self.temp_dir, "test_auth.json")
        self.perm_storage = os.path.join(self.temp_dir, "test_perm.json")
        self.pairing_storage = os.path.join(self.temp_dir, "test_pairing.json")

        # Test secrets
        self.jwt_secret = "audit-super-secret-jwt-signing-key-32ch!"

        # Configure environment
        os.environ["SUPABASE_URL"] = "https://audit-project.supabase.co"
        os.environ["SUPABASE_PUBLISHABLE_KEY"] = "sb_publishable_audit_test_key_12345"
        os.environ["SUPABASE_SECRET_KEY"] = "sb_secret_audit_test_key_67890"
        os.environ["SUPABASE_JWT_SECRET"] = self.jwt_secret
        os.environ["MIKASA_REQUIRE_AUTH"] = "true"

        # Initialize managers
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
        self.supabase_auth = AccountAuthManager.get_default_instance(storage_path=self.auth_storage)
        self.supabase_auth.supabase_jwt_secret = self.jwt_secret
        self.account_auth = self.supabase_auth

        DevicePairingManager._default_instance = None
        DevicePairingManager._instance = None
        self.pairing_mgr = DevicePairingManager.get_default_instance(storage_path=self.pairing_storage)
        self.pairing_mgr._sessions.clear()

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
        SupabaseAuthManager._default_instance = None
        AccountAuthManager._default_instance = None
        DevicePairingManager._default_instance = None
        PermissionStore._default_instance = None
        with _pending_oauth_lock:
            _pending_oauth_sessions.clear()

    def create_token(self, user_id: str, email: str = "user@mikasa.ai", exp_seconds: int = 3600, secret: Optional[str] = None) -> str:
        sec = secret or self.jwt_secret
        return self.supabase_auth.create_mock_jwt(
            user_id=user_id,
            email=email,
            username=user_id.split("-")[0],
            role="authenticated",
            exp_seconds=exp_seconds,
            secret=sec
        )


# =====================================================================
# 1. AUTHENTICATION (JWT, JWKS, EXPIRATION, FORGERY)
# =====================================================================

class TestSecurityAuthentication(BaseSecurityAuditTest):
    """Scenarios 1-7: JWT validation, signature verification, expiration, fail-closed JWKS."""

    def test_01_auth_valid_jwt_returns_200(self):
        """Scenario 1: Protected endpoint with valid Supabase JWT returns 200 OK."""
        token = self.create_token(user_id="user-uuid-101")
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.text)
        self.assertTrue(data["ok"])

    def test_02_auth_invalid_signature_returns_401(self):
        """Scenario 2: Token signed with unauthorized secret key returns 401 Unauthorized."""
        forged_token = self.create_token(user_id="attacker-999", secret="wrong-unauthorized-key-000000000000")
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {forged_token}"}
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 401)
        data = json.loads(resp.text)
        self.assertFalse(data["ok"])
        self.assertIn("Token yaroqsiz", data["error"])

    def test_03_auth_expired_jwt_returns_401(self):
        """Scenario 3: Expired JWT (exp in the past) returns 401 Unauthorized."""
        expired_token = self.create_token(user_id="user-uuid-101", exp_seconds=-300)
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 401)
        data = json.loads(resp.text)
        self.assertFalse(data["ok"])
        self.assertIn("Token yaroqsiz", data["error"])

    def test_04_auth_missing_token_returns_401_when_enforced(self):
        """Scenario 4: When auth is enforced, missing Bearer token returns 401 Unauthorized."""
        req = MockRequest(method="GET", headers={})
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 401)
        data = json.loads(resp.text)
        self.assertFalse(data["ok"])
        self.assertIn("Bearer token talab qilinadi", data["error"])

    def test_05_auth_malformed_token_returns_401(self):
        """Scenario 5: Malformed tokens (not three dot-separated segments) return 401."""
        for bad_token in ["not-a-token", "a.b", "...", "header.payload.bad_base64!!!"]:
            req = MockRequest(method="GET", headers={"Authorization": f"Bearer {bad_token}"})
            resp = asyncio.run(handle_devices_list(req))
            self.assertEqual(resp.status, 401, f"Failed for token: {bad_token}")

    def test_06_auth_asymmetric_rs256_jwks_verification(self):
        """Scenario 6: Asymmetric RS256 JWT verified via JWKS mock key with fail-closed security."""
        # Generate temporary RSA keypair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        kid = "supabase-test-key-2026"

        # Register key in JWKS client (sets _last_fetched to current time)
        self.supabase_auth.jwks_client.add_mock_key(kid, public_key)

        # Build RS256 token with correct issuer
        header = {"alg": "RS256", "typ": "JWT", "kid": kid}
        payload = {
            "sub": "user-uuid-rs256",
            "email": "rs256@mikasa.ai",
            "role": "authenticated",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "iss": f"{self.supabase_auth.supabase_url}/auth/v1"
        }
        h_b64 = self.supabase_auth._base64url_encode(json.dumps(header).encode("utf-8"))
        p_b64 = self.supabase_auth._base64url_encode(json.dumps(payload).encode("utf-8"))
        signing_input = f"{h_b64}.{p_b64}".encode("utf-8")
        sig = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        sig_b64 = self.supabase_auth._base64url_encode(sig)
        rs256_token = f"{h_b64}.{p_b64}.{sig_b64}"

        # 1. Verification directly via SupabaseAuthManager
        ok, msg, claims = self.supabase_auth.verify_supabase_jwt(rs256_token)
        self.assertTrue(ok, f"Verification failed: {msg}")
        self.assertEqual(claims.user_id, "user-uuid-rs256")

        # 2. Endpoint verification
        req = MockRequest(method="GET", headers={"Authorization": f"Bearer {rs256_token}"})
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 200)

    def test_07_auth_rs256_unknown_kid_rejected(self):
        """Scenario 7: RS256 token with unknown kid rejected by fail-closed JWKS client."""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        header = {"alg": "RS256", "typ": "JWT", "kid": "unknown-nonexistent-kid"}
        payload = {"sub": "user-uuid-fail", "exp": int(time.time()) + 3600}
        h_b64 = self.supabase_auth._base64url_encode(json.dumps(header).encode("utf-8"))
        p_b64 = self.supabase_auth._base64url_encode(json.dumps(payload).encode("utf-8"))
        signing_input = f"{h_b64}.{p_b64}".encode("utf-8")
        sig = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        bad_token = f"{h_b64}.{p_b64}.{self.supabase_auth._base64url_encode(sig)}"

        ok, msg, claims = self.supabase_auth.verify_supabase_jwt(bad_token)
        self.assertFalse(ok)
        self.assertIn("JWKS", msg)


# =====================================================================
# 2. MULTI-TENANT AUTHORIZATION & IDENTITY ENFORCEMENT
# =====================================================================

class TestSecurityMultiTenantAuthorization(BaseSecurityAuditTest):
    """Scenarios 8-12: Strict tenant boundaries, parameter spoofing, cross-tenant 403."""

    def test_08_tenant_user_a_accesses_own_devices(self):
        """Scenario 8: User A accesses User A's devices -> 200 OK."""
        user_a_id = "user-uuid-alice"
        self.adm.register_device(user_a_id, "alice-pc-1", "Alice Workstation")

        token_a = self.create_token(user_id=user_a_id)
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.text)
        self.assertEqual(len(data["devices"]), 1)
        self.assertEqual(data["devices"][0]["device_id"], "alice-pc-1")

    def test_09_tenant_user_a_spoofs_user_b_in_query_param_rejected_403(self):
        """Scenario 9: User A token with ?user_id=user-B is rejected with 403 Forbidden."""
        user_a_id = "user-uuid-alice"
        user_b_id = "user-uuid-bob"
        self.adm.register_device(user_b_id, "bob-secret-pc", "Bob Private PC")

        token_a = self.create_token(user_id=user_a_id)
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {token_a}"},
            query={"user_id": user_b_id}
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 403)
        data = json.loads(resp.text)
        self.assertFalse(data["ok"])
        self.assertIn("Cross-tenant access denied", data["error"])

    def test_10_tenant_spoofed_x_mikasa_user_id_header_rejected_403(self):
        """Scenario 10: User A token with X-Mikasa-User-Id: user-B is rejected with 403 Forbidden."""
        user_a_id = "user-uuid-alice"
        user_b_id = "user-uuid-bob"

        token_a = self.create_token(user_id=user_a_id)
        req = MockRequest(
            method="GET",
            headers={
                "Authorization": f"Bearer {token_a}",
                "X-Mikasa-User-Id": user_b_id
            }
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 403)
        data = json.loads(resp.text)
        self.assertIn("Cross-tenant access denied", data["error"])

    def test_11_tenant_spoofed_admin_param_rejected_403(self):
        """Scenario 11: Normal user attempting to spoof ?user_id=admin is rejected with 403."""
        user_a_id = "user-uuid-alice"
        token_a = self.create_token(user_id=user_a_id)

        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {token_a}"},
            query={"user_id": "admin"}
        )
        resp = asyncio.run(handle_devices_list(req))
        self.assertEqual(resp.status, 403)

    def test_12_tenant_device_isolation_between_two_users(self):
        """Scenario 12: Devices of User A are completely invisible to User B."""
        user_a_id = "user-uuid-alice"
        user_b_id = "user-uuid-bob"

        self.adm.register_device(user_a_id, "alice-pc", "Alice PC")
        self.adm.register_device(user_b_id, "bob-pc", "Bob PC")

        # User A list
        token_a = self.create_token(user_id=user_a_id)
        req_a = MockRequest(method="GET", headers={"Authorization": f"Bearer {token_a}"})
        resp_a = asyncio.run(handle_devices_list(req_a))
        devices_a = json.loads(resp_a.text)["devices"]
        self.assertEqual(len(devices_a), 1)
        self.assertEqual(devices_a[0]["device_id"], "alice-pc")

        # User B list
        token_b = self.create_token(user_id=user_b_id)
        req_b = MockRequest(method="GET", headers={"Authorization": f"Bearer {token_b}"})
        resp_b = asyncio.run(handle_devices_list(req_b))
        devices_b = json.loads(resp_b.text)["devices"]
        self.assertEqual(len(devices_b), 1)
        self.assertEqual(devices_b[0]["device_id"], "bob-pc")


# =====================================================================
# 3. DEVICE ACCESS CONTROLS & LIFECYCLE
# =====================================================================

class TestSecurityDeviceAccess(BaseSecurityAuditTest):
    """Scenarios 13-17: Device ownership, unauthorized mutation blocking, revocation."""

    def setUp(self):
        super().setUp()
        self.user_a_id = "user-uuid-alice"
        self.user_b_id = "user-uuid-bob"
        self.adm.register_device(self.user_a_id, "alice-device-1", "Alice Main PC", status="online")
        self.token_a = self.create_token(user_id=self.user_a_id)
        self.token_b = self.create_token(user_id=self.user_b_id)

    def test_13_device_owner_detail_access_200(self):
        """Scenario 13: Owner can view their own device details."""
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {self.token_a}"},
            match_info={"device_id": "alice-device-1"}
        )
        resp = asyncio.run(handle_device_detail(req))
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.text)
        self.assertTrue(data["ok"])
        self.assertEqual(data["device"]["name"], "Alice Main PC")

    def test_14_device_non_owner_detail_access_rejected_404(self):
        """Scenario 14: Non-owner cannot view another user's device details (returns 404)."""
        req = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {self.token_b}"},
            match_info={"device_id": "alice-device-1"}
        )
        resp = asyncio.run(handle_device_detail(req))
        self.assertEqual(resp.status, 404)

    def test_15_device_non_owner_rename_blocked_404(self):
        """Scenario 15: Non-owner cannot rename another user's device."""
        req = MockRequest(
            method="PATCH",
            headers={"Authorization": f"Bearer {self.token_b}"},
            match_info={"device_id": "alice-device-1"},
            body={"name": "Hacked Name"}
        )
        resp = asyncio.run(handle_device_rename(req))
        self.assertEqual(resp.status, 404)
        # Verify original name untouched
        dev = self.adm.get_device("alice-device-1", user_id=self.user_a_id)
        self.assertIsNotNone(dev)
        self.assertEqual(dev.name, "Alice Main PC")

    def test_16_device_non_owner_select_blocked_404(self):
        """Scenario 16: Non-owner cannot select another user's device as active."""
        req = MockRequest(
            method="POST",
            headers={"Authorization": f"Bearer {self.token_b}"},
            match_info={"device_id": "alice-device-1"}
        )
        resp = asyncio.run(handle_device_select(req))
        self.assertEqual(resp.status, 404)

    def test_17_device_revoked_cannot_be_selected(self):
        """Scenario 17: Revoked device cannot be selected as active."""
        # Revoke device
        req_revoke = MockRequest(
            method="DELETE",
            headers={"Authorization": f"Bearer {self.token_a}"},
            match_info={"device_id": "alice-device-1"}
        )
        resp_revoke = asyncio.run(handle_device_revoke(req_revoke))
        self.assertEqual(resp_revoke.status, 200)

        # Attempt to select revoked device (returns 400 or 404)
        req_sel = MockRequest(
            method="POST",
            headers={"Authorization": f"Bearer {self.token_a}"},
            match_info={"device_id": "alice-device-1"}
        )
        resp_sel = asyncio.run(handle_device_select(req_sel))
        self.assertIn(resp_sel.status, (400, 404))


# =====================================================================
# 4. SECURE PAIRING (BRUTE-FORCE, REPLAY, EXPIRATION)
# =====================================================================

class TestSecurityDevicePairing(BaseSecurityAuditTest):
    """Scenarios 18-23: Cryptographic pairing code security, lockout, single-use."""

    def setUp(self):
        super().setUp()
        self.user_id = "user-uuid-alice"
        self.token = self.create_token(user_id=self.user_id)

    def test_18_pairing_valid_code_succeeds(self):
        """Scenario 18: Valid 6-digit code successfully completes pairing session."""
        sess, raw_code = self.pairing_mgr.start_pairing(self.user_id)
        ok, msg, completed_sess = self.pairing_mgr.complete_pairing(
            pairing_id=sess.id,
            code=raw_code,
            device_id="agent-pc-1",
            user_id=self.user_id
        )
        self.assertTrue(ok)
        self.assertEqual(completed_sess.status, "COMPLETED")

    def test_19_pairing_wrong_code_fails(self):
        """Scenario 19: Incorrect pairing code fails verification."""
        sess, _ = self.pairing_mgr.start_pairing(self.user_id)
        ok, msg, _ = self.pairing_mgr.verify_code(sess.id, "000000", user_id=self.user_id)
        self.assertFalse(ok)
        self.assertIn("noto'g'ri", msg.lower())
        updated_sess = self.pairing_mgr.get_session(sess.id)
        self.assertEqual(updated_sess.attempt_count, 1)

    def test_20_pairing_max_5_attempts_lockout(self):
        """Scenario 20: 5 incorrect code attempts triggers lockout protection."""
        sess, _ = self.pairing_mgr.start_pairing(self.user_id)
        for i in range(5):
            ok, msg, _ = self.pairing_mgr.verify_code(sess.id, f"99999{i}", user_id=self.user_id)
            self.assertFalse(ok)

        locked_sess = self.pairing_mgr.get_session(sess.id)
        self.assertEqual(locked_sess.status, "FAILED")

        # 6th attempt immediately rejected
        ok, msg, _ = self.pairing_mgr.verify_code(sess.id, "123456", user_id=self.user_id)
        self.assertFalse(ok)
        self.assertTrue("failed" in msg.lower() or "cheklovidan oshdi" in msg.lower())

    def test_21_pairing_expired_code_fails(self):
        """Scenario 21: Pairing session with expired TTL is rejected."""
        sess, raw_code = self.pairing_mgr.start_pairing(self.user_id, ttl_seconds=-10)
        self.assertTrue(sess.is_expired)
        ok, msg, _ = self.pairing_mgr.verify_code(sess.id, raw_code, user_id=self.user_id)
        self.assertFalse(ok)
        self.assertIn("tugagan", msg.lower())

    def test_22_pairing_single_use_replay_prevention(self):
        """Scenario 22: Once consumed, pairing code cannot be replayed."""
        sess, raw_code = self.pairing_mgr.start_pairing(self.user_id)
        ok1, _, _ = self.pairing_mgr.complete_pairing(sess.id, raw_code, "agent-pc-1", user_id=self.user_id)
        self.assertTrue(ok1)

        # Replay attempt with same code
        ok2, msg2, _ = self.pairing_mgr.complete_pairing(sess.id, raw_code, "agent-pc-2", user_id=self.user_id)
        self.assertFalse(ok2)
        self.assertIn("allaqachon", msg2.lower())

    def test_23_pairing_cancellation_by_owner(self):
        """Scenario 23: Owner can cancel pending pairing session."""
        req_start = MockRequest(
            method="POST",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        resp_start = asyncio.run(handle_device_pairing_start(req_start))
        pairing_id = json.loads(resp_start.text)["pairing_id"]

        req_cancel = MockRequest(
            method="POST",
            headers={"Authorization": f"Bearer {self.token}"},
            match_info={"pairing_id": pairing_id}
        )
        resp_cancel = asyncio.run(handle_device_pairing_cancel(req_cancel))
        self.assertEqual(resp_cancel.status, 200)

        sess = self.pairing_mgr.get_session(pairing_id)
        self.assertEqual(sess.status, "REVOKED")


# =====================================================================
# 5. OAUTH FLOW & SESSION ISOLATION
# =====================================================================

class TestSecurityOAuthFlow(BaseSecurityAuditTest):
    """Scenarios 24-28: State-bound OAuth session storage, single-use, concurrent isolation."""

    def test_24_oauth_state_bound_save_and_retrieve(self):
        """Scenario 24: Valid OAuth session saved with cryptographic state and retrieved once."""
        state = "state-crypto-abc-123"

        # Save session (matching frontend payload structure)
        req_save = MockRequest(
            method="POST",
            body={
                "access_token": "sb-token-oauth-111",
                "user": {"id": "user-uuid-oauth", "email": "oauth@mikasa.ai"},
                "state": state
            }
        )
        resp_save = asyncio.run(handle_oauth_session_save(req_save))
        self.assertEqual(resp_save.status, 200)

        # Retrieve session with state
        req_get = MockRequest(
            method="GET",
            query={"state": state}
        )
        resp_get = asyncio.run(handle_oauth_session_get(req_get))
        self.assertEqual(resp_get.status, 200)
        data = json.loads(resp_get.text)
        self.assertTrue(data["ok"])
        self.assertEqual(data["session"]["access_token"], "sb-token-oauth-111")

    def test_25_oauth_single_use_consumption_pop(self):
        """Scenario 25: OAuth session is consumed via pop() on first read; second read returns 404."""
        state = "state-single-use-999"

        req_save = MockRequest(method="POST", body={"access_token": "token-only-once", "state": state})
        asyncio.run(handle_oauth_session_save(req_save))

        # 1st get -> 200 OK
        req_get1 = MockRequest(method="GET", query={"state": state})
        resp1 = asyncio.run(handle_oauth_session_get(req_get1))
        self.assertEqual(resp1.status, 200)

        # 2nd get -> 404 Not Found (consumed)
        req_get2 = MockRequest(method="GET", query={"state": state})
        resp2 = asyncio.run(handle_oauth_session_get(req_get2))
        self.assertEqual(resp2.status, 404)

    def test_26_oauth_expired_state_returns_404(self):
        """Scenario 26: OAuth session with expired TTL returns 404."""
        state = "state-expired-555"
        # Manually insert expired entry into pending sessions
        with _pending_oauth_lock:
            _pending_oauth_sessions[state] = (time.time() - 10.0, {"access_token": "expired-token"})

        req_get = MockRequest(method="GET", query={"state": state})
        resp = asyncio.run(handle_oauth_session_get(req_get))
        self.assertEqual(resp.status, 404)

    def test_27_oauth_concurrent_states_isolation(self):
        """Scenario 27: User A state and User B state coexist without collision or cross-contamination."""
        state_a = "state-user-alice-001"
        state_b = "state-user-bob-002"

        session_a = {"user": "alice", "access_token": "token-alice", "state": state_a}
        session_b = {"user": "bob", "access_token": "token-bob", "state": state_b}

        req_save_a = MockRequest(method="POST", body=session_a)
        req_save_b = MockRequest(method="POST", body=session_b)

        asyncio.run(handle_oauth_session_save(req_save_a))
        asyncio.run(handle_oauth_session_save(req_save_b))

        # Retrieve B first
        req_b = MockRequest(method="GET", query={"state": state_b})
        resp_b = asyncio.run(handle_oauth_session_get(req_b))
        self.assertEqual(resp_b.status, 200)
        self.assertEqual(json.loads(resp_b.text)["session"]["user"], "bob")

        # Alice's session remains intact
        req_a = MockRequest(method="GET", query={"state": state_a})
        resp_a = asyncio.run(handle_oauth_session_get(req_a))
        self.assertEqual(resp_a.status, 200)
        self.assertEqual(json.loads(resp_a.text)["session"]["user"], "alice")

    def test_28_oauth_unknown_state_returns_404(self):
        """Scenario 28: Non-existent state returns 404 Not Found."""
        req_get = MockRequest(method="GET", query={"state": "completely-random-state-xyz"})
        resp = asyncio.run(handle_oauth_session_get(req_get))
        self.assertEqual(resp.status, 404)


# =====================================================================
# 6. REMOTE CONTROL & PERMISSION SCOPING
# =====================================================================

class TestSecurityRemotePermissions(BaseSecurityAuditTest):
    """Scenarios 29-30: Scoped permissions, user profile isolation."""

    def test_29_remote_permissions_scoped_to_user(self):
        """Scenario 29: Updating permissions applies strictly to authenticated user profile."""
        user_id = "user-uuid-alice"
        token = self.create_token(user_id=user_id)
        dev_id = "target-pc-01"

        req_put = MockRequest(
            method="PUT",
            headers={"Authorization": f"Bearer {token}"},
            match_info={"device_id": dev_id},
            body={
                "permissions": {"filesystem": False, "process": True}
            }
        )
        resp_put = asyncio.run(handle_remote_permissions_put(req_put))
        self.assertEqual(resp_put.status, 200)

        # Get permissions
        req_get = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {token}"},
            match_info={"device_id": dev_id}
        )
        resp_get = asyncio.run(handle_remote_permissions_get(req_get))
        self.assertEqual(resp_get.status, 200)
        data = json.loads(resp_get.text)
        self.assertEqual(data["profile"]["permissions"]["filesystem"], False)
        self.assertEqual(data["profile"]["permissions"]["process"], True)

    def test_30_remote_permissions_isolated_between_users(self):
        """Scenario 30: User B querying same device ID does not see User A's updated permissions."""
        dev_id = "shared-hw-pc"
        user_a_id = "user-uuid-alice"
        user_b_id = "user-uuid-bob"

        # Alice configures custom permissions
        self.perm_store.update_permissions(user_a_id, dev_id, {"system_control": False})

        # Bob gets his own profile
        token_b = self.create_token(user_id=user_b_id)
        req_b = MockRequest(
            method="GET",
            headers={"Authorization": f"Bearer {token_b}"},
            match_info={"device_id": dev_id}
        )
        resp_b = asyncio.run(handle_remote_permissions_get(req_b))
        self.assertEqual(resp_b.status, 200)
        data_b = json.loads(resp_b.text)
        # Bob's profile should have default permissions (True), not Alice's False setting
        self.assertTrue(data_b["profile"]["permissions"].get("system_control", True))


# =====================================================================
# 7. STATIC REPOSITORY AUDIT & SECRET SCAN
# =====================================================================

class TestSecurityStaticAudit(unittest.TestCase):
    """Scenarios 31-33: Source code secret scan, AST evaluation, and zero fallback secrets."""

    def test_31_no_default_test_secret_in_codebase(self):
        """Scenario 31: Default test secret pattern must NOT exist anywhere in source code."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        forbidden = "-".join(["mikasa", "default", "test", "secret"])

        checked_extensions = (".py", ".ts", ".tsx", ".js", ".json", ".sql", ".env.example")
        violations = []

        for root, dirs, files in os.walk(base_dir):
            if any(p in root for p in [".git", "node_modules", ".venv", "__pycache__", "dist", "build"]):
                continue
            for fname in files:
                if fname.endswith(checked_extensions):
                    # Skip test_v8_security_audit.py itself
                    if fname == "test_v8_security_audit.py":
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            if forbidden in content:
                                violations.append(fpath)
                    except Exception:
                        pass

        self.assertEqual(
            len(violations), 0,
            f"FORBIDDEN test secret found in files: {violations}"
        )

    def test_32_ast_scan_no_eval_or_exec_in_core_auth(self):
        """Scenario 32: AST scan verifies no eval() or exec() in core/v8/account_auth.py."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        target_file = os.path.join(base_dir, "core", "v8", "account_auth.py")

        with open(target_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=target_file)

        eval_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                    eval_calls.append((func.id, node.lineno))

        self.assertEqual(len(eval_calls), 0, f"Dangerous eval/exec found: {eval_calls}")

    def test_33_no_plain_passwords_in_config(self):
        """Scenario 33: data/config.json has no plaintext API key or credential."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(base_dir, "data", "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            gemini_key = cfg.get("ai", {}).get("gemini_api_key", "")
            self.assertFalse(
                gemini_key.startswith("AIzaSy"),
                "Unsanitized Gemini API key found in data/config.json"
            )


if __name__ == "__main__":
    unittest.main()
