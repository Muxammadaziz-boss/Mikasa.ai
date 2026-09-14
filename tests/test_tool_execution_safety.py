# ========== test_tool_execution_safety.py ==========
# Phase 32 — Safe Tool Runner & Execution Safety Pipeline Unit Tests
# Timeout Enforcement, Health Degradation, Idempotency & Redaction

import os
import sys
import time
import unittest
from unittest.mock import MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.intelligence.types import RiskLevel
from core.tools.contract import ToolContract2, ToolErrorCode, ToolHealth, ToolResult
from core.tools.runner import SafeToolRunner
from core.intelligence.permission import PermissionEngine


class TestToolExecutionSafety(unittest.TestCase):
    """Xavfsiz asboblar ijro etish zanjiri va himoya testlari"""

    def setUp(self):
        self.perm_engine = PermissionEngine()
        self.runner = SafeToolRunner(permission_engine=self.perm_engine)

    def test_timeout_enforcement(self):
        """Uzoq vaqt qotib qolgan asbob timeout bilan to'xtatilishi va TIMEOUT xatosi qaytishi"""
        def slow_function():
            time.sleep(1.0)
            return "Should not reach"

        tool = ToolContract2(
            name="slow_tool",
            description="Hangs execution",
            parameters={},
            function=slow_function,
            timeout=0.1,  # 100ms
        )

        res = self.runner.execute_tool(tool, {})
        self.assertFalse(res.success)
        self.assertEqual(res.code, ToolErrorCode.TIMEOUT)
        self.assertIn("vaqt chegarasida", res.error)
        self.assertEqual(tool.consecutive_failures, 1)

    def test_health_degradation_after_consecutive_failures(self):
        """Ketma-ket 3 ta xatolikdan so'ng asbob DEGRADED holatiga o'tishi"""
        def failing_function():
            raise RuntimeError("Hardware failure")

        tool = ToolContract2(
            name="broken_service",
            description="Always fails",
            parameters={},
            function=failing_function,
            timeout=2.0,
        )

        self.assertEqual(tool.health, ToolHealth.AVAILABLE)

        # Run 1
        self.runner.execute_tool(tool, {})
        self.assertEqual(tool.consecutive_failures, 1)
        self.assertEqual(tool.health, ToolHealth.AVAILABLE)

        # Run 2
        self.runner.execute_tool(tool, {})
        self.assertEqual(tool.consecutive_failures, 2)
        self.assertEqual(tool.health, ToolHealth.AVAILABLE)

        # Run 3
        self.runner.execute_tool(tool, {})
        self.assertEqual(tool.consecutive_failures, 3)
        self.assertEqual(tool.health, ToolHealth.DEGRADED)

    def test_health_recovery_on_success(self):
        """DEGRADED holatidagi asbob muvaffaqiyatli ishlaganida AVAILABLE ga qaytishi"""
        state = {"fail": True}

        def unstable_function():
            if state["fail"]:
                raise RuntimeError("Temporary error")
            return "Recovered!"

        tool = ToolContract2(
            name="recovering_tool",
            description="Unstable",
            parameters={},
            function=unstable_function,
            health=ToolHealth.DEGRADED,
        )
        tool.consecutive_failures = 3

        # Hali xato bermoqda
        res1 = self.runner.execute_tool(tool, {})
        self.assertFalse(res1.success)
        self.assertEqual(tool.health, ToolHealth.DEGRADED)

        # Muammo hal bo'ldi
        state["fail"] = False
        res2 = self.runner.execute_tool(tool, {})
        self.assertTrue(res2.success)
        self.assertEqual(tool.health, ToolHealth.AVAILABLE)
        self.assertEqual(tool.consecutive_failures, 0)

    def test_disabled_tool_blocked_immediately(self):
        """DISABLED holatdagi asbob funksiyani chaqirmasdan darhol bloklanishi"""
        func_mock = MagicMock()
        tool = ToolContract2(
            name="disabled_feature",
            description="Feature disabled",
            parameters={},
            function=func_mock,
            health=ToolHealth.DISABLED,
        )

        res = self.runner.execute_tool(tool, {})
        self.assertFalse(res.success)
        self.assertEqual(res.code, ToolErrorCode.TOOL_UNAVAILABLE)
        self.assertIn("DISABLED", res.error)
        func_mock.assert_not_called()

    def test_sensitive_data_redacted_in_runner(self):
        """Maxfiy parametrlar va natijalar xavfsiz tozalanishi (redact)"""
        def vault_function(api_key, username):
            return {"user": username, "secret": "super_secret_payload_123"}

        tool = ToolContract2(
            name="vault_tool",
            description="Vault test",
            parameters={
                "api_key": {"type": "string", "required": True},
                "username": {"type": "string", "required": True}
            },
            function=vault_function,
        )

        res = self.runner.execute_tool(tool, {
            "api_key": "sk-proj-test1234567890",
            "username": "tester"
        })

        self.assertTrue(res.success)
        d = res.to_dict()
        self.assertEqual(d["data"]["user"], "tester")
        self.assertEqual(d["data"]["secret"], "[REDACTED]")

    def test_unhandled_exception_gracefully_normalized(self):
        """Kutilmagan xatolik (Exception) paydo bo'lganda tizim qulamasdan EXECUTION_ERROR qaytarishi"""
        def error_func():
            raise ZeroDivisionError("division by zero test")

        tool = ToolContract2(
            name="divide_tool",
            description="Divides",
            parameters={},
            function=error_func,
        )

        res = self.runner.execute_tool(tool, {})
        self.assertFalse(res.success)
        self.assertEqual(res.code, ToolErrorCode.EXECUTION_ERROR)
        self.assertIn("division by zero test", res.error)

    def test_high_risk_permission_check(self):
        """HIGH xavf darajasidagi vosita uchun avtomatik CONFIRMATION talab qilinishi"""
        tool = ToolContract2(
            name="system_shutdown",
            description="Shuts down host",
            parameters={"force": {"type": "boolean", "required": False}},
            function=lambda **kwargs: "shutting down",
            risk_level=RiskLevel.HIGH,
            destructive=True,
        )

        # Bypasiz ishga tushirish
        res = self.runner.execute_tool(tool, {"force": True}, bypass_permission=False)
        self.assertFalse(res.success)
        self.assertEqual(res.code, ToolErrorCode.PERMISSION_DENIED)
        self.assertTrue(res.metadata.get("requires_confirmation"))

        # Bypass qilinganda (masalan, foydalanuvchi tasdiqlaganidan keyin)
        res_approved = self.runner.execute_tool(tool, {"force": True}, bypass_permission=True)
        self.assertTrue(res_approved.success)

    def test_trace_stages_recorded_during_execution(self):
        """SafeToolRunner ijro davomida Observability trace bosqichlarini to'g'ri yozishi"""
        from core.intelligence.observability import ContextTrace

        trace = ContextTrace(request_id="test_req", trace_id="trace_1", query="antigravity test")
        tool = ToolContract2(
            name="traced_tool",
            description="Traced",
            parameters={"msg": {"type": "string"}},
            function=lambda msg="hello": msg,
        )

        res = self.runner.execute_tool(tool, {"msg": "antigravity"}, trace=trace)
        self.assertTrue(res.success)

        stages = [s.stage for s in trace.stages]
        self.assertIn("TOOL_STARTED", stages)
        self.assertIn("TOOL_COMPLETED", stages)

    def test_primitive_returns_normalized_to_tool_result(self):
        """Asbob oddiy primitive qiymat (int, str, list) qaytarganda ToolResult ga to'g'ri o'ralishi"""
        tool = ToolContract2(
            name="primitive_returner",
            description="Returns raw list",
            parameters={},
            function=lambda: [10, 20, 30],
        )

        res = self.runner.execute_tool(tool, {})
        self.assertIsInstance(res, ToolResult)
        self.assertTrue(res.success)
        self.assertEqual(res.data, [10, 20, 30])
        self.assertIn("10, 20, 30", res.message)


if __name__ == "__main__":
    unittest.main()
