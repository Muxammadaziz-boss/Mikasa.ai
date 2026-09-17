# ========== tests/test_v8_phase38.py ==========
# Phase 38 — Mikasa Online Remote Control + User Permission Center Test Suite
# Exactly 20 comprehensive unit & integration tests covering:
# 1. Telegram identity numeric ID validation & user creation
# 2. Pairing code generation (MK-XXXXXX format, 5-minute TTL)
# 3. Pairing code redemption & single-use enforcement
# 4. Expired pairing code rejection
# 5. UserLinkingStore device-to-user linking, resolution & unlinking
# 6. Standard permission definitions catalog & categories
# 7. PermissionStore permission grant, revoke, and persistence
# 8. Immediate permission propagation via observer callbacks
# 9. Capability flag resolution (ADMIN_SYSTEM_INFO, ADMIN_POWER_CONTROL, etc.)
# 10. Unauthorized command rejection (❌ Bu amal uchun ruxsat berilmagan)
# 11. Authorized command success with active permission
# 12. High-risk command (power.shutdown/restart/sleep) confirmation requirement
# 13. Dangerous confirmation cancellation & timeout
# 14. Dangerous confirmation approval & execution
# 15. RemoteCommandEnvelope nonce replay protection & command_id validation
# 16. RemoteToolRegistry safe tool execution (system.status, network.info, app.list)
# 17. Rejection of arbitrary shell / eval / exec commands
# 18. Wake-on-LAN permission gating (power.wake required to wake offline device)
# 19. Secret redaction in audit logs (pairing_code, secret_hash, raw_file_content)
# 20. Full E2E: Account pairing -> Grant permission -> Execute command -> Revoke -> Immediate block

import os
import sys
import time
import asyncio
import unittest
import tempfile
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.v8 import (  # noqa: E402
    DeviceIdentity,
    DeviceRegistry,
    DeviceState,
    HeartbeatPayload,
    HeartbeatManager,
    WakeOnLanManager,
    WakeRelay,
    EnvelopeManager,
    TelegramRemoteGateway,
    MockTelegramTransport,
    RemoteOrchestrator,
    TelegramIdentity,
    UserLinkingStore,
    PermissionStore,
    RemoteToolRegistry,
    sanitize_event_data
)


class MockWakeRelay(WakeRelay):
    """Testlar uchun mock relay: tarmoqqa ehtiyoj yo'q"""

    def __init__(self, succeed: bool = True):
        self.succeed = succeed
        self.sent_packets = []

    async def send_wake(self, mac_address: str, broadcast_ip: str = "255.255.255.255", port: int = 9) -> bool:
        self.sent_packets.append((mac_address, broadcast_ip, port))
        return self.succeed


class TestPhase38UserLinking(unittest.TestCase):
    """Foydalanuvchi va qurilmalarni bog'lash (User & Device Linking) testlari"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.link_file = os.path.join(self.temp_dir, "links.json")
        self.tokens_file = os.path.join(self.temp_dir, "tokens.json")
        self.store = UserLinkingStore(self.link_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_telegram_identity_numeric_validation(self):
        """1. Telegram identifikatori faqat musbat butun son bo'lishi kerak"""
        ident = TelegramIdentity("987654321", "alisher_dev", "Alisher")
        self.assertTrue(ident.is_valid())
        self.assertEqual(ident.user_id, 987654321)

        # Noto'g'ri ID
        ident_bad = TelegramIdentity("abc_invalid", "bad_user")
        self.assertFalse(ident_bad.is_valid())
        self.assertIsNone(ident_bad.user_id)

    def test_02_pairing_code_generation(self):
        """2. Pairing code 'MK-XXXXXX' formatida va 5 daqiqalik TTL bilan hosil qilinishi kerak"""
        code = self.store.generate_pairing_code("user_1", "dev_pc_1", ttl=300.0)
        self.assertTrue(code.startswith("MK-"))
        self.assertEqual(len(code), 9)  # MK- (3) + 6 belgili kod = 9 belgi
        token = self.store.get_token(code)
        self.assertIsNotNone(token)
        self.assertFalse(token.is_used)
        self.assertFalse(token.is_expired())

    def test_03_pairing_code_redemption_and_single_use(self):
        """3. Pairing kod bir marta ishlatilishi kerak; ikkinchi marta foydalanish rad etiladi"""
        code = self.store.generate_pairing_code("user_1", "dev_pc_1", ttl=300.0)
        ok, msg, link = self.store.redeem_pairing_code(code, "123456789", metadata={"username": "sherzod"})
        self.assertTrue(ok)
        self.assertIsNotNone(link)
        self.assertEqual(link.telegram_user_id, "123456789")
        self.assertEqual(link.device_id, "dev_pc_1")

        # Ikkinchi marta ishlatish urinishi
        ok2, msg2, link2 = self.store.redeem_pairing_code(code, "123456789")
        self.assertFalse(ok2)
        self.assertIn("allaqachon ishlatilgan", msg2)

    def test_04_expired_pairing_code_rejected(self):
        """4. Muddati o'tgan pairing kod bilan ulanish rad etilishi kerak"""
        code = self.store.generate_pairing_code("user_1", "dev_pc_1", ttl=0.01)
        time.sleep(0.05)
        ok, msg, link = self.store.redeem_pairing_code(code, "123456789")
        self.assertFalse(ok)
        self.assertIn("muddati o'tgan", msg)

    def test_05_device_resolution_and_unlinking(self):
        """5. Foydalanuvchini Telegram ID orqali aniqlash va bog'lanishni bekor qilish"""
        code = self.store.generate_pairing_code("user_1", "dev_pc_1", ttl=300.0)
        self.store.redeem_pairing_code(code, "555666777")

        link = self.store.get_link_by_telegram("555666777")
        self.assertIsNotNone(link)
        self.assertEqual(link.device_id, "dev_pc_1")

        # Unlink qilish
        unlinked = self.store.unlink_telegram("dev_pc_1")
        self.assertTrue(unlinked)
        self.assertIsNone(self.store.get_link_by_telegram("555666777"))


class TestPhase38PermissionCenter(unittest.TestCase):
    """Ruxsatlar Markazi (Permission Center) testlari"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.perm_file = os.path.join(self.temp_dir, "permissions.json")
        self.store = PermissionStore(self.perm_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_06_standard_permission_catalog(self):
        """6. Standart ruxsatlar katalogi barcha 6 ta toifani qamrab oladi"""
        catalog = self.store.get_catalog()
        categories = {item["category"] for item in catalog}
        self.assertIn("SYSTEM", categories)
        self.assertIn("APPLICATIONS", categories)
        self.assertIn("FILES", categories)
        self.assertIn("NETWORK", categories)
        self.assertIn("POWER", categories)
        self.assertIn("ADVANCED", categories)

        # Kamida 15 ta standart ruxsat mavjud
        self.assertGreaterEqual(len(catalog), 15)

    def test_07_permission_grant_and_persist(self):
        """7. Ruxsatlarni berish va diskka saqlash"""
        profile = self.store.get_profile("admin", "pc_01")
        self.assertFalse(profile.permissions.get("power.shutdown", False))

        updated = self.store.grant_permission("admin", "pc_01", "power.shutdown")
        self.assertTrue(updated.permissions.get("power.shutdown"))
        self.assertEqual(updated.version, 2)

        # Yangi store ochib diskdan o'qish
        store2 = PermissionStore(self.perm_file)
        profile2 = store2.get_profile("admin", "pc_01")
        self.assertTrue(profile2.permissions.get("power.shutdown"))

    def test_08_immediate_propagation_via_observer(self):
        """8. Ruxsat o'zgarganda observerlar orqali zudlik bilan tarqalishi kerak"""
        notified = []

        def on_change(user_id, dev_id, profile):
            notified.append((user_id, dev_id, profile.version))

        self.store.add_observer(on_change)
        self.store.grant_permission("user_x", "dev_y", "system.screenshot")

        self.assertEqual(len(notified), 1)
        self.assertEqual(notified[0][0], "user_x")
        self.assertEqual(notified[0][1], "dev_y")
        self.assertEqual(notified[0][2], 2)

    def test_09_capability_flag_resolution(self):
        """9. Ruxsatlar tegishli ADMIN_* capability flaglari bilan to'g'ri moslashadi"""
        profile = self.store.get_profile("admin", "pc_01")
        self.assertIsNotNone(profile)
        self.store.grant_permission("admin", "pc_01", "file.read")
        self.store.grant_permission("admin", "pc_01", "power.restart")

        self.assertTrue(self.store.has_permission("admin", "pc_01", "file.read"))
        self.assertTrue(self.store.has_permission("admin", "pc_01", "power.restart"))
        self.assertFalse(self.store.has_permission("admin", "pc_01", "advanced.raw_execute"))

        caps = self.store.get_effective_capabilities("admin", "pc_01")
        self.assertIn("ADMIN_FILE_ACCESS", caps)
        self.assertIn("ADMIN_POWER_CONTROL", caps)
        self.assertNotIn("ADMIN_ADVANCED", caps)


class TestPhase38RemoteOrchestration(unittest.TestCase):
    """Masofaviy buyruqlarni xavfsiz boshqarish (Orchestration & Gating) testlari"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.device = DeviceIdentity(
            device_id="test_pc",
            mac_address="00:11:22:33:44:55",
            local_ip="192.168.1.100",
            hostname="TestPC",
            agent_version="8.0.0"
        )
        self.registry = DeviceRegistry()
        self.registry.register_or_update(self.device)

        self.heartbeat = HeartbeatManager()
        self.wake_relay = MockWakeRelay()
        self.wol_mgr = WakeOnLanManager(relay=self.wake_relay)

        self.transport = MockTelegramTransport()
        self.gateway = TelegramRemoteGateway(admin_id="admin", transport=self.transport, allowed_user_ids=["111222333"])

        self.link_file = os.path.join(self.temp_dir, "links.json")
        self.token_file = os.path.join(self.temp_dir, "tokens.json")
        self.perm_file = os.path.join(self.temp_dir, "perms.json")

        self.linking_store = UserLinkingStore(self.link_file)
        self.perm_store = PermissionStore(self.perm_file)

        self.orchestrator = RemoteOrchestrator(
            device_registry=self.registry,
            heartbeat_manager=self.heartbeat,
            wol_manager=self.wol_mgr,
            telegram_gateway=self.gateway,
            user_linking_store=self.linking_store,
            permission_store=self.perm_store
        )

        # Telegram foydalanuvchini qurilmaga bog'laymiz
        code = self.linking_store.generate_pairing_code("admin", "test_pc", ttl=300.0)
        self.linking_store.redeem_pairing_code(code, "111222333")

        # Qurilmani online holatiga o'tkazamiz
        self.heartbeat.record_heartbeat(HeartbeatPayload(
            device_id="test_pc",
            timestamp=time.time(),
            agent_version="8.0.0",
            state=DeviceState.ONLINE,
            metrics={"cpu": 10.0, "ram": 20.0}
        ))

        # Sessiya ochamiz
        self.orchestrator.session_manager.open_session("admin", "test_pc")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_10_unauthorized_command_rejected_immediately(self):
        """10. Ruxsat berilmagan buyruq darhol rad etiladi (❌ Bu amal uchun ruxsat berilmagan)"""
        # screenshot uchun ruxsat yo'q
        self.perm_store.revoke_permission("admin", "test_pc", "system.screenshot")

        async def run():
            await self.orchestrator.process_telegram_message("111222333", "/screenshot")

        asyncio.run(run())

        self.assertTrue(any("Bu amal uchun ruxsat berilmagan" in m.get("text", "") for m in self.transport.sent_messages))

    def test_11_authorized_command_success(self):
        """11. Ruxsat berilgan buyruq xatosiz bajariladi"""
        self.perm_store.grant_permission("admin", "test_pc", "system.status")

        async def run():
            await self.orchestrator.process_telegram_message("111222333", "/status")

        asyncio.run(run())

        msg_texts = [m.get("text", "").upper() for m in self.transport.sent_messages]
        self.assertTrue(any("HOLAT" in txt or "TESTPC" in txt or "ONLINE" in txt for txt in msg_texts))

    def test_12_dangerous_command_confirmation_required(self):
        """12. Yuqori xavfli buyruqlar (power.shutdown) bajarilishdan oldin tasdiqlash talab qiladi"""
        self.perm_store.grant_permission("admin", "test_pc", "power.shutdown")

        async def run():
            await self.orchestrator.process_telegram_message("111222333", "/shutdown")

        asyncio.run(run())

        self.assertTrue(any("TASDIQLASH" in m.get("text", "").upper() or "/CONFIRM" in m.get("text", "").upper() for m in self.transport.sent_messages))
        self.assertGreater(len(self.orchestrator.pending_confirmations), 0)

    def test_13_dangerous_confirmation_cancellation(self):
        """13. Yuqori xavfli buyruqni bekor qilish (/cancel) buyruqni to'xtatadi"""
        self.perm_store.grant_permission("admin", "test_pc", "power.restart")

        async def run():
            await self.orchestrator.process_telegram_message("111222333", "/restart")
            await self.orchestrator.process_telegram_message("111222333", "/cancel")

        asyncio.run(run())

        self.assertEqual(len(self.orchestrator.pending_confirmations), 0)
        self.assertTrue(any("bekor qilindi" in m.get("text", "").lower() for m in self.transport.sent_messages))

    def test_14_dangerous_confirmation_approval_executes(self):
        """14. Yuqori xavfli buyruq tasdiqlangach (/confirm) muvaffaqiyatli bajariladi"""
        self.perm_store.grant_permission("admin", "test_pc", "power.sleep")

        async def run():
            await self.orchestrator.process_telegram_message("111222333", "/sleep")
            await self.orchestrator.process_telegram_message("111222333", "/confirm")

        asyncio.run(run())

        self.assertEqual(len(self.orchestrator.pending_confirmations), 0)
        self.assertTrue(any("uyqu" in m.get("text", "").lower() or "bajarildi" in m.get("text", "").lower() for m in self.transport.sent_messages))

    def test_15_envelope_nonce_replay_protection(self):
        """15. RemoteCommandEnvelope takroriy nonce bilan kelgan soxta buyruqlarni bloklaydi"""
        env_mgr = EnvelopeManager()
        env = env_mgr.create_envelope(
            device_id="test_pc",
            action="system.status",
            params={"verbose": True}
        )

        ok, err = env_mgr.validate_envelope(env)
        self.assertTrue(ok)

        # Takroriy nonce bilan qayta yuborish
        ok_replay, err_replay = env_mgr.validate_envelope(env)
        self.assertFalse(ok_replay)
        self.assertIn("replay", err_replay.lower())

    def test_16_remote_tool_registry_safe_execution(self):
        """16. RemoteToolRegistry faqat xavfsiz belgilangan asboblarni bajaradi"""
        registry = RemoteToolRegistry.get_default_instance()
        self.assertTrue(registry.has_tool("system.status"))
        self.assertTrue(registry.has_tool("network.info"))
        self.assertTrue(registry.has_tool("file.list"))

        res = registry.execute_tool("system.status", {})
        self.assertTrue(res.get("ok"))
        self.assertIn("platform", res)

    def test_17_rejection_of_arbitrary_shell_and_eval(self):
        """17. Ixtiyoriy shell / eval / exec buyruqlari registry tomonidan qat'iy rad etiladi"""
        registry = RemoteToolRegistry.get_default_instance()
        res = registry.execute_tool("bash.execute", {"cmd": "rm -rf /"})
        self.assertFalse(res.get("ok"))
        self.assertIn("TOOL_NOT_FOUND", res.get("error", ""))

        res2 = registry.execute_tool("eval", {"code": "os.system('whoami')"})
        self.assertFalse(res2.get("ok"))

    def test_18_wol_permission_gating(self):
        """18. O'chiq kompyuterni uyg'otish uchun 'power.wake' ruxsati talab etiladi"""
        # Qurilmani offline qilamiz
        self.heartbeat._devices["test_pc"]["last_seen"] = time.time() - 100.0

        # power.wake ruxsati yo'q
        self.perm_store.revoke_permission("admin", "test_pc", "power.wake")

        async def run():
            await self.orchestrator.process_telegram_message("111222333", "/wake")

        asyncio.run(run())

        self.assertTrue(any("uyg'otish (WoL) uchun ruxsat berilmagan" in m.get("text", "") for m in self.transport.sent_messages))
        self.assertEqual(len(self.wake_relay.sent_packets), 0)

    def test_19_audit_log_secret_redaction(self):
        """19. Audit loglarida maxfiy kalitlar va pairing kodlar to'liq yashiriladi"""
        data = {
            "pairing_code": "MK-998877",
            "password": "SuperSecret123",
            "secret_hash": "sha256$abcdef",
            "device_id": "pc_01"
        }
        sanitized = sanitize_event_data(data)
        self.assertEqual(sanitized["pairing_code"], "***REDACTED***")
        self.assertEqual(sanitized["password"], "***REDACTED***")
        self.assertEqual(sanitized["secret_hash"], "***REDACTED***")
        self.assertEqual(sanitized["device_id"], "pc_01")

    def test_20_full_e2e_linking_permission_toggle_flow(self):
        """20. To'liq E2E: Hisobni ulash -> Ruxsat berish -> Buyruq bajarish -> Ruxsatni olish -> Darhol bloklash"""
        new_tg_user = "777888999"

        # A) Telegramda /pair orqali ulaymiz
        code = self.linking_store.generate_pairing_code("admin", "test_pc")

        async def step_a():
            await self.orchestrator.process_telegram_message(new_tg_user, f"/pair {code}")

        asyncio.run(step_a())
        self.assertTrue(any("muvaffaqiyatli bog'landi" in m.get("text", "") for m in self.transport.sent_messages))

        # B) Sessiyani ochamiz
        self.orchestrator.session_manager.open_session("admin", "test_pc")

        # C) Ruxsat beramiz: system.info
        self.perm_store.grant_permission("admin", "test_pc", "system.info")

        async def step_b():
            await self.orchestrator.process_telegram_message(new_tg_user, "/info")

        asyncio.run(step_b())
        step_b_texts = [m.get("text", "").upper() for m in self.transport.sent_messages]
        self.assertTrue(any("MA'LUMOT" in txt or "WINDOWS" in txt or "BAJARILDI" in txt for txt in step_b_texts))

        # D) Ruxsatni bekor qilamiz (serverni qayta ishga tushirmasdan)
        self.perm_store.revoke_permission("admin", "test_pc", "system.info")

        self.transport.sent_messages.clear()

        async def step_c():
            await self.orchestrator.process_telegram_message(new_tg_user, "/info")

        asyncio.run(step_c())
        self.assertTrue(any("Bu amal uchun ruxsat berilmagan" in m.get("text", "") for m in self.transport.sent_messages))


if __name__ == "__main__":
    unittest.main()
