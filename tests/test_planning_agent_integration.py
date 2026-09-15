# ========== test_planning_agent_integration.py ==========
# Mikasa AI 7.x — Integration Tests for Planning & Reasoning 2.0 Loop

import unittest
from unittest.mock import MagicMock

from core.intelligence.types import (
    AgentState,
    PlanStatus,
    StepStatus,
    RiskLevel,
    PlanStep,
    AgentPlan,
    StepResult,
    FailureCategory,
)
from core.intelligence.agent_loop import AgentLoop
from core.intelligence.observability import ObservabilityManager, get_observability_manager
from core.tools.contract import ToolContract2, ToolHealth


class TestPlanningAgentIntegration(unittest.TestCase):
    """Planning & Reasoning 2.0 to'liq integratsiya testlari (AgentLoop + Planner)"""

    def setUp(self):
        self.mock_registry = MagicMock()
        self.events = []

        def _event_emitter(event_type, data):
            self.events.append((event_type, data))

        self.loop = AgentLoop(
            tool_registry=self.mock_registry,
            event_emitter=_event_emitter,
        )

    def test_execution_order_traversal(self):
        """Reja qadamlari plan.execution_order ketma-ketligi bo'yicha bajariladi"""
        # s1 va s2 yaratamiz, s2 s1 ga bog'liq
        s1 = PlanStep(step_id="s1", order=1, intent="calc", tool="calculator", parameters={"expression": "2*2"})
        s2 = PlanStep(step_id="s2", order=2, intent="calc", tool="calculator", parameters={"expression": "4*4"}, dependencies=["s1"])

        plan = AgentPlan(
            plan_id="p-order",
            goal="Tartibli ijro",
            steps=[s1, s2],
            dependencies={"s2": ["s1"], "s1": []},
            execution_order=["s1", "s2"],
        )

        # Mock tool execution
        self.mock_registry.get.return_value = MagicMock()
        self.mock_registry.call.side_effect = [
            {"success": True, "result": "4"},
            {"success": True, "result": "16"},
        ]

        resp = self.loop.execute_plan(plan)
        self.assertTrue(resp.verified)
        self.assertEqual(plan.status, PlanStatus.COMPLETED)
        self.assertEqual(s1.status, StepStatus.COMPLETED)
        self.assertEqual(s2.status, StepStatus.COMPLETED)

        # Metadata tekshiruvi
        self.assertEqual(resp.metadata.get("plan_version"), 1)
        self.assertEqual(resp.metadata.get("execution_order"), ["s1", "s2"])

    def test_dependency_blocking_when_prerequisite_fails(self):
        """Oldingi qadam muvaffaqiyatsiz bo'lsa, unga bog'liq qadam BLOCKED holatiga o'tadi"""
        s1 = PlanStep(step_id="s1", order=1, intent="fail_tool", tool="calculator", parameters={"expression": "1/0"})
        s2 = PlanStep(step_id="s2", order=2, intent="next_tool", tool="weather", dependencies=["s1"])

        plan = AgentPlan(
            plan_id="p-block",
            goal="Bog'liqlik blokirovkasi",
            steps=[s1, s2],
            dependencies={"s2": ["s1"], "s1": []},
            execution_order=["s1", "s2"],
        )

        # Mock s1 failing
        self.mock_registry.get.return_value = MagicMock()
        self.mock_registry.call.return_value = {"success": False, "error": "ZeroDivisionError"}

        resp = self.loop.execute_plan(plan)
        self.assertFalse(resp.verified)
        self.assertEqual(plan.status, PlanStatus.FAILED)
        self.assertEqual(s1.status, StepStatus.FAILED)
        self.assertIn("bajarilmadi", resp.content.lower())

    def test_replan_on_tool_failure_with_fallback(self):
        """Birlamchi asbob xato berganda replan ishga tushadi, fallback tanlanadi va versiya oshadi"""
        s1 = PlanStep(
            step_id="s1",
            order=1,
            intent="search",
            tool="google_search",
            required_capability="search",
        )
        plan = AgentPlan(
            plan_id="p-replan-integ",
            goal="Zaxirali qidiruv",
            steps=[s1],
            dependencies={},
            execution_order=["s1"],
        )

        primary_tool = ToolContract2(name="google_search", description="Google", capabilities=["search"])
        fallback_tool = ToolContract2(name="duckduckgo", description="DuckDuckGo", capabilities=["search"])

        def mock_get(name):
            if name == "google_search":
                return primary_tool
            return fallback_tool

        self.mock_registry.get.side_effect = mock_get

        sel_res = MagicMock()
        sel_res.fallback_tool = fallback_tool
        self.mock_registry.select_tool.return_value = sel_res

        # 1-marta google_search xato beradi, 2-marta duckduckgo muvaffaqiyatli ishlaydi
        call_results = [
            {"success": False, "error": "Rate limit 429"},
            {"success": False, "error": "Rate limit 429"},  # retry
            {"success": True, "result": "Qidiruv natijalari"},  # replanned call
        ]
        self.mock_registry.call.side_effect = call_results

        resp = self.loop.execute_plan(plan)

        # Qayta rejalashtirish natijasida v2 bo'ldi
        self.assertEqual(plan.plan_version, 2)
        self.assertEqual(plan.replan_count, 1)
        self.assertEqual(s1.tool, "duckduckgo")
        self.assertEqual(resp.metadata.get("plan_version"), 2)
        self.assertEqual(resp.metadata.get("replan_count"), 1)

        # agent_plan_replanned hodisasi tarqatilganini tekshirish
        replan_events = [e for e in self.events if e[0] == "agent_plan_replanned"]
        self.assertEqual(len(replan_events), 1)
        self.assertEqual(replan_events[0][1]["version"], 2)

    def test_plan_optimizer_removes_duplicates_in_creation(self):
        """create_plan_from_goal davomida dublikat qadamlar optimallashtiriladi"""
        plan = self.loop.create_plan_from_goal("youtube ni och va youtube ni och")
        # Dublikat bartaraf etilgan bo'lishi kerak
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].tool, "open_youtube")

    def test_observability_planning_stages_recorded(self):
        """Plan ijrosi davomida yangi kuzatuv bosqichlari (STEP_READY, STEP_DEPENDENCY_RESOLVED) qayd etiladi"""
        s1 = PlanStep(step_id="s1", order=1, intent="calc", tool="calculator", parameters={"expression": "5+5"})
        plan = AgentPlan(
            plan_id="p-obs",
            goal="Observability testi",
            steps=[s1],
            dependencies={"s1": []},
            execution_order=["s1"],
        )
        self.mock_registry.get.return_value = MagicMock()
        self.mock_registry.call.return_value = {"success": True, "result": "10"}

        obs = get_observability_manager()
        trace = obs.create_trace()

        resp = self.loop.execute_plan(plan, trace=trace)
        self.assertTrue(resp.verified)

        stage_names = [st.stage for st in trace.stages]
        self.assertIn("STEP_READY", stage_names)
        self.assertIn("STEP_COMPLETED", stage_names)
        self.assertIn("PLAN_COMPLETED", stage_names)


if __name__ == "__main__":
    unittest.main()
