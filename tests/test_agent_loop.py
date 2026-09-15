# ========== test_agent_loop.py ==========
# Phase 31 — Agent Execution Loop Unit & Integration Tests
# PLAN → ACT → OBSERVE → VERIFY → CONTINUE → COMPLETE

import os
import sys
import json
import time
import asyncio
import unittest
from unittest.mock import MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.intelligence.types import (
    AgentState,
    PlanStatus,
    StepStatus,
    VerificationStatus,
    RiskLevel,
    PlanStep,
    AgentPlan,
    AgentExecutionState,
    VerificationResult,
    StepResult,
    IntelligenceResponse,
)
from core.intelligence.agent_loop import AgentLoop, get_agent_loop
from core.intelligence.permission import PermissionEngine
from core.intelligence.verifier import AgentVerifier
from core.api_server import (
    handle_agent_execute,
    handle_agent_confirm,
    handle_agent_abort,
    handle_agent_state,
)


class MockRequest:
    def __init__(self, json_data=None, query_data=None):
        self._json_data = json_data or {}
        self.query = query_data or {}
        self.can_read_body = True

    async def json(self):
        return self._json_data


class TestAgentLoop(unittest.TestCase):
    """AgentLoop to'liq sikl va deterministik agentlik testlari"""

    def setUp(self):
        self.mock_registry = MagicMock()
        # Default mock tool responses
        self.mock_registry.get.return_value = MagicMock()
        self.mock_registry.call.return_value = {"success": True, "result": "Muvaffaqiyatli bajarildi"}

        self.perm_engine = PermissionEngine()
        self.verifier = AgentVerifier(tool_registry=self.mock_registry)
        self.events = []

        def _emitter(evt, data):
            self.events.append((evt, data))

        self.loop = AgentLoop(
            tool_registry=self.mock_registry,
            permission_engine=self.perm_engine,
            verifier=self.verifier,
            event_emitter=_emitter,
        )

    # 1. Ma'lumot modellari (Data models serialization)
    def test_dataclasses_serialization(self):
        """PlanStep, AgentPlan va AgentExecutionState to'g'ri lug'atga o'giriladi va tiklanadi"""
        step = PlanStep(
            step_id="st-1",
            order=1,
            intent="weather",
            tool="weather",
            parameters={"city": "Toshkent"},
            expected_result="havo ochiq",
            risk_level=RiskLevel.LOW,
            status=StepStatus.PENDING,
        )
        s_dict = step.to_dict()
        self.assertEqual(s_dict["tool"], "weather")
        self.assertEqual(s_dict["status"], "pending")

        restored_step = PlanStep.from_dict(s_dict)
        self.assertEqual(restored_step.step_id, "st-1")
        self.assertEqual(restored_step.risk_level, RiskLevel.LOW)

        plan = AgentPlan(
            plan_id="p-1",
            goal="Test maqsad",
            steps=[step],
            status=PlanStatus.RUNNING,
        )
        p_dict = plan.to_dict()
        self.assertEqual(p_dict["goal"], "Test maqsad")
        self.assertEqual(len(p_dict["steps"]), 1)

        restored_plan = AgentPlan.from_dict(p_dict)
        self.assertEqual(restored_plan.plan_id, "p-1")
        self.assertEqual(len(restored_plan.steps), 1)

    # 2. Reja yaratish: Conjunction 'va'
    def test_create_plan_conjunction_va(self):
        """'A va B' formatidagi maqsad 2 qadamli rejaga ajratiladi"""
        plan = self.loop.create_plan_from_goal("Toshkent ob-havosini bil va 25 * 4 ni hisobla")
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].tool, "weather")
        self.assertEqual(plan.steps[1].tool, "calculator")
        self.assertEqual(plan.steps[0].order, 1)
        self.assertEqual(plan.steps[1].order, 2)

    # 3. Reja yaratish: Conjunction 'keyin'
    def test_create_plan_conjunction_keyin(self):
        """'A keyin B' formatidagi maqsad 2 qadamli rejaga ajratiladi"""
        plan = self.loop.create_plan_from_goal("youtube ni och keyin brave brauzerini och")
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].tool, "open_youtube")
        self.assertEqual(plan.steps[1].tool, "open_brave")

    # 4. Yagona maqsad (Single step goal)
    def test_create_plan_single_goal(self):
        """Yakka buyruq 1 qadamli rejaga aylanadi"""
        plan = self.loop.create_plan_from_goal("Valyuta kursini bilish")
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].tool, "currency")

    # 5. Rejani tekshirish (Validation)
    def test_validate_plan_valid(self):
        """Qoidalarga mos reja validatsiyadan muvaffaqiyatli o'tadi"""
        plan = self.loop.create_plan_from_goal("Toshkent ob-havosi va hisoblash")
        is_valid, err = self.loop.validate_plan(plan)
        self.assertTrue(is_valid)
        self.assertIsNone(err)

    def test_validate_plan_empty(self):
        """Qadamsiz bo'sh reja rad etiladi"""
        plan = AgentPlan(plan_id="p-0", goal="Bo'sh", steps=[])
        is_valid, err = self.loop.validate_plan(plan)
        self.assertFalse(is_valid)
        self.assertIn("AGENT_PLAN_INVALID", err)

    def test_validate_plan_exceed_max_steps(self):
        """8 tadan ko'p qadamli reja rad etiladi"""
        steps = [
            PlanStep(step_id=f"s{i}", order=i, intent="tool", tool="calculator")
            for i in range(1, 10)
        ]
        plan = AgentPlan(plan_id="p-overflow", goal="Limitdan katta", steps=steps)
        is_valid, err = self.loop.validate_plan(plan)
        self.assertFalse(is_valid)
        self.assertIn("limitdan oshib ketdi", err)

    # 6. State Machine Holatlar o'tishi
    def test_state_machine_valid_transitions(self):
        """Holatlar o'tishi tekshiriladi"""
        self.assertEqual(self.loop.state, AgentState.IDLE)
        self.loop._transition_to(AgentState.PLANNING)
        self.assertEqual(self.loop.state, AgentState.PLANNING)
        self.loop._transition_to(AgentState.VALIDATING)
        self.assertEqual(self.loop.state, AgentState.VALIDATING)
        self.loop._transition_to(AgentState.EXECUTING)
        self.assertEqual(self.loop.state, AgentState.EXECUTING)
        self.loop._transition_to(AgentState.OBSERVING)
        self.assertEqual(self.loop.state, AgentState.OBSERVING)
        self.loop._transition_to(AgentState.VERIFYING)
        self.assertEqual(self.loop.state, AgentState.VERIFYING)
        self.loop._transition_to(AgentState.COMPLETED)
        self.assertEqual(self.loop.state, AgentState.COMPLETED)

    def test_state_machine_invalid_transition_raises(self):
        """Noto'g'ri o'tish (masalan IDLE -> COMPLETED) ValueError qo'zg'atadi"""
        self.assertEqual(self.loop.state, AgentState.IDLE)
        with self.assertRaises(ValueError):
            self.loop._transition_to(AgentState.COMPLETED)

    # 7. Ketma-ket muvaffaqiyatli ijro (Execution flow)
    def test_execute_plan_all_steps_success(self):
        """2 qadamli reja to'liq va muvaffaqiyatli yakunlanadi"""
        plan = self.loop.create_plan_from_goal("25 * 4 ni hisobla va Toshkent ob-havosini ko'r")
        # Mock calculator va weather natijalari
        def _mock_call(tool, **kwargs):
            if tool == "calculator":
                return {"success": True, "result": "100"}
            elif tool == "weather":
                return {"success": True, "result": "Toshkentda havo ochiq +22°C"}
            return {"success": True, "result": "OK"}

        self.mock_registry.call.side_effect = _mock_call

        resp = self.loop.execute_plan(plan)

        self.assertEqual(resp.type, "answer")
        self.assertTrue(resp.verified)
        self.assertEqual(plan.status, PlanStatus.COMPLETED)
        self.assertEqual(self.loop.state, AgentState.COMPLETED)
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(plan.steps[1].status, StepStatus.COMPLETED)

    # 8. WebSocket hodisalarining tarqatilishi (Event Emission)
    def test_execute_plan_events_emitted(self):
        """Reja ijrosi davomida barcha agent_* hodisalari tarqatiladi"""
        plan = self.loop.create_plan_from_goal("25 * 4 ni hisobla")
        self.mock_registry.call.return_value = {"success": True, "result": "100"}

        self.loop.execute_plan(plan)

        event_names = [e[0] for e in self.events]
        self.assertIn("agent_plan_created", event_names)
        self.assertIn("agent_step_started", event_names)
        self.assertIn("agent_verification", event_names)
        self.assertIn("agent_step_completed", event_names)
        self.assertIn("agent_completed", event_names)

    # 9. Qadamni qayta urinish (Transient retry)
    def test_execute_plan_transient_retry_success(self):
        """1-marta xato berib, 2-qayta urinishda o'nglanadigan asbob muvaffaqiyatli o'tadi"""
        step = PlanStep(
            step_id="st-retry-1",
            order=1,
            intent="calculator",
            tool="calculator",
            parameters={"expression": "10+5"},
            risk_level=RiskLevel.LOW,
            max_retries=1,
        )
        plan = AgentPlan(plan_id="p-ret-1", goal="Hisoblash", steps=[step])

        calls = [
            {"success": False, "error": "Vaqtinchalik xato"},  # 1-urinish xato
            {"success": True, "result": "15"},                 # 2-urinish muvaffaqiyatli
        ]

        def _side_effect(*args, **kwargs):
            return calls.pop(0)

        self.mock_registry.call.side_effect = _side_effect

        resp = self.loop.execute_plan(plan)
        self.assertEqual(resp.type, "answer")
        self.assertEqual(step.status, StepStatus.COMPLETED)
        self.assertEqual(step.retry_count, 1)

    # 10. Qayta urinish limiti tugaganda to'xtatish
    def test_execute_plan_retry_exhausted_fails(self):
        """Qayta urinish ham xato bersa, reja STEP_FAILED xatosi bilan to'xtaydi"""
        step = PlanStep(
            step_id="st-retry-fail",
            order=1,
            intent="calculator",
            tool="calculator",
            parameters={"expression": "10/0"},
            risk_level=RiskLevel.LOW,
            max_retries=1,
        )
        plan = AgentPlan(plan_id="p-ret-fail", goal="Hisoblash", steps=[step])

        self.mock_registry.call.return_value = {"success": False, "error": "Nolga bo'lish"}

        resp = self.loop.execute_plan(plan)
        self.assertEqual(resp.type, "error")
        self.assertEqual(resp.error_code, "STEP_FAILED")
        self.assertEqual(plan.status, PlanStatus.FAILED)

    # 11. Tasdiqlash kutish va davom ettirish (WAITING_CONFIRMATION -> RESUME)
    def test_confirmation_pause_and_resume(self):
        """Yuqori xavfli qadam rejani to'xtatadi va confirm_step(approve=True) uni davom ettiradi"""
        steps = [
            PlanStep(
                step_id="s-conf-1",
                order=1,
                intent="shutdown",
                tool="shutdown",
                parameters={},
                risk_level=RiskLevel.HIGH,
            )
        ]
        plan = AgentPlan(plan_id="p-conf-1", goal="Kompyuterni o'chirish", steps=steps)

        # Boshlang'ich ijro -> Tasdiqlash talab etiladi
        resp1 = self.loop.execute_plan(plan)
        self.assertEqual(resp1.type, "confirmation")
        self.assertEqual(self.loop.state, AgentState.WAITING_CONFIRMATION)

        # Foydalanuvchi tasdiqlaydi
        self.mock_registry.call.return_value = {"success": True, "result": "Tizim o'chirilmoqda"}
        resp2 = self.loop.confirm_step("p-conf-1", "s-conf-1", approve=True)

        self.assertEqual(resp2.type, "answer")
        self.assertEqual(plan.status, PlanStatus.COMPLETED)
        self.assertEqual(steps[0].status, StepStatus.COMPLETED)

    # 12. Tasdiqlash rad etilishi (Reject aborts plan)
    def test_confirmation_reject_aborts(self):
        """Foydalanuvchi qadamni rad etsa (approve=False), reja bekor qilinadi"""
        steps = [
            PlanStep(
                step_id="s-rej-1",
                order=1,
                intent="shutdown",
                tool="shutdown",
                parameters={},
                risk_level=RiskLevel.HIGH,
            )
        ]
        plan = AgentPlan(plan_id="p-rej-1", goal="Kompyuterni o'chirish", steps=steps)

        self.loop.execute_plan(plan)
        self.assertEqual(self.loop.state, AgentState.WAITING_CONFIRMATION)

        resp = self.loop.confirm_step("p-rej-1", "s-rej-1", approve=False)
        self.assertEqual(resp.type, "answer")
        self.assertIn("bekor qilindi", resp.content.lower())
        self.assertEqual(plan.status, PlanStatus.ABORTED)
        self.assertEqual(self.loop.state, AgentState.ABORTED)

    # 13. Foydalanuvchi tomonidan to'xtatish (User Abort)
    def test_abort_plan_active(self):
        """abort_plan faol rejani xavfsiz to'xtatadi"""
        plan = AgentPlan(
            plan_id="p-ab-1",
            goal="Uzoq reja",
            steps=[PlanStep(step_id="s-ab-1", order=1, intent="calc", tool="calculator")],
        )
        self.loop._active_plan = plan
        self.loop._state = AgentState.EXECUTING

        stopped, msg = self.loop.abort_plan("p-ab-1")
        self.assertTrue(stopped)
        self.assertEqual(self.loop.state, AgentState.ABORTED)
        self.assertEqual(plan.status, PlanStatus.ABORTED)

    # 14. API Server Endpoints Integratsiyasi
    def test_api_endpoints_integration(self):
        """REST /api/agent/* endpointlari to'g'ri ishlaydi"""
        async def _test():
            # 1. POST /api/agent/execute
            req_exec = MockRequest({"goal": "25 * 4 ni hisobla"})
            resp_exec = await handle_agent_execute(req_exec)
            data_exec = json.loads(resp_exec.text)
            self.assertTrue(data_exec.get("ok"))
            self.assertIn("plan", data_exec)

            # 2. GET /api/agent/state
            req_st = MockRequest()
            resp_st = await handle_agent_state(req_st)
            data_st = json.loads(resp_st.text)
            self.assertTrue(data_st.get("ok"))
            self.assertIn("state", data_st)
            self.assertIn("execution", data_st)

            # 3. POST /api/agent/abort
            req_ab = MockRequest({"plan_id": data_exec["plan"]["plan_id"]})
            resp_ab = await handle_agent_abort(req_ab)
            data_ab = json.loads(resp_ab.text)
            self.assertIn("ok", data_ab)

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
