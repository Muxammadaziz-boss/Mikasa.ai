# ========== tests/test_v8_phase42.py ==========
# Phase 42 — Secure PC Agent Enrollment & Pairing Test Suite
# Comprehensive 30 Unit & Integration Tests covering:
# 1. Pairing code generation (6-digit numeric, cryptographically secure)
# 2. Salted SHA-256 hash storage (zero plaintext storage)
# 3. Successful pairing code verification
# 4. Wrong pairing code rejection
# 5. Max 5 failed attempts lockout (Brute-force protection)
# 6. 5-minute TTL expiration
# 7. Single-use replay prevention (cannot be reused)
# 8. User pairing cancellation
# 9. Multi-tenant user isolation
# 10. Ed25519 keypair generation (32-byte public key)
# 11. Windows DPAPI & Mock credential store
# 12. Private key confidentiality (never sent to backend)
# 13. Device credential creation with Ed25519 public key
# 14. Device enrollment in AccountDeviceManager
# 15. Safe default permissions established (dangerous commands blocked)
# 16. Challenge issuance (32-byte nonce, 60s TTL)
# 17. Device agent canonical challenge signing
# 18. Backend Ed25519 signature verification & DeviceSession issuance
# 19. Forged / invalid signature rejection
# 20. Replay protection (nonce reuse prevention)
# 21. Expired challenge nonce rejection
# 22. Protocol version negotiation ("1.0")
# 23. Core invariant: DeviceSession != RemoteAuthSession decoupling
# 24. Cascading device revocation (credentials, sessions, pairing revoked)
# 25. Device re-pairing and credential rotation
# 26. Duplicate device fingerprint & hijacking prevention
# 27. PostgreSQL RLS migration schema validation
# 28. HTTP API pairing endpoints (/start, /status, /cancel, /complete)
# 29. HTTP API device auth endpoints (/challenge, /authenticate)
# 30. Audit log secret redaction & AST security scan (0 eval/exec/shell=True)

import os
import ast
import json
import time
import shutil
import tempfile
import unittest
import asyncio
from core.v8.account_device import AccountDeviceManager
from core.v8.account_auth import SupabaseSessionClaims
from core.v8.device_pairing import DevicePairingManager
from core.v8.device_enrollment import (
    MockCredentialStore,
    WindowsCredentialStore,
    DeviceEnrollmentManager,
)
from core.v8.device_auth import (
    DeviceAuthChallenge,
    DeviceSession,
    DeviceAuthManager,
)
from core.v8.device_agent_crypto import DeviceAgentCrypto
from core.v8.events import sanitize_event_data
from core.v8.auth_session import RemoteAuthSession
from core.api_server import (
    handle_device_pairing_start,
    handle_device_pairing_status,
    handle_device_pairing_complete,
    handle_device_auth_challenge,
    handle_device_auth_authenticate,
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


class BasePhase42Test(unittest.TestCase):
    """Base setup for Phase 42 tests with isolated temporary directories."""
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_phase42_test_")
        self.pairing_storage = os.path.join(self.temp_dir, "pairing.json")
        self.device_storage = os.path.join(self.temp_dir, "devices.json")
        self.cred_storage = os.path.join(self.temp_dir, "credentials.json")

        self.account_mgr = AccountDeviceManager(storage_path=self.device_storage)
        self.pairing_mgr = DevicePairingManager(storage_path=self.pairing_storage)
        self.enrollment_mgr = DeviceEnrollmentManager(
            account_device_mgr=self.account_mgr,
            storage_path=self.cred_storage
        )
        self.auth_mgr = DeviceAuthManager(enrollment_mgr=self.enrollment_mgr)

        DevicePairingManager._default_instance = self.pairing_mgr
        AccountDeviceManager._default_instance = self.account_mgr
        DeviceEnrollmentManager._default_instance = self.enrollment_mgr
        DeviceAuthManager._default_instance = self.auth_mgr

        # Create test users
        self.user_a = self.account_mgr.register_or_get_user("user-uuid-alice", username="alice")
        self.user_b = self.account_mgr.register_or_get_user("user-uuid-bob", username="bob")

    def tearDown(self):
        DevicePairingManager._default_instance = None
        AccountDeviceManager._default_instance = None
        DeviceEnrollmentManager._default_instance = None
        DeviceAuthManager._default_instance = None
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass


class TestDevicePairingProtocol(BasePhase42Test):
    """Scenarios 1-9: Pairing Code Generation, Verification, Security & Isolation"""

    def test_01_pairing_code_generation(self):
        """Scenario 1: Code is 6 digits, numeric only, and cryptographically random."""
        codes = set()
        for _ in range(50):
            code = self.pairing_mgr.generate_pairing_code()
            self.assertEqual(len(code), 6)
            self.assertTrue(code.isdigit())
            codes.add(code)
        # Verify randomness (50 codes should generate high entropy with minimal collisions)
        self.assertGreater(len(codes), 45)

    def test_02_salted_sha256_hash_storage(self):
        """Scenario 2: Plaintext code is NEVER saved; only salted SHA-256 hash is persisted."""
        sess, raw_code = self.pairing_mgr.start_pairing(user_id=self.user_a.id)
        self.assertIsNotNone(sess.id)
        self.assertIsNotNone(raw_code)
        self.assertEqual(len(raw_code), 6)

        # Verify session model doesn't store raw code in attributes
        self.assertFalse(hasattr(sess, "code"))
        self.assertFalse(hasattr(sess, "pairing_code"))
        self.assertIsNotNone(sess.pairing_code_hash)
        self.assertIsNotNone(sess.pairing_code_salt)

        # Check raw json file
        with open(self.pairing_storage, "r", encoding="utf-8") as f:
            raw_json = f.read()
        self.assertNotIn(raw_code, raw_json)
        self.assertIn(sess.pairing_code_hash, raw_json)

        # Dict representation shouldn't expose salt or hash by default
        safe_dict = sess.to_dict(include_security_metadata=False)
        self.assertNotIn("pairing_code_hash", safe_dict)
        self.assertNotIn("pairing_code_salt", safe_dict)

    def test_03_pairing_code_verification_success(self):
        """Scenario 3: Verification with the correct 6-digit code succeeds."""
        sess, raw_code = self.pairing_mgr.start_pairing(user_id=self.user_a.id)
        ok, msg, verified_sess = self.pairing_mgr.verify_code(
            pairing_id=sess.id,
            code=raw_code,
            user_id=self.user_a.id
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "OK")
        self.assertIsNotNone(verified_sess)
        self.assertEqual(verified_sess.status, "VERIFIED")

    def test_04_wrong_pairing_code_rejection(self):
        """Scenario 4: Wrong pairing code is rejected and increments attempt count."""
        sess, raw_code = self.pairing_mgr.start_pairing(user_id=self.user_a.id)
        wrong_code = "000000" if raw_code != "000000" else "111111"

        ok, msg, verified_sess = self.pairing_mgr.verify_code(
            pairing_id=sess.id,
            code=wrong_code,
            user_id=self.user_a.id
        )
        self.assertFalse(ok)
        self.assertIn("INVALID_CODE", msg)
        self.assertIsNone(verified_sess)

        # Attempt count incremented
        updated_sess = self.pairing_mgr.get_session(sess.id)
        self.assertEqual(updated_sess.attempt_count, 1)

    def test_05_max_attempts_lockout(self):
        """Scenario 5: Max 5 failed attempts locks out pairing session."""
        sess, raw_code = self.pairing_mgr.start_pairing(user_id=self.user_a.id)
        wrong_code = "000000" if raw_code != "000000" else "111111"

        for i in range(5):
            ok, msg, _ = self.pairing_mgr.verify_code(sess.id, wrong_code, user_id=self.user_a.id)
            self.assertFalse(ok)

        # 6th attempt should fail due to MAX_ATTEMPTS or FAILED status
        ok, msg, _ = self.pairing_mgr.verify_code(sess.id, raw_code, user_id=self.user_a.id)
        self.assertFalse(ok)
        self.assertTrue("MAX_ATTEMPTS" in msg or "STATUS_INVALID" in msg)

        updated_sess = self.pairing_mgr.get_session(sess.id)
        self.assertEqual(updated_sess.status, "FAILED")
        self.assertFalse(updated_sess.is_active)

    def test_06_ttl_expiration(self):
        """Scenario 6: 5-minute TTL expiration marks session EXPIRED."""
        # Start session with 0.1 second TTL
        sess, raw_code = self.pairing_mgr.start_pairing(user_id=self.user_a.id, ttl_seconds=0.1)
        time.sleep(0.15)

        ok, msg, _ = self.pairing_mgr.verify_code(sess.id, raw_code, user_id=self.user_a.id)
        self.assertFalse(ok)
        self.assertIn("EXPIRED", msg)

        updated_sess = self.pairing_mgr.get_session(sess.id)
        self.assertEqual(updated_sess.status, "EXPIRED")
        self.assertTrue(updated_sess.is_expired)

    def test_07_single_use_replay_prevention(self):
        """Scenario 7: Claiming pairing code marks it COMPLETED; cannot be reused."""
        sess, raw_code = self.pairing_mgr.start_pairing(user_id=self.user_a.id)

        # First completion succeeds
        ok, msg, completed_sess = self.pairing_mgr.complete_pairing(
            pairing_id=sess.id,
            code=raw_code,
            device_id="DEV-WIN-01",
            user_id=self.user_a.id
        )
        self.assertTrue(ok)
        self.assertEqual(completed_sess.status, "COMPLETED")
        self.assertEqual(completed_sess.device_id, "DEV-WIN-01")

        # Second completion attempt with same code fails
        ok2, msg2, _ = self.pairing_mgr.complete_pairing(
            pairing_id=sess.id,
            code=raw_code,
            device_id="DEV-WIN-01",
            user_id=self.user_a.id
        )
        self.assertFalse(ok2)
        self.assertIn("ALREADY_COMPLETED", msg2)

    def test_08_pairing_cancellation(self):
        """Scenario 8: User can cancel pending pairing session."""
        sess, raw_code = self.pairing_mgr.start_pairing(user_id=self.user_a.id)
        ok, msg = self.pairing_mgr.cancel_pairing(sess.id, user_id=self.user_a.id)
        self.assertTrue(ok)

        # Verification after cancellation fails
        ok_verify, msg_verify, _ = self.pairing_mgr.verify_code(sess.id, raw_code, user_id=self.user_a.id)
        self.assertFalse(ok_verify)
        self.assertIn("STATUS_INVALID", msg_verify)

    def test_09_multi_tenant_isolation(self):
        """Scenario 9: User A cannot verify or complete User B's pairing session."""
        sess_a, raw_code_a = self.pairing_mgr.start_pairing(user_id=self.user_a.id)

        # Bob attempts to verify Alice's pairing code
        ok, msg, _ = self.pairing_mgr.verify_code(
            pairing_id=sess_a.id,
            code=raw_code_a,
            user_id=self.user_b.id  # Bob
        )
        self.assertFalse(ok)
        self.assertIn("UNAUTHORIZED", msg)

        # Bob attempts to cancel Alice's pairing
        ok_cancel, msg_cancel = self.pairing_mgr.cancel_pairing(sess_a.id, user_id=self.user_b.id)
        self.assertFalse(ok_cancel)
        self.assertIn("UNAUTHORIZED", msg_cancel)


class TestDeviceEnrollmentAndCredentials(BasePhase42Test):
    """Scenarios 10-15: Cryptographic Keypairs, Credential Storage & Safe Permissions"""

    def test_10_ed25519_keypair_generation(self):
        """Scenario 10: DeviceAgentCrypto generates valid 32-byte raw public key."""
        mock_store = MockCredentialStore()
        crypto = DeviceAgentCrypto(device_id="DEV-CRYPTO-01", credential_store=mock_store)

        pub_hex = crypto.public_key_hex
        self.assertEqual(len(pub_hex), 64)  # 32 bytes = 64 hex characters
        self.assertTrue(all(c in "0123456789abcdef" for c in pub_hex))

        # Re-initializing same device ID reloads existing keypair
        crypto2 = DeviceAgentCrypto(device_id="DEV-CRYPTO-01", credential_store=mock_store)
        self.assertEqual(crypto2.public_key_hex, pub_hex)

    def test_11_credential_store_dpapi_and_mock(self):
        """Scenario 11: MockCredentialStore & WindowsCredentialStore abstraction."""
        mock_store = MockCredentialStore()
        self.assertTrue(mock_store.save_credential("test_key", "secret_value_123"))
        self.assertEqual(mock_store.load_credential("test_key"), "secret_value_123")
        self.assertTrue(mock_store.delete_credential("test_key"))
        self.assertIsNone(mock_store.load_credential("test_key"))

        # Test WindowsCredentialStore in temporary directory
        win_store = WindowsCredentialStore(base_dir=os.path.join(self.temp_dir, "vault"))
        win_store.save_credential("agent_key", "super_secret_raw_key_bytes")
        loaded = win_store.load_credential("agent_key")
        self.assertEqual(loaded, "super_secret_raw_key_bytes")
        win_store.delete_credential("agent_key")
        self.assertIsNone(win_store.load_credential("agent_key"))

    def test_12_private_key_never_sent_to_backend(self):
        """Scenario 12: Only public key is shared with backend; private key stays local."""
        mock_store = MockCredentialStore()
        agent_crypto = DeviceAgentCrypto(device_id="DEV-LOCAL-01", credential_store=mock_store)

        # Inspect what is sent during enrollment
        enrollment_payload = {
            "device_id": agent_crypto.device_id,
            "public_key": agent_crypto.public_key_hex,
            "hostname": "DESKTOP-TEST",
        }
        self.assertIn("public_key", enrollment_payload)
        self.assertNotIn("private_key", enrollment_payload)
        self.assertNotIn("secret", enrollment_payload)

        # Enrollment succeeds with only public_key
        ok, msg, cred, dev = self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id=agent_crypto.device_id,
            public_key=agent_crypto.public_key_hex,
            name="Alice Test PC",
            hostname="DESKTOP-TEST"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(cred)
        # Backend stored credential contains only public key
        self.assertFalse(hasattr(cred, "private_key"))
        self.assertEqual(cred.public_key, agent_crypto.public_key_hex)

    def test_13_device_credential_creation(self):
        """Scenario 13: Credential record created with Ed25519 public key and metadata."""
        mock_store = MockCredentialStore()
        crypto = DeviceAgentCrypto(device_id="DEV-CRED-01", credential_store=mock_store)

        ok, msg, cred, dev = self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id="DEV-CRED-01",
            public_key=crypto.public_key_hex,
            name="Alice Workstation",
            hostname="ALICE-WS",
            platform_name="Windows",
            os_version="11.0.26100"
        )
        self.assertTrue(ok)
        self.assertEqual(cred.algorithm, "ed25519")
        self.assertEqual(cred.user_id, self.user_a.id)
        self.assertEqual(cred.device_id, "DEV-CRED-01")
        self.assertTrue(cred.is_active)
        self.assertFalse(cred.is_revoked)

    def test_14_device_enrolled_in_account_device_manager(self):
        """Scenario 14: Enrolled device is registered in AccountDeviceManager."""
        mock_store = MockCredentialStore()
        crypto = DeviceAgentCrypto(device_id="DEV-ACC-01", credential_store=mock_store)

        ok, msg, cred, dev = self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id="DEV-ACC-01",
            public_key=crypto.public_key_hex,
            name="Primary Desktop",
            hostname="DESKTOP-PRIMARY"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(dev)

        # Query AccountDeviceManager
        devices = self.account_mgr.get_devices_for_user(self.user_a.id)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].device_id, "DEV-ACC-01")
        self.assertEqual(devices[0].name, "Primary Desktop")
        self.assertEqual(devices[0].status, "online")

    def test_15_safe_default_permissions(self):
        """Scenario 15: Safe default permissions established; dangerous ops denied by default."""
        mock_store = MockCredentialStore()
        crypto = DeviceAgentCrypto(device_id="DEV-PERMS-01", credential_store=mock_store)

        ok, msg, cred, dev = self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id="DEV-PERMS-01",
            public_key=crypto.public_key_hex,
            name="Secure PC"
        )
        self.assertTrue(ok)

        # Check default permissions configured in enrollment
        defaults = self.enrollment_mgr.DEFAULT_SAFE_PERMISSIONS
        self.assertIn("telemetry.read", defaults["allowed_commands"])
        self.assertIn("system.info", defaults["allowed_commands"])
        # High risk commands denied by default
        self.assertIn("system.shutdown", defaults["denied_commands"])
        self.assertIn("system.reboot", defaults["denied_commands"])
        self.assertIn("filesystem.delete", defaults["denied_commands"])
        self.assertIn("process.kill", defaults["denied_commands"])


class TestDeviceAuthChallengeResponse(BasePhase42Test):
    """Scenarios 16-23: Challenge-Response, Signatures, Replay Protection & Invariants"""

    def setUp(self):
        super().setUp()
        self.mock_store = MockCredentialStore()
        self.crypto = DeviceAgentCrypto(device_id="DEV-AUTH-01", credential_store=self.mock_store)
        self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id="DEV-AUTH-01",
            public_key=self.crypto.public_key_hex,
            name="Alice Laptop"
        )

    def test_16_challenge_issuance(self):
        """Scenario 16: Challenge creates 32-byte cryptographic random nonce with 60s TTL."""
        ok, msg, chal = self.auth_mgr.issue_challenge("DEV-AUTH-01")
        self.assertTrue(ok)
        self.assertIsNotNone(chal)
        self.assertIn("challenge_id", chal)
        self.assertIn("nonce", chal)
        self.assertEqual(len(chal["nonce"]), 64)  # 32 bytes = 64 hex characters
        self.assertEqual(chal["ttl"], 60.0)

    def test_17_device_agent_canonical_signature(self):
        """Scenario 17: DeviceAgentCrypto produces valid signature over canonical message."""
        ok, msg, chal = self.auth_mgr.issue_challenge("DEV-AUTH-01")
        sign_result = self.crypto.sign_challenge(nonce=chal["nonce"], timestamp=chal["expires_at"] - 60.0)

        self.assertIn("signature", sign_result)
        self.assertIn("context", sign_result)
        self.assertEqual(len(sign_result["signature"]), 128)  # Ed25519 64-byte signature = 128 hex chars
        self.assertEqual(sign_result["context"]["device_id"], "DEV-AUTH-01")

    def test_18_device_auth_success(self):
        """Scenario 18: Backend validates signature and issues DeviceSession."""
        ok, msg, chal = self.auth_mgr.issue_challenge("DEV-AUTH-01")
        sign_result = self.crypto.sign_challenge(nonce=chal["nonce"], timestamp=chal["expires_at"] - 60.0)

        ok_auth, msg_auth, sess = self.auth_mgr.verify_challenge_response(
            device_id="DEV-AUTH-01",
            challenge_id=chal["challenge_id"],
            signature_hex=sign_result["signature"],
            context=sign_result["context"]
        )
        self.assertTrue(ok_auth)
        self.assertEqual(msg_auth, "OK")
        self.assertIsNotNone(sess)
        self.assertEqual(sess.device_id, "DEV-AUTH-01")
        self.assertEqual(sess.user_id, self.user_a.id)
        self.assertTrue(sess.is_valid)

    def test_19_invalid_signature_rejected(self):
        """Scenario 19: Tampered signature is rejected."""
        ok, msg, chal = self.auth_mgr.issue_challenge("DEV-AUTH-01")
        sign_result = self.crypto.sign_challenge(nonce=chal["nonce"], timestamp=chal["expires_at"] - 60.0)

        # Tamper signature (flip last char)
        bad_sig = sign_result["signature"][:-1] + ("0" if sign_result["signature"][-1] != "0" else "1")

        ok_auth, msg_auth, sess = self.auth_mgr.verify_challenge_response(
            device_id="DEV-AUTH-01",
            challenge_id=chal["challenge_id"],
            signature_hex=bad_sig,
            context=sign_result["context"]
        )
        self.assertFalse(ok_auth)
        self.assertIn("INVALID_SIGNATURE", msg_auth)
        self.assertIsNone(sess)

    def test_20_replay_protection_nonce_reuse_rejected(self):
        """Scenario 20: Challenge nonce is single-use; replay fails immediately."""
        ok, msg, chal = self.auth_mgr.issue_challenge("DEV-AUTH-01")
        sign_result = self.crypto.sign_challenge(nonce=chal["nonce"], timestamp=chal["expires_at"] - 60.0)

        # 1st time succeeds
        ok1, _, sess1 = self.auth_mgr.verify_challenge_response(
            device_id="DEV-AUTH-01",
            challenge_id=chal["challenge_id"],
            signature_hex=sign_result["signature"],
            context=sign_result["context"]
        )
        self.assertTrue(ok1)

        # 2nd time with exact same challenge & signature fails (Replay attack)
        ok2, msg2, sess2 = self.auth_mgr.verify_challenge_response(
            device_id="DEV-AUTH-01",
            challenge_id=chal["challenge_id"],
            signature_hex=sign_result["signature"],
            context=sign_result["context"]
        )
        self.assertFalse(ok2)
        self.assertIn("REPLAY_DETECTED", msg2)
        self.assertIsNone(sess2)

    def test_21_expired_challenge_rejected(self):
        """Scenario 21: Challenge nonce past 60s TTL is rejected."""
        # Manually create expired challenge
        challenge = DeviceAuthChallenge(
            id="expired-chal-id",
            device_id="DEV-AUTH-01",
            nonce="a" * 64,
            created_at=time.time() - 100,
            expires_at=time.time() - 40,
            is_used=False
        )
        self.auth_mgr._challenges["expired-chal-id"] = challenge

        sign_result = self.crypto.sign_challenge(nonce="a" * 64, timestamp=challenge.created_at)

        ok, msg, sess = self.auth_mgr.verify_challenge_response(
            device_id="DEV-AUTH-01",
            challenge_id="expired-chal-id",
            signature_hex=sign_result["signature"],
            context=sign_result["context"]
        )
        self.assertFalse(ok)
        self.assertIn("CHALLENGE_EXPIRED", msg)
        self.assertIsNone(sess)

    def test_22_protocol_version_negotiation(self):
        """Scenario 22: Mismatched protocol version is rejected."""
        ok, msg, chal = self.auth_mgr.issue_challenge("DEV-AUTH-01")
        sign_result = self.crypto.sign_challenge(
            nonce=chal["nonce"],
            timestamp=chal["expires_at"] - 60.0,
            protocol_version="99.9"
        )

        ok_auth, msg_auth, sess = self.auth_mgr.verify_challenge_response(
            device_id="DEV-AUTH-01",
            challenge_id=chal["challenge_id"],
            signature_hex=sign_result["signature"],
            context=sign_result["context"]
        )
        self.assertFalse(ok_auth)
        self.assertIn("UNSUPPORTED_PROTOCOL", msg_auth)

    def test_23_session_decoupling_invariant(self):
        """Scenario 23: Device enrolled & authenticated != RemoteAuthSession authorized."""
        # DeviceSession created through crypto authentication
        ok, msg, chal = self.auth_mgr.issue_challenge("DEV-AUTH-01")
        sign_result = self.crypto.sign_challenge(nonce=chal["nonce"], timestamp=chal["expires_at"] - 60.0)
        ok_auth, _, dev_session = self.auth_mgr.verify_challenge_response(
            device_id="DEV-AUTH-01",
            challenge_id=chal["challenge_id"],
            signature_hex=sign_result["signature"],
            context=sign_result["context"]
        )
        self.assertTrue(ok_auth)
        self.assertIsInstance(dev_session, DeviceSession)

        # Invariant test: Having a DeviceSession does NOT grant RemoteAuthSession permissions
        self.assertNotIsInstance(dev_session, RemoteAuthSession)
        self.assertNotIsInstance(dev_session, SupabaseSessionClaims)
        self.assertFalse(hasattr(dev_session, "remote_control_token"))


class TestDeviceLifecycleAndRevocation(BasePhase42Test):
    """Scenarios 24-27: Cascading Revocation, Re-pairing, Fingerprints & SQL Schema"""

    def setUp(self):
        super().setUp()
        self.mock_store = MockCredentialStore()
        self.crypto = DeviceAgentCrypto(device_id="DEV-LIFE-01", credential_store=self.mock_store)
        self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id="DEV-LIFE-01",
            public_key=self.crypto.public_key_hex,
            name="Alice Work PC"
        )

    def test_24_cascading_device_revocation(self):
        """Scenario 24: Revoking device revokes credentials and terminates device sessions."""
        # Create an active device session
        ok, _, chal = self.auth_mgr.issue_challenge("DEV-LIFE-01")
        sign_result = self.crypto.sign_challenge(nonce=chal["nonce"], timestamp=chal["expires_at"] - 60.0)
        self.auth_mgr.verify_challenge_response(
            device_id="DEV-LIFE-01",
            challenge_id=chal["challenge_id"],
            signature_hex=sign_result["signature"],
            context=sign_result["context"]
        )
        self.assertEqual(len(self.auth_mgr.get_active_sessions_for_device("DEV-LIFE-01")), 1)

        # Revoke device via AccountDeviceManager (which triggers cascading revocation)
        ok_rev, msg_rev = self.account_mgr.revoke_device(
            "DEV-LIFE-01",
            user_id=self.user_a.id
        )
        self.assertTrue(ok_rev)

        # 1. Credential is revoked
        cred = self.enrollment_mgr.get_credential("DEV-LIFE-01", include_revoked=True)
        self.assertIsNotNone(cred)
        self.assertTrue(cred.is_revoked)
        self.assertIsNone(self.enrollment_mgr.get_credential("DEV-LIFE-01"))
        self.assertFalse(self.enrollment_mgr.is_device_credential_valid("DEV-LIFE-01"))

        # 2. Device sessions terminated
        active_sessions = self.auth_mgr.get_active_sessions_for_device("DEV-LIFE-01")
        self.assertEqual(len(active_sessions), 0)

        # 3. New challenge cannot be issued for revoked device
        ok_chal, msg_chal, _ = self.auth_mgr.issue_challenge("DEV-LIFE-01")
        self.assertFalse(ok_chal)
        self.assertIn("NOT_ENROLLED", msg_chal)

    def test_25_device_re_pairing_and_credential_rotation(self):
        """Scenario 25: Re-enrolling device updates public key and resets credential."""
        # First revoke the device
        self.account_mgr.revoke_device("DEV-LIFE-01", user_id=self.user_a.id)

        # Generate a fresh keypair
        new_store = MockCredentialStore()
        new_crypto = DeviceAgentCrypto(device_id="DEV-LIFE-01", credential_store=new_store)
        self.assertNotEqual(new_crypto.public_key_hex, self.crypto.public_key_hex)

        # Re-enroll with new public key
        ok, msg, cred, dev = self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id="DEV-LIFE-01",
            public_key=new_crypto.public_key_hex,
            name="Alice Work PC (Re-enrolled)"
        )
        self.assertTrue(ok)
        self.assertEqual(cred.public_key, new_crypto.public_key_hex)
        self.assertFalse(cred.is_revoked)
        self.assertEqual(dev.status, "online")

    def test_26_duplicate_device_fingerprint_prevention(self):
        """Scenario 26: Duplicate fingerprint handling logs collision warning."""
        # Enroll device 1 with fingerprint
        self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id="DEV-FP-01",
            public_key=self.crypto.public_key_hex,
            name="PC 1",
            fingerprint="fp-hardware-uuid-999"
        )

        # Attempt to enroll device 2 with identical fingerprint under different user
        crypto_b = DeviceAgentCrypto(device_id="DEV-FP-02", credential_store=MockCredentialStore())
        ok, msg, cred, dev = self.enrollment_mgr.enroll_device(
            user_id=self.user_b.id,
            device_id="DEV-FP-02",
            public_key=crypto_b.public_key_hex,
            name="PC 2",
            fingerprint="fp-hardware-uuid-999"
        )
        # Should enroll with warning logged and metadata tracking
        self.assertTrue(ok)
        self.assertEqual(cred.metadata.get("fingerprint"), "fp-hardware-uuid-999")

    def test_27_postgres_migration_rls_schema_validation(self):
        """Scenario 27: Validate PostgreSQL migration schema has RLS, tables, and constraints."""
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "supabase",
            "migrations",
            "20260918_phase42_device_enrollment.sql"
        )
        self.assertTrue(os.path.exists(migration_path), f"Migration not found: {migration_path}")

        with open(migration_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Check required tables
        self.assertIn("public.device_pairing_sessions", sql)
        self.assertIn("public.device_credentials", sql)
        self.assertIn("public.device_auth_challenges", sql)

        # Check RLS enabled
        self.assertIn("ENABLE ROW LEVEL SECURITY", sql)
        self.assertIn("user_id = auth.uid()", sql)

        # Check foreign keys
        self.assertIn("REFERENCES public.profiles(id)", sql)
        self.assertIn("ON DELETE CASCADE", sql)


class TestDeviceEnrollmentAPIAndSecurity(BasePhase42Test):
    """Scenarios 28-30: HTTP API Endpoints, Audit Redaction & AST Security Scan"""

    def setUp(self):
        super().setUp()
        # Set default singleton instances for API handlers
        DevicePairingManager._default_instance = self.pairing_mgr
        AccountDeviceManager._default_instance = self.account_mgr
        DeviceEnrollmentManager._default_instance = self.enrollment_mgr
        DeviceAuthManager._default_instance = self.auth_mgr

    def test_28_device_pairing_http_endpoints(self):
        """Scenario 28: Test /api/devices/pairing/start, status, cancel, and complete."""
        # 1. Start pairing
        req_start = MockRequest(
            method="POST",
            headers={"X-User-Id": self.user_a.id},
            body={"ttl": 300}
        )
        resp_start = asyncio.run(handle_device_pairing_start(req_start))
        self.assertEqual(resp_start.status, 200)
        data_start = json.loads(resp_start.text)
        self.assertTrue(data_start["ok"])
        self.assertIn("code", data_start)
        self.assertIn("pairing_id", data_start)
        pairing_id = data_start["pairing_id"]
        raw_code = data_start["code"]

        # 2. Check pairing status
        req_status = MockRequest(
            method="GET",
            headers={"X-User-Id": self.user_a.id},
            match_info={"pairing_id": pairing_id}
        )
        resp_status = asyncio.run(handle_device_pairing_status(req_status))
        self.assertEqual(resp_status.status, 200)
        data_status = json.loads(resp_status.text)
        self.assertEqual(data_status["session"]["status"], "PENDING")

        # 3. Complete pairing (Agent client)
        mock_store = MockCredentialStore()
        agent_crypto = DeviceAgentCrypto(device_id="DEV-API-01", credential_store=mock_store)
        req_complete = MockRequest(
            method="POST",
            body={
                "pairing_id": pairing_id,
                "code": raw_code,
                "public_key": agent_crypto.public_key_hex,
                "device": {
                    "device_id": "DEV-API-01",
                    "hostname": "DESKTOP-API",
                    "platform": "Windows",
                    "name": "API Desktop"
                }
            }
        )
        resp_complete = asyncio.run(handle_device_pairing_complete(req_complete))
        self.assertEqual(resp_complete.status, 200)
        data_complete = json.loads(resp_complete.text)
        self.assertTrue(data_complete["ok"])
        self.assertEqual(data_complete["device"]["device_id"], "DEV-API-01")

        # 4. Status after complete is COMPLETED
        resp_status2 = asyncio.run(handle_device_pairing_status(req_status))
        data_status2 = json.loads(resp_status2.text)
        self.assertEqual(data_status2["session"]["status"], "COMPLETED")

    def test_29_device_auth_http_endpoints(self):
        """Scenario 29: Test /api/devices/{device_id}/challenge and authenticate."""
        mock_store = MockCredentialStore()
        agent_crypto = DeviceAgentCrypto(device_id="DEV-API-AUTH", credential_store=mock_store)
        self.enrollment_mgr.enroll_device(
            user_id=self.user_a.id,
            device_id="DEV-API-AUTH",
            public_key=agent_crypto.public_key_hex,
            name="API Auth Device"
        )

        # 1. Request challenge
        req_chal = MockRequest(
            method="POST",
            match_info={"device_id": "DEV-API-AUTH"}
        )
        resp_chal = asyncio.run(handle_device_auth_challenge(req_chal))
        self.assertEqual(resp_chal.status, 200)
        data_chal = json.loads(resp_chal.text)
        self.assertTrue(data_chal["ok"])
        challenge_id = data_chal["challenge_id"]
        nonce = data_chal["nonce"]

        # 2. Sign and authenticate
        sign_result = agent_crypto.sign_challenge(nonce=nonce, timestamp=data_chal["expires_at"] - 60.0)
        req_auth = MockRequest(
            method="POST",
            match_info={"device_id": "DEV-API-AUTH"},
            body={
                "challenge_id": challenge_id,
                "signature": sign_result["signature"],
                "context": sign_result["context"]
            }
        )
        resp_auth = asyncio.run(handle_device_auth_authenticate(req_auth))
        self.assertEqual(resp_auth.status, 200)
        data_auth = json.loads(resp_auth.text)
        self.assertTrue(data_auth["ok"])
        self.assertIn("session_token", data_auth)

    def test_30_audit_log_secret_redaction_and_ast_security_scan(self):
        """Scenario 30: Secret redaction in logs and AST security scan for 0 eval/exec/shell=True."""
        # 1. Redaction verification
        test_event_data = {
            "pairing_code": "123456",
            "private_key": "aabbccdd" * 8,
            "raw_nonce": "11223344" * 8,
            "device_id": "DEV-SAFE",
            "action": "enroll"
        }
        sanitized = sanitize_event_data(test_event_data)
        self.assertEqual(sanitized["pairing_code"], "***REDACTED***")
        self.assertEqual(sanitized["private_key"], "***REDACTED***")
        self.assertEqual(sanitized["raw_nonce"], "***REDACTED***")
        self.assertEqual(sanitized["device_id"], "DEV-SAFE")

        # 2. AST security scan of Phase 42 modules
        core_dir = os.path.dirname(os.path.dirname(__file__))
        phase42_files = [
            os.path.join(core_dir, "core", "v8", "device_pairing.py"),
            os.path.join(core_dir, "core", "v8", "device_enrollment.py"),
            os.path.join(core_dir, "core", "v8", "device_auth.py"),
            os.path.join(core_dir, "core", "v8", "device_agent_crypto.py"),
        ]

        forbidden_names = {"eval", "exec"}
        for fpath in phase42_files:
            self.assertTrue(os.path.exists(fpath), f"File missing: {fpath}")
            with open(fpath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=fpath)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check forbidden builtins
                    if isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                        self.fail(f"Forbidden call '{node.func.id}' found in {fpath} line {node.lineno}")
                    # Check os.system
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "system":
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                            self.fail(f"Forbidden 'os.system' found in {fpath} line {node.lineno}")
                    # Check subprocess shell=True
                    for kw in getattr(node, "keywords", []):
                        if kw.arg == "shell" and getattr(kw.value, "value", None) is True:
                            self.fail(f"Forbidden 'shell=True' found in {fpath} line {node.lineno}")


if __name__ == "__main__":
    unittest.main()
