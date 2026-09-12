# ========== test_commands_api.py ==========
# Phase 11 — Command Center & ToolRegistry API Unit Tests

import os
import sys
import json
import asyncio
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.api_server import (
    handle_commands_list,
    handle_commands_execute,
    format_tool_result,
    TOOL_METADATA,
    QUICK_APP_SHORTCUTS,
)
from core.agent_tools import get_registry


class MockRequest:
    def __init__(self, json_data=None):
        self._json_data = json_data or {}

    async def json(self):
        return self._json_data


class TestCommandsAPI(unittest.TestCase):
    """Command Center backend API testlari"""

    def test_tool_registry_loaded(self):
        """ToolRegistry kamida 29 ta haqiqiy tool bilan yuklangan"""
        reg = get_registry()
        self.assertGreaterEqual(reg.count, 29)
        self.assertIsNotNone(reg.get("system_info"))
        self.assertIsNotNone(reg.get("app_check"))
        self.assertIsNotNone(reg.get("calculator"))
        self.assertIsNotNone(reg.get("currency"))
        self.assertIsNotNone(reg.get("audio_control"))

    def test_handle_commands_list(self):
        """GET /api/commands to'liq toollar va qisqartmalar ro'yxatini qaytaradi"""
        async def _run():
            resp = await handle_commands_list(MockRequest())
            data = json.loads(resp.text)
            return data

        data = asyncio.run(_run())
        self.assertTrue(data.get("ok"))
        self.assertIn("categories", data)
        self.assertIn("Tizim", data["categories"])
        self.assertIn("Utilitlar", data["categories"])
        self.assertIn("Ilovalar", data["categories"])
        
        commands = data.get("commands", [])
        self.assertGreaterEqual(len(commands), 35)
        
        # Tool'lar mavjudligini tekshirish
        tool_names = [c.get("tool_name") for c in commands if c.get("is_tool")]
        self.assertIn("system_info", tool_names)
        self.assertIn("calculator", tool_names)
        self.assertIn("app_check", tool_names)
        self.assertIn("audio_control", tool_names)

        # Quick shortcuts
        app_names = [c.get("id") for c in commands if not c.get("is_tool")]
        self.assertIn("app_telegram", app_names)
        self.assertIn("app_vscode", app_names)

    def test_handle_commands_execute_tool(self):
        """POST /api/commands/execute to'g'ridan-to'g'ri tool'ni muvaffaqiyatli bajaradi"""
        async def _run():
            req = MockRequest({"command": "system_info"})
            resp = await handle_commands_execute(req)
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data.get("ok"))
        self.assertIn("cpu", data.get("result", "").lower())

    def test_handle_commands_execute_calculator_with_args(self):
        """Kalkulyator ifodani hisoblaydi"""
        async def _run():
            req = MockRequest({"command": "calculator 45 * 2"})
            resp = await handle_commands_execute(req)
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data.get("ok"))
        self.assertIn("90", data.get("result", ""))

    def test_handle_commands_execute_with_parameters_dict(self):
        """Parametrlar dictionary ko'rinishida berilganda to'g'ri chaqiriladi"""
        async def _run():
            req = MockRequest({
                "command": "calculator",
                "parameters": {"expression": "250 + 750"}
            })
            resp = await handle_commands_execute(req)
            return json.loads(resp.text)

        data = asyncio.run(_run())
        self.assertTrue(data.get("ok"))
        self.assertIn("1000", data.get("result", ""))

    def test_format_tool_result(self):
        """Formatlovchi xabarlarni toza va xatosiz qaytaradi"""
        res_info = {"success": True, "result": {"info": {"cpu": "10%", "ram": "40%"}}}
        formatted = format_tool_result("system_info", res_info)
        self.assertIn("CPU: 10%", formatted)
        self.assertIn("RAM: 40%", formatted)

        res_err = {"success": False, "error": "Bo'sh qiymat"}
        formatted_err = format_tool_result("calc", res_err)
        self.assertTrue(formatted_err.startswith("Xatolik:"))


if __name__ == "__main__":
    unittest.main()
