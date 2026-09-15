# ========== test_replanning.py ==========
# Mikasa AI 7.x — Unit Tests for Replanning Engine 2.0 (ReplanningEngine)

import unittest
from unittest.mock import MagicMock

from core.intelligence.types import (
    StepStatus,
    PlanStep,
    AgentPlan,
    StepResult,
    FailureCategory,
)
from core.tools.contract import ToolContract2, ToolHealth
from core.intelligence.planner import ReplanningEngine


class TestReplanningEngine(unittest.TestCase):
    """ReplanningEngine sinovi: zaxira asbob, xavfsizlik chegaralari va versiyalash"""

    def setUp(self):
        self.engine = ReplanningEngine()

    def test_replan_with_fallback_tool(self):
        """Birlamchi asbob ishlamay qolganda, zaxira (fallback) asbob tanlanadi va versiya yangilanadi"""
        s1 = PlanStep(
            step_id="step_1",
            order=1,
            intent="web_search",
            tool="google_search",
            required_capability="search",
        )
        plan = AgentPlan(
            plan_id="p-replan-1",
            goal="Qidiruv",
            steps=[s1],
        )

        # Mock ToolRegistry
        mock_registry = MagicMock()
        primary_tool = ToolContract2(
            name="google_search",
            description="Google Search",
            capabilities=["search"],
        )
        fallback_tool = ToolContract2(
            name="duckduckgo_search",
            description="DuckDuckGo Search",
            capabilities=["search"],
        )
        mock_registry.get.return_value = primary_tool

        sel_result = MagicMock()
        sel_result.fallback_tool = fallback_tool
        mock_registry.select_tool.return_value = sel_result

        step_res = StepResult(
            step_id="step_1",
            tool="google_search",
            success=False,
            error="Rate limit exceeded",
        )

        engine = ReplanningEngine(tool_registry=mock_registry)
        did_replan, reason = engine.evaluate_and_replan(
            plan=plan,
            failed_step=s1,
            step_result=step_res,
            failure_reason="Rate limit exceeded",
        )

        self.assertTrue(did_replan)
        self.assertEqual(plan.plan_version, 2)
        self.assertEqual(plan.replan_count, 1)
        self.assertEqual(s1.tool, "duckduckgo_search")
        self.assertEqual(s1.status, StepStatus.PENDING)
        self.assertEqual(s1.retry_count, 0)
        self.assertIn("mos zaxira asbob", reason)
        self.assertEqual(len(plan.replan_history), 1)

    def test_replan_security_blocked_strictly_refused(self):
        """Xavfsizlik chegarasi buzilgan holatlarda (SECURITY_BLOCKED) replan mutlaqo qilinmaydi"""
        s1 = PlanStep(
            step_id="step_sec",
            order=1,
            intent="file_delete",
            tool="delete_system_file",
        )
        plan = AgentPlan(
            plan_id="p-sec",
            goal="Xavfli amal",
            steps=[s1],
        )

        step_res = StepResult(
            step_id="step_sec",
            tool="delete_system_file",
            success=False,
            error="SECURITY_BLOCKED: Tizim fayllarini o'chirish taqiqlangan",
        )

        did_replan, reason = self.engine.evaluate_and_replan(
            plan=plan,
            failed_step=s1,
            step_result=step_res,
            failure_reason="SECURITY_BLOCKED",
        )

        self.assertFalse(did_replan)
        self.assertEqual(plan.plan_version, 1)
        self.assertEqual(plan.replan_count, 0)
        self.assertIn("SECURITY_BLOCKED", reason)

    def test_replan_permission_denied_refused(self):
        """Foydalanuvchi ruxsati rad etilganda avtomatik replan qilinmaydi"""
        s1 = PlanStep(step_id="s1", order=1, intent="power", tool="shutdown")
        plan = AgentPlan(plan_id="p-perm", goal="O'chirish", steps=[s1])

        step_res = StepResult(
            step_id="s1",
            tool="shutdown",
            success=False,
            error="PERMISSION_DENIED: Foydalanuvchi amalni rad etdi",
        )

        did_replan, reason = self.engine.evaluate_and_replan(
            plan=plan,
            failed_step=s1,
            step_result=step_res,
            failure_reason="PERMISSION_DENIED",
        )

        self.assertFalse(did_replan)
        self.assertIn("ruxsat talab etilganligi sababli", reason)

    def test_replan_max_count_limit(self):
        """Replan limiti (MAX_REPLANS = 2) tugaganda reja to'xtatiladi"""
        s1 = PlanStep(step_id="s1", order=1, intent="calc", tool="calculator")
        plan = AgentPlan(plan_id="p-limit", goal="Limit testi", steps=[s1], replan_count=2, max_replans=2)

        step_res = StepResult(step_id="s1", tool="calculator", success=False, error="timeout")
        did_replan, reason = self.engine.evaluate_and_replan(
            plan=plan,
            failed_step=s1,
            step_result=step_res,
            failure_reason="timeout",
        )

        self.assertFalse(did_replan)
        self.assertIn("limiti tugadi", reason)

    def test_replan_opportunistic_pruning(self):
        """Muammo topilmaganda keraksiz tuzatish qadamlari olib tashlanadi (opportunistic pruning)"""
        s1 = PlanStep(step_id="s1", order=1, intent="check", tool="app_check", observed_result="status: no_issues_found")
        s2 = PlanStep(step_id="s2", order=2, intent="fix_app", tool="app_fix", dependencies=["s1"])

        plan = AgentPlan(
            plan_id="p-prune",
            goal="Tekshirish va tuzatish",
            steps=[s1, s2],
        )

        did_replan, reason = self.engine.evaluate_and_replan(
            plan=plan,
            failed_step=s1,
            failure_reason="inspection_completed",
        )

        self.assertTrue(did_replan)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].step_id, "s1")
        self.assertIn("ortiqcha 1 ta qadam olib tashlandi", reason)


if __name__ == "__main__":
    unittest.main()
