# ========== tests/test_v8_phase47.py ==========
# Phase 47 — Full Agent Access & User Consent — Security Tests
# 38+ tests covering: default LIMITED, 4-step flow, failed reauth,
# cross-tenant blocking, device-scoped isolation, override, emergency revoke,
# audit events, permission integration, Telegram commands, AST scan

import os
import sys
import time
import unittest
import ast
import json
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from core.v8.agent_access import (
        AgentAccessManager, AgentAccessGrant, AccessLevel,
        ActivationChallenge, FULL_ACCESS_SECURITY_WARNING_TEXT,
        DEFAULT_POLICY_VERSION, CHALLENGE_TTL_SECONDS,
        RATE_LIMIT_MAX_ATTEMPTS
    )
except ImportError:
    AgentAccessManager = None
    AgentAccessGrant = None
    AccessLevel = None
    ActivationChallenge = None
    FULL_ACCESS_SECURITY_WARNING_TEXT = ""
    DEFAULT_POLICY_VERSION = "1.0.0"
    CHALLENGE_TTL_SECONDS = 300
    RATE_LIMIT_MAX_ATTEMPTS = 5

try:
    from core.v8.events import RemoteEventType
except ImportError:
    RemoteEventType = None

try:
    from core.v8.permission_center import (
        UserPermissionProfile, PermissionStore, STANDARD_PERMISSIONS, PERMISSIONS_BY_ID
    )
except ImportError:
    UserPermissionProfile = None
    PermissionStore = None
    STANDARD_PERMISSIONS = []
    PERMISSIONS_BY_ID = {}

try:
    from core.v8.command_queue import CommandQueueManager, CommandState
except ImportError:
    CommandQueueManager = None
    CommandState = None


def _reset_singletons():
    """Barcha singleton instancelarni tozalash"""
    if AgentAccessManager and hasattr(AgentAccessManager, '_default_instance'):
        AgentAccessManager._default_instance = None
    if PermissionStore and hasattr(PermissionStore, '_default_instance'):
        PermissionStore._default_instance = None
    if CommandQueueManager and hasattr(CommandQueueManager, '_default_instance'):
        CommandQueueManager._default_instance = None


def _make_manager(tmp_dir=None):
    """Fresh AgentAccessManager yaratish"""
    if not AgentAccessManager:
        return None
    path = os.path.join(tmp_dir or tempfile.mkdtemp(), "test_access.json")
    return AgentAccessManager(storage_path=path)


# ================================================================
# 1. DEFAULT STATE TESTS (5 tests)
# ================================================================
class TestDefaultState(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_default_access_level_is_limited(self):
        """Yangi user+device uchun access level LIMITED bo'lishi kerak"""
        if not AgentAccessManager: self.skipTest("Module not found")
        mgr = _make_manager(self.tmp)
        status = mgr.get_access_status("user1", "dev1")
        self.assertEqual(status["access_level"], "LIMITED")
        self.assertFalse(status["is_full_access"])

    def test_default_grant_none(self):
        """Grant mavjud bo'lmasligi kerak"""
        if not AgentAccessManager: self.skipTest("Module not found")
        mgr = _make_manager(self.tmp)
        self.assertIsNone(mgr.get_grant("user1", "dev1"))

    def test_is_full_access_false_by_default(self):
        """is_full_access False bo'lishi kerak"""
        if not AgentAccessManager: self.skipTest("Module not found")
        mgr = _make_manager(self.tmp)
        self.assertFalse(mgr.is_full_access("user1", "dev1"))

    def test_default_status_has_all_fields(self):
        """Status dict barcha kerakli fieldlarga ega bo'lishi kerak"""
        if not AgentAccessManager: self.skipTest("Module not found")
        mgr = _make_manager(self.tmp)
        status = mgr.get_access_status("user1", "dev1")
        required = {"user_id", "device_id", "access_level", "is_full_access",
                    "policy_version", "enabled_at", "permissions_granted",
                    "total_supported_permissions", "overrides", "revoked_at"}
        self.assertTrue(required.issubset(set(status.keys())))

    def test_access_level_enum_values(self):
        """AccessLevel enum to'g'ri qiymatlarni saqlashi kerak"""
        if not AccessLevel: self.skipTest("Module not found")
        self.assertEqual(AccessLevel.LIMITED.value, "LIMITED")
        self.assertEqual(AccessLevel.FULL.value, "FULL")
        self.assertEqual(AccessLevel.CUSTOM.value, "CUSTOM")


# ================================================================
# 2. FULL ACTIVATION FLOW TESTS (8 tests)
# ================================================================
class TestFullActivationFlow(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()
        self.mgr = _make_manager(self.tmp)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_step1_initiate_activation(self):
        """Warning ko'rsatish muvaffaqiyatli bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, msg, payload = self.mgr.initiate_activation("user1", "dev1")
        self.assertTrue(ok)
        self.assertIn("warning_token", payload)
        self.assertIn("challenge_id", payload)
        self.assertIn("warning_text", payload)
        self.assertIn("expires_in", payload)

    def test_step2_acknowledge_warning(self):
        """Warning tasdiqlash muvaffaqiyatli bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, payload = self.mgr.initiate_activation("user1", "dev1")
        self.assertTrue(ok)
        ok2, msg2 = self.mgr.acknowledge_warning("user1", "dev1", payload["warning_token"])
        self.assertTrue(ok2)

    def test_step3_verify_reauthentication(self):
        """Qayta autentifikatsiya to'g'ri parol bilan muvaffaqiyatli bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, payload = self.mgr.initiate_activation("user1", "dev1")
        self.mgr.acknowledge_warning("user1", "dev1", payload["warning_token"])
        ok3, msg3, confirm_token = self.mgr.verify_reauthentication(
            "user1", "dev1", payload["warning_token"], "correct_password"
        )
        self.assertTrue(ok3)
        self.assertIsNotNone(confirm_token)
        self.assertGreater(len(confirm_token), 10)

    def test_step4_confirm_activation(self):
        """Yakuniy tasdiqlash Full Access berishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        # Full 4-step flow
        ok, _, payload = self.mgr.initiate_activation("user1", "dev1")
        self.mgr.acknowledge_warning("user1", "dev1", payload["warning_token"])
        ok3, _, confirm_token = self.mgr.verify_reauthentication(
            "user1", "dev1", payload["warning_token"], "good_pass"
        )
        ok4, msg4 = self.mgr.confirm_activation("user1", "dev1", confirm_token)
        self.assertTrue(ok4)
        self.assertTrue(self.mgr.is_full_access("user1", "dev1"))

    def test_full_flow_creates_grant(self):
        """Full flow tugagach grant yaratilishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, p = self.mgr.initiate_activation("user1", "dev1")
        self.mgr.acknowledge_warning("user1", "dev1", p["warning_token"])
        _, _, ct = self.mgr.verify_reauthentication("user1", "dev1", p["warning_token"], "pass123")
        self.mgr.confirm_activation("user1", "dev1", ct)

        grant = self.mgr.get_grant("user1", "dev1")
        self.assertIsNotNone(grant)
        self.assertEqual(grant.access_level, "FULL")
        self.assertTrue(grant.warning_acknowledged)
        self.assertIsNotNone(grant.enabled_at)

    def test_full_flow_status_check(self):
        """Full access status dict is_full_access=True qaytarishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, p = self.mgr.initiate_activation("user1", "dev1")
        self.mgr.acknowledge_warning("user1", "dev1", p["warning_token"])
        _, _, ct = self.mgr.verify_reauthentication("user1", "dev1", p["warning_token"], "pass123")
        self.mgr.confirm_activation("user1", "dev1", ct)

        status = self.mgr.get_access_status("user1", "dev1")
        self.assertTrue(status["is_full_access"])
        self.assertEqual(status["access_level"], "FULL")

    def test_warning_payload_contains_uzbek_text(self):
        """Warning text o'zbek tilida bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, payload = self.mgr.initiate_activation("user1", "dev1")
        self.assertIn("OGOHLANTIRISHI", payload["warning_text"])

    def test_policy_version_in_payload(self):
        """Warning payload da policy_version bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, payload = self.mgr.initiate_activation("user1", "dev1")
        self.assertEqual(payload["policy_version"], DEFAULT_POLICY_VERSION)


# ================================================================
# 3. FAILED REAUTH TESTS (4 tests)
# ================================================================
class TestFailedReauth(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()
        self.mgr = _make_manager(self.tmp)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_wrong_password_rejected(self):
        """Noto'g'ri parol bilan reauth rad etilishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, p = self.mgr.initiate_activation("user1", "dev1")
        self.mgr.acknowledge_warning("user1", "dev1", p["warning_token"])
        ok3, msg3, ct = self.mgr.verify_reauthentication(
            "user1", "dev1", p["warning_token"], "wrong_password"
        )
        self.assertFalse(ok3)
        self.assertIsNone(ct)

    def test_empty_password_rejected(self):
        """Bo'sh parol rad etilishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, p = self.mgr.initiate_activation("user1", "dev1")
        self.mgr.acknowledge_warning("user1", "dev1", p["warning_token"])
        ok3, _, ct = self.mgr.verify_reauthentication(
            "user1", "dev1", p["warning_token"], ""
        )
        self.assertFalse(ok3)

    def test_reauth_before_acknowledge_rejected(self):
        """Warning tasdiqlanmagan holda reauth rad etilishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, p = self.mgr.initiate_activation("user1", "dev1")
        ok3, msg3, ct = self.mgr.verify_reauthentication(
            "user1", "dev1", p["warning_token"], "pass123"
        )
        self.assertFalse(ok3)
        self.assertIn("tasdiqlang", msg3.lower())

    def test_invalid_warning_token(self):
        """Noto'g'ri warning token bilan acknowledge rad etilishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, msg = self.mgr.acknowledge_warning("user1", "dev1", "invalid_token_abc")
        self.assertFalse(ok)


# ================================================================
# 4. CROSS-TENANT BLOCKING (3 tests)
# ================================================================
class TestCrossTenantBlocking(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()
        self.mgr = _make_manager(self.tmp)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_cross_tenant_activation_blocked(self):
        """Boshqa foydalanuvchining qurilmasida activation bloklash kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, msg, _ = self.mgr.initiate_activation(
            "attacker", "victim_device", device_owner_user_id="real_owner"
        )
        self.assertFalse(ok)
        self.assertIn("tegishli emas", msg.lower())

    def test_same_owner_allowed(self):
        """O'z qurilmasida activation ruxsat berilishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, payload = self.mgr.initiate_activation(
            "user1", "dev1", device_owner_user_id="user1"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(payload)

    def test_no_owner_check_when_none(self):
        """device_owner_user_id=None bo'lganda ownership tekshirilmasligi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, _ = self.mgr.initiate_activation("user1", "dev1", device_owner_user_id=None)
        self.assertTrue(ok)


# ================================================================
# 5. DEVICE-SCOPED ISOLATION (3 tests)
# ================================================================
class TestDeviceScopedIsolation(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()
        self.mgr = _make_manager(self.tmp)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def _activate_full(self, user, device):
        ok, _, p = self.mgr.initiate_activation(user, device)
        self.mgr.acknowledge_warning(user, device, p["warning_token"])
        _, _, ct = self.mgr.verify_reauthentication(user, device, p["warning_token"], "pass123")
        self.mgr.confirm_activation(user, device, ct)

    def test_full_access_isolated_per_device(self):
        """Full access faqat bitta qurilmaga tegishli bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self.assertTrue(self.mgr.is_full_access("user1", "dev1"))
        self.assertFalse(self.mgr.is_full_access("user1", "dev2"))

    def test_multiple_devices_independent(self):
        """Turli qurilmalarda mustaqil grantlar bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self._activate_full("user1", "dev2")
        self.assertTrue(self.mgr.is_full_access("user1", "dev1"))
        self.assertTrue(self.mgr.is_full_access("user1", "dev2"))
        # dev1 ni disable qilish dev2 ga ta'sir qilmasligi kerak
        self.mgr.disable_full_access("user1", "dev1")
        self.assertFalse(self.mgr.is_full_access("user1", "dev1"))
        self.assertTrue(self.mgr.is_full_access("user1", "dev2"))

    def test_different_users_isolated(self):
        """Turli foydalanuvchilar izolyatsiya qilinishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self.assertFalse(self.mgr.is_full_access("user2", "dev1"))


# ================================================================
# 6. PERMISSION OVERRIDE TESTS (4 tests)
# ================================================================
class TestPermissionOverride(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()
        self.mgr = _make_manager(self.tmp)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def _activate_full(self, user, device):
        ok, _, p = self.mgr.initiate_activation(user, device)
        self.mgr.acknowledge_warning(user, device, p["warning_token"])
        _, _, ct = self.mgr.verify_reauthentication(user, device, p["warning_token"], "pass123")
        self.mgr.confirm_activation(user, device, ct)

    def test_override_in_full_mode(self):
        """FULL modda individual ruxsatni o'chirish mumkin"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        ok, msg = self.mgr.set_permission_override("user1", "dev1", "file.read", False)
        self.assertTrue(ok)
        grant = self.mgr.get_grant("user1", "dev1")
        self.assertFalse(grant.overrides["file.read"])

    def test_override_in_limited_rejected(self):
        """LIMITED modda override qilib bo'lmaydi"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self.mgr.disable_full_access("user1", "dev1")
        ok, msg = self.mgr.set_permission_override("user1", "dev1", "file.read", True)
        self.assertFalse(ok)
        self.assertIn("limited", msg.lower())

    def test_disable_permission_changes_to_custom(self):
        """O'chirilgan override FULL dan CUSTOM ga o'tkazishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self.mgr.set_permission_override("user1", "dev1", "power.shutdown", False)
        grant = self.mgr.get_grant("user1", "dev1")
        self.assertEqual(grant.access_level, "CUSTOM")

    def test_no_grant_override_rejected(self):
        """Grant mavjud bo'lmaganda override qilib bo'lmaydi"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _ = self.mgr.set_permission_override("nouser", "nodev", "file.read", True)
        self.assertFalse(ok)


# ================================================================
# 7. EMERGENCY REVOKE TESTS (4 tests)
# ================================================================
class TestEmergencyRevoke(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()
        self.mgr = _make_manager(self.tmp)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def _activate_full(self, user, device):
        ok, _, p = self.mgr.initiate_activation(user, device)
        self.mgr.acknowledge_warning(user, device, p["warning_token"])
        _, _, ct = self.mgr.verify_reauthentication(user, device, p["warning_token"], "pass123")
        self.mgr.confirm_activation(user, device, ct)

    def test_emergency_revoke_sets_limited(self):
        """Emergency revoke LIMITED ga qaytarishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self.assertTrue(self.mgr.is_full_access("user1", "dev1"))
        ok, msg = self.mgr.emergency_revoke("user1", "dev1")
        self.assertTrue(ok)
        self.assertFalse(self.mgr.is_full_access("user1", "dev1"))

    def test_emergency_revoke_sets_revoked_at(self):
        """Emergency revoke revoked_at timestamp qo'yishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self.mgr.emergency_revoke("user1", "dev1")
        grant = self.mgr.get_grant("user1", "dev1")
        self.assertIsNotNone(grant.revoked_at)

    def test_emergency_revoke_clears_overrides(self):
        """Emergency revoke barcha overridesni tozalashi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self.mgr.set_permission_override("user1", "dev1", "file.read", True)
        self.mgr.emergency_revoke("user1", "dev1")
        grant = self.mgr.get_grant("user1", "dev1")
        self.assertEqual(len(grant.overrides), 0)

    def test_emergency_revoke_cancels_challenges(self):
        """Emergency revoke pending challengelarni bekor qilishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _, p = self.mgr.initiate_activation("user1", "dev1")
        self.assertTrue(ok)
        # Challenge mavjud
        self.assertGreater(len(self.mgr._challenges), 0)
        self.mgr.emergency_revoke("user1", "dev1")
        # Challenge tozalangan bo'lishi kerak
        remaining = [
            c for c in self.mgr._challenges.values()
            if c.user_id == "user1" and c.device_id == "dev1"
        ]
        self.assertEqual(len(remaining), 0)


# ================================================================
# 8. DISABLE FULL ACCESS TESTS (3 tests)
# ================================================================
class TestDisableFullAccess(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()
        self.mgr = _make_manager(self.tmp)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def _activate_full(self, user, device):
        ok, _, p = self.mgr.initiate_activation(user, device)
        self.mgr.acknowledge_warning(user, device, p["warning_token"])
        _, _, ct = self.mgr.verify_reauthentication(user, device, p["warning_token"], "pass123")
        self.mgr.confirm_activation(user, device, ct)

    def test_disable_returns_limited(self):
        """Disable qilish LIMITED ga qaytarishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        ok, _ = self.mgr.disable_full_access("user1", "dev1")
        self.assertTrue(ok)
        self.assertFalse(self.mgr.is_full_access("user1", "dev1"))

    def test_disable_already_limited_fails(self):
        """Allaqachon LIMITED qurilmani disable qilish fail bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        self._activate_full("user1", "dev1")
        self.mgr.disable_full_access("user1", "dev1")
        ok, msg = self.mgr.disable_full_access("user1", "dev1")
        self.assertFalse(ok)

    def test_disable_nonexistent_fails(self):
        """Mavjud bo'lmagan grant uchun disable fail bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        ok, _ = self.mgr.disable_full_access("nouser", "nodev")
        self.assertFalse(ok)


# ================================================================
# 9. RATE LIMITING TESTS (2 tests)
# ================================================================
class TestRateLimiting(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()
        self.mgr = _make_manager(self.tmp)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_rate_limit_blocks_excessive_attempts(self):
        """5 dan ortiq urinish bloklashi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        for i in range(RATE_LIMIT_MAX_ATTEMPTS):
            ok, _, _ = self.mgr.initiate_activation("user1", "dev1")
            self.assertTrue(ok, f"Attempt {i+1} should succeed")

        # 6th attempt should be blocked
        ok, msg, _ = self.mgr.initiate_activation("user1", "dev1")
        self.assertFalse(ok)
        self.assertIn("ko'p urinish", msg.lower())

    def test_rate_limit_per_device(self):
        """Rate limit device-scoped bo'lishi kerak"""
        if not self.mgr: self.skipTest("Module not found")
        for i in range(RATE_LIMIT_MAX_ATTEMPTS):
            self.mgr.initiate_activation("user1", "dev1")
        # dev2 hali limitga yetmagan bo'lishi kerak
        ok, _, _ = self.mgr.initiate_activation("user1", "dev2")
        self.assertTrue(ok)


# ================================================================
# 10. PERMISSION INTEGRATION TESTS (3 tests)
# ================================================================
class TestPermissionIntegration(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_limited_profile_uses_defaults(self):
        """LIMITED profileda standart ruxsatlar ishlatilishi kerak"""
        if not UserPermissionProfile: self.skipTest("Module not found")
        profile = UserPermissionProfile(user_id="u1", device_id="d1", access_level="LIMITED")
        # file.read standart bo'yicha yoqilgan
        if PERMISSIONS_BY_ID.get("file.read"):
            expected = PERMISSIONS_BY_ID["file.read"].default_enabled
            self.assertEqual(profile.is_granted("file.read"), expected)

    def test_full_profile_grants_all(self):
        """FULL profileda barcha ruxsatlar berilishi kerak"""
        if not UserPermissionProfile: self.skipTest("Module not found")
        profile = UserPermissionProfile(user_id="u1", device_id="d1", access_level="FULL")
        # Barcha STANDARD_PERMISSIONS uchun is_granted True qaytarishi kerak
        for perm in STANDARD_PERMISSIONS:
            self.assertTrue(
                profile.is_granted(perm.id),
                f"FULL access should grant {perm.id}"
            )

    def test_from_dict_backward_compatible(self):
        """from_dict noma'lum fieldlarni e'tiborsiz qoldirishi kerak"""
        if not UserPermissionProfile: self.skipTest("Module not found")
        data = {
            "user_id": "u1",
            "device_id": "d1",
            "permissions": {},
            "unknown_field_xyz": 42,
            "access_level": "FULL"
        }
        profile = UserPermissionProfile.from_dict(data)
        self.assertEqual(profile.access_level, "FULL")


# ================================================================
# 11. PERSISTENCE TESTS (2 tests)
# ================================================================
class TestPersistence(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def _activate_full(self, mgr, user, device):
        ok, _, p = mgr.initiate_activation(user, device)
        mgr.acknowledge_warning(user, device, p["warning_token"])
        _, _, ct = mgr.verify_reauthentication(user, device, p["warning_token"], "pass123")
        mgr.confirm_activation(user, device, ct)

    def test_grants_persist_to_disk(self):
        """Grantlar diskka saqlanishi va qayta yuklanishi kerak"""
        if not AgentAccessManager: self.skipTest("Module not found")
        path = os.path.join(self.tmp, "persist_test.json")
        mgr1 = AgentAccessManager(storage_path=path)
        self._activate_full(mgr1, "user1", "dev1")
        self.assertTrue(mgr1.is_full_access("user1", "dev1"))
        self.assertTrue(os.path.exists(path))

        # Yangi instance yaratib qayta yuklash
        mgr2 = AgentAccessManager(storage_path=path)
        self.assertTrue(mgr2.is_full_access("user1", "dev1"))

    def test_save_creates_valid_json(self):
        """Save to'g'ri JSON yaratishi kerak"""
        if not AgentAccessManager: self.skipTest("Module not found")
        path = os.path.join(self.tmp, "json_test.json")
        mgr = AgentAccessManager(storage_path=path)
        self._activate_full(mgr, "user1", "dev1")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("user1:dev1", data)


# ================================================================
# 12. EVENT TYPES TESTS (2 tests)
# ================================================================
class TestEventTypes(unittest.TestCase):
    def test_phase47_event_types_exist(self):
        """Phase 47 event type'lari mavjud bo'lishi kerak"""
        if not RemoteEventType: self.skipTest("Module not found")
        expected = [
            "FULL_ACCESS_WARNING_SHOWN",
            "FULL_ACCESS_WARNING_ACKNOWLEDGED",
            "FULL_ACCESS_REAUTH_PASSED",
            "FULL_ACCESS_REAUTH_FAILED",
            "FULL_ACCESS_ENABLED",
            "FULL_ACCESS_DISABLED",
            "FULL_ACCESS_CROSS_TENANT_BLOCKED",
            "FULL_ACCESS_PERMISSION_OVERRIDE",
            "FULL_ACCESS_EMERGENCY_REVOKE",
            "FULL_ACCESS_DEVICE_SCOPE_VIOLATION",
        ]
        for name in expected:
            self.assertTrue(
                hasattr(RemoteEventType, name),
                f"RemoteEventType should have {name}"
            )

    def test_event_values_match_names(self):
        """Event qiymatlari nomlarga mos kelishi kerak"""
        if not RemoteEventType: self.skipTest("Module not found")
        self.assertEqual(
            RemoteEventType.FULL_ACCESS_ENABLED.value,
            "FULL_ACCESS_ENABLED"
        )


# ================================================================
# 13. AST SECURITY SCAN (1 test)
# ================================================================
class TestASTSecurityScan(unittest.TestCase):
    """0 eval, 0 exec, 0 os.system, 0 shell=True skaneri"""

    def test_no_dangerous_calls_in_phase47(self):
        """Phase 47 fayllarida xavfli funksiya chaqiruvlari bo'lmasligi kerak"""
        dangerous = {"eval", "exec", "os.system"}
        phase47_files = [
            os.path.join(BASE_DIR, "core", "v8", "agent_access.py"),
        ]

        for filepath in phase47_files:
            if not os.path.exists(filepath):
                continue
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    # Check direct calls: eval(), exec()
                    if isinstance(func, ast.Name) and func.id in dangerous:
                        self.fail(f"{filepath}: xavfli chaqiruv topildi: {func.id}() satr {node.lineno}")
                    # Check attribute calls: os.system()
                    if isinstance(func, ast.Attribute):
                        if isinstance(func.value, ast.Name):
                            full_name = f"{func.value.id}.{func.attr}"
                            if full_name in dangerous:
                                self.fail(f"{filepath}: xavfli chaqiruv topildi: {full_name}() satr {node.lineno}")

                # Check for shell=True in subprocess calls
                if isinstance(node, ast.keyword) and node.arg == "shell":
                    if isinstance(node.value, ast.Constant) and node.value.value is True:
                        self.fail(f"shell=True topildi!")


# ================================================================
# 14. GRANT DATACLASS TESTS (2 tests)
# ================================================================
class TestAgentAccessGrant(unittest.TestCase):
    def test_grant_to_dict(self):
        """to_dict barcha fieldlarni qaytarishi kerak"""
        if not AgentAccessGrant: self.skipTest("Module not found")
        grant = AgentAccessGrant(user_id="u1", device_id="d1", access_level="FULL")
        d = grant.to_dict()
        self.assertEqual(d["user_id"], "u1")
        self.assertEqual(d["access_level"], "FULL")

    def test_grant_from_dict(self):
        """from_dict to'g'ri grant yaratishi kerak"""
        if not AgentAccessGrant: self.skipTest("Module not found")
        data = {"user_id": "u1", "device_id": "d1", "access_level": "FULL", "warning_acknowledged": True}
        grant = AgentAccessGrant.from_dict(data)
        self.assertEqual(grant.user_id, "u1")
        self.assertTrue(grant.warning_acknowledged)
        self.assertTrue(grant.is_full_access)


if __name__ == "__main__":
    unittest.main()
