# ========== test_logging.py ==========
# Phase 22 — Production Logging & Sanitization Tests

import os
import sys
import logging
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.logger import (
    get_mikasa_handler,
    get_backend_handler,
    log_crash,
    sanitize_text,
    SensitiveDataFilter,
    MIKASA_LOG_PATH,
    BACKEND_LOG_PATH,
    CRASH_LOG_PATH,
)


class TestLoggingSubsystem(unittest.TestCase):
    """Production log fayllari va maxfiy ma'lumotlarni tozalash testlari"""

    def test_sensitive_data_sanitization(self):
        """API kalitlari va parollar loglarda yashiriladi (maskalanadi)"""
        raw_text = (
            "Google API key: AIzaSyD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4y. "
            "OpenAI key: sk-abcdefghijklmnopqrstuvwxyz1234567890. "
            "Authorization: Bearer mySecretToken123456789. "
            'Payload: {"user": "ali", "password": "super_secret_password_123"}'
        )
        cleaned = sanitize_text(raw_text)

        # Xavfli kalitlar ochiq qolmasligi kerak
        self.assertNotIn("AIzaSyD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4y", cleaned)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz1234567890", cleaned)
        self.assertNotIn("mySecretToken123456789", cleaned)
        self.assertNotIn("super_secret_password_123", cleaned)

        # Maskalangan markerlar mavjudligi
        self.assertIn("AIza***MASKED_KEY***", cleaned)
        self.assertIn("sk-***MASKED_KEY***", cleaned)
        self.assertIn("***MASKED_TOKEN***", cleaned)
        self.assertIn('"***MASKED***"', cleaned)

    def test_mikasa_log_writing(self):
        """logs/mikasa.log fayliga yozish va filtr ishlashi"""
        test_logger = logging.getLogger("TestMikasaLogger")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(get_mikasa_handler())

        test_msg = "Phase 22 test logging message: AIzaSy1234567890abcdefghijklmnopqrstuvwxyz"
        test_logger.info(test_msg)

        self.assertTrue(os.path.exists(MIKASA_LOG_PATH), "mikasa.log mavjud emas")
        with open(MIKASA_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Phase 22 test logging message", content)
        self.assertNotIn("AIzaSy1234567890abcdefghijklmnopqrstuvwxyz", content)

    def test_backend_log_writing(self):
        """logs/backend.log fayliga yozish va filtr ishlashi"""
        test_logger = logging.getLogger("TestBackendLogger")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(get_backend_handler())

        test_msg = "Backend route hit: /api/status sk-prodSecretKey1234567890abcdef1234"
        test_logger.info(test_msg)

        self.assertTrue(os.path.exists(BACKEND_LOG_PATH), "backend.log mavjud emas")
        with open(BACKEND_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Backend route hit", content)
        self.assertNotIn("sk-prodSecretKey1234567890abcdef1234", content)

    def test_crash_log_writing(self):
        """logs/crash.log fayliga istisno (exception) traceback to'liq yoziladi"""
        try:
            # Simulyatsiya qilingan xatolik
            raise ValueError("Kritik xatolik sinovi sk-secretInCrash1234567890abcdef")
        except Exception as e:
            exc_type, exc_val, exc_tb = sys.exc_info()
            log_crash(exc_type, exc_val, exc_tb, context="Unit Test Crash")

        self.assertTrue(os.path.exists(CRASH_LOG_PATH), "crash.log mavjud emas")
        with open(CRASH_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("CRASH REPORT", content)
        self.assertIn("ValueError", content)
        self.assertIn("Kritik xatolik sinovi", content)
        self.assertNotIn("sk-secretInCrash1234567890abcdef", content)


if __name__ == "__main__":
    unittest.main()
