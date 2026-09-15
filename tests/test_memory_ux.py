# ========== test_memory_ux.py ==========
# Mikasa AI 7.x — Phase 30: Memory UX, User Control & Privacy Unit Tests
# Comprehensive test cases covering Memory Inspector, Edit, Safe Delete, Pinning,
# Do-Not-Remember policies, and Atomic persistence.

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.intelligence.memory_types import (
    MemoryType,
    MemorySource,
    MemoryConfidence,
    MemoryItem,
)
from core.intelligence.memory_policy import (
    MemoryPolicy,
    PolicyDecision,
    get_policy_config,
    update_policy_config,
    reset_policy_config,
    is_persistence_blocked,
)
from core.intelligence.memory_retriever import MemoryRetriever
from core.agent_memory import AgentMemory


class TestMemoryUX(unittest.TestCase):
    """Phase 30 Memory UX & User Control Tests"""

    def setUp(self):
        reset_policy_config()
        self.memory = AgentMemory(max_short_term=10, max_conversations=50)
        self.memory.clear_knowledge()
        self.memory.clear_conversations()
        self.memory.clear_context()

    def tearDown(self):
        reset_policy_config()
        self.memory.clear_knowledge()
        self.memory.clear_conversations()
        self.memory.clear_context()

    # 1. Inspector: MemoryItem serialization includes all required metadata fields
    def test_01_memory_item_has_full_metadata(self):
        item = MemoryItem(
            key="shahar",
            content="Toshkent",
            type=MemoryType.FACT,
            source=MemorySource.USER,
            importance=0.9,
            confidence=1.0,
            pinned=True,
        )
        d = item.to_dict()
        self.assertIn("id", d)
        self.assertEqual(d["key"], "shahar")
        self.assertEqual(d["content"], "Toshkent")
        self.assertEqual(d["type"], "fact")
        self.assertEqual(d["source"], "user")
        self.assertEqual(d["importance"], 0.9)
        self.assertEqual(d["confidence"], 1.0)
        self.assertTrue(d["pinned"])
        self.assertTrue(d["is_active"])
        self.assertIn("created_at", d)
        self.assertIn("updated_at", d)
        self.assertIn("access_count", d)

    # 2. Deserialization preserves pinned flag
    def test_02_memory_item_from_dict_preserves_pinned(self):
        raw = {
            "id": "mem_test_123",
            "key": "framework",
            "content": "React 19",
            "type": "fact",
            "source": "user",
            "importance": 0.85,
            "confidence": 1.0,
            "pinned": True,
            "is_active": True,
        }
        item = MemoryItem.from_dict(raw)
        self.assertEqual(item.id, "mem_test_123")
        self.assertTrue(item.pinned)
        self.assertEqual(item.key, "framework")

    # 3. Memory update: edit existing item content and importance
    def test_03_update_knowledge_item_content(self):
        self.memory.add_knowledge("kasb", "Junior Dasturchi", category="profile")
        item = self.memory.knowledge[0]
        original_id = item.id

        updated = self.memory.update_knowledge_item(
            item_id_or_key=original_id,
            content="Senior AI Muhandis",
            importance=0.95,
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated.content, "Senior AI Muhandis")
        self.assertEqual(updated.importance, 0.95)
        self.assertEqual(updated.id, original_id)

    # 4. Memory update by key
    def test_04_update_knowledge_item_by_key(self):
        self.memory.add_knowledge("muhit", "Windows 11", category="work")
        updated = self.memory.update_knowledge_item(
            item_id_or_key="muhit",
            content="Windows 11 Pro 64-bit",
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated.content, "Windows 11 Pro 64-bit")

    # 5. Memory update validation: empty content rejected
    def test_05_update_knowledge_empty_content_rejected(self):
        self.memory.add_knowledge("loyiha", "Mikasa AI", category="work")
        item = self.memory.knowledge[0]

        res = self.memory.update_knowledge_item(item.id, content="   ")
        self.assertIsNone(res)

    # 6. Memory update: nonexistent ID returns None
    def test_06_update_nonexistent_returns_none(self):
        res = self.memory.update_knowledge_item("nonexistent_id_999", content="Test")
        self.assertIsNone(res)

    # 7. Safe Delete: delete item by ID
    def test_07_delete_knowledge_item_by_id(self):
        self.memory.add_knowledge("rang", "Ko'k", category="preference")
        item = self.memory.knowledge[0]
        item_id = item.id

        success = self.memory.delete_knowledge_item(item_id)
        self.assertTrue(success)
        self.assertEqual(len(self.memory.knowledge), 0)
        self.assertIsNone(self.memory.get_memory_item_by_id(item_id))

    # 8. Safe Delete: delete item by key
    def test_08_delete_knowledge_item_by_key(self):
        self.memory.add_knowledge("editor", "VSCode", category="work")
        success = self.memory.delete_knowledge_item("editor")
        self.assertTrue(success)
        self.assertEqual(len(self.memory.knowledge), 0)

    # 9. Safe Delete: delete nonexistent returns False (no crash)
    def test_09_delete_nonexistent_returns_false(self):
        success = self.memory.delete_knowledge_item("nonexistent_key_xyz")
        self.assertFalse(success)

    # 10. Pin / Unpin knowledge item
    def test_10_pin_and_unpin_knowledge_item(self):
        self.memory.add_knowledge("muhim_fakt", "Server porti: 18420", category="work")
        item = self.memory.knowledge[0]
        self.assertFalse(item.pinned)

        # Pin it
        success = self.memory.pin_knowledge_item(item.id, pinned=True)
        self.assertTrue(success)
        pinned_item = self.memory.get_memory_item_by_id(item.id)
        self.assertIsNotNone(pinned_item)
        self.assertTrue(pinned_item.pinned)

        # Unpin it
        success_unpin = self.memory.pin_knowledge_item(item.id, pinned=False)
        self.assertTrue(success_unpin)
        unpinned_item = self.memory.get_memory_item_by_id(item.id)
        self.assertIsNotNone(unpinned_item)
        self.assertFalse(unpinned_item.pinned)

    # 11. Pin bonus boosts retrieval score
    def test_11_pin_boosts_relevance_score(self):
        item_normal = MemoryItem(
            key="server",
            content="Mikasa serveri",
            importance=0.5,
            pinned=False,
        )
        item_pinned = MemoryItem(
            key="server",
            content="Mikasa serveri",
            importance=0.5,
            pinned=True,
        )

        query = "server qayerda"
        score_normal = MemoryRetriever.calculate_relevance_score(query, item_normal)
        score_pinned = MemoryRetriever.calculate_relevance_score(query, item_pinned)

        # Pinned score must be noticeably higher due to 0.35 boost
        self.assertGreater(score_pinned, score_normal)
        self.assertAlmostEqual(score_pinned - score_normal, 0.35, places=2)

    # 12. Pinned items rank higher in retrieval
    def test_12_pinned_items_rank_higher(self):
        item_unpinned = MemoryItem(
            id="item1",
            key="tillar",
            content="JavaScript va Python",
            importance=0.5,
            pinned=False,
        )
        item_pinned = MemoryItem(
            id="item2",
            key="boshqa",
            content="Rust va Go tillari",
            importance=0.5,
            pinned=True,
        )

        # Query has equal weak match for both ("tillar" vs "tillari")
        results = MemoryRetriever.retrieve("tillari", [item_unpinned, item_pinned], limit=2)
        self.assertEqual(len(results), 2)
        # item_pinned gets +0.35 bonus so it should rank first
        self.assertEqual(results[0].id, "item2")

    # 13. Do-Not-Remember: global disable blocks writes
    def test_13_do_not_remember_global_blocks_writes(self):
        update_policy_config({"do_not_remember": True})
        self.assertTrue(is_persistence_blocked("anything", MemoryType.FACT))

        item = MemoryItem(key="test", content="secret fact", type=MemoryType.FACT)
        decision = MemoryPolicy.evaluate_write(item)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "DO_NOT_REMEMBER_ALL_ENABLED")

    # 14. Do-Not-Remember: blocked types selectively block
    def test_14_do_not_remember_blocked_types(self):
        update_policy_config({
            "do_not_remember": False,
            "blocked_types": ["work_context", "preference"],
        })
        self.assertTrue(is_persistence_blocked("job", MemoryType.WORK_CONTEXT))
        self.assertFalse(is_persistence_blocked("city", MemoryType.FACT))

        item_work = MemoryItem(key="job", content="dev", type=MemoryType.WORK_CONTEXT)
        decision_work = MemoryPolicy.evaluate_write(item_work)
        self.assertFalse(decision_work.allowed)
        self.assertEqual(decision_work.reason, "BLOCKED_TYPE_WORK_CONTEXT")

        item_fact = MemoryItem(key="city", content="Samarkand", type=MemoryType.FACT)
        decision_fact = MemoryPolicy.evaluate_write(item_fact)
        self.assertTrue(decision_fact.allowed)

    # 15. Do-Not-Remember: blocked keys selectively block
    def test_15_do_not_remember_blocked_keys(self):
        update_policy_config({
            "do_not_remember": False,
            "blocked_keys": ["maosh", "password"],
        })
        self.assertTrue(is_persistence_blocked("maosh", MemoryType.FACT))
        self.assertFalse(is_persistence_blocked("ism", MemoryType.FACT))

        item = MemoryItem(key="maosh", content="5000 USD", type=MemoryType.FACT)
        decision = MemoryPolicy.evaluate_write(item)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "BLOCKED_KEY_MAOSH")

    # 16. Policy config update and persistence
    def test_16_policy_config_persistence(self):
        update_policy_config({
            "do_not_remember": True,
            "blocked_types": ["fact"],
            "blocked_keys": ["secret_key"],
        })
        cfg = get_policy_config()
        self.assertTrue(cfg["do_not_remember"])
        self.assertIn("fact", cfg["blocked_types"])
        self.assertIn("secret_key", cfg["blocked_keys"])

    # 17. Stats includes active and pinned counts
    def test_17_memory_stats_includes_active_and_pinned(self):
        self.memory.add_knowledge("k1", "Bilim 1")
        self.memory.add_knowledge("k2", "Bilim 2")
        item1 = self.memory.knowledge[0]
        self.memory.pin_knowledge_item(item1.id, pinned=True)

        stats = self.memory.stats
        self.assertEqual(stats["bilimlar_soni"], 2)
        self.assertEqual(stats["faol_bilimlar_soni"], 2)
        self.assertEqual(stats["pinned_bilimlar_soni"], 1)

    # 18. Atomic file persistence produces valid JSON on disk
    def test_18_atomic_save_produces_valid_json(self):
        self.memory.add_knowledge("atomik_test", "Ma'lumot saqlandi")
        file_path = self.memory.knowledge_file
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)
        self.assertIn("atomik_test", data)
        self.assertEqual(data["atomik_test"]["value"], "Ma'lumot saqlandi")


if __name__ == "__main__":
    unittest.main()
