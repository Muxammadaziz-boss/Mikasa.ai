# ========== test_tool_contract.py ==========
# Phase 32 — Tool Contract 2.0 & Normalized Data Structures Unit Tests
# Standardized Metadata, Health Transitions, Serialization & Backward Compatibility

import os
import sys
import unittest
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.intelligence.types import RiskLevel
from core.tools.contract import ToolContract2, ToolErrorCode, ToolHealth, ToolResult
from core.agent_tools import Tool


class TestToolContract(unittest.TestCase):
    """Tool Contract 2.0 spetsifikatsiyasi va metadata testlari"""

    def test_contract_initialization_defaults(self):
        """ToolContract2 standart parametrlar bilan to'g'ri initsializatsiya qilinishi"""
        tool = ToolContract2(
            name="echo_tool",
            description="Returns input text",
            parameters={"text": {"type": "string", "description": "Text to echo"}},
            function=lambda text: f"Echo: {text}",
        )

        self.assertEqual(tool.name, "echo_tool")
        self.assertEqual(tool.version, "2.0.0")
        self.assertEqual(tool.health, ToolHealth.AVAILABLE)
        self.assertEqual(tool.risk_level, RiskLevel.LOW)
        self.assertEqual(tool.timeout, 10.0)
        self.assertTrue(tool.idempotent)
        self.assertFalse(tool.destructive)
        self.assertEqual(tool.capabilities, ["echo_tool"])
        self.assertEqual(tool.required_parameters, [])
        self.assertEqual(tool.failure_count, 0)
        self.assertEqual(tool.success_count, 0)

    def test_contract_automatic_required_params_inference(self):
        """Parametrlarda required: True bo'lsa, required_parameters ga avtomatik kiritilishi"""
        tool = ToolContract2(
            name="calc_tool",
            description="Calculates expression",
            parameters={
                "expression": {"type": "string", "description": "Math expression", "required": True},
                "precision": {"type": "integer", "description": "Decimal places", "required": False},
            },
            function=lambda expression, precision=2: round(eval(expression), precision),
        )

        self.assertIn("expression", tool.required_parameters)
        self.assertNotIn("precision", tool.required_parameters)

    def test_contract_enum_coercion(self):
        """String formatdagi risk_level va health enumlarga to'g'ri keltirilishi"""
        tool = ToolContract2(
            name="risky_tool",
            description="Deletes system items",
            parameters={},
            function=lambda: None,
            risk_level="high",
            health="degraded",
        )

        self.assertEqual(tool.risk_level, RiskLevel.HIGH)
        self.assertEqual(tool.health, ToolHealth.DEGRADED)

    def test_contract_to_dict_serialization(self):
        """to_dict() metodi barcha frontend va observability maydonlarini to'liq qaytarishi"""
        tool = ToolContract2(
            name="search_tool",
            description="Searches web",
            parameters={"query": {"type": "string", "description": "Search query", "required": True}},
            function=lambda query: [],
            category="web",
            capabilities=["web_search", "lookup"],
            aliases=["google", "find"],
            risk_level=RiskLevel.LOW,
            timeout=15.0,
            idempotent=True,
            destructive=False,
        )

        d = tool.to_dict()
        self.assertEqual(d["name"], "search_tool")
        self.assertEqual(d["version"], "2.0.0")
        self.assertEqual(d["category"], "web")
        self.assertIn("web_search", d["capabilities"])
        self.assertIn("google", d["aliases"])
        self.assertEqual(d["parameters"]["query"]["type"], "string")
        self.assertTrue(d["parameters"]["query"]["required"])
        self.assertEqual(d["risk_level"], "low")
        self.assertEqual(d["timeout"], 15.0)
        self.assertEqual(d["health"], "available")
        self.assertIn("metrics", d)

    def test_contract_health_success_recovery(self):
        """mark_success() muvaffaqiyat hisoblagichini oshirishi va DEGRADED holatini tiklashi"""
        tool = ToolContract2(
            name="test_tool",
            description="Test",
            parameters={},
            function=lambda: None,
            health=ToolHealth.DEGRADED,
        )
        tool.consecutive_failures = 3

        tool.mark_success(duration_ms=45.2)
        self.assertEqual(tool.success_count, 1)
        self.assertEqual(tool.consecutive_failures, 0)
        self.assertEqual(tool.last_duration_ms, 45.2)
        self.assertEqual(tool.health, ToolHealth.AVAILABLE)
        self.assertIsNotNone(tool.last_executed)

    def test_contract_health_failure_degradation(self):
        """Ketma-ket 3 ta xatolikdan so'ng asbob salomatligi DEGRADED bo'lishi"""
        tool = ToolContract2(
            name="flaky_tool",
            description="Flaky service",
            parameters={},
            function=lambda: None,
        )

        self.assertEqual(tool.health, ToolHealth.AVAILABLE)
        tool.mark_failure("Error 1", 10.0)
        self.assertEqual(tool.consecutive_failures, 1)
        self.assertEqual(tool.health, ToolHealth.AVAILABLE)

        tool.mark_failure("Error 2", 15.0)
        self.assertEqual(tool.consecutive_failures, 2)
        self.assertEqual(tool.health, ToolHealth.AVAILABLE)

        tool.mark_failure("Error 3", 20.0)
        self.assertEqual(tool.consecutive_failures, 3)
        self.assertEqual(tool.health, ToolHealth.DEGRADED)
        self.assertEqual(tool.last_error, "Error 3")

    def test_tool_result_creation_and_fields(self):
        """ToolResult to'g'ri maydonlar bilan shakllantirilishi"""
        result = ToolResult(
            success=True,
            code=None,
            message="Bajarildi",
            data={"value": 42},
            duration_ms=12.5,
            tool="calc",
            trace_id="trace-123"
        )

        self.assertTrue(result.success)
        self.assertIsNone(result.code)
        self.assertEqual(result.data["value"], 42)
        self.assertEqual(result.duration_ms, 12.5)
        self.assertEqual(result.tool, "calc")
        self.assertEqual(result.trace_id, "trace-123")

    def test_tool_result_legacy_dict_emulation(self):
        """ToolResult eski dict interfeysi bilan 100% mos ishlashi (getitem, get, in)"""
        result = ToolResult(
            success=True,
            message="Operatsiya muvaffaqiyatli",
            data="output_content",
            tool="reader"
        )

        # Legacy dict access
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "output_content")
        self.assertEqual(result["data"], "output_content")
        self.assertEqual(result.get("message"), "Operatsiya muvaffaqiyatli")
        self.assertEqual(result.get("non_existent", "default_val"), "default_val")
        self.assertIn("success", result)
        self.assertIn("result", result)

        with self.assertRaises(KeyError):
            _ = result["unknown_key"]

    def test_tool_result_sensitive_data_redaction(self):
        """ToolResult.to_dict() maxfiy ma'lumotlarni avtomatik qoralamasi (redact)"""
        result = ToolResult(
            success=True,
            data={"api_key": "sk-1234567890abcdef", "user_password": "supersecretpassword"},
            metadata={"token": "Bearer abcdef123456"}
        )

        d = result.to_dict()
        self.assertEqual(d["data"]["api_key"], "[REDACTED]")
        self.assertEqual(d["data"]["user_password"], "[REDACTED]")
        self.assertEqual(d["metadata"]["token"], "[REDACTED]")

    def test_tool_result_from_legacy_dict(self):
        """from_legacy_dict() eski lug'at natijalarini normalizatsiya qilishi"""
        legacy_success = {"success": True, "result": "100.0", "message": "Hisoblandi"}
        res1 = ToolResult.from_legacy_dict(legacy_success, tool_name="calculator", duration_ms=5.0)
        self.assertTrue(res1.success)
        self.assertEqual(res1.data, "100.0")
        self.assertEqual(res1.tool, "calculator")

        legacy_error = {"success": False, "error": "Bo'lish nolga teng"}
        res2 = ToolResult.from_legacy_dict(legacy_error, tool_name="calculator")
        self.assertFalse(res2.success)
        self.assertEqual(res2.code, ToolErrorCode.EXECUTION_ERROR)
        self.assertEqual(res2.error, "Bo'lish nolga teng")

    def test_legacy_tool_subclass_backward_compatibility(self):
        """core.agent_tools.Tool eski konstruktor orqali ToolContract2 sifatida ishlashi"""
        def dummy_action(text):
            return {"success": True, "result": text.upper()}

        tool = Tool(
            name="uppercase",
            description="Converts to uppercase",
            func=dummy_action,
            parameters={"text": {"type": "string", "required": True}},
            category="string_helpers"
        )

        self.assertIsInstance(tool, ToolContract2)
        self.assertEqual(tool.name, "uppercase")
        self.assertEqual(tool.category, "string_helpers")
        self.assertEqual(tool.function, dummy_action)
        self.assertIn("text", tool.required_parameters)
        # Call invocation
        res = tool.call(text="salom")
        self.assertIsInstance(res, ToolResult)
        self.assertTrue(res.success)
        self.assertEqual(res["result"], "SALOM")

    def test_tool_contract_and_result_json_serializable(self):
        """to_dict() JSON ga to'liq muvaffaqiyatli serialize bo'lishi"""
        import json
        tool = Tool(
            name="json_test",
            description="Test json",
            function=lambda: {"ok": True},
            parameters={"arg": {"type": "string"}},
            risk_level=RiskLevel.MEDIUM,
        )
        tool_json = json.dumps(tool.to_dict())
        self.assertIn("json_test", tool_json)

        res = ToolResult(success=True, data={"list": [1, 2, 3]}, tool="json_test")
        res_json = json.dumps(res.to_dict())
        self.assertIn("json_test", res_json)
        self.assertIn("list", res_json)

    def test_registry_tool_not_found(self):
        """ToolRegistry topilmagan vosita uchun to'g'ri TOOL_NOT_FOUND xatoligini qaytarishi"""
        from core.agent_tools import ToolRegistry
        reg = ToolRegistry()
        res = reg.call("non_existent_tool_xyz")
        self.assertIsInstance(res, ToolResult)
        self.assertFalse(res.success)
        self.assertEqual(res.code, ToolErrorCode.TOOL_NOT_FOUND)
        self.assertIn("topilmadi", res.error)


if __name__ == "__main__":
    unittest.main()
