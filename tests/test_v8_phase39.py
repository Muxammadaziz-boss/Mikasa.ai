# ========== tests/test_v8_phase39.py ==========
# Phase 39 — Universal Telegram Bot ↔ Mikasa User App
# Comprehensive Multi-User Identity & OTP Account Linking Test Suite
# Minimum 27 unit & integration tests covering all Phase 39 specifications

import os
import shutil
import tempfile
import unittest
import asyncio

from core.v8.events import RemoteEventType, RemoteAuditLogger
from core.v8.telegram_gateway import MockTelegramTransport
from core.v8.telegram_identity import (
    TelegramIdentity,
    TelegramIdentityManager
)
from core.v8.universal_bot import UniversalTelegramBot


class TestPhase39TelegramIdentity(unittest.TestCase):
    """1-5: Canonical Identity, Entropy, Data Models, Plaintext Secret Protection"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p39_")
        self.storage_file = os.path.join(self.temp_dir, "telegram_links.json")
        self.mgr = TelegramIdentityManager(storage_path=self.storage_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_telegram_identity_canonical_numeric_id(self):
        """1. Telegram identity must be strictly canonicalized by positive integer."""
        # Valid integer
        ident1 = TelegramIdentity(123456789, first_name="Ali", username="ali_dev")
        self.assertTrue(ident1.is_valid())
        self.assertEqual(ident1.user_id, 123456789)

        # Valid string digits normalized to integer
        is_val, uid = TelegramIdentity.validate_user_id("987654321")
        self.assertTrue(is_val)
        self.assertEqual(uid, 987654321)

        # Rejection of invalid types and values
        invalid_cases = [-100, 0, "abc", "-123", "", None, True, False, "@username", "12.34"]
        for invalid in invalid_cases:
            is_valid, parsed = TelegramIdentity.validate_user_id(invalid)
            self.assertFalse(is_valid, f"Expected {invalid} to be invalid")
            self.assertIsNone(parsed)

    def test_02_telegram_identity_serialization(self):
        """2. TelegramIdentity serialization and deserialization roundtrip."""
        ident = TelegramIdentity(
            telegram_user_id=999888777,
            first_name="Sardor",
            username="sardor_uz",
            created_at=1000.0,
            last_seen_at=2000.0,
            is_verified=True,
            is_linked=True
        )
        d = ident.to_dict()
        self.assertEqual(d["telegram_user_id"], 999888777)
        self.assertEqual(d["first_name"], "Sardor")
        self.assertEqual(d["username"], "sardor_uz")
        self.assertTrue(d["is_verified"])
        self.assertTrue(d["is_linked"])

        reconstructed = TelegramIdentity.from_dict(d)
        self.assertEqual(reconstructed.telegram_user_id, 999888777)
        self.assertEqual(reconstructed.username, "sardor_uz")
        self.assertTrue(reconstructed.is_valid())

    def test_03_otp_generation_format_and_entropy(self):
        """3. OTP generation produces 6-digit numeric string with high entropy."""
        otps = set()
        for _ in range(50):
            req, otp, deep_link, err = self.mgr.create_link_request(
                mikasa_user_id=f"user_{_}",
                current_time=1000.0
            )
            self.assertIsNone(err)
            self.assertIsNotNone(otp)
            self.assertEqual(len(otp), 6)
            self.assertTrue(otp.isdigit())
            self.assertTrue(100000 <= int(otp) <= 999999)
            otps.add(otp)

        # High entropy: in 50 random 6-digit numbers, virtually all should be unique
        self.assertGreater(len(otps), 45)

    def test_04_plaintext_otp_not_persisted(self):
        """4. Plaintext OTP is NEVER stored in request object, database, or disk."""
        req, plaintext_otp, deep_link, err = self.mgr.create_link_request("alice")
        self.assertIsNone(err)

        # Inspect request object
        req_dict = req.to_dict()
        self.assertNotIn("otp", req_dict)
        self.assertIn("otp_hash", req_dict)
        self.assertIn("salt", req_dict)
        self.assertNotEqual(req.otp_hash, plaintext_otp)

        # Inspect saved file on disk
        self.mgr.save()
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn(plaintext_otp, content)
        self.assertIn(req.otp_hash, content)

    def test_05_link_token_generation(self):
        """5. Cryptographically secure link_token and deep link URL format."""
        req, otp, deep_link, err = self.mgr.create_link_request(
            mikasa_user_id="bob",
            bot_username="MikasaTestBot"
        )
        self.assertIsNone(err)
        self.assertIsNotNone(req.link_token)
        self.assertGreaterEqual(len(req.link_token), 24)
        self.assertTrue(deep_link.startswith("https://t.me/MikasaTestBot?start="))
        self.assertTrue(deep_link.endswith(req.link_token))


class TestPhase39OtpVerificationAndSecurity(unittest.TestCase):
    """6-12: OTP Verification, Constant-time compare, Replay, Expiry, Lockout, Rate Limiting"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p39_sec_")
        self.storage_file = os.path.join(self.temp_dir, "telegram_links.json")
        self.mgr = TelegramIdentityManager(storage_path=self.storage_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_06_otp_verification_success(self):
        """6. Successful OTP verification creates active UserTelegramLink."""
        req, otp, deep_link, err = self.mgr.create_link_request("user_alpha")
        self.assertIsNone(err)

        ok, msg, link = self.mgr.verify_otp(
            otp=otp,
            telegram_user_id=123456789,
            first_name="Alpha",
            username="alpha_tg"
        )
        self.assertTrue(ok)
        self.assertIn("muvaffaqiyatli", msg)
        self.assertIsNotNone(link)
        self.assertEqual(link.mikasa_user_id, "user_alpha")
        self.assertEqual(link.telegram_user_id, 123456789)
        self.assertEqual(link.status, "ACTIVE")
        self.assertTrue(link.is_active)

        # Check request state
        req_updated = self.mgr.get_request(req.request_id)
        self.assertEqual(req_updated.status, "VERIFIED")
        self.assertEqual(req_updated.telegram_user_id, 123456789)

    def test_07_constant_time_comparison(self):
        """7. Constant-time digest comparison rejects invalid hashes."""
        salt = "0123456789abcdef"
        otp = "654321"
        valid_hash = self.mgr.hash_otp(otp, salt)

        # Correct hash returns True
        self.assertTrue(self.mgr.verify_otp_hash(otp, salt, valid_hash))
        # Wrong OTP returns False
        self.assertFalse(self.mgr.verify_otp_hash("000000", salt, valid_hash))
        # Tampered hash returns False
        tampered_hash = valid_hash[:-4] + "0000"
        self.assertFalse(self.mgr.verify_otp_hash(otp, salt, tampered_hash))

    def test_08_single_use_otp_replay_protection(self):
        """8. Replay protection: Used OTP cannot be redeemed a second time."""
        req, otp, _, _ = self.mgr.create_link_request("user_beta")
        ok1, _, link1 = self.mgr.verify_otp(otp, 111222333)
        self.assertTrue(ok1)

        # Second attempt with same OTP
        ok2, msg2, link2 = self.mgr.verify_otp(otp, 111222333)
        self.assertFalse(ok2)
        self.assertIn("CODE_ALREADY_USED", msg2)
        self.assertIsNone(link2)

    def test_09_expired_otp_rejection(self):
        """9. Expired OTP (beyond 300s TTL) is rejected."""
        t0 = 10000.0
        req, otp, _, _ = self.mgr.create_link_request("user_gamma", ttl=300.0, current_time=t0)

        # Attempt redemption at t0 + 301 seconds
        ok, msg, link = self.mgr.verify_otp(otp, 444555666, current_time=t0 + 301.0)
        self.assertFalse(ok)
        self.assertIn("CODE_EXPIRED", msg)
        self.assertIsNone(link)

    def test_10_invalid_otp_attempt_counter(self):
        """10. Wrong OTP attempts increment attempt_count and report remaining attempts."""
        req, otp, _, _ = self.mgr.create_link_request("user_delta")
        ok, msg, link = self.mgr.verify_otp("000000", 777888999, request_id=req.request_id)
        self.assertFalse(ok)
        self.assertIn("INVALID_OTP", msg)
        self.assertIn("Qolgan urinishlar", msg)

        req_updated = self.mgr.get_request(req.request_id)
        self.assertEqual(req_updated.attempt_count, 1)

    def test_11_max_attempts_lockout(self):
        """11. 5 consecutive wrong OTP attempts transition request to FAILED (lockout)."""
        req, otp, _, _ = self.mgr.create_link_request("user_epsilon")

        # 5 wrong attempts
        for i in range(5):
            ok, msg, _ = self.mgr.verify_otp("000000", 123123123, request_id=req.request_id)
            self.assertFalse(ok)

        req_updated = self.mgr.get_request(req.request_id)
        self.assertEqual(req_updated.status, "FAILED")
        self.assertEqual(req_updated.attempt_count, 5)

        # 6th attempt with correct OTP is rejected because request is locked
        ok6, msg6, _ = self.mgr.verify_otp(otp, 123123123, request_id=req.request_id)
        self.assertFalse(ok6)
        self.assertIn("MAX_ATTEMPTS_EXCEEDED", msg6)

    def test_12_rate_limiting_otp_generation(self):
        """12. Rate limiting: max 3 OTP generation requests per 10 minutes per Mikasa account."""
        t0 = 50000.0
        # 3 allowed requests
        for i in range(3):
            req, otp, _, err = self.mgr.create_link_request("heavy_user", current_time=t0 + i)
            self.assertIsNone(err)
            self.assertIsNotNone(req)

        # 4th request within 10 minutes is blocked
        req4, otp4, _, err4 = self.mgr.create_link_request("heavy_user", current_time=t0 + 100.0)
        self.assertIsNone(req4)
        self.assertIn("RATE_LIMITED", err4)

        # After 10 minutes (601 seconds), new request is allowed
        req5, otp5, _, err5 = self.mgr.create_link_request("heavy_user", current_time=t0 + 601.0)
        self.assertIsNone(err5)
        self.assertIsNotNone(req5)


class TestPhase39DeepLinkAndUnlink(unittest.TestCase):
    """13-17: Deep-link token, Unlink, Cleanup, Multi-user Isolation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p39_link_")
        self.storage_file = os.path.join(self.temp_dir, "telegram_links.json")
        self.mgr = TelegramIdentityManager(storage_path=self.storage_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_13_deep_link_token_verification(self):
        """13. Deep-link token redemption links Telegram account directly."""
        req, otp, deep_link, err = self.mgr.create_link_request("deeplink_user")
        self.assertIsNone(err)

        ok, msg, link = self.mgr.verify_link_token(
            link_token=req.link_token,
            telegram_user_id=987123654,
            first_name="Deep",
            username="deep_link_user"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(link)
        self.assertEqual(link.telegram_user_id, 987123654)
        self.assertEqual(link.mikasa_user_id, "deeplink_user")

    def test_14_single_use_link_token(self):
        """14. Single-use deep-link token cannot be reused."""
        req, _, _, _ = self.mgr.create_link_request("token_user")
        ok1, _, _ = self.mgr.verify_link_token(req.link_token, 11223344)
        self.assertTrue(ok1)

        # Attempt 2
        ok2, msg2, _ = self.mgr.verify_link_token(req.link_token, 11223344)
        self.assertFalse(ok2)
        self.assertIn("TOKEN_ALREADY_USED", msg2)

    def test_15_unlink_flow(self):
        """15. Unlinking sets link status to REVOKED and removes active association."""
        req, otp, _, _ = self.mgr.create_link_request("unlink_user")
        self.mgr.verify_otp(otp, 99001122)
        self.assertIsNotNone(self.mgr.get_link_by_telegram_user(99001122))

        # Unlink by Telegram ID
        unlinked = self.mgr.unlink(telegram_user_id=99001122)
        self.assertTrue(unlinked)
        self.assertIsNone(self.mgr.get_link_by_telegram_user(99001122))
        self.assertIsNone(self.mgr.get_link_by_mikasa_user("unlink_user"))

        # Unlinking non-existent returns False
        self.assertFalse(self.mgr.unlink(telegram_user_id=99001122))

    def test_16_pending_requests_cancelled_on_unlink(self):
        """16. Unlinking revokes pending pairing requests for that user."""
        req1, otp1, _, _ = self.mgr.create_link_request("user_cancel")
        self.mgr.verify_otp(otp1, 55443322)

        # Create a second pending request
        req2, otp2, _, _ = self.mgr.create_link_request("user_cancel")
        self.assertEqual(req2.status, "PENDING")

        # Unlink user
        self.mgr.unlink(mikasa_user_id="user_cancel")
        req2_updated = self.mgr.get_request(req2.request_id)
        self.assertEqual(req2_updated.status, "EXPIRED")

    def test_17_multi_user_isolation(self):
        """17. Complete multi-user tenant isolation without state bleeding."""
        # User 1
        req1, otp1, _, _ = self.mgr.create_link_request("user_one")
        ok1, _, link1 = self.mgr.verify_otp(otp1, 1010101, username="one_tg")
        self.assertTrue(ok1)

        # User 2
        req2, otp2, _, _ = self.mgr.create_link_request("user_two")
        ok2, _, link2 = self.mgr.verify_otp(otp2, 2020202, username="two_tg")
        self.assertTrue(ok2)

        # Assert isolated lookups
        l1 = self.mgr.get_link_by_telegram_user(1010101)
        l2 = self.mgr.get_link_by_telegram_user(2020202)
        self.assertEqual(l1.mikasa_user_id, "user_one")
        self.assertEqual(l2.mikasa_user_id, "user_two")

        # Unlink user_one should NOT affect user_two
        self.mgr.unlink(mikasa_user_id="user_one")
        self.assertIsNone(self.mgr.get_link_by_mikasa_user("user_one"))
        self.assertIsNotNone(self.mgr.get_link_by_mikasa_user("user_two"))


class TestPhase39UniversalBot(unittest.TestCase):
    """18-25: Universal Bot Commands (/start, /link, raw OTP, /unlink, /account, /status, /help)"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p39_bot_")
        self.storage_file = os.path.join(self.temp_dir, "telegram_links.json")
        self.mgr = TelegramIdentityManager(storage_path=self.storage_file)
        self.transport = MockTelegramTransport()
        self.bot = UniversalTelegramBot(
            transport=self.transport,
            identity_manager=self.mgr,
            bot_username="MikasaUniversalBot"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_18_bot_start_without_token(self):
        """18. Bot /start without arguments returns welcome guide in Uzbek."""
        update = {
            "message": {
                "message_id": 1,
                "chat": {"id": 1001},
                "from": {"id": 1001, "first_name": "Islom", "username": "islom_dev"},
                "text": "/start"
            }
        }
        asyncio.run(self.bot.process_update(update))
        self.assertEqual(len(self.transport.sent_messages), 1)
        sent = self.transport.sent_messages[0]
        self.assertEqual(sent["chat"]["id"], 1001)
        self.assertIn("Assalomu alaykum", sent["text"])
        self.assertIn("Mikasa AI Universal Telegram Botiga xush kelibsiz", sent["text"])

    def test_19_bot_start_with_token(self):
        """19. Bot /start <link_token> performs automatic account linking."""
        req, otp, _, _ = self.mgr.create_link_request("bot_user_1")
        update = {
            "message": {
                "message_id": 2,
                "chat": {"id": 2002},
                "from": {"id": 2002, "first_name": "Aziz", "username": "aziz_tg"},
                "text": f"/start {req.link_token}"
            }
        }
        asyncio.run(self.bot.process_update(update))
        self.assertEqual(len(self.transport.sent_messages), 1)
        sent = self.transport.sent_messages[0]
        self.assertIn("Tabriklaymiz", sent["text"])
        self.assertIn("bot_user_1", sent["text"])

        # Check identity manager state
        link = self.mgr.get_link_by_telegram_user(2002)
        self.assertIsNotNone(link)
        self.assertEqual(link.mikasa_user_id, "bot_user_1")

    def test_20_bot_link_command_with_code(self):
        """20. Bot /link <otp> verifies 6-digit code and links account."""
        req, otp, _, _ = self.mgr.create_link_request("bot_user_2")
        update = {
            "message": {
                "message_id": 3,
                "chat": {"id": 3003},
                "from": {"id": 3003, "first_name": "Bekzod", "username": "bekzod_tg"},
                "text": f"/link {otp}"
            }
        }
        asyncio.run(self.bot.process_update(update))
        sent = self.transport.sent_messages[0]
        self.assertIn("muvaffaqiyatli bog'landi", sent["text"])
        self.assertIn("bot_user_2", sent["text"])

    def test_21_bot_link_command_prompt(self):
        """21. Bot /link with no argument prompts for 6-digit verification code."""
        update = {
            "message": {
                "message_id": 4,
                "chat": {"id": 4004},
                "from": {"id": 4004, "first_name": "Jasur"},
                "text": "/link"
            }
        }
        asyncio.run(self.bot.process_update(update))
        sent = self.transport.sent_messages[0]
        self.assertIn("Tasdiqlash kodi talab qilinadi", sent["text"])

    def test_22_bot_raw_otp_message(self):
        """22. User sending raw 6-digit number (e.g. 583921) triggers OTP verification."""
        req, otp, _, _ = self.mgr.create_link_request("bot_user_3")
        update = {
            "message": {
                "message_id": 5,
                "chat": {"id": 5005},
                "from": {"id": 5005, "first_name": "Bobur", "username": "bobur_tg"},
                "text": otp  # Raw 6-digit code without /link
            }
        }
        asyncio.run(self.bot.process_update(update))
        sent = self.transport.sent_messages[0]
        self.assertIn("muvaffaqiyatli bog'landi", sent["text"])
        self.assertIn("bot_user_3", sent["text"])

    def test_23_bot_account_command(self):
        """23. /account shows linking status for both linked and unlinked users."""
        # Unlinked user
        update1 = {
            "message": {
                "message_id": 6,
                "chat": {"id": 6006},
                "from": {"id": 6006, "first_name": "Nodir"},
                "text": "/account"
            }
        }
        asyncio.run(self.bot.process_update(update1))
        sent1 = self.transport.sent_messages[0]
        self.assertIn("Bog'lanmagan (Not Linked)", sent1["text"])

        # Link user and check again
        req, otp, _, _ = self.mgr.create_link_request("nodir_mikasa")
        self.mgr.verify_otp(otp, 6006, username="nodir_dev")

        update2 = {
            "message": {
                "message_id": 7,
                "chat": {"id": 6006},
                "from": {"id": 6006, "first_name": "Nodir", "username": "nodir_dev"},
                "text": "/account"
            }
        }
        asyncio.run(self.bot.process_update(update2))
        sent2 = self.transport.sent_messages[1]
        self.assertIn("Faol (Active)", sent2["text"])
        self.assertIn("nodir_mikasa", sent2["text"])

    def test_24_bot_unlink_command(self):
        """24. /unlink decouples Telegram account from Mikasa account."""
        req, otp, _, _ = self.mgr.create_link_request("unlink_bot_user")
        self.mgr.verify_otp(otp, 7007)

        update = {
            "message": {
                "message_id": 8,
                "chat": {"id": 7007},
                "from": {"id": 7007, "first_name": "Sanjar"},
                "text": "/unlink"
            }
        }
        asyncio.run(self.bot.process_update(update))
        sent = self.transport.sent_messages[0]
        self.assertIn("Hisob uzildi", sent["text"])
        self.assertIsNone(self.mgr.get_link_by_telegram_user(7007))

    def test_25_bot_status_and_help(self):
        """25. /status and /help return accurate system health and command directory."""
        # Test /status
        update_status = {
            "message": {
                "message_id": 9,
                "chat": {"id": 8008},
                "from": {"id": 8008, "first_name": "TestUser"},
                "text": "/status"
            }
        }
        asyncio.run(self.bot.process_update(update_status))
        sent_status = self.transport.sent_messages[0]
        self.assertIn("Mikasa Universal Telegram Bot Holati", sent_status["text"])
        self.assertIn("Phase 39", sent_status["text"])

        # Test /help
        update_help = {
            "message": {
                "message_id": 10,
                "chat": {"id": 8008},
                "from": {"id": 8008, "first_name": "TestUser"},
                "text": "/help"
            }
        }
        asyncio.run(self.bot.process_update(update_help))
        sent_help = self.transport.sent_messages[1]
        self.assertIn("Mikasa Telegram Bot Buyruqlari", sent_help["text"])
        self.assertIn("/start", sent_help["text"])
        self.assertIn("/link", sent_help["text"])
        self.assertIn("/unlink", sent_help["text"])
        self.assertIn("/account", sent_help["text"])


class TestPhase39AuditAndE2E(unittest.TestCase):
    """26-27: Audit Logging Secret Redaction and Full E2E Lifecycle"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mikasa_v8_p39_e2e_")
        self.storage_file = os.path.join(self.temp_dir, "telegram_links.json")
        self.mgr = TelegramIdentityManager(storage_path=self.storage_file)
        self.transport = MockTelegramTransport()
        self.bot = UniversalTelegramBot(
            transport=self.transport,
            identity_manager=self.mgr,
            bot_username="MikasaUniversalBot"
        )
        self.audit = RemoteAuditLogger.get_instance()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_26_audit_logging_secret_redaction(self):
        """26. Audit events strictly redact otp, otp_hash, and link_token."""
        req, otp, deep_link, _ = self.mgr.create_link_request("audit_user")
        self.mgr.verify_otp(otp, 99887766)

        history = self.audit.get_history(limit=50)
        found_create = False
        found_success = False

        for ev in history:
            d = ev.to_dict()
            details = d.get("details", {})

            # Check creation event
            if ev.event_type == RemoteEventType.TELEGRAM_LINK_REQUEST_CREATED:
                found_create = True
                self.assertNotIn(otp, str(details))
                self.assertNotIn(req.link_token, str(details))

            # Check verification success
            if ev.event_type == RemoteEventType.TELEGRAM_OTP_VERIFICATION_SUCCESS:
                found_success = True
                self.assertNotIn(otp, str(details))

        self.assertTrue(found_create)
        self.assertTrue(found_success)

    def test_27_full_e2e_otp_linking_lifecycle(self):
        """27. Full End-to-End: Start link -> Get OTP -> Bot verifies -> Linked -> Check -> Unlink."""
        # 1. User app initiates pairing via API / Manager
        req, plaintext_otp, deep_link, err = self.mgr.create_link_request("admin_owner")
        self.assertIsNone(err)
        self.assertEqual(self.mgr.count_pending_requests(), 1)
        self.assertEqual(self.mgr.count_active_links(), 0)

        # 2. User receives OTP in UI and opens Telegram bot
        update_open = {
            "message": {
                "message_id": 100,
                "chat": {"id": 777111222},
                "from": {"id": 777111222, "first_name": "Admin", "username": "admin_telegram"},
                "text": "/start"
            }
        }
        asyncio.run(self.bot.process_update(update_open))
        self.assertIn("Mikasa AI Universal Telegram Botiga xush kelibsiz", self.transport.sent_messages[-1]["text"])

        # 3. User sends 6-digit OTP code to the bot
        update_otp = {
            "message": {
                "message_id": 101,
                "chat": {"id": 777111222},
                "from": {"id": 777111222, "first_name": "Admin", "username": "admin_telegram"},
                "text": plaintext_otp
            }
        }
        asyncio.run(self.bot.process_update(update_otp))
        self.assertIn("Hisob muvaffaqiyatli bog'landi", self.transport.sent_messages[-1]["text"])

        # 4. Assert system state
        self.assertEqual(self.mgr.count_active_links(), 1)
        link = self.mgr.get_link_by_telegram_user(777111222)
        self.assertIsNotNone(link)
        self.assertEqual(link.mikasa_user_id, "admin_owner")
        self.assertEqual(link.status, "ACTIVE")

        # 5. User inspects account via bot
        update_acc = {
            "message": {
                "message_id": 102,
                "chat": {"id": 777111222},
                "from": {"id": 777111222, "first_name": "Admin", "username": "admin_telegram"},
                "text": "/account"
            }
        }
        asyncio.run(self.bot.process_update(update_acc))
        self.assertIn("Faol (Active)", self.transport.sent_messages[-1]["text"])
        self.assertIn("admin_owner", self.transport.sent_messages[-1]["text"])

        # 6. User unlinks via bot
        update_unl = {
            "message": {
                "message_id": 103,
                "chat": {"id": 777111222},
                "from": {"id": 777111222, "first_name": "Admin", "username": "admin_telegram"},
                "text": "/unlink"
            }
        }
        asyncio.run(self.bot.process_update(update_unl))
        self.assertIn("Hisob uzildi", self.transport.sent_messages[-1]["text"])
        self.assertEqual(self.mgr.count_active_links(), 0)

        # 7. Replay old OTP should fail
        update_replay = {
            "message": {
                "message_id": 104,
                "chat": {"id": 777111222},
                "from": {"id": 777111222, "first_name": "Admin", "username": "admin_telegram"},
                "text": plaintext_otp
            }
        }
        asyncio.run(self.bot.process_update(update_replay))
        self.assertIn("muvaffaqiyatsiz", self.transport.sent_messages[-1]["text"])


if __name__ == "__main__":
    unittest.main()
