# ========== test_dependency_graph.py ==========
# Mikasa AI 7.x — Unit Tests for Dependency Graph & Validation (DependencyGraph & PlanValidator)

import unittest
from core.intelligence.types import PlanStep, AgentPlan
from core.intelligence.planner import DependencyGraph, PlanValidator


class TestDependencyGraph(unittest.TestCase):
    """DependencyGraph tahlili, tsikl aniqlash va topologik saralash testlari"""

    def setUp(self):
        self.graph = DependencyGraph()
        self.validator = PlanValidator()

    def test_build_graph_from_steps(self):
        """PlanStep ro'yxatidan to'g'ri bog'liqlik xaritasi tuziladi"""
        s1 = PlanStep(step_id="step_1", order=1, intent="search", tool="search")
        s2 = PlanStep(step_id="step_2", order=2, intent="calc", tool="calculator", dependencies=["step_1"])
        s3 = PlanStep(step_id="step_3", order=3, intent="weather", tool="weather", dependencies=["step_1", "step_2"])

        dep_map = self.graph.build_graph([s1, s2, s3])
        self.assertEqual(dep_map["step_1"], [])
        self.assertEqual(dep_map["step_2"], ["step_1"])
        self.assertEqual(dep_map["step_3"], ["step_1", "step_2"])

    def test_validate_dependencies_exist_success(self):
        """Barcha bog'liqliklar mavjud bo'lganda muvaffaqiyatli tekshiriladi"""
        s1 = PlanStep(step_id="s1", order=1, intent="a", tool="search")
        s2 = PlanStep(step_id="s2", order=2, intent="b", tool="calculator", dependencies=["s1"])
        is_valid, err = self.graph.validate_dependencies_exist([s1, s2], {"s2": ["s1"], "s1": []})
        self.assertTrue(is_valid)
        self.assertIsNone(err)

    def test_validate_dependencies_missing_detected(self):
        """Mavjud bo'lmagan qadamga bog'liqlik bo'lsa PLAN_MISSING_DEPENDENCY xatosi beriladi"""
        s1 = PlanStep(step_id="s1", order=1, intent="a", tool="search")
        s2 = PlanStep(step_id="s2", order=2, intent="b", tool="calculator", dependencies=["s_ghost"])

        is_valid, err = self.graph.validate_dependencies_exist([s1, s2], {"s2": ["s_ghost"], "s1": []})
        self.assertFalse(is_valid)
        self.assertIn("s_ghost", err)

        # PlanValidator tekshiruvi
        plan = AgentPlan(
            plan_id="p-missing",
            goal="Yetishmayotgan bog'liqlik",
            steps=[s1, s2],
            dependencies={"s2": ["s_ghost"]},
        )
        val_ok, val_err = self.validator.validate(plan)
        self.assertFalse(val_ok)
        self.assertIn("PLAN_MISSING_DEPENDENCY", val_err)

    def test_detect_cycles_direct(self):
        """2 qadamli bevosita tsikl (s1 -> s2 -> s1) aniqlanadi"""
        s1 = PlanStep(step_id="s1", order=1, intent="a", tool="search", dependencies=["s2"])
        s2 = PlanStep(step_id="s2", order=2, intent="b", tool="calculator", dependencies=["s1"])

        cycle = self.graph.detect_cycles([s1, s2], {"s1": ["s2"], "s2": ["s1"]})
        self.assertTrue(len(cycle) > 0)
        self.assertIn("s1", cycle)
        self.assertIn("s2", cycle)

        # PlanValidator tekshiruvi
        plan = AgentPlan(
            plan_id="p-cycle",
            goal="Tsiklik reja",
            steps=[s1, s2],
            dependencies={"s1": ["s2"], "s2": ["s1"]},
        )
        val_ok, val_err = self.validator.validate(plan)
        self.assertFalse(val_ok)
        self.assertIn("PLAN_CIRCULAR_DEPENDENCY", val_err)

    def test_detect_cycles_multi_node(self):
        """3 qadamli bilvosita tsikl (s1 -> s2 -> s3 -> s1) aniqlanadi"""
        s1 = PlanStep(step_id="s1", order=1, intent="a", tool="search", dependencies=["s3"])
        s2 = PlanStep(step_id="s2", order=2, intent="b", tool="calculator", dependencies=["s1"])
        s3 = PlanStep(step_id="s3", order=3, intent="c", tool="weather", dependencies=["s2"])

        cycle = self.graph.detect_cycles([s1, s2, s3], {"s1": ["s3"], "s2": ["s1"], "s3": ["s2"]})
        self.assertTrue(len(cycle) > 0)

    def test_detect_cycles_acyclic(self):
        """Asiklik to'g'ri DAG uchun bo'sh ro'yxat qaytariladi"""
        s1 = PlanStep(step_id="s1", order=1, intent="a", tool="search")
        s2 = PlanStep(step_id="s2", order=2, intent="b", tool="calculator", dependencies=["s1"])
        s3 = PlanStep(step_id="s3", order=3, intent="c", tool="weather", dependencies=["s2"])

        cycle = self.graph.detect_cycles([s1, s2, s3], {"s1": [], "s2": ["s1"], "s3": ["s2"]})
        self.assertEqual(cycle, [])

    def test_topological_sort_execution_order(self):
        """Kahn algoritmi orqali ijro tartibi hisoblanadi: avval bog'liqsiz, keyin bog'liqlar"""
        # s3 depends on s1, s2 depends on s1, s4 depends on s2 and s3
        s1 = PlanStep(step_id="s1", order=1, intent="a", tool="search")
        s2 = PlanStep(step_id="s2", order=2, intent="b", tool="calculator", dependencies=["s1"])
        s3 = PlanStep(step_id="s3", order=3, intent="c", tool="weather", dependencies=["s1"])
        s4 = PlanStep(step_id="s4", order=4, intent="d", tool="currency", dependencies=["s2", "s3"])

        deps = {
            "s1": [],
            "s2": ["s1"],
            "s3": ["s1"],
            "s4": ["s2", "s3"],
        }
        order = self.graph.compute_execution_order([s1, s2, s3, s4], deps)
        self.assertEqual(len(order), 4)
        # s1 har doim 1-bo'lishi shart
        self.assertEqual(order[0], "s1")
        # s4 har doim s2 va s3 dan keyin bo'lishi shart
        self.assertGreater(order.index("s4"), order.index("s2"))
        self.assertGreater(order.index("s4"), order.index("s3"))


if __name__ == "__main__":
    unittest.main()
