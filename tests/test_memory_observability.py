# ========== test_memory_observability.py ==========
# Mikasa AI 7.x — Phase 30: Context Observability & Memory Telemetry Unit Tests
# Comprehensive test cases covering retrieve_with_explanation, ContextTrace ring buffer,
# Sensitive data redaction, MemoryMetrics telemetry, and Orchestrator integration.

import os
import sys
import json
import asyncio
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
from core.intelligence.memory_policy import reset_policy_config
from core.intelligence.memory_retriever import MemoryRetriever
from core.intelligence.observability import (
    ContextTraceStage,
    ContextTrace,
    MemoryMetricsManager,
    ObservabilityManager,
    get_observability_manager,
    redact_sensitive_data,
)
from core.agent_memory import AgentMemory
from core.api_server import (
    handle_context_traces_get,
    handle_context_last_trace_get,
    handle_memory_metrics_get,
)


class MockRequest:
    def __init__(self, json_data=None, match_info=None, query=None):
        self._json_data = json_data or {}
        self.match_info = match_info or {}
        self.query = query or {}

    async def json(self):
        return self._json_data


class TestMemoryObservability(unittest.TestCase):
    """Phase 30 Context Observability and Telemetry Tests"""

    def setUp(self):
        reset_policy_config()
        self.obs = ObservabilityManager(max_traces=25)
        self.memory = AgentMemory(max_short_term=10, max_conversations=50)
        self.memory.clear_knowledge()

    def tearDown(self):
        reset_policy_config()
        self.obs.clear()
        self.memory.clear_knowledge()

    # 1. retrieve_with_explanation returns both selected items and explanation records
    def test_01_retrieve_with_explanation_structure(self):
        item1 = MemoryItem(id="m1", key="shahar", content="Toshkent shahri", importance=0.8)
        item2 = MemoryItem(id="m2", key="kasb", content="Python dasturchisi", importance=0.9)

        items, explanations = MemoryRetriever.retrieve_with_explanation(
            query="Toshkent shahri",
            items=[item1, item2],
            limit=2,
        )

        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0].id, "m1")
        self.assertGreaterEqual(len(explanations), 1)

        exp = explanations[0]
        self.assertEqual(exp["memory_id"], "m1")
        self.assertEqual(exp["key"], "shahar")
        self.assertIn("score", exp)
        self.assertIn("reason", exp)
        self.assertIn("details", exp)

    # 2. Explanation details contain matched terms, task bonus, and pinned status
    def test_02_explanation_details_completeness(self):
        item = MemoryItem(
            id="m_pinned",
            key="loyiha",
            content="Mikasa AI desktop ilovasi",
            importance=0.9,
            pinned=True,
        )

        items, explanations = MemoryRetriever.retrieve_with_explanation(
            query="Mikasa loyihasi bo'yicha",
            items=[item],
            limit=1,
            task_entities=["desktop"],
        )

        self.assertEqual(len(explanations), 1)
        det = explanations[0]["details"]
        self.assertTrue(det["pinned"])
        self.assertGreater(det["task_bonus"], 0.0)
        self.assertIn("mikasa", det["matched_terms"])
        self.assertIn("qadalgan", explanations[0]["reason"].lower())

    # 3. Uzbek explanation string includes rationale
    def test_03_uzbek_explanation_rationale(self):
        item = MemoryItem(id="m_lang", key="til", content="O'zbek tili", importance=0.7)
        items, explanations = MemoryRetriever.retrieve_with_explanation(
            query="til bo'yicha",
            items=[item],
            limit=1,
        )
        self.assertEqual(len(explanations), 1)
        reason = explanations[0]["reason"]
        self.assertTrue(any(w in reason.lower() for w in ["so'zlar", "mos", "til"]))

    # 4. Redaction replaces API keys, bearer tokens, passwords, and sensitive patterns
    def test_04_redact_sensitive_data(self):
        raw_text = "Mening API kalitim AIzaSyD1234567890abcdefghijklmnopqr va token Bearer secret_token_xyz"
        redacted = redact_sensitive_data(raw_text)
        self.assertNotIn("AIzaSyD1234567890", redacted)
        self.assertNotIn("secret_token_xyz", redacted)
        self.assertIn("[REDACTED", redacted)

    # 5. Redaction works recursively on dicts and lists
    def test_05_redact_nested_structures(self):
        data = {
            "api_key": "sk-1234567890abcdef1234567890",
            "info": {
                "password": "supersecretpassword",
                "normal": "hello",
            },
            "tokens": ["sk-proj-abcde1234567890", "safe_token"],
        }
        redacted = redact_sensitive_data(data)
        self.assertEqual(redacted["api_key"], "[REDACTED]")
        self.assertEqual(redacted["info"]["password"], "[REDACTED]")
        self.assertEqual(redacted["info"]["normal"], "hello")
        self.assertEqual(redacted["tokens"][0], "[REDACTED]")
        self.assertEqual(redacted["tokens"][1], "safe_token")

    # 6. ContextTrace records stages with duration and timestamp
    def test_06_context_trace_lifecycle(self):
        trace = ContextTrace(trace_id="tr_1001", query="salom")
        trace.add_stage("REQUEST", {"query": "salom"})
        trace.add_stage("INTENT", {"category": "conversation"})
        trace.finish(success=True)

        d = trace.to_dict()
        self.assertEqual(d["trace_id"], "tr_1001")
        self.assertTrue(d["success"])
        self.assertEqual(len(d["stages"]), 2)
        self.assertEqual(d["stages"][0]["stage"], "REQUEST")
        self.assertEqual(d["stages"][1]["stage"], "INTENT")
        self.assertGreaterEqual(d["duration_ms"], 0.0)

    # 7. ContextTrace automatically redacts sensitive data added to stages
    def test_07_context_trace_auto_redaction(self):
        trace = ContextTrace(trace_id="tr_1002", query="test")
        trace.add_stage("TOOL", {"key": "AIzaSyABC12345678901234567890", "safe": "val"})
        d = trace.to_dict()
        tool_stage = d["stages"][0]
        self.assertEqual(tool_stage["data"]["key"], "[REDACTED]")
        self.assertEqual(tool_stage["data"]["safe"], "val")

    # 8. ObservabilityManager stores and retrieves traces
    def test_08_observability_manager_store_and_get(self):
        trace = self.obs.start_trace("so'rov matni")
        trace.add_stage("REQUEST", {"text": "so'rov matni"})
        self.obs.end_trace(trace, success=True)

        found = self.obs.get_trace(trace.trace_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.trace_id, trace.trace_id)

        last = self.obs.get_last_trace()
        self.assertIsNotNone(last)
        self.assertEqual(last["trace_id"], trace.trace_id)

    # 9. Bounded ring buffer: strictly limits to max_traces (25 items)
    def test_09_bounded_ring_buffer_eviction(self):
        manager = ObservabilityManager(max_traces=5)
        for i in range(10):
            t = manager.start_trace(f"query {i}")
            manager.end_trace(t, success=True)

        all_traces = manager.get_all_traces()
        self.assertEqual(len(all_traces), 5)
        # Should contain newest items (5 through 9)
        trace_queries = [t["query"] for t in all_traces]
        self.assertIn("query 9", trace_queries)
        self.assertNotIn("query 0", trace_queries)

    # 10. MemoryMetricsManager records retrievals, hits, and calculates hit_rate
    def test_10_memory_metrics_retrievals_and_hit_rate(self):
        metrics = MemoryMetricsManager()
        metrics.record_retrieval("q1", retrieved_count=2, was_hit=True)
        metrics.record_retrieval("q2", retrieved_count=0, was_hit=False)
        metrics.record_retrieval("q3", retrieved_count=1, was_hit=True)
        metrics.record_retrieval("q4", retrieved_count=0, was_hit=False)

        self.assertEqual(metrics.total_retrieval_requests, 4)
        self.assertEqual(metrics.hit_count, 2)
        self.assertAlmostEqual(metrics.hit_rate, 0.5)

    # 11. MemoryMetricsManager records policy and sensitive rejections
    def test_11_memory_metrics_rejections(self):
        metrics = MemoryMetricsManager()
        metrics.record_sensitive_rejection()
        metrics.record_sensitive_rejection()
        metrics.record_policy_rejection()

        self.assertEqual(metrics.sensitive_data_rejections, 2)
        self.assertEqual(metrics.policy_rejections, 1)

    # 12. MemoryMetricsManager records deletions
    def test_12_memory_metrics_deletions(self):
        metrics = MemoryMetricsManager()
        metrics.record_deletion()
        metrics.record_deletion()
        self.assertEqual(metrics.user_deletions, 2)

    # 13. MemoryMetrics snapshot accurately reflects memory state
    def test_13_memory_metrics_snapshot(self):
        metrics = MemoryMetricsManager()
        self.memory.add_knowledge("k1", "Fact 1", pinned=True)
        self.memory.add_knowledge("k2", "Fact 2", pinned=False)

        snap = metrics.snapshot(self.memory)
        self.assertEqual(snap["total_memories"], 2)
        self.assertEqual(snap["active_memories"], 2)
        self.assertEqual(snap["pinned_memories"], 1)
        self.assertEqual(snap["superseded_memories"], 0)
        self.assertIn("hit_rate", snap)

    # 14. GET /api/context/traces returns traces list
    def test_14_api_context_traces_get(self):
        global_obs = get_observability_manager()
        t = global_obs.start_trace("test query")
        t.add_stage("REQUEST", {"q": "test query"})
        global_obs.end_trace(t, success=True)

        async def _run():
            resp = await handle_context_traces_get(MockRequest())
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data["ok"])
        self.assertIn("traces", data)
        self.assertGreaterEqual(len(data["traces"]), 1)

    # 15. GET /api/context/last-trace returns latest trace
    def test_15_api_context_last_trace_get(self):
        global_obs = get_observability_manager()
        t = global_obs.start_trace("latest query for last-trace")
        t.add_stage("REQUEST", {"test": 1})
        global_obs.end_trace(t, success=True)

        async def _run():
            resp = await handle_context_last_trace_get(MockRequest())
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data["ok"])
        self.assertIn("trace", data)
        self.assertEqual(data["trace"]["query"], "latest query for last-trace")

    # 16. GET /api/memory/metrics returns complete telemetry
    def test_16_api_memory_metrics_get(self):
        async def _run():
            resp = await handle_memory_metrics_get(MockRequest())
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data["ok"])
        self.assertIn("metrics", data)
        m = data["metrics"]
        self.assertIn("total_retrieval_requests", m)
        self.assertIn("hit_rate", m)
        self.assertIn("user_deletions", m)


if __name__ == "__main__":
    unittest.main()
