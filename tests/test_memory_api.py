# ========== test_memory_api.py ==========
# Phase 12 — Memory & Knowledge Space API Unit Tests

import os
import sys
import json
import asyncio
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.api_server import (
    handle_memory_get,
    handle_memory_profile_save,
    handle_memory_knowledge_save,
    handle_memory_knowledge_delete,
    handle_memory_knowledge_clear,
    handle_memory_context_clear,
    handle_memory_history_clear,
)
from core.agent_memory import get_memory


class MockRequest:
    def __init__(self, json_data=None, query_data=None):
        self._json_data = json_data or {}
        self.query = query_data or {}

    async def json(self):
        return self._json_data


class TestMemoryAPI(unittest.TestCase):
    """Memory & Knowledge Space backend API testlari"""

    def setUp(self):
        self.mem = get_memory()

    def test_memory_get_structure(self):
        """GET /api/memory barcha 4 qism (profile, knowledge, context, conversations) ni qaytaradi"""
        async def _run():
            resp = await handle_memory_get(MockRequest())
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data.get("ok"))
        self.assertIn("profile", data)
        self.assertIn("knowledge", data)
        self.assertIn("context", data)
        self.assertIn("conversations", data)
        self.assertIn("stats", data)

    def test_knowledge_add_delete_flow(self):
        """Bilim qo'shish va o'chirish oqimi to'g'ri ishlaydi"""
        async def _add():
            req = MockRequest({"key": "test_unit_key", "value": "test_unit_val"})
            resp = await handle_memory_knowledge_save(req)
            return json.loads(resp.text)

        data_add = asyncio.run(_add())
        self.assertTrue(data_add.get("ok"))
        self.assertEqual(self.mem.get_knowledge("test_unit_key")["value"], "test_unit_val")

        async def _del():
            req = MockRequest(query_data={"key": "test_unit_key"})
            resp = await handle_memory_knowledge_delete(req)
            return json.loads(resp.text)

        data_del = asyncio.run(_del())
        self.assertTrue(data_del.get("ok"))
        self.assertIsNone(self.mem.get_knowledge("test_unit_key"))

    def test_profile_update(self):
        """POST /api/memory/profile profil maydonlarini muvaffaqiyatli yangilaydi"""
        async def _run():
            req = MockRequest({"kasb": "Dasturchi", "shahar": "Toshkent"})
            resp = await handle_memory_profile_save(req)
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data.get("ok"))
        self.assertEqual(self.mem.get_profile("kasb"), "Dasturchi")
        self.assertEqual(self.mem.get_profile("shahar"), "Toshkent")

    def test_context_clear(self):
        """POST /api/memory/context/clear operativ xotirani tozalaydi"""
        self.mem.add_to_context("user", "Test message")
        self.assertGreaterEqual(len(self.mem.get_context()), 1)

        async def _run():
            resp = await handle_memory_context_clear(MockRequest())
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data.get("ok"))
        self.assertEqual(len(self.mem.get_context()), 0)


if __name__ == "__main__":
    unittest.main()
