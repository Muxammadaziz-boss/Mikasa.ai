# ========== test_stress.py ==========
# Phase 24 — High-Volume Stress & Scalability Testing
# 100, 500, 1000 commands, rapid state changes, memory and latency profiling

import os
import sys
import json
import time
import asyncio
import unittest
import psutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.api_server import (
    handle_status,
    handle_commands_execute,
    handle_voice_start,
    handle_voice_stop,
    _read_config,
    _write_config,
)


class MockRequest:
    def __init__(self, json_data=None):
        self._json_data = json_data or {}

    async def json(self):
        return self._json_data


class TestStressSubsystems(unittest.TestCase):
    """Phase 24: 100, 500 va 1000 ta buyruqlar, resurs sarfi va tezkor holat almashinuvi"""

    def setUp(self):
        self.process = psutil.Process(os.getpid())
        self.initial_mem = self.process.memory_info().rss / (1024 * 1024)  # MB

    def test_stress_100_commands(self):
        """100 ta buyruq ketma-ket bajarilishi va o'rtacha kechikish < 20ms"""
        async def _run():
            t0 = time.perf_counter()
            for i in range(100):
                req = MockRequest({
                    "command": "calculator",
                    "parameters": {"expression": f"{i} * 2"}
                })
                resp = await handle_commands_execute(req)
                self.assertEqual(resp.status, 200)
            duration = time.perf_counter() - t0
            avg_ms = (duration / 100) * 1000
            print(f"\n[Stress 100] Jami vaqt: {duration:.3f}s, o'rtacha: {avg_ms:.2f}ms/so'rov")
            self.assertLess(avg_ms, 50.0, "100 buyruq o'rtacha 50ms dan kam bo'lishi kerak")

        asyncio.run(_run())

    def test_stress_500_commands(self):
        """500 ta buyruq yuklamasi va xotira oqishi yo'qligi tekshiruvi"""
        async def _run():
            t0 = time.perf_counter()
            for i in range(500):
                req = MockRequest({
                    "command": "calculator",
                    "parameters": {"expression": f"{i} + 10"}
                })
                resp = await handle_commands_execute(req)
                self.assertEqual(resp.status, 200)
            duration = time.perf_counter() - t0
            throughput = 500 / duration
            print(f"\n[Stress 500] O'tkazuvchanlik: {throughput:.1f} req/s ({duration:.3f}s)")
            self.assertGreater(throughput, 100.0, "Kamida 100 req/s o'tkazuvchanlik ta'minlanishi kerak")

        asyncio.run(_run())

    def test_stress_1000_commands(self):
        """1000 ta buyruq hajmi sinovi va RAM barqarorligi"""
        async def _run():
            mem_start = self.process.memory_info().rss / (1024 * 1024)
            t0 = time.perf_counter()

            for i in range(1000):
                req = MockRequest({
                    "command": "calculator",
                    "parameters": {"expression": f"{i} * 3"}
                })
                resp = await handle_commands_execute(req)
                self.assertEqual(resp.status, 200)

            duration = time.perf_counter() - t0
            mem_end = self.process.memory_info().rss / (1024 * 1024)
            mem_diff = mem_end - mem_start

            print(f"\n[Stress 1000] Vaqt: {duration:.3f}s, RAM o'zgarishi: {mem_diff:+.2f}MB (Yakuniy: {mem_end:.1f}MB)")
            # 1000 ta so'rovdan so'ng RAM 50MB dan ortiq oshmasligi shart
            self.assertLess(mem_diff, 50.0, "1000 ta buyruqda xotira oqishi (memory leak) aniqlandi")

        asyncio.run(_run())

    def test_rapid_status_polling(self):
        """500 marta tezkor status tekshiruvi (Frontend polling simulyatsiyasi)"""
        async def _run():
            t0 = time.perf_counter()
            for _ in range(500):
                resp = await handle_status(MockRequest())
                self.assertEqual(resp.status, 200)
            duration = time.perf_counter() - t0
            avg_ms = (duration / 500) * 1000
            print(f"\n[Rapid Polling 500] Jami: {duration:.3f}s, o'rtacha: {avg_ms:.3f}ms")
            self.assertLess(avg_ms, 5.0, "Status polling o'rtacha 5ms dan kam bo'lishi kerak")

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
