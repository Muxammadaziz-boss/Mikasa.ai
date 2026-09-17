# ========== tests/test_v8_phase40.py ==========
# Phase 40 — Universal Account & Device Management 2.0
# Multi-User Identity -> Account -> Multi-Device Architecture
# Comprehensive Test Suite covering all 30 specification scenarios

import os
import shutil
import tempfile
import unittest
import asyncio
import json
import time

from core.v8.device import DeviceIdentity
from core.v8.telegram_gateway import MockTelegramTransport
from core.v8.telegram_identity import TelegramIdentityManager
from core.v8.account_device import (
    MikasaUser,
    Device,
    UserDeviceLink,
    UserDeviceContext,
    AccountDeviceManager
)
from core.v8.universal_bot import UniversalTelegramBot
from core.v8.auth_session import SessionManager
from core.v8.permission_center import PermissionStore
from core.api_server import (
    handle_account_get,
    handle_devices_list,
    handle_device_detail,
    handle_device_rename,
    handle_device_revoke,
    handle_device_select,
    handle_account_sessions,
    handle_account_sessions_logout_all
)


class MockRequest:
    """Mock aiohttp request for endpoint unit testing."""
    def __init__(self, method="GET", query=None, headers=None, body=None, match_info=None):
        self.method = method
        self.query = query or {}
        self.headers = headers or {}
        self._body = body or {}
        self.match_info = match_info or {}
        self.remote = "127.0.0.1"

    async def json(self):
        return self._body


class TestPhase40Models(unittest.TestCase):
    """Scenarios 1-5: Models, Conversions, Data Integrity"""

    def test_01_mikasa_user_model(self):
        """Scenario 1: MikasaUser model serialization and defaults."""
        user = MikasaUser(id="user_123", username="Alisher")
        self.assertEqual(user.id, "user_123")
        self.assertEqual(user.username, "Alisher")
        self.assertTrue(user.is_active)
        self.assertEqual(user.status, "ACTIVE")

        data = user.to_dict()
        self.assertEqual(data["id"], "user_123")
        self.assertEqual(data["username"], "Alisher")

        restored = MikasaUser.from_dict(data)
        self.assertEqual(restored.id, user.id)
        self.assertEqual(restored.username, user.username)

    def test_02_device_model(self):
        """Scenario 2: Device model creation, status properties, and heartbeat."""
        dev = Device(
            mikasa_user_id="user_123",
            device_id="hw-dev-001",
            name="Uy Noutbuki",
            hostname="DESKTOP-ALI",
            platform="windows",
            agent_version="8.0.0",
            status="offline"
        )
        self.assertFalse(dev.is_online)
        self.assertFalse(dev.is_revoked)

        # Status change
        dev.status = "online"
        self.assertTrue(dev.is_online)

        dev.status = "revoked"
        self.assertTrue(dev.is_revoked)

        # Dict roundtrip
        data = dev.to_dict()
        restored = Device.from_dict(data)
        self.assertEqual(restored.device_id, dev.device_id)
        self.assertEqual(restored.name, "Uy Noutbuki")
        self.assertEqual(restored.mikasa_user_id, "user_123")

    def test_03_device_identity_conversion(self):
        """Scenario 3: Device <-> DeviceIdentity conversion helpers."""
        ident = DeviceIdentity(
            device_id="hw-mac-001",
            hostname="WORKSTATION",
            agent_version="8.0.0",
            metadata={"ip": "192.168.1.50"}
        )
        # from_device_identity
        dev = Device.from_device_identity(ident, user_id="user_abc", name="Ishxona PC")
        self.assertEqual(dev.device_id, "hw-mac-001")
        self.assertEqual(dev.name, "Ishxona PC")
        self.assertEqual(dev.hostname, "WORKSTATION")
        self.assertEqual(dev.mikasa_user_id, "user_abc")

        # to_device_identity
        ident_out = dev.to_device_identity()
        self.assertEqual(ident_out.device_id, "hw-mac-001")
        self.assertEqual(ident_out.agent_version, "8.0.0")

    def test_04_user_device_link_model(self):
        """Scenario 4: UserDeviceLink model serialization and lifecycle."""
        link = UserDeviceLink(
            mikasa_user_id="user_1",
            device_id="hw-001",
            status="ACTIVE"
        )
        self.assertTrue(link.is_active)
        data = link.to_dict()
        restored = UserDeviceLink.from_dict(data)
        self.assertEqual(restored.mikasa_user_id, "user_1")
        self.assertEqual(restored.device_id, "hw-001")

        link.status = "REVOKED"
        self.assertFalse(link.is_active)

    def test_05_user_device_context(self):
        """Scenario 5: UserDeviceContext validity and expiration."""
        ctx = UserDeviceContext(
            user_id="user_1",
            device_id="hw-001",
            selected_at=time.time(),
            expires_at=time.time() + 60.0
        )
        self.assertTrue(ctx.is_valid())

        # Expired context
        ctx_expired = UserDeviceContext(
            user_id="user_1",
            device_id="hw-001",
            selected_at=time.time() - 100.0,
            expires_at=time.time() - 10.0
        )
        self.assertFalse(ctx_expired.is_valid())

        # Indefinite context
        ctx_indef = UserDeviceContext(user_id="user_1", device_id="hw-001", expires_at=None)
        self.assertTrue(ctx_indef.is_valid())


class TestPhase40AccountDeviceManager(unittest.TestCase):
    """Scenarios 6-15: Manager logic, isolation, renaming, cascading revocation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p40_")
        self.storage_file = os.path.join(self.temp_dir, "test_account_devices.json")
        self.sess_file = os.path.join(self.temp_dir, "test_sessions.json")
        self.perm_file = os.path.join(self.temp_dir, "test_perms.json")

        self.session_mgr = SessionManager()
        self.perm_store = PermissionStore(storage_path=self.perm_file)
        self.adm = AccountDeviceManager(
            storage_path=self.storage_file,
            session_manager=self.session_mgr,
            perm_store=self.perm_store
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_06_manager_persistence(self):
        """Scenario 6: Persistence to disk and reloading state intact."""
        self.adm.register_or_get_user("u1", "Alisher")
        self.adm.register_device("u1", "hw1", "Noutbuk 1")
        self.adm.register_device("u1", "hw2", "PC 2")
        self.adm.select_device("u1", "hw1")

        # Reload from a fresh manager instance
        fresh_adm = AccountDeviceManager(storage_path=self.storage_file)
        self.assertIsNotNone(fresh_adm.get_user("u1"))
        devs = fresh_adm.get_devices_for_user("u1")
        self.assertEqual(len(devs), 2)
        selected = fresh_adm.get_selected_device("u1")
        self.assertIsNotNone(selected)
        self.assertEqual(selected.device_id, "hw1")

    def test_07_user_registration_and_status(self):
        """Scenario 7: User registration, retrieval, and status updates."""
        user = self.adm.register_or_get_user("user_x", "Bobur")
        self.assertEqual(user.username, "Bobur")

        # Idempotent call
        user2 = self.adm.register_or_get_user("user_x")
        self.assertEqual(user.id, user2.id)

        # Update status
        ok = self.adm.update_user_status("user_x", "DISABLED")
        self.assertTrue(ok)
        self.assertEqual(self.adm.get_user("user_x").status, "DISABLED")

    def test_08_device_registration_and_ownership(self):
        """Scenario 8: Device registration and hardware collision handling."""
        dev = self.adm.register_device(
            user_id="user_a",
            device_id="hw-unique-1",
            name="Asosiy PC",
            hostname="DESKTOP-1",
            status="online"
        )
        self.assertEqual(dev.name, "Asosiy PC")
        self.assertEqual(dev.mikasa_user_id, "user_a")

        # Re-registering by same user updates device
        updated = self.adm.register_device(
            user_id="user_a",
            device_id="hw-unique-1",
            name="Asosiy PC (Yangilangan)"
        )
        self.assertEqual(updated.name, "Asosiy PC (Yangilangan)")

        # Attempting to register same hardware ID by different user raises ValueError
        with self.assertRaises(ValueError):
            self.adm.register_device(
                user_id="user_b",
                device_id="hw-unique-1",
                name="O'g'irlangan PC"
            )

    def test_09_multi_user_device_isolation(self):
        """Scenario 9: Strict user isolation. User A cannot see User B's devices."""
        self.adm.register_device("user_a", "dev_a1", "User A PC 1")
        self.adm.register_device("user_a", "dev_a2", "User A PC 2")
        self.adm.register_device("user_b", "dev_b1", "User B PC 1")

        devs_a = self.adm.get_devices_for_user("user_a")
        devs_b = self.adm.get_devices_for_user("user_b")

        self.assertEqual(len(devs_a), 2)
        self.assertEqual(len(devs_b), 1)

        # User A cannot get User B's device
        self.assertIsNone(self.adm.get_device("dev_b1", user_id="user_a"))
        # User B cannot get User A's device
        self.assertIsNone(self.adm.get_device("dev_a1", user_id="user_b"))

    def test_10_friendly_renaming_validation(self):
        """Scenario 10: Renaming validation (1-64 chars, whitespace stripping, rejection)."""
        self.adm.register_device("u1", "hw1", "Eski Nom")

        # Valid rename
        ok, msg, updated = self.adm.rename_device("hw1", "u1", "  Yangi Noutbuk  ")
        self.assertTrue(ok)
        self.assertEqual(updated.name, "Yangi Noutbuk")

        # Empty name rejected
        ok, msg, _ = self.adm.rename_device("hw1", "u1", "   ")
        self.assertFalse(ok)
        self.assertIn("VALIDATION_ERROR", msg)

        # Name > 64 chars rejected
        long_name = "A" * 65
        ok, msg, _ = self.adm.rename_device("hw1", "u1", long_name)
        self.assertFalse(ok)
        self.assertIn("VALIDATION_ERROR", msg)

    def test_11_unowned_device_rename_rejection(self):
        """Scenario 11: Renaming unowned device is rejected."""
        self.adm.register_device("user_owner", "hw-owned", "Ega Kompyuteri")

        ok, msg, _ = self.adm.rename_device("hw-owned", "user_attacker", "Xaker PC")
        self.assertFalse(ok)
        self.assertIn("NOT_FOUND", msg)

        # Name must remain unchanged
        self.assertEqual(self.adm.get_device("hw-owned").name, "Ega Kompyuteri")

    def test_12_device_revocation_and_state(self):
        """Scenario 12: Device revocation marks status=revoked and excludes from active list."""
        dev = self.adm.register_device("u1", "hw-rev", "Vaqtinchalik PC")
        self.assertFalse(dev.is_revoked)

        ok, msg = self.adm.revoke_device("hw-rev", "u1")
        self.assertTrue(ok)
        self.assertTrue(dev.is_revoked)
        self.assertEqual(dev.status, "revoked")

        # Excluded from active list
        active_devs = self.adm.get_devices_for_user("u1", include_revoked=False)
        self.assertEqual(len(active_devs), 0)

        # Included when include_revoked=True
        all_devs = self.adm.get_devices_for_user("u1", include_revoked=True)
        self.assertEqual(len(all_devs), 1)

    def test_13_unowned_device_revocation_rejection(self):
        """Scenario 13: Revoking unowned device is rejected."""
        self.adm.register_device("user_owner", "hw-target", "Himoyalangan PC")

        ok, msg = self.adm.revoke_device("hw-target", "user_intruder")
        self.assertFalse(ok)
        self.assertIn("NOT_FOUND", msg)
        self.assertFalse(self.adm.get_device("hw-target").is_revoked)

    def test_14_cascading_revocation_sessions(self):
        """Scenario 14: Cascading revocation terminates all active sessions in SessionManager."""
        self.adm.register_device("u1", "hw-sess", "Sessiya PC")
        # Start active session
        sess = self.session_mgr.create_session("u1", "hw-sess", ttl=900)
        self.assertIsNotNone(sess)
        self.assertTrue(sess.is_active)
        self.assertEqual(len(self.session_mgr.get_sessions_for_user("u1")), 1)

        # Revoke device
        self.adm.revoke_device("hw-sess", "u1", session_manager=self.session_mgr)

        # Sessions for this device must be closed
        active_sessions = self.session_mgr.get_sessions_for_user("u1")
        self.assertEqual(len(active_sessions), 0)

    def test_15_cascading_revocation_permissions(self):
        """Scenario 15: Cascading revocation cleans up permissions in PermissionStore."""
        self.adm.register_device("u1", "hw-perm", "Ruxsat PC")
        # Set custom permissions
        self.perm_store.update_permissions("u1", "hw-perm", {"remote.files.write": True})
        prof = self.perm_store.get_profile("u1", "hw-perm")
        self.assertTrue(prof.permissions.get("remote.files.write"))

        # Revoke device
        self.adm.revoke_device("hw-perm", "u1", perm_store=self.perm_store)

        # Permissions should be revoked / reset
        prof_after = self.perm_store.get_profile("u1", "hw-perm")
        self.assertFalse(prof_after.permissions.get("remote.files.write", False))


class TestPhase40DeviceSelectionAndContext(unittest.TestCase):
    """Scenarios 16-22: Selection by query, context isolation, ambiguity, heartbeat"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p40_sel_")
        self.storage_file = os.path.join(self.temp_dir, "test_sel.json")
        self.adm = AccountDeviceManager(storage_path=self.storage_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_16_cascading_revocation_clears_selection_context(self):
        """Scenario 16: Cascading revocation clears active device selection context."""
        self.adm.register_device("u1", "hw-active", "Tanlangan PC")
        self.adm.select_device("u1", "hw-active")
        self.assertIsNotNone(self.adm.get_selected_device("u1"))

        # Revoke active device
        self.adm.revoke_device("hw-active", "u1")
        self.assertIsNone(self.adm.get_selected_device("u1"))

    def test_17_select_device_by_id_and_uuid(self):
        """Scenario 17: Select device by hardware ID and UUID."""
        dev = self.adm.register_device("u1", "hw-007", "Maxfiy Noutbuk")

        # Select by hardware ID
        ok, msg, s1 = self.adm.select_device("u1", "hw-007")
        self.assertTrue(ok)
        self.assertEqual(s1.device_id, "hw-007")
        self.assertEqual(self.adm.get_selected_device("u1").name, "Maxfiy Noutbuk")

        # Select by UUID
        ok, msg, s2 = self.adm.select_device("u1", dev.id)
        self.assertTrue(ok)
        self.assertEqual(s2.id, dev.id)

    def test_18_select_device_by_query_exact_and_partial(self):
        """Scenario 18: select_device_by_query with exact and substring matching."""
        self.adm.register_device("u1", "pc-work-01", "Ofis Kompyuteri")
        self.adm.register_device("u1", "pc-home-01", "Uy Noutbuki")

        # Exact name
        ok, _, dev = self.adm.select_device_by_query("u1", "Ofis Kompyuteri")
        self.assertTrue(ok)
        self.assertEqual(dev.device_id, "pc-work-01")

        # Substring / partial name (case-insensitive)
        ok, _, dev = self.adm.select_device_by_query("u1", "noutbuk")
        self.assertTrue(ok)
        self.assertEqual(dev.device_id, "pc-home-01")

        # Exact device ID
        ok, _, dev = self.adm.select_device_by_query("u1", "pc-work-01")
        self.assertTrue(ok)
        self.assertEqual(dev.device_id, "pc-work-01")

    def test_19_select_device_by_query_ambiguity(self):
        """Scenario 19: Ambiguous query matching multiple devices returns error."""
        self.adm.register_device("u1", "pc-01", "Ofis Noutbuk 1")
        self.adm.register_device("u1", "pc-02", "Ofis Noutbuk 2")

        ok, msg, dev = self.adm.select_device_by_query("u1", "Ofis")
        self.assertFalse(ok)
        self.assertIsNone(dev)
        self.assertIn("AMBIGUOUS", msg)

    def test_20_multi_user_selection_isolation(self):
        """Scenario 20: Multi-user selection isolation (no global state)."""
        self.adm.register_device("user_a", "dev_a", "A Noutbuk")
        self.adm.register_device("user_b", "dev_b", "B Kompyuter")

        self.adm.select_device("user_a", "dev_a")
        self.adm.select_device("user_b", "dev_b")

        sel_a = self.adm.get_selected_device("user_a")
        sel_b = self.adm.get_selected_device("user_b")

        self.assertEqual(sel_a.device_id, "dev_a")
        self.assertEqual(sel_b.device_id, "dev_b")

    def test_21_unowned_device_selection_rejection(self):
        """Scenario 21: User cannot select device owned by another user."""
        self.adm.register_device("user_a", "dev_a", "User A PC")
        self.adm.register_device("user_b", "dev_b", "User B PC")

        ok, msg, dev = self.adm.select_device("user_a", "dev_b")
        self.assertFalse(ok)
        self.assertIn("NOT_FOUND", msg)
        self.assertIsNone(dev)

    def test_22_device_heartbeat_and_account_summary(self):
        """Scenario 22: Heartbeat tracking and user account summary generation."""
        dev = self.adm.register_device("u1", "hw-hb", "Heartbeat PC", status="offline")
        self.assertEqual(dev.status, "offline")

        # Update heartbeat
        self.adm.update_device_heartbeat("hw-hb", status="online")
        self.assertEqual(dev.status, "online")
        self.assertIsNotNone(dev.last_heartbeat_at)

        # Account summary
        summary = self.adm.get_user_account_summary("u1")
        self.assertEqual(summary["user_id"], "u1")
        self.assertEqual(summary["devices_count"], 1)
        self.assertEqual(summary["active_sessions_count"], 0)


class TestPhase40UniversalTelegramBot(unittest.TestCase):
    """Scenarios 23-28: Telegram bot /devices and /select commands"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p40_tg_")
        self.tg_storage = os.path.join(self.temp_dir, "tg_links.json")
        self.adm_storage = os.path.join(self.temp_dir, "adm.json")

        self.identity_mgr = TelegramIdentityManager(storage_path=self.tg_storage)
        self.adm = AccountDeviceManager(storage_path=self.adm_storage)
        self.transport = MockTelegramTransport()
        self.bot = UniversalTelegramBot(
            identity_manager=self.identity_mgr,
            account_device_manager=self.adm,
            transport=self.transport,
            bot_username="MikasaUniversalBot"
        )

        # Register Mikasa user and link to Telegram user 888111
        req, otp, _, _ = self.identity_mgr.create_link_request("mikasa_usr_1")
        self.identity_mgr.verify_otp(otp, telegram_user_id=888111, username="testuser")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_23_telegram_devices_command_unlinked(self):
        """Scenario 23: Unlinked user sending /devices receives link prompt."""
        update = {
            "message": {
                "message_id": 1,
                "chat": {"id": 999999},
                "from": {"id": 999999, "username": "stranger"},
                "text": "/devices"
            }
        }
        asyncio.run(self.bot.process_update(update))
        self.assertIn("Hisob bog'lanmagan", self.transport.sent_messages[-1]["text"])

    def test_24_telegram_devices_empty(self):
        """Scenario 24: Linked user with no devices gets helpful message."""
        update = {
            "message": {
                "message_id": 2,
                "chat": {"id": 888111},
                "from": {"id": 888111, "username": "testuser"},
                "text": "/devices"
            }
        }
        asyncio.run(self.bot.process_update(update))
        self.assertIn("birorta ham kompyuter ulanmagan", self.transport.sent_messages[-1]["text"])

    def test_25_telegram_devices_listing(self):
        """Scenario 25: Linked user with devices sees list with online indicator and active badge."""
        self.adm.register_device("mikasa_usr_1", "pc-1", "Uy Kompyuteri", status="online")
        self.adm.register_device("mikasa_usr_1", "pc-2", "Ofis Noutbuki", status="standby")
        self.adm.select_device("mikasa_usr_1", "pc-1")

        update = {
            "message": {
                "message_id": 3,
                "chat": {"id": 888111},
                "from": {"id": 888111, "username": "testuser"},
                "text": "/devices"
            }
        }
        asyncio.run(self.bot.process_update(update))
        text = self.transport.sent_messages[-1]["text"]
        self.assertIn("Uy Kompyuteri", text)
        self.assertIn("Ofis Noutbuki", text)
        self.assertIn("(Faol)", text)

    def test_26_telegram_select_by_name(self):
        """Scenario 26: Select device via Telegram /select <name>."""
        self.adm.register_device("mikasa_usr_1", "pc-1", "Uy Kompyuteri", status="online")
        self.adm.register_device("mikasa_usr_1", "pc-2", "Ofis Noutbuki", status="online")

        update = {
            "message": {
                "message_id": 4,
                "chat": {"id": 888111},
                "from": {"id": 888111, "username": "testuser"},
                "text": "/select Ofis"
            }
        }
        asyncio.run(self.bot.process_update(update))
        text = self.transport.sent_messages[-1]["text"]
        self.assertIn("Faol qurilma tanlandi", text)
        self.assertIn("Ofis Noutbuki", text)

        selected = self.adm.get_selected_device("mikasa_usr_1")
        self.assertEqual(selected.device_id, "pc-2")

    def test_27_telegram_select_by_id(self):
        """Scenario 27: Select device via Telegram /select <id>."""
        self.adm.register_device("mikasa_usr_1", "pc-xyz-99", "Asosiy Server", status="online")

        update = {
            "message": {
                "message_id": 5,
                "chat": {"id": 888111},
                "from": {"id": 888111, "username": "testuser"},
                "text": "/select pc-xyz-99"
            }
        }
        asyncio.run(self.bot.process_update(update))
        text = self.transport.sent_messages[-1]["text"]
        self.assertIn("Faol qurilma tanlandi", text)
        self.assertIn("pc-xyz-99", text)

    def test_28_telegram_select_unowned_and_account_summary(self):
        """Scenario 28: Telegram /select unowned device rejected, /account displays PC summary."""
        # Another user's device
        self.adm.register_device("other_user", "pc-secret", "Begona PC")

        update_sel = {
            "message": {
                "message_id": 6,
                "chat": {"id": 888111},
                "from": {"id": 888111, "username": "testuser"},
                "text": "/select pc-secret"
            }
        }
        asyncio.run(self.bot.process_update(update_sel))
        self.assertIn("Xatolik", self.transport.sent_messages[-1]["text"])

        # /account check
        update_acc = {
            "message": {
                "message_id": 7,
                "chat": {"id": 888111},
                "from": {"id": 888111, "username": "testuser"},
                "text": "/account"
            }
        }
        asyncio.run(self.bot.process_update(update_acc))
        acc_text = self.transport.sent_messages[-1]["text"]
        self.assertIn("Ulangan kompyuterlar", acc_text)
        self.assertIn("Faol tanlangan kompyuter", acc_text)


class TestPhase40RestAPI(unittest.TestCase):
    """Scenarios 29-30: REST API handlers for devices, sessions, account summary"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p40_api_")
        self.adm_storage = os.path.join(self.temp_dir, "api_adm.json")
        self.adm = AccountDeviceManager.get_default_instance(storage_path=self.adm_storage)
        self.adm._users.clear()
        self.adm._devices.clear()
        self.adm._devices_by_hw_id.clear()
        self.adm._user_devices.clear()
        self.adm._contexts.clear()

        self.sess_mgr = SessionManager.get_default_instance()
        self.sess_mgr._sessions.clear()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_29_rest_api_devices_endpoints(self):
        """Scenario 29: REST API device CRUD, rename, select, revoke."""
        async def _test():
            # 1. Register device
            self.adm.register_device("admin", "dev-api-1", "Test PC", status="online")

            # GET /api/devices
            req = MockRequest(method="GET", query={"user_id": "admin"})
            resp = await handle_devices_list(req)
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.text)
            self.assertTrue(data["ok"])
            self.assertEqual(len(data["devices"]), 1)
            self.assertEqual(data["devices"][0]["device_id"], "dev-api-1")

            # GET /api/devices/{device_id}
            req_det = MockRequest(method="GET", query={"user_id": "admin"}, match_info={"device_id": "dev-api-1"})
            resp_det = await handle_device_detail(req_det)
            self.assertEqual(resp_det.status, 200)
            data_det = json.loads(resp_det.text)
            self.assertTrue(data_det["ok"])
            self.assertEqual(data_det["device"]["name"], "Test PC")

            # PATCH /api/devices/{device_id} - Rename
            req_ren = MockRequest(
                method="PATCH",
                query={"user_id": "admin"},
                match_info={"device_id": "dev-api-1"},
                body={"name": "Yangi Test PC"}
            )
            resp_ren = await handle_device_rename(req_ren)
            self.assertEqual(resp_ren.status, 200)
            data_ren = json.loads(resp_ren.text)
            self.assertTrue(data_ren["ok"])
            self.assertEqual(data_ren["device"]["name"], "Yangi Test PC")

            # POST /api/devices/{device_id}/select
            req_sel = MockRequest(
                method="POST",
                query={"user_id": "admin"},
                match_info={"device_id": "dev-api-1"}
            )
            resp_sel = await handle_device_select(req_sel)
            self.assertEqual(resp_sel.status, 200)
            data_sel = json.loads(resp_sel.text)
            self.assertTrue(data_sel["ok"])
            self.assertEqual(data_sel["selected_device"]["device_id"], "dev-api-1")

            # DELETE /api/devices/{device_id} - Revoke
            req_rev = MockRequest(
                method="DELETE",
                query={"user_id": "admin"},
                match_info={"device_id": "dev-api-1"}
            )
            resp_rev = await handle_device_revoke(req_rev)
            self.assertEqual(resp_rev.status, 200)
            data_rev = json.loads(resp_rev.text)
            self.assertTrue(data_rev["ok"])

        asyncio.run(_test())

    def test_30_rest_api_sessions_and_logout_all(self):
        """Scenario 30: REST API session listing and logout-all."""
        async def _test():
            self.adm.register_device("admin", "dev-sess-1", "Sessiya Kompyuteri")
            # Create 2 sessions
            self.sess_mgr.create_session("admin", "dev-sess-1", ttl=600)
            self.sess_mgr.create_session("admin", "dev-sess-2", ttl=600)

            # GET /api/account/sessions
            req_s = MockRequest(method="GET", query={"user_id": "admin"})
            resp_s = await handle_account_sessions(req_s)
            self.assertEqual(resp_s.status, 200)
            data_s = json.loads(resp_s.text)
            self.assertTrue(data_s["ok"])
            self.assertEqual(data_s["total"], 2)

            # POST /api/account/sessions/logout-all
            req_lo = MockRequest(method="POST", query={"user_id": "admin"})
            resp_lo = await handle_account_sessions_logout_all(req_lo)
            self.assertEqual(resp_lo.status, 200)
            data_lo = json.loads(resp_lo.text)
            self.assertTrue(data_lo["ok"])
            self.assertEqual(data_lo["terminated_count"], 2)

            # Check sessions empty
            self.assertEqual(len(self.sess_mgr.get_sessions_for_user("admin")), 0)

            # GET /api/account summary check
            req_acc = MockRequest(method="GET", query={"user_id": "admin"})
            resp_acc = await handle_account_get(req_acc)
            self.assertEqual(resp_acc.status, 200)
            data_acc = json.loads(resp_acc.text)
            self.assertTrue(data_acc["ok"])
            self.assertIn("account", data_acc)
            self.assertEqual(data_acc["active_sessions_count"], 0)

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
