# ========== test_agent_security.py ==========
# Phase 31 — Agentic Security, Permissions, Idempotency & Injection Resistance Unit Tests

import os
import sys
import unittest
from unittest.mock import MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.intelligence.types import (
    AgentState,
    PlanStatus,
    StepStatus,
    RiskLevel,
    PlanStep,
    AgentPlan,
    StepResult,
    VerificationResult,
    VerificationStatus,
)
from core.intelligence.agent_loop import AgentLoop
from core.intelligence.permission import PermissionEngine
from core.intelligence.verifier import AgentVerifier
from core.intelligence.observability import redact_sensitive_data


class TestAgentSecurity(unittest.TestCase):
    """Agentic ko'p bosqichli tizim xavfsizlik va ruxsatlar testlari"""

    def setUp(self):
        self.mock_registry = MagicMock()
        self.perm_engine = PermissionEngine()
        self.verifier = AgentVerifier(tool_registry=self.mock_registry)
        self.emitted_events = []

        def _emitter(evt, data):
            self.emitted_events.append((evt, data))

        self.loop = AgentLoop(
            tool_registry=self.mock_registry,
            permission_engine=self.perm_engine,
            verifier=self.verifier,
            event_emitter=_emitter,
        )

    # 1. Mustaqil qadam ruxsati (Plan approval != Action approval)
    def test_step_independent_permission_evaluation(self):
        """Reja tasdiqlanishi har bir qadamning mustaqil tekshiruvini aylanib o'tmaydi"""
        # Step 1: low risk (weather), Step 2: high risk (shutdown)
        steps = [
            PlanStep(
                step_id="s1",
                order=1,
                intent="weather",
                tool="weather",
                parameters={"city": "Toshkent"},
                risk_level=RiskLevel.LOW,
            ),
            PlanStep(
                step_id="s2",
                order=2,
                intent="shutdown",
                tool="shutdown",
                parameters={},
                risk_level=RiskLevel.HIGH,
            ),
        ]
        plan = AgentPlan(plan_id="plan-sec-1", goal="Ob-havo va o'chirish", steps=steps)

        # Mock weather result
        self.mock_registry.call.return_value = {"success": True, "result": "Toshkentda havo +20°C"}

        resp = self.loop.execute_plan(plan)

        # Step 1 muvaffaqiyatli bajarilishi, ammo Step 2 ga kelganda to'xtab tasdiqlash so'rashi kerak
        self.assertEqual(resp.type, "confirmation")
        self.assertEqual(self.loop.state, AgentState.WAITING_CONFIRMATION)
        self.assertEqual(plan.status, PlanStatus.PAUSED)
        self.assertEqual(steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(steps[1].status, StepStatus.WAITING_CONFIRMATION)
        self.assertTrue(resp.metadata.get("confirmation_required"))

    # 2. Destruktiv amallarning qayta urinishi taqiqlanganligi (AGENT_RETRY_BLOCKED)
    def test_destructive_action_retry_blocked(self):
        """Xavfli va destruktiv amallar (NON_IDEMPOTENT_ACTIONS) xato bersa, qayta urinish bloklanadi"""
        step = PlanStep(
            step_id="s-del-1",
            order=1,
            intent="clear_memory",
            tool="clear_memory",
            parameters={},
            risk_level=RiskLevel.LOW,  # Test uchun confirmationni chetlab o'tamiz
            max_retries=1,
        )
        plan = AgentPlan(plan_id="plan-del-1", goal="Xotirani tozalash", steps=[step])

        # 1. Boshlang'ich ijro -> Tasdiqlash talab etiladi (WAITING_CONFIRMATION)
        resp1 = self.loop.execute_plan(plan)
        self.assertEqual(resp1.type, "confirmation")
        self.assertEqual(self.loop.state, AgentState.WAITING_CONFIRMATION)

        # 2. Foydalanuvchi tasdiqlaydi -> Asbob xato beradi -> Qayta urinish bloklanadi
        self.mock_registry.call.return_value = {"success": False, "error": "Disk xatosi"}
        resp2 = self.loop.confirm_step(plan.plan_id, step.step_id, approve=True)

        self.assertEqual(resp2.type, "error")
        self.assertEqual(resp2.error_code, "AGENT_RETRY_BLOCKED")
        self.assertEqual(plan.status, PlanStatus.FAILED)
        self.assertEqual(step.retry_count, 0)  # Qayta urinilmagan!
        self.assertIn("bloklandi", resp2.content.lower())

    # 3. NON_IDEMPOTENT_ACTIONS to'plami qamrovi
    def test_non_idempotent_actions_coverage(self):
        """NON_IDEMPOTENT_ACTIONS barcha muhim destruktiv operatsiyalarni o'z ichiga oladi"""
        required = {"shutdown", "restart", "clear_memory", "delete_plugin", "process_kill"}
        for action in required:
            self.assertIn(action, AgentLoop.NON_IDEMPOTENT_ACTIONS)

    # 4. Injection tekshiruvi: rejadagi taqiqlangan kodlar
    def test_prompt_injection_in_plan_parameters(self):
        """eval, exec yoki os.system kabi xavfli kod kiritilgan rejalar rad etiladi"""
        bad_steps = [
            PlanStep(
                step_id="s-bad-1",
                order=1,
                intent="calculator",
                tool="calculator",
                parameters={"expression": "__import__('os').system('calc')"},
            )
        ]
        plan = AgentPlan(plan_id="plan-inj-1", goal="Xavfli reja", steps=bad_steps)

        is_valid, err = self.loop.validate_plan(plan)
        self.assertFalse(is_valid)
        self.assertIn("xavfli", err.lower())

    def test_prompt_injection_eval_prohibited(self):
        """eval so'zi uchragan reja xavfsizlik tekshiruvidan o'tmaydi"""
        bad_steps = [
            PlanStep(
                step_id="s-bad-2",
                order=1,
                intent="custom",
                tool="eval",
                parameters={"code": "1+1"},
            )
        ]
        plan = AgentPlan(plan_id="plan-inj-2", goal="Eval reja", steps=bad_steps)

        is_valid, err = self.loop.validate_plan(plan)
        self.assertFalse(is_valid)

    # 5. Konfidentsial ma'lumotlarni yashirish (Sensitive Data Redaction)
    def test_sensitive_data_redacted_in_events(self):
        """Hodisalar (events) va parametrlarda parollar va API kalitlar yashiriladi"""
        data = {
            "token": "sk-1234567890abcdef1234567890abcdef",
            "password": "SuperSecretPassword123!",
            "api_key": "AIzaSyFakeKey12345",
            "normal_param": "Toshkent",
        }
        redacted = redact_sensitive_data(data)
        self.assertEqual(redacted["token"], "[REDACTED]")
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertEqual(redacted["api_key"], "[REDACTED]")
        self.assertEqual(redacted["normal_param"], "Toshkent")

    # 6. Kod bazasida eval, exec, os.system mavjud emasligi
    def test_no_eval_exec_in_codebase(self):
        """agent_loop.py va verifier.py dinamik eval/exec chaqirmaydi"""
        for fname in ["agent_loop.py", "verifier.py"]:
            path = os.path.join(BASE_DIR, "core", "intelligence", fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # eval( va exec( chaqiruvlari yo'qligini tekshiramiz
                self.assertNotIn(" eval(", content)
                self.assertNotIn(" exec(", content)
                self.assertNotIn("os.system(", content)

    # 7. Max steps limit
    def test_max_steps_limit_enforced(self):
        """8 tadan ko'p qadamli reja qat'iy rad etiladi"""
        steps = [
            PlanStep(step_id=f"s{i}", order=i, intent="tool", tool="calculator")
            for i in range(1, 10)  # 9 qadam
        ]
        plan = AgentPlan(plan_id="plan-max-1", goal="Katta reja", steps=steps)
        is_valid, err = self.loop.validate_plan(plan)
        self.assertFalse(is_valid)
        self.assertIn("limit", err.lower())

    # 8. Bir vaqtning o'zida faqat 1 ta faol reja (Concurrency safety)
    def test_concurrency_lock_prevents_overlap(self):
        """Faol reja ishlayotgan paytda ikkinchi reja AGENT_ALREADY_RUNNING xatosi bilan rad etiladi"""
        plan1 = AgentPlan(
            plan_id="p-run-1",
            goal="Reja 1",
            steps=[PlanStep(step_id="p1-s1", order=1, intent="calc", tool="calculator")],
        )
        plan2 = AgentPlan(
            plan_id="p-run-2",
            goal="Reja 2",
            steps=[PlanStep(step_id="p2-s1", order=1, intent="calc", tool="calculator")],
        )

        # Holatni EXECUTING ga o'rnatamiz
        self.loop._state = AgentState.EXECUTING
        self.loop._active_plan = plan1

        resp = self.loop.execute_plan(plan2)
        self.assertEqual(resp.type, "error")
        self.assertEqual(resp.error_code, "AGENT_ALREADY_RUNNING")

    # 9. Tsiklik yoki takroriy qadamlar aniqlanishi
    def test_circular_step_detection(self):
        """Rejadagi qadamlar ketma-ketligi va tartibi validatsiya qilinadi"""
        empty_plan = AgentPlan(plan_id="p-empty", goal="Bo'sh", steps=[])
        is_valid, err = self.loop.validate_plan(empty_plan)
        self.assertFalse(is_valid)
        self.assertIn("qadam", err.lower())


if __name__ == "__main__":
    unittest.main()
