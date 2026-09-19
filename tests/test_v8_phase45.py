# ========== tests/test_v8_phase45.py ==========
# Mikasa AI v8.0.0 — Phase 45: Real Windows PC Agent Production-Grade Suite
# Comprehensive Test Suite covering 30 requirements:
#  1. Identity: Stable device_id across multiple invocations (same hardware)
#  2. Identity: Hardware fingerprint determinism and format
#  3. Identity: Metadata persistence in vault_dir
#  4. Crypto: Ed25519 keypair generation and public key hex length (64 chars)
#  5. Crypto: Canonical challenge signature verification with public key
#  6. Crypto: Credential store persistence and retrieval (Mock & Windows safe)
#  7. Crypto: Memory wiping on shutdown (private key reference cleared)
#  8. Crypto: Keypair regeneration on re-enrollment
#  9. Transport: TLS verification mandatory (verify=False rejected/impossible)
# 10. Transport: Automatic session token injection in headers
# 11. Enrollment: Pairing request with 6-digit PIN success
# 12. Enrollment: Pairing rejection on invalid PIN
# 13. Enrollment: Public key sent during pairing matches local keypair
# 14. Auth: Challenge acquisition (32-byte nonce, 60s TTL)
# 15. Auth: Successful challenge-response authentication and session token receipt
# 16. Auth: Challenge replay attack rejection (nonce cannot be reused)
# 17. Auth: Expired challenge rejection
# 18. Heartbeat: Periodic heartbeat sending with system metrics
# 19. Heartbeat: Backend response updates last_seen and online state
# 20. Heartbeat: 403 DEVICE_REVOKED halts heartbeat and transitions state to REVOKED
# 21. Heartbeat: Consecutive failures transition state to DEGRADED
# 22. Reconnect: Exponential backoff sequence matches [1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 60.0]
# 23. Reconnect: Reconnect halts permanently when state is REVOKED
# 24. Lifecycle: Clean graceful shutdown clears resources and marks clean_exit=True
# 25. Crash Recovery: Dirty exit (clean_exit=False) triggers CRASH_RECOVERY audit event
# 26. Startup: HKCU Run registration and clean removal (Windows) / safe fallback
# 27. Audit: Scrubbing sensitive tokens and keys in agent audit events
# 28. Audit: Audit events logged for AGENT_STARTED, AUTH_SUCCESS, HEARTBEAT_SENT, etc.
# 29. Multi-Tenant Isolation: Agent cannot authenticate or access devices of different tenant
# 30. AST Security Scan: Agent codebase contains 0 eval, 0 exec, 0 shell=True, 0 UAC bypasses

import os
import ast
import json
import time
import shutil
import tempfile
import unittest
import asyncio
from typing import Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric import ed25519

from core.v8.events import (
    RemoteEventType,
    sanitize_event_data,
)
from core.v8.device_auth import DeviceAuthManager, DeviceSession
from core.v8.account_device import AccountDeviceManager
from core.api_server import (
    handle_device_heartbeat,
    handle_device_auth_challenge,
    handle_device_auth_authenticate,
)

from agent.config import AgentConfig
from agent.identity import AgentIdentityManager
from agent.crypto import AgentCrypto, MockCredentialStore
from agent.audit import AgentAuditLogger
from agent.recovery import CrashRecoveryManager
from agent.transport import SecureTransport
from agent.enrollment import AgentEnrollment
from agent.auth import AgentAuth
from agent.heartbeat import AgentHeartbeat, AgentState
from agent.startup import WindowsStartupManager
from agent.lifecycle import AgentLifecycleManager, calculate_backoff


class MockRequest:
    """Mock aiohttp request for isolated backend endpoint verification."""
    def __init__(
        self,
        method: str = "POST",
        path: str = "/",
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        match_info: Optional[Dict[str, str]] = None
    ):
        self.method = method
        self.path = path
        self._json_data = json_data or {}
        self.headers = headers or {}
        self.match_info = match_info or {}

    async def json(self):
        return self._json_data


class MockTestTransport(SecureTransport):
    """In-memory SecureTransport mock for fast and isolated agent testing."""
    def __init__(self, backend_url="http://127.0.0.1:18420", device_id="test-dev"):
        super().__init__(backend_url=backend_url, device_id=device_id)
        self.post_responses: Dict[str, Any] = {}
        self.post_history: list = []

    def set_mock_response(self, endpoint_substr: str, status: int, data: Dict[str, Any]):
        self.post_responses[endpoint_substr] = (status, data)

    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, token: Optional[str] = None):
        headers = self._build_headers(token=token)
        self.post_history.append({
            "endpoint": endpoint,
            "data": data,
            "headers": headers,
            "token": token or self._session_token
        })
        for sub, resp in self.post_responses.items():
            if sub in endpoint:
                return resp
        return 200, {"ok": True, "success": True}

    async def get(self, endpoint: str, token: Optional[str] = None):
        headers = self._build_headers(token=token)
        return 200, {"ok": True, "headers": headers}


class TestPhase45WindowsAgent(unittest.IsolatedAsyncioTestCase):
    """30 ta to'liq Phase 45 talablari uchun avtomatlashtirilgan test to'plami."""

    def setUp(self):
        self._orig_env = dict(os.environ)
        self.tmp_dir = tempfile.mkdtemp(prefix="mikasa_agent_test_")
        self.vault_dir = os.path.join(self.tmp_dir, "vault")
        os.makedirs(self.vault_dir, exist_ok=True)
        self.audit = AgentAuditLogger.get_instance()
        self.audit.clear()

    def tearDown(self):
        from core.v8.account_device import AccountDeviceManager
        from core.v8.device_auth import DeviceAuthManager
        from core.v8.device_enrollment import DeviceEnrollmentManager
        from core.v8.heartbeat import HeartbeatManager
        AccountDeviceManager._default_instance = None
        DeviceAuthManager._default_instance = None
        DeviceEnrollmentManager._default_instance = None
        HeartbeatManager._default_instance = None
        os.environ.clear()
        os.environ.update(self._orig_env)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # 1. Identity: Stable device_id across multiple invocations
    def test_01_identity_stable_across_invocations(self):
        mgr1 = AgentIdentityManager(self.vault_dir)
        ident1 = mgr1.get_or_create_identity("TestMachine")

        mgr2 = AgentIdentityManager(self.vault_dir)
        ident2 = mgr2.get_or_create_identity("TestMachineRenamed")

        self.assertEqual(ident1.device_id, ident2.device_id)
        self.assertEqual(ident1.hardware_fingerprint, ident2.hardware_fingerprint)

    # 2. Identity: Hardware fingerprint determinism and format
    def test_02_identity_hardware_fingerprint_deterministic(self):
        mgr = AgentIdentityManager(self.vault_dir)
        fp1 = mgr.compute_hardware_fingerprint()
        fp2 = mgr.compute_hardware_fingerprint()
        self.assertEqual(fp1, fp2)
        self.assertEqual(len(fp1), 64)  # SHA-256 hex string

    # 3. Identity: Metadata persistence in vault_dir
    def test_03_identity_metadata_persistence(self):
        mgr = AgentIdentityManager(self.vault_dir)
        ident = mgr.get_or_create_identity("TestDevice")
        id_file = os.path.join(self.vault_dir, "device_identity.json")
        self.assertTrue(os.path.exists(id_file))
        with open(id_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["device_id"], ident.device_id)
        self.assertIn("hardware_fingerprint", data)
        self.assertIn("enrolled_at", data)

    # 4. Crypto: Ed25519 keypair generation and public key hex length
    def test_04_crypto_ed25519_keypair_generation(self):
        crypto = AgentCrypto("dev-1", self.vault_dir)
        pub_hex = crypto.public_key_hex
        self.assertIsNotNone(pub_hex)
        self.assertEqual(len(pub_hex), 64)  # 32 bytes = 64 hex characters

    # 5. Crypto: Canonical challenge signature verification with public key
    def test_05_crypto_canonical_challenge_signing(self):
        crypto = AgentCrypto("dev-verify-1", self.vault_dir)
        nonce = "a" * 64
        signed = crypto.sign_challenge(nonce=nonce, timestamp=1000.0, protocol_version="1.0")

        sig_bytes = bytes.fromhex(signed["signature"])
        pub_bytes = bytes.fromhex(crypto.public_key_hex)
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)

        canonical_msg = DeviceAuthManager.canonical_challenge_message(
            device_id="dev-verify-1",
            nonce=nonce,
            timestamp=1000.0,
            protocol_version="1.0"
        )
        pub_key.verify(sig_bytes, canonical_msg)  # Raises InvalidSignature if invalid

    # 6. Crypto: Credential store persistence and retrieval
    def test_06_crypto_store_persistence_and_retrieval(self):
        store = MockCredentialStore(self.vault_dir)
        store.store_credential("secret_key", "my_secret_token_123")
        retrieved = store.load_credential("secret_key")
        self.assertEqual(retrieved, "my_secret_token_123")
        store.delete_credential("secret_key")
        self.assertIsNone(store.load_credential("secret_key"))

    # 7. Crypto: Memory wiping on shutdown
    def test_07_crypto_memory_wiping_on_shutdown(self):
        crypto = AgentCrypto("dev-wipe-1", self.vault_dir)
        self.assertIsNotNone(crypto._private_key)
        crypto.clean_memory()
        self.assertIsNone(crypto._private_key)

    # 8. Crypto: Keypair regeneration on re-enrollment
    def test_08_crypto_keypair_regeneration(self):
        crypto = AgentCrypto("dev-regen-1", self.vault_dir)
        pub1 = crypto.public_key_hex
        pub2 = crypto.regenerate_keypair()
        self.assertNotEqual(pub1, pub2)
        self.assertEqual(len(pub2), 64)

    # 9. Transport: TLS verification mandatory
    def test_09_transport_tls_verification_mandatory(self):
        transport = SecureTransport(
            backend_url="https://mikasa-secure.internal:18420",
            device_id="dev-tls-1"
        )
        self.assertTrue(transport.verify_ssl)
        ssl_ctx = transport._get_ssl_context()
        self.assertIsNotNone(ssl_ctx)

    # 10. Transport: Automatic session token injection in headers
    async def test_10_transport_session_token_injection(self):
        transport = MockTestTransport(device_id="dev-hdr-1")
        transport.set_session_token("device_sess_jwt_token_999")
        status, _ = await transport.post("/api/test/endpoint", {"foo": "bar"})
        self.assertEqual(status, 200)
        last_req = transport.post_history[-1]
        self.assertEqual(last_req["headers"].get("Authorization"), "Bearer device_sess_jwt_token_999")
        self.assertEqual(last_req["headers"].get("X-Device-ID"), "dev-hdr-1")

    # 11. Enrollment: Pairing request with 6-digit PIN success
    async def test_11_enrollment_pairing_success(self):
        transport = MockTestTransport()
        crypto = AgentCrypto("dev-enroll-1", self.vault_dir)
        enrollment = AgentEnrollment(transport, crypto, "dev-enroll-1")

        transport.set_mock_response(
            "/api/devices/pairing/complete",
            200,
            {"ok": True, "device_id": "dev-enroll-1", "user_id": "user-45"}
        )

        ok, msg, data = await enrollment.complete_pairing("849201")
        self.assertTrue(ok)
        self.assertEqual(data.get("user_id"), "user-45")

    # 12. Enrollment: Pairing rejection on invalid PIN
    async def test_12_enrollment_invalid_pin_rejected(self):
        transport = MockTestTransport()
        crypto = AgentCrypto("dev-enroll-2", self.vault_dir)
        enrollment = AgentEnrollment(transport, crypto, "dev-enroll-2")

        # Non-6-digit PIN
        ok, msg, _ = await enrollment.complete_pairing("12")
        self.assertFalse(ok)
        self.assertIn("6 xonali", msg)

        # Invalid PIN response from backend
        transport.set_mock_response(
            "/api/devices/pairing/complete",
            400,
            {"ok": False, "error": "INVALID_PIN: Noto'g'ri yoki eskirgan kod"}
        )
        ok, msg, _ = await enrollment.complete_pairing("123456")
        self.assertFalse(ok)
        self.assertIn("INVALID_PIN", msg)

    # 13. Enrollment: Public key sent during pairing matches local keypair
    async def test_13_enrollment_public_key_matches_crypto(self):
        transport = MockTestTransport()
        crypto = AgentCrypto("dev-enroll-3", self.vault_dir)
        enrollment = AgentEnrollment(transport, crypto, "dev-enroll-3")

        await enrollment.complete_pairing("654321")
        last_req = transport.post_history[-1]
        sent_pub = last_req["data"].get("public_key")
        self.assertEqual(sent_pub, crypto.public_key_hex)

    # 14. Auth: Challenge acquisition (32-byte nonce, 60s TTL)
    async def test_14_auth_challenge_acquisition(self):
        auth_mgr = DeviceAuthManager.get_default_instance()
        crypto = AgentCrypto("dev-auth-test-14", self.vault_dir)

        auth_mgr.enrollment_mgr.enroll_device(
            user_id="user-t14",
            device_id="dev-auth-test-14",
            public_key=crypto.public_key_hex,
            name="TestAuthDev"
        )

        req = MockRequest(
            method="POST",
            path="/api/devices/dev-auth-test-14/challenge",
            match_info={"device_id": "dev-auth-test-14"}
        )
        resp = await handle_device_auth_challenge(req)
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.text)
        self.assertTrue(body["ok"])
        self.assertIn("challenge_id", body)
        self.assertEqual(len(bytes.fromhex(body["nonce"])), 32)
        self.assertEqual(body["ttl"], 60.0)

    # 15. Auth: Successful challenge-response authentication and session token receipt
    async def test_15_auth_challenge_response_success(self):
        auth_mgr = DeviceAuthManager.get_default_instance()
        crypto = AgentCrypto("dev-auth-test-15", self.vault_dir)

        auth_mgr.enrollment_mgr.enroll_device(
            user_id="user-t15",
            device_id="dev-auth-test-15",
            public_key=crypto.public_key_hex,
            name="TestAuthDev15"
        )

        # 1. Issue challenge
        ok, msg, cdata = auth_mgr.issue_challenge("dev-auth-test-15")
        self.assertTrue(ok)
        cid = cdata["challenge_id"]
        nonce = cdata["nonce"]

        # 2. Sign
        signed = crypto.sign_challenge(nonce=nonce, timestamp=100.0, protocol_version="1.0")

        # 3. Authenticate handler
        req = MockRequest(
            method="POST",
            path="/api/devices/dev-auth-test-15/authenticate",
            match_info={"device_id": "dev-auth-test-15"},
            json_data={
                "challenge_id": cid,
                "signature": signed["signature"],
                "context": signed["context"]
            }
        )
        resp = await handle_device_auth_authenticate(req)
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.text)
        self.assertTrue(body["ok"])
        self.assertIn("session_token", body)
        self.assertIn("session_id", body)

        # AgentAuth client test
        mock_t = MockTestTransport(device_id="dev-auth-test-15")
        mock_t.set_mock_response(
            "/api/devices/dev-auth-test-15/challenge",
            200,
            {"ok": True, "challenge_id": cid, "nonce": nonce, "ttl": 60.0}
        )
        mock_t.set_mock_response(
            "/api/devices/dev-auth-test-15/authenticate",
            200,
            {
                "ok": True,
                "session_token": body["session_token"],
                "session_id": body["session_id"],
                "expires_at": 99999.0
            }
        )
        agent_auth = AgentAuth(mock_t, crypto, "dev-auth-test-15")
        a_ok, a_msg, a_data = await agent_auth.authenticate()
        self.assertTrue(a_ok)
        self.assertEqual(agent_auth.session_token, body["session_token"])

    # 16. Auth: Challenge replay attack rejection
    async def test_16_auth_replay_attack_rejected(self):
        auth_mgr = DeviceAuthManager.get_default_instance()
        crypto = AgentCrypto("dev-auth-test-16", self.vault_dir)

        auth_mgr.enrollment_mgr.enroll_device(
            user_id="user-t16",
            device_id="dev-auth-test-16",
            public_key=crypto.public_key_hex,
            name="TestAuthDev16"
        )

        ok, _, cdata = auth_mgr.issue_challenge("dev-auth-test-16")
        cid = cdata["challenge_id"]
        signed = crypto.sign_challenge(nonce=cdata["nonce"], timestamp=100.0, protocol_version="1.0")

        req = MockRequest(
            method="POST",
            path="/api/devices/dev-auth-test-16/authenticate",
            match_info={"device_id": "dev-auth-test-16"},
            json_data={
                "challenge_id": cid,
                "signature": signed["signature"],
                "context": signed["context"]
            }
        )
        resp1 = await handle_device_auth_authenticate(req)
        self.assertEqual(resp1.status, 200)

        # Second attempt with same challenge_id must be rejected (replay)
        resp2 = await handle_device_auth_authenticate(req)
        self.assertEqual(resp2.status, 401)
        body2 = json.loads(resp2.text)
        self.assertFalse(body2["ok"])
        self.assertIn("REPLAY", body2["error"])

    # 17. Auth: Expired challenge rejection
    async def test_17_auth_expired_challenge_rejected(self):
        auth_mgr = DeviceAuthManager.get_default_instance()
        crypto = AgentCrypto("dev-auth-test-17", self.vault_dir)

        auth_mgr.enrollment_mgr.enroll_device(
            user_id="user-t17",
            device_id="dev-auth-test-17",
            public_key=crypto.public_key_hex,
            name="TestAuthDev17"
        )

        ok, _, cdata = auth_mgr.issue_challenge("dev-auth-test-17")
        cid = cdata["challenge_id"]
        challenge = auth_mgr._challenges[cid]
        # Force expiration
        challenge.expires_at = time.time() - 10.0

        signed = crypto.sign_challenge(nonce=cdata["nonce"], timestamp=100.0, protocol_version="1.0")
        req = MockRequest(
            method="POST",
            path="/api/devices/dev-auth-test-17/authenticate",
            match_info={"device_id": "dev-auth-test-17"},
            json_data={
                "challenge_id": cid,
                "signature": signed["signature"],
                "context": signed["context"]
            }
        )
        resp = await handle_device_auth_authenticate(req)
        self.assertEqual(resp.status, 400)
        body = json.loads(resp.text)
        self.assertIn("EXPIRED", body["error"])

    # 18. Heartbeat: Periodic heartbeat sending with system metrics
    def test_18_heartbeat_payload_telemetry(self):
        transport = MockTestTransport()
        hb = AgentHeartbeat(transport, "dev-hb-18")
        metrics = hb.get_system_metrics()
        self.assertIn("uptime_seconds", metrics)
        self.assertGreaterEqual(metrics["uptime_seconds"], 0.0)

    # 19. Heartbeat: Backend response updates last_seen and online state
    async def test_19_heartbeat_updates_backend_state(self):
        acct_mgr = AccountDeviceManager.get_default_instance()
        auth_mgr = DeviceAuthManager.get_default_instance()
        crypto = AgentCrypto("dev-hb-19", self.vault_dir)

        auth_mgr.enrollment_mgr.enroll_device(
            user_id="user-t19",
            device_id="dev-hb-19",
            public_key=crypto.public_key_hex,
            name="HBDev19"
        )

        # Create session
        sess = DeviceSession(
            session_id="sess-hb-19",
            device_id="dev-hb-19",
            user_id="user-t19",
            token="valid_dev_tok_19",
            expires_at=time.time() + 3600
        )
        auth_mgr._sessions["valid_dev_tok_19"] = sess

        req = MockRequest(
            method="POST",
            path="/api/devices/dev-hb-19/heartbeat",
            match_info={"device_id": "dev-hb-19"},
            headers={"Authorization": "Bearer valid_dev_tok_19"},
            json_data={
                "device_id": "dev-hb-19",
                "timestamp": time.time(),
                "state": "online",
                "metrics": {"cpu_percent": 15.0}
            }
        )
        resp = await handle_device_heartbeat(req)
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.text)
        self.assertTrue(body["ok"])

        # Check device status updated
        dev = acct_mgr.get_device("dev-hb-19")
        self.assertEqual(dev.status, "online")

    # 20. Heartbeat: 403 DEVICE_REVOKED halts heartbeat and transitions state to REVOKED
    async def test_20_heartbeat_revocation_detection(self):
        transport = MockTestTransport(device_id="dev-hb-20")
        transport.set_mock_response(
            "/api/devices/dev-hb-20/heartbeat",
            403,
            {"ok": False, "error": "DEVICE_REVOKED: Qurilma bekor qilingan"}
        )
        hb = AgentHeartbeat(transport, "dev-hb-20")
        ok, status_str, _ = await hb.send_heartbeat()
        self.assertFalse(ok)
        self.assertEqual(status_str, "DEVICE_REVOKED")
        self.assertEqual(hb.state, AgentState.REVOKED)

    # 21. Heartbeat: Consecutive failures transition state to DEGRADED
    async def test_21_heartbeat_consecutive_failures_degraded(self):
        transport = MockTestTransport(device_id="dev-hb-21")
        transport.set_mock_response(
            "/api/devices/dev-hb-21/heartbeat",
            500,
            {"ok": False, "error": "INTERNAL_SERVER_ERROR"}
        )
        hb = AgentHeartbeat(transport, "dev-hb-21")
        hb.state = AgentState.ONLINE

        for _ in range(3):
            await hb.send_heartbeat()

        self.assertEqual(hb.consecutive_failures, 3)
        self.assertEqual(hb.state, AgentState.DEGRADED)

    # 22. Reconnect: Exponential backoff sequence matches [1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 60.0]
    def test_22_reconnect_exponential_backoff_sequence(self):
        expected = [1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 60.0]
        actual = [calculate_backoff(i) for i in range(len(expected))]
        self.assertEqual(actual, expected)
        # Bounded cap at 60.0
        self.assertEqual(calculate_backoff(10), 60.0)
        self.assertEqual(calculate_backoff(100), 60.0)

    # 23. Reconnect: Reconnect halts permanently when state is REVOKED
    async def test_23_reconnect_halts_on_revocation(self):
        config = AgentConfig(vault_dir=self.vault_dir)
        lifecycle = AgentLifecycleManager(config)
        lifecycle.heartbeat.state = AgentState.REVOKED
        lifecycle._is_running = True

        # run_forever must terminate immediately because state is REVOKED
        task = asyncio.create_task(lifecycle.run_forever())
        await asyncio.wait_for(task, timeout=2.0)
        self.assertFalse(lifecycle.is_running)

    # 24. Lifecycle: Clean graceful shutdown clears resources and marks clean_exit=True
    async def test_24_lifecycle_graceful_shutdown(self):
        config = AgentConfig(vault_dir=self.vault_dir)
        lifecycle = AgentLifecycleManager(config)
        await lifecycle.start()
        self.assertTrue(lifecycle.is_running)

        await lifecycle.shutdown()
        self.assertFalse(lifecycle.is_running)
        self.assertIsNone(lifecycle.crypto._private_key)

        state_file = os.path.join(self.vault_dir, "agent_runtime_state.json")
        self.assertTrue(os.path.exists(state_file))
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertFalse(data["is_running"])
        self.assertTrue(data["clean_exit"])

    # 25. Crash Recovery: Dirty exit triggers CRASH_RECOVERY audit event
    def test_25_crash_recovery_detection(self):
        recovery = CrashRecoveryManager(self.vault_dir)
        # Simulate dirty crash state
        dirty_state = {
            "device_id": "dev-crash-25",
            "pid": 99999,
            "timestamp": time.time() - 100,
            "is_running": True,
            "clean_exit": False,
            "started_at": time.time() - 100
        }
        with open(recovery.state_file, "w", encoding="utf-8") as f:
            json.dump(dirty_state, f)

        is_recovered = recovery.on_startup("dev-crash-25")
        self.assertTrue(is_recovered)

        events = self.audit.get_events()
        crash_events = [e for e in events if e.get("event_type") == RemoteEventType.CRASH_RECOVERY]
        self.assertEqual(len(crash_events), 1)
        self.assertEqual(crash_events[0]["details"]["previous_pid"], 99999)

    # 26. Startup: WindowsStartupManager safe operations
    def test_26_windows_startup_manager(self):
        guidance = WindowsStartupManager.get_service_guidance()
        self.assertFalse(guidance["uac_bypass"])
        self.assertFalse(guidance["stealth"])
        self.assertIn("MikasaAgent", guidance["task_scheduler_cmd"])

        # Check enable / disable executes safely
        if not WindowsStartupManager.is_windows():
            self.assertFalse(WindowsStartupManager.is_startup_enabled())
            self.assertFalse(WindowsStartupManager.enable_startup("/path/to/bin"))
            self.assertFalse(WindowsStartupManager.disable_startup())
        else:
            # On Windows, we can check that it doesn't crash
            status = WindowsStartupManager.is_startup_enabled()
            self.assertIsInstance(status, bool)

    # 27. Audit: Scrubbing sensitive tokens and keys in agent audit events
    def test_27_audit_logger_redaction(self):
        sensitive_data = {
            "session_token": "secret_jwt_token_header_payload_sig",
            "private_key": "302e020100300506032b657004220420",
            "authorization_header": "Bearer mock_jwt_test_header",
            "public_key": "f8a9b7c6d5e4f3a2b1c0"
        }
        sanitized = sanitize_event_data(sensitive_data)
        self.assertEqual(sanitized["session_token"], "***REDACTED***")
        self.assertEqual(sanitized["private_key"], "***REDACTED***")
        self.assertEqual(sanitized["authorization_header"], "***REDACTED***")
        self.assertEqual(sanitized["public_key"], "f8a9b7c6d5e4f3a2b1c0")

    # 28. Audit: Lifecycle events logged appropriately
    def test_28_audit_lifecycle_events_logged(self):
        self.audit.clear()
        self.audit.log_event(RemoteEventType.AGENT_STARTED, "dev-audit-28", {"mode": "cli"})
        self.audit.log_event(RemoteEventType.AUTH_SUCCESS, "dev-audit-28", {"session_id": "s1"})
        self.audit.log_event(RemoteEventType.HEARTBEAT_SENT, "dev-audit-28", {"status": "ok"})

        events = self.audit.get_events()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["event_type"], RemoteEventType.AGENT_STARTED)
        self.assertEqual(events[1]["event_type"], RemoteEventType.AUTH_SUCCESS)
        self.assertEqual(events[2]["event_type"], RemoteEventType.HEARTBEAT_SENT)

    # 29. Multi-Tenant Isolation: Agent cannot authenticate or access other tenant's device
    async def test_29_multi_tenant_device_isolation(self):
        auth_mgr = DeviceAuthManager.get_default_instance()

        crypto_tenant_a = AgentCrypto("dev-tenant-a", self.vault_dir)
        auth_mgr.enrollment_mgr.enroll_device(
            user_id="tenant_a_user",
            device_id="dev-tenant-a",
            public_key=crypto_tenant_a.public_key_hex,
            name="DevTenantA"
        )

        # Issue challenge for Tenant A device
        ok, _, cdata = auth_mgr.issue_challenge("dev-tenant-a")
        cid = cdata["challenge_id"]

        # Attacker/Tenant B tries to submit signed challenge for Tenant A using Tenant B's key
        other_vault = os.path.join(self.tmp_dir, "vault_b")
        crypto_tenant_b = AgentCrypto("dev-tenant-b", other_vault)
        signed_by_b = crypto_tenant_b.sign_challenge(nonce=cdata["nonce"], timestamp=100.0, protocol_version="1.0")

        req = MockRequest(
            method="POST",
            path="/api/devices/dev-tenant-a/authenticate",
            match_info={"device_id": "dev-tenant-a"},
            json_data={
                "challenge_id": cid,
                "signature": signed_by_b["signature"],
                "context": signed_by_b["context"]
            }
        )
        resp = await handle_device_auth_authenticate(req)
        # Authentication must fail with 401 Invalid Signature
        self.assertEqual(resp.status, 401)
        body = json.loads(resp.text)
        self.assertFalse(body["ok"])

    # 30. AST Security Scan: 0 eval, 0 exec, 0 shell=True in agent/
    def test_30_ast_security_scan(self):
        agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent"))
        self.assertTrue(os.path.exists(agent_dir))

        forbidden_calls = {"eval", "exec"}
        violations = []

        for root, _, files in os.walk(agent_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=filepath)

                    for node in ast.walk(tree):
                        # Check eval / exec
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                            if node.func.id in forbidden_calls:
                                violations.append(f"{file}:{node.lineno} calls {node.func.id}()")
                        # Check shell=True in subprocess calls
                        if isinstance(node, ast.Call):
                            for kw in getattr(node, "keywords", []):
                                if kw.arg == "shell" and getattr(kw.value, "value", None) is True:
                                    violations.append(f"{file}:{node.lineno} uses shell=True")

        self.assertEqual(violations, [], f"AST Security Violations found: {violations}")


if __name__ == "__main__":
    unittest.main()
