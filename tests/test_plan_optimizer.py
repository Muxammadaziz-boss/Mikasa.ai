# ========== test_plan_optimizer.py ==========
# Mikasa AI 7.x — Unit Tests for Plan Optimizer 2.0 (PlanOptimizer)

import unittest
from unittest.mock import MagicMock

from core.intelligence.types import (
    StepStatus,
    PlanStep,
    AgentPlan,
)
from core.intelligence.planner import PlanOptimizer


class TestPlanOptimizer(unittest.TestCase):
    """PlanOptimizer sinovi: dublikatlarni yo'qotish va kontekstdan qayta foydalanish"""

    def setUp(self):
        self.optimizer = PlanOptimizer()

    def test_duplicate_step_removal(self):
        """Bir xil parametrli takroriy qadamlar optimallashtiriladi va qisqartiriladi"""
        s1 = PlanStep(step_id="s1", order=1, intent="search", tool="search", parameters={"query": "Mikasa AI"})
        s2 = PlanStep(step_id="s2", order=2, intent="calc", tool="calculator", parameters={"expression": "10 * 10"})
        s3 = PlanStep(step_id="s3", order=3, intent="search", tool="search", parameters={"query": "Mikasa AI"}, dependencies=["s2"])

        plan = AgentPlan(
            plan_id="p-dup",
            goal="Dublikatli reja",
            steps=[s1, s2, s3],
        )

        opt_plan, notes = PlanOptimizer.optimize(plan)
        # s3 (s1 ning dublikati) o'chirilishi kerak
        self.assertEqual(len(opt_plan.steps), 2)
        step_tools = [s.tool for s in opt_plan.steps]
        self.assertEqual(step_tools, ["search", "calculator"])
        self.assertTrue(any("Dublikat qadam" in n for n in notes))
        # Qadam tartiblari 1 va 2 ga to'g'rilangan bo'lishi shart
        self.assertEqual(opt_plan.steps[0].order, 1)
        self.assertEqual(opt_plan.steps[1].order, 2)

    def test_context_memory_reuse(self):
        """TaskContext dagi mavjud natija qayta ishlatilib, ortiqcha chaqiruv olib tashlanadi"""
        s1 = PlanStep(step_id="s1", order=1, intent="info", tool="system_info", parameters={})
        s2 = PlanStep(step_id="s2", order=2, intent="search", tool="search", parameters={"query": "CPU yuklamasi"})

        plan = AgentPlan(
            plan_id="p-ctx",
            goal="Kontekstli reja",
            steps=[s1, s2],
        )

        # Mock TaskContextManager
        mock_task_mgr = MagicMock()
        mock_task = MagicMock()
        mock_act = MagicMock()
        mock_act.action = "system_info"
        mock_act.result = "CPU: 12%, RAM: 45%"
        mock_task.action_history = [mock_act]
        mock_task_mgr.get_active_task.return_value = mock_task

        optimizer = PlanOptimizer(task_context_manager=mock_task_mgr)
        opt_plan = optimizer.optimize(plan)

        self.assertEqual(opt_plan.steps[0].tool, "system_info")
        self.assertEqual(opt_plan.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(opt_plan.steps[0].observed_result, "CPU: 12%, RAM: 45%")
        self.assertTrue(opt_plan.metadata.get("optimized"))
        self.assertTrue(any("mavjud kontekstdan natija qayta ishlatildi" in n for n in opt_plan.metadata.get("optimization_notes", [])))

    def test_empty_plan_handling(self):
        """Bo'sh reja xatosiz qaytariladi"""
        plan = AgentPlan(plan_id="p-empty", goal="Bo'sh", steps=[])
        opt_plan = self.optimizer.optimize(plan)
        self.assertEqual(len(opt_plan.steps), 0)


if __name__ == "__main__":
    unittest.main()
