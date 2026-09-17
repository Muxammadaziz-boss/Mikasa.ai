# ========== tests/test_v8_phase37.py ==========
# Phase 37 — Secure Remote Session Authentication Test Suite
# Exactly 14 comprehensive tests covering:
# 1. AuthEngine initialization & default credentials
# 2. Salted PBKDF2-HMAC-SHA256 hashing & constant-time verification
# 3. Wake pipeline challenge issuance upon reaching ONLINE
# 4. Correct password verification & session opening
# 5. Session TTL lifecycle & expiration cleanup
# 6. Wrong password remaining attempts decrement (3 -> 2 -> 1)
# 7. 3 consecutive failures activating 5-minute cooldown lockout
# 8. Cooldown lock blocking authentication attempts
# 9. Cooldown expiration & attempt reset
# 10. Session gating for protected commands
# 11. /logout and /session commands closing & inspecting sessions
# 12. Sensitive password & token sanitization in audit logs
# 13. Full Telegram E2E: Wake -> Online -> Challenge -> PIN Auth -> Command Execution
# 14. Full Telegram E2E: Wake -> 3 Wrong Passwords -> 5-min Cooldown Lockout

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
    MikasaPCAgent,
    TelegramRemoteGateway,
    MockTelegramTransport,
    RemoteOrchestrator,
    RemoteAuthSession,
    SessionManager,
    RemoteAuthEngine,
    RemoteEventType,
    RemoteAuditLogger,
    sanitize_sensitive_string,
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


class TestV8Phase37(unittest.TestCase):
    """
    Phase 37: Secure Remote Session Authentication
    14 ta talab bo'yicha to'liq test to'plami.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_v8_p37_")
        self.registry_path = os.path.join(self.test_dir, "devices.json")
        self.registry = DeviceRegistry(storage_path=self.registry_path)

        self.admin_id = "998901234567"
        self.transport = MockTelegramTransport()
        self.gateway = TelegramRemoteGateway(
            admin_id=self.admin_id,
            transport=self.transport
        )
        self.heartbeat_mgr = HeartbeatManager(stale_timeout=2.0)
        self.relay = MockWakeRelay(succeed=True)
        self.wol_mgr = WakeOnLanManager(relay=self.relay)
        self.envelope_mgr = EnvelopeManager(authorized_user_id=self.admin_id)

        self.session_mgr = SessionManager(default_ttl=900.0)
        self.auth_engine = RemoteAuthEngine(
            default_password="SecurePassword2026!",
            default_pin="7890",
            max_attempts=3,
            cooldown_seconds=300.0,
            session_manager=self.session_mgr
        )

        # Register dummy agent and target PC
        self.target_dev_id = "home_workstation_37"
        self.target_mac = "AA:BB:CC:DD:EE:37"
        self.target_device = DeviceIdentity(
            device_id=self.target_dev_id,
            hostname="WORKSTATION-37",
            mac_address=self.target_mac,
            fingerprint="f" * 64
        )
        self.registry.register_or_update(self.target_device)
        self.registry.pair_device(
            device_id=self.target_dev_id,
            user_id=self.admin_id,
            fingerprint=self.target_device.fingerprint,
            mac_address=self.target_mac
        )

        self.pc_agent = MikasaPCAgent(
            identity=self.target_device,
            envelope_manager=self.envelope_mgr,
            heartbeat_interval=0.1
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # ========================================================
    # TEST 1: AuthEngine Initialization
    # ========================================================
    def test_01_auth_engine_init(self):
        """1. RemoteAuthEngine standart parametrlari va dastlabki holati tekshiruvi"""
        engine = RemoteAuthEngine(
            default_password="SecretPass123!",
            default_pin="4321",
            max_attempts=3,
            cooldown_seconds=300.0
        )
        self.assertEqual(engine.max_attempts, 3)
        self.assertEqual(engine.cooldown_seconds, 300.0)
        self.assertIsNotNone(engine.session_manager)
        self.assertIsNotNone(engine._password_hash)
        self.assertIsNotNone(engine._pin_hash)
        self.assertTrue(engine._password_hash.startswith("pbkdf2:sha256:100000:"))
        self.assertTrue(engine._pin_hash.startswith("pbkdf2:sha256:100000:"))

        # Dastlabki holatda hech qanday foydalanuvchi cooldown'da emas
        is_cd, rem = engine.is_in_cooldown("user1")
        self.assertFalse(is_cd)
        self.assertEqual(rem, 0.0)
        self.assertEqual(engine.get_remaining_attempts("user1"), 3)
        self.assertFalse(engine.is_auth_pending("user1"))

    # ========================================================
    # TEST 2: PBKDF2 Password Hashing & Constant-Time Verification
    # ========================================================
    def test_02_password_hashing(self):
        """2. Tuzlangan PBKDF2-HMAC-SHA256 xeshlash va constant-time solishtirish"""
        secret = "MySuperSecretKey"
        hash1 = RemoteAuthEngine.hash_secret(secret)
        hash2 = RemoteAuthEngine.hash_secret(secret)

        # Turli tuz (salt) ishlatilgani sabab xeshlar bir-biriga teng bo'lmasligi kerak
        self.assertNotEqual(hash1, hash2)
        self.assertTrue(hash1.startswith("pbkdf2:sha256:100000:"))

        # To'g'ri kalit bilan tekshirish
        self.assertTrue(RemoteAuthEngine.verify_hash(secret, hash1))
        self.assertTrue(RemoteAuthEngine.verify_hash(secret, hash2))

        # Noto'g'ri kalit bilan tekshirish
        self.assertFalse(RemoteAuthEngine.verify_hash("WrongSecretKey", hash1))
        self.assertFalse(RemoteAuthEngine.verify_hash("", hash1))

        # Buzilgan xesh stringlari xato tashlamay False qaytarishi
        self.assertFalse(RemoteAuthEngine.verify_hash(secret, "invalid_hash_format"))
        self.assertFalse(RemoteAuthEngine.verify_hash(secret, "pbkdf2:md5:100:salt:key"))

    # ========================================================
    # TEST 3: Challenge Issued on Wake Pipeline
    # ========================================================
    def test_03_challenge_issued_on_wake(self):
        """3. Kompyuter ONLINE holatiga yetgach avtomatik auth challenge chiqarilishi"""
        async def _run():
            orch = RemoteOrchestrator(
                gateway=self.gateway,
                heartbeat_manager=self.heartbeat_mgr,
                wol_manager=self.wol_mgr,
                envelope_manager=self.envelope_mgr,
                device_registry=self.registry,
                pc_agent=self.pc_agent,
                session_manager=self.session_mgr,
                auth_engine=self.auth_engine
            )

            self.heartbeat_mgr.register_device(self.target_dev_id, initial_state=DeviceState.OFFLINE)

            # Simulyatsiya: WoL yuborilgach PC agent heartbeat yuboradi
            async def _delayed_heartbeat():
                await asyncio.sleep(0.1)
                self.heartbeat_mgr.record_heartbeat(
                    HeartbeatPayload(device_id=self.target_dev_id, timestamp=time.time(), state=DeviceState.ONLINE)
                )

            asyncio.create_task(_delayed_heartbeat())

            res = await orch.execute_wake_pipeline(
                device_id=self.target_dev_id,
                mac_address=self.target_mac,
                chat_id=1001,
                user_id=self.admin_id,
                wait_timeout=2.0,
                poll_interval=0.05
            )

            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("state"), "online")
            self.assertTrue(res.get("auth_required"))
            self.assertTrue(self.auth_engine.is_auth_pending(self.admin_id))

            # Telegramga parol so'rovi xabari yuborilganini tekshirish
            sent_msgs = self.transport.sent_messages
            self.assertTrue(any("Parolni tasdiqlang" in m.get("text", "") for m in sent_msgs))

        asyncio.run(_run())

    # ========================================================
    # TEST 4: Correct Password Opens Session
    # ========================================================
    def test_04_correct_password_opens_session(self):
        """4. To'g'ri parol yoki PIN kiritilganda faol sessiya ochilishi"""
        async def _run():
            orch = RemoteOrchestrator(
                gateway=self.gateway,
                heartbeat_manager=self.heartbeat_mgr,
                wol_manager=self.wol_mgr,
                envelope_manager=self.envelope_mgr,
                device_registry=self.registry,
                pc_agent=self.pc_agent,
                session_manager=self.session_mgr,
                auth_engine=self.auth_engine
            )

            # Autentifikatsiya kutish holatiga qo'yish
            self.auth_engine.set_auth_pending(self.admin_id, self.target_dev_id, True)
            self.assertTrue(self.auth_engine.is_auth_pending(self.admin_id))

            # To'g'ri parolni yuborish
            res = await orch.handle_message(
                chat_id=1002,
                user_id=self.admin_id,
                text="SecurePassword2026!"
            )

            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("action"), "auth_success")
            self.assertIsNotNone(res.get("session_id"))

            # Pending challenge yopilgan bo'lishi kerak
            self.assertFalse(self.auth_engine.is_auth_pending(self.admin_id))

            # Faol sessiya mavjudligi
            session = self.session_mgr.get_active_session(self.admin_id, self.target_dev_id)
            self.assertIsNotNone(session)
            self.assertTrue(session.is_valid())
            self.assertEqual(session.session_id, res.get("session_id"))

            # Telegram xabari
            last_msg = self.transport.sent_messages[-1]["text"]
            self.assertIn("Parol tasdiqlandi", last_msg)

        asyncio.run(_run())

    # ========================================================
    # TEST 5: Session TTL and Expiry
    # ========================================================
    def test_05_session_ttl_and_expiry(self):
        """5. Sessiya TTL muddati, yaroqliligi va muddati o'tganda avtomatik yopilishi"""
        session = self.session_mgr.create_session("u5", "dev5", ttl=900.0)
        self.assertIsInstance(session, RemoteAuthSession)
        self.assertEqual(session.user_id, "u5")
        self.assertEqual(session.device_id, "dev5")
        self.assertTrue(session.is_active)

        # Yaratilgan vaqtdan 500s o'tgach faol
        self.assertTrue(session.is_valid(current_time=session.created_at + 500.0))

        # Yaratilgan vaqtdan 901s o'tgach muddati o'tgan
        self.assertFalse(session.is_valid(current_time=session.created_at + 901.0))

        # SessionManager orqali so'ralganda muddati o'tgan sessiya None qaytaradi
        active = self.session_mgr.get_active_session("u5", "dev5", current_time=session.created_at + 901.0)
        self.assertIsNone(active)
        self.assertFalse(session.is_active)

        # cleanup_expired_sessions
        s2 = self.session_mgr.create_session("u5_2", "dev5", ttl=100.0)
        cleaned = self.session_mgr.cleanup_expired_sessions(current_time=s2.created_at + 150.0)
        self.assertGreaterEqual(cleaned, 1)

    # ========================================================
    # TEST 6: Wrong Password Remaining Attempts Decrement
    # ========================================================
    def test_06_wrong_password_decrement(self):
        """6. Noto'g'ri parol kiritilganda urinishlar sonining kamayishi (3 -> 2 -> 1)"""
        uid = "user_6"
        dev = "dev_6"

        self.assertEqual(self.auth_engine.get_remaining_attempts(uid), 3)

        # 1-noto'g'ri urinish
        ok, msg, sess = self.auth_engine.verify_secret(uid, dev, "wrong_pass_1")
        self.assertFalse(ok)
        self.assertIsNone(sess)
        self.assertEqual(self.auth_engine.get_remaining_attempts(uid), 2)
        self.assertIn("2 ta", msg)

        # 2-noto'g'ri urinish
        ok, msg, sess = self.auth_engine.verify_secret(uid, dev, "wrong_pass_2")
        self.assertFalse(ok)
        self.assertIsNone(sess)
        self.assertEqual(self.auth_engine.get_remaining_attempts(uid), 1)
        self.assertIn("1 ta", msg)

        # Hali cooldown faollashmagan
        in_cd, _ = self.auth_engine.is_in_cooldown(uid)
        self.assertFalse(in_cd)

    # ========================================================
    # TEST 7: Three Consecutive Failures Triggers Cooldown
    # ========================================================
    def test_07_three_failures_triggers_cooldown(self):
        """7. Ketma-ket 3 ta xato urinishdan so'ng 5 daqiqalik cooldown faollashishi"""
        uid = "user_7"
        dev = "dev_7"

        self.auth_engine.verify_secret(uid, dev, "bad1")
        self.auth_engine.verify_secret(uid, dev, "bad2")
        ok, msg, sess = self.auth_engine.verify_secret(uid, dev, "bad3")

        self.assertFalse(ok)
        self.assertIsNone(sess)
        self.assertIn("COOLDOWN_ACTIVATED", msg)
        self.assertEqual(self.auth_engine.get_remaining_attempts(uid), 0)

        in_cd, rem = self.auth_engine.is_in_cooldown(uid)
        self.assertTrue(in_cd)
        self.assertGreater(rem, 250.0)
        self.assertLessEqual(rem, 300.0)

    # ========================================================
    # TEST 8: Cooldown Blocks Further Attempts
    # ========================================================
    def test_08_cooldown_blocks_attempts(self):
        """8. Cooldown davrida hatto to'g'ri parol ham qat'iy bloklanishi"""
        uid = "user_8"
        dev = "dev_8"

        # 3 ta xato urinish bilan cooldown'ga tushirish
        for _ in range(3):
            self.auth_engine.verify_secret(uid, dev, "bad_secret")

        in_cd, _ = self.auth_engine.is_in_cooldown(uid)
        self.assertTrue(in_cd)

        # Endi TO'G'RI parolni kiritishga urinish
        ok, msg, sess = self.auth_engine.verify_secret(uid, dev, "SecurePassword2026!")
        self.assertFalse(ok)
        self.assertIsNone(sess)
        self.assertIn("COOLDOWN_ACTIVE", msg)

        # Sessiya ochilmaganligini tekshirish
        self.assertIsNone(self.session_mgr.get_active_session(uid, dev))

    # ========================================================
    # TEST 9: Cooldown Expiry and Reset
    # ========================================================
    def test_09_cooldown_expiry(self):
        """9. Cooldown muddati (300s) o'tgach yoki reset qilinganda blokirovkaning yechilishi"""
        uid = "user_9"
        dev = "dev_9"
        start_time = 1000.0

        for _ in range(3):
            self.auth_engine.verify_secret(uid, dev, "bad", current_time=start_time)

        # 100 soniyadan so'ng hali ham cooldown faol
        in_cd, rem = self.auth_engine.is_in_cooldown(uid, current_time=start_time + 100.0)
        self.assertTrue(in_cd)
        self.assertEqual(int(rem), 200)

        # 301 soniyadan so'ng cooldown tugagan
        in_cd, rem = self.auth_engine.is_in_cooldown(uid, current_time=start_time + 301.0)
        self.assertFalse(in_cd)
        self.assertEqual(rem, 0.0)

        # Endi to'g'ri parol bilan muvaffaqiyatli autentifikatsiya
        ok, msg, sess = self.auth_engine.verify_secret(uid, dev, "SecurePassword2026!", current_time=start_time + 302.0)
        self.assertTrue(ok)
        self.assertIsNotNone(sess)

        # reset_cooldown funksiyasi
        self.auth_engine.reset_cooldown(uid)
        self.assertEqual(self.auth_engine.get_remaining_attempts(uid), 3)

    # ========================================================
    # TEST 10: Session Command Authorization Gating
    # ========================================================
    def test_10_session_command_authorization(self):
        """10. require_session_auth=True bo'lganda himoyalangan buyruqlarning sessiya talab qilishi"""
        async def _run():
            orch = RemoteOrchestrator(
                gateway=self.gateway,
                heartbeat_manager=self.heartbeat_mgr,
                wol_manager=self.wol_mgr,
                envelope_manager=self.envelope_mgr,
                device_registry=self.registry,
                pc_agent=self.pc_agent,
                session_manager=self.session_mgr,
                auth_engine=self.auth_engine,
                require_session_auth=True
            )

            # 1. Sessiyasiz himoyalangan buyruq yuborish
            res = await orch.handle_message(chat_id=1010, user_id=self.admin_id, text="system_info")
            self.assertFalse(res.get("success"))
            self.assertEqual(res.get("error"), "SESSION_REQUIRED")
            self.assertTrue(res.get("auth_required"))
            self.assertTrue(self.auth_engine.is_auth_pending(self.admin_id))

            # 2. To'g'ri PIN orqali sessiya ochish
            auth_res = await orch.handle_message(chat_id=1010, user_id=self.admin_id, text="7890")
            self.assertTrue(auth_res.get("success"))
            self.assertEqual(auth_res.get("action"), "auth_success")

            # 3. Endi himoyalangan buyruq muvaffaqiyatli bajarilishi
            exec_res = await orch.handle_message(chat_id=1010, user_id=self.admin_id, text="system_info")
            self.assertTrue(exec_res.get("success"))

        asyncio.run(_run())

    # ========================================================
    # TEST 11: /logout and /session Commands
    # ========================================================
    def test_11_logout_and_session_close(self):
        """11. /logout buyrug'i orqali sessiyani yopish va /session orqali holatni ko'rish"""
        async def _run():
            orch = RemoteOrchestrator(
                gateway=self.gateway,
                heartbeat_manager=self.heartbeat_mgr,
                wol_manager=self.wol_mgr,
                envelope_manager=self.envelope_mgr,
                device_registry=self.registry,
                pc_agent=self.pc_agent,
                session_manager=self.session_mgr,
                auth_engine=self.auth_engine
            )

            # Sessiya yaratish
            self.session_mgr.create_session(self.admin_id, self.target_dev_id, ttl=600.0)
            self.assertIsNotNone(self.session_mgr.get_active_session(self.admin_id, self.target_dev_id))

            # /session buyrug'i
            sess_res = await orch.handle_message(chat_id=1011, user_id=self.admin_id, text="/session")
            self.assertTrue(sess_res.get("success"))
            self.assertTrue(sess_res.get("active"))

            # /logout buyrug'i
            logout_res = await orch.handle_message(chat_id=1011, user_id=self.admin_id, text="/logout")
            self.assertTrue(logout_res.get("success"))
            self.assertTrue(logout_res.get("closed"))

            # Endi faol sessiya yo'qligini tekshirish
            self.assertIsNone(self.session_mgr.get_active_session(self.admin_id, self.target_dev_id))

            # Qayta /session buyrug'i nofaol qaytarishi kerak
            sess_res2 = await orch.handle_message(chat_id=1011, user_id=self.admin_id, text="/session")
            self.assertTrue(sess_res2.get("success"))
            self.assertFalse(sess_res2.get("active"))

        asyncio.run(_run())

    # ========================================================
    # TEST 12: Password Sanitization in Audit Logs
    # ========================================================
    def test_12_password_sanitization_in_logs(self):
        """12. Parol, PIN va tokenlarning audit loglarda ochiq matn ko'rinishida saqlanmasligi"""
        # Matn sanitizatsiyasi
        plain = "My secret is password123 and pin=9988"
        masked = sanitize_sensitive_string(plain)
        self.assertNotIn("password123", masked)
        self.assertNotIn("9988", masked)

        # Lug'at sanitizatsiyasi
        data = {
            "user_id": "123",
            "password": "SuperSecretPassword!",
            "pin": "1234",
            "session_token": "tok_xyz_999",
            "safe_param": "hello"
        }
        sanitized = sanitize_event_data(data)
        self.assertEqual(sanitized["user_id"], "123")
        self.assertEqual(sanitized["safe_param"], "hello")
        self.assertEqual(sanitized["password"], "***REDACTED***")
        self.assertEqual(sanitized["pin"], "***REDACTED***")
        self.assertEqual(sanitized["session_token"], "***REDACTED***")

        # Audit loggerga yozilganda ham tekshirish
        logger = RemoteAuditLogger.get_instance()
        event = logger.log(RemoteEventType.AUTH_ATTEMPT_FAILED, user_id="u12", pin="9876", password="plain_secret")
        self.assertEqual(event.details["pin"], "***REDACTED***")
        self.assertEqual(event.details["password"], "***REDACTED***")

    # ========================================================
    # TEST 13: Mocked Telegram Auth E2E (Success Flow)
    # ========================================================
    def test_13_mocked_telegram_auth_e2e(self):
        """13. To'liq E2E ssenariy: Wake -> PC Online -> Telegram PIN so'rovi -> PIN Auth -> Buyruq bajarilishi"""
        async def _run():
            orch = RemoteOrchestrator(
                gateway=self.gateway,
                heartbeat_manager=self.heartbeat_mgr,
                wol_manager=self.wol_mgr,
                envelope_manager=self.envelope_mgr,
                device_registry=self.registry,
                pc_agent=self.pc_agent,
                session_manager=self.session_mgr,
                auth_engine=self.auth_engine,
                require_session_auth=True
            )

            dev_id = self.target_dev_id
            self.heartbeat_mgr.register_device(dev_id, initial_state=DeviceState.OFFLINE)

            # 1. Foydalanuvchi Telegramdan "Kompyuterni uyg'ot" yozadi
            async def _reply_online():
                await asyncio.sleep(0.1)
                self.heartbeat_mgr.record_heartbeat(
                    HeartbeatPayload(device_id=dev_id, timestamp=time.time(), state=DeviceState.ONLINE)
                )

            asyncio.create_task(_reply_online())

            wake_res = await orch.handle_message(
                chat_id=1013,
                user_id=self.admin_id,
                text="Kompyuterni uyg'ot"
            )
            self.assertTrue(wake_res.get("success"))
            self.assertTrue(wake_res.get("auth_required"))
            self.assertTrue(self.auth_engine.is_auth_pending(self.admin_id))

            # 2. Telegramda parolni kiritish taklifi borligini tasdiqlash
            last_msg = self.transport.sent_messages[-1]["text"]
            self.assertIn("Parolni tasdiqlang", last_msg)

            # 3. Foydalanuvchi to'g'ri PIN kodni yuboradi: "7890"
            pin_res = await orch.handle_message(
                chat_id=1013,
                user_id=self.admin_id,
                text="7890"
            )
            self.assertTrue(pin_res.get("success"))
            self.assertEqual(pin_res.get("action"), "auth_success")
            self.assertFalse(self.auth_engine.is_auth_pending(self.admin_id))

            # 4. Sessiya muvaffaqiyatli ochilganidan so'ng buyruq yuborish
            cmd_res = await orch.handle_message(
                chat_id=1013,
                user_id=self.admin_id,
                text="system_info"
            )
            self.assertTrue(cmd_res.get("success"))

        asyncio.run(_run())

    # ========================================================
    # TEST 14: Mocked Telegram Auth Failure & Cooldown E2E
    # ========================================================
    def test_14_mocked_telegram_auth_failure_and_cooldown_e2e(self):
        """14. To'liq E2E ssenariy: Wake -> 3 ta xato parol -> 5 daqiqalik blokirovka -> Keyingi urinishlar rad etilishi"""
        async def _run():
            orch = RemoteOrchestrator(
                gateway=self.gateway,
                heartbeat_manager=self.heartbeat_mgr,
                wol_manager=self.wol_mgr,
                envelope_manager=self.envelope_mgr,
                device_registry=self.registry,
                pc_agent=self.pc_agent,
                session_manager=self.session_mgr,
                auth_engine=self.auth_engine,
                require_session_auth=True
            )

            # Autentifikatsiya so'rovini yoqish
            self.auth_engine.set_auth_pending(self.admin_id, self.target_dev_id, True)

            # 1-noto'g'ri urinish
            res1 = await orch.handle_message(chat_id=1014, user_id=self.admin_id, text="wrong1")
            self.assertFalse(res1.get("success"))
            self.assertEqual(res1.get("action"), "auth_failed")
            self.assertIn("Qolgan urinishlar: `2` ta", self.transport.sent_messages[-1]["text"])

            # 2-noto'g'ri urinish
            res2 = await orch.handle_message(chat_id=1014, user_id=self.admin_id, text="wrong2")
            self.assertFalse(res2.get("success"))
            self.assertEqual(res2.get("action"), "auth_failed")
            self.assertIn("Qolgan urinishlar: `1` ta", self.transport.sent_messages[-1]["text"])

            # 3-noto'g'ri urinish -> Cooldown
            res3 = await orch.handle_message(chat_id=1014, user_id=self.admin_id, text="wrong3")
            self.assertFalse(res3.get("success"))
            self.assertEqual(res3.get("action"), "auth_failed")
            self.assertIn("Xavfsizlik blokirovkasi", self.transport.sent_messages[-1]["text"])

            # Cooldown holatini tekshirish
            is_cd, rem = self.auth_engine.is_in_cooldown(self.admin_id)
            self.assertTrue(is_cd)
            self.assertGreater(rem, 250.0)

            # 4-urinish (hatto to'g'ri parol bo'lsa ham) qat'iy rad etilishi
            res4 = await orch.handle_message(chat_id=1014, user_id=self.admin_id, text="SecurePassword2026!")
            self.assertFalse(res4.get("success"))
            self.assertIn("Xavfsizlik blokirovkasi", self.transport.sent_messages[-1]["text"])

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
