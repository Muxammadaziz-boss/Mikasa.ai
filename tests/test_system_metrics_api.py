# ========== test_system_metrics_api.py ==========
# Phase 34 — System Telemetry Metrics API Tests (GET /api/system/metrics)

import os
import sys
import json
import asyncio
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.api_server import handle_system_metrics


class MockRequest:
    def __init__(self, json_data=None, query_data=None):
        self._json_data = json_data or {}
        self.query = query_data or {}

    async def json(self):
        return self._json_data


class TestSystemMetricsAPI(unittest.TestCase):
    """Phase 34: Tizim telemetriyasi API testlari"""

    def test_system_metrics_endpoint(self):
        """GET /api/system/metrics to'liq telemetriya metrikalarini qaytaradi"""
        async def _run():
            resp = await handle_system_metrics(MockRequest())
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.text)

            self.assertTrue(data.get("ok"))
            self.assertIn("cpu_percent", data)
            self.assertIn("ram_percent", data)
            self.assertIn("ram_used_gb", data)
            self.assertIn("ram_total_gb", data)
            self.assertIn("disk_percent", data)
            self.assertIn("disk_free_gb", data)
            self.assertIn("network_sent_kb", data)
            self.assertIn("network_recv_kb", data)
            self.assertIn("timestamp", data)

            self.assertIsInstance(data["cpu_percent"], (int, float))
            self.assertIsInstance(data["ram_percent"], (int, float))
            self.assertIsInstance(data["disk_percent"], (int, float))
            self.assertGreaterEqual(data["cpu_percent"], 0.0)
            self.assertLessEqual(data["cpu_percent"], 100.0)

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
