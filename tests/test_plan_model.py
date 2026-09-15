# ========== test_plan_model.py ==========
# Mikasa AI 7.x — Unit Tests for Planning Model 2.0 (PlanStep & AgentPlan)

import unittest
from core.intelligence.types import (
    RiskLevel,
    PlanStatus,
    StepStatus,
    VerificationStatus,
    FailureCategory,
    PlanStep,
    AgentPlan,
)


class TestPlanModel(unittest.TestCase):
    """Planning Model 2.0 ma'lumotlar modellari va metodlari testlari"""

    def test_plan_step_defaults_and_synchronization(self):
        """PlanStep tool va selected_tool o'rtasidagi sinxronizatsiya va birlamchi qiymatlar"""
        step = PlanStep(
            step_id="step_1",
            order=1,
            intent="search",
            tool="search",
        )
        self.assertEqual(step.step_id, "step_1")
        self.assertEqual(step.order, 1)
        self.assertEqual(step.tool, "search")
        self.assertEqual(step.selected_tool, "search")
        self.assertEqual(step.dependencies, [])
        self.assertEqual(step.required_capability, "search")
        self.assertEqual(step.status, StepStatus.PENDING)
        self.assertEqual(step.retry_policy, {})
        self.assertEqual(step.verification_policy, "oracle_or_heuristic")

    def test_plan_step_to_dict_and_from_dict(self):
        """PlanStep to'liq to_dict va from_dict serializatsiyasi"""
        step = PlanStep(
            step_id="step_2",
            order=2,
            intent="calculator",
            tool="calculator",
            parameters={"expression": "50 * 2"},
            expected_result="100",
            risk_level=RiskLevel.LOW,
            status=StepStatus.COMPLETED,
            dependencies=["step_1"],
            required_capability="calculation",
            observed_result="100",
            failure_reason="none",
        )
        d = step.to_dict()
        self.assertEqual(d["step_id"], "step_2")
        self.assertEqual(d["tool"], "calculator")
        self.assertEqual(d["selected_tool"], "calculator")
        self.assertEqual(d["dependencies"], ["step_1"])
        self.assertEqual(d["required_capability"], "calculation")
        self.assertEqual(d["observed_result"], "100")

        restored = PlanStep.from_dict(d)
        self.assertEqual(restored.step_id, step.step_id)
        self.assertEqual(restored.tool, step.tool)
        self.assertEqual(restored.dependencies, ["step_1"])
        self.assertEqual(restored.required_capability, "calculation")
        self.assertEqual(restored.observed_result, "100")
        self.assertEqual(restored.status, StepStatus.COMPLETED)

    def test_agent_plan_creation_and_helpers(self):
        """AgentPlan yordamchi funksiyalari (get_step, get_dependencies, get_ready_steps)"""
        s1 = PlanStep(step_id="s1", order=1, intent="search", tool="search")
        s2 = PlanStep(step_id="s2", order=2, intent="calc", tool="calculator", dependencies=["s1"])
        s3 = PlanStep(step_id="s3", order=3, intent="weather", tool="weather", dependencies=["s1"])

        plan = AgentPlan(
            plan_id="p-test",
            goal="Ko'p bosqichli reja",
            steps=[s1, s2, s3],
            dependencies={"s2": ["s1"], "s3": ["s1"]},
            execution_order=["s1", "s2", "s3"],
        )

        # get_step
        self.assertEqual(plan.get_step("s1"), s1)
        self.assertEqual(plan.get_step("s2"), s2)
        self.assertIsNone(plan.get_step("non_existent"))

        # get_dependencies
        self.assertEqual(plan.get_dependencies("s1"), [])
        self.assertEqual(plan.get_dependencies("s2"), ["s1"])

        # get_ready_steps: boshida faqat s1 tayyor
        ready = plan.get_ready_steps()
        self.assertEqual([s.step_id for s in ready], ["s1"])

        # s1 completed bo'lgach, s2 va s3 tayyor bo'ladi
        s1.status = StepStatus.COMPLETED
        ready_after = plan.get_ready_steps()
        ready_ids = [s.step_id for s in ready_after]
        self.assertIn("s2", ready_ids)
        self.assertIn("s3", ready_ids)

    def test_agent_plan_risk_calculation(self):
        """AgentPlan risk darajasini eng yuqori qadam asosida hisoblash"""
        s1 = PlanStep(step_id="s1", order=1, intent="search", tool="search", risk_level=RiskLevel.LOW)
        s2 = PlanStep(step_id="s2", order=2, intent="sys", tool="system_info", risk_level=RiskLevel.MEDIUM)
        plan = AgentPlan(plan_id="p-risk", goal="Risk testi", steps=[s1, s2])
        self.assertEqual(plan.calculate_plan_risk(), RiskLevel.MEDIUM)

        # High risk qadam qo'shilganda
        s3 = PlanStep(step_id="s3", order=3, intent="down", tool="shutdown", risk_level=RiskLevel.HIGH)
        plan.steps.append(s3)
        self.assertEqual(plan.calculate_plan_risk(), RiskLevel.HIGH)

    def test_agent_plan_versioning(self):
        """create_next_version yangi versiya (v1 -> v2) va tarixni qayd etadi"""
        s1 = PlanStep(step_id="s1", order=1, intent="search", tool="search")
        plan = AgentPlan(plan_id="p-ver", goal="Versiyalash testi", steps=[s1])
        self.assertEqual(plan.plan_version, 1)
        self.assertEqual(plan.replan_count, 0)
        self.assertEqual(len(plan.replan_history), 0)

        plan.create_next_version(reason="Primary tool timeout, switching to alternative", changed_steps=["s1"])
        self.assertEqual(plan.plan_version, 2)
        self.assertEqual(plan.replan_count, 1)
        self.assertEqual(len(plan.replan_history), 1)
        self.assertEqual(plan.replan_history[0]["version"], 2)
        self.assertIn("Primary tool timeout", plan.replan_history[0]["reason"])
        self.assertEqual(plan.replan_history[0]["changed_steps"], ["s1"])

    def test_agent_plan_serialization(self):
        """AgentPlan to'liq to_dict va from_dict serializatsiyasi"""
        s1 = PlanStep(step_id="s1", order=1, intent="calc", tool="calculator", parameters={"expression": "10+5"})
        plan = AgentPlan(
            plan_id="p-serial",
            goal="Serializatsiya testi",
            intent="calculator",
            desired_outcome="15",
            steps=[s1],
            assumptions=["Aniq ifoda"],
            constraints=["60 soniya limit"],
            execution_order=["s1"],
            required_capabilities=["calculator"],
            plan_version=2,
            replan_count=1,
            replan_history=[{"version": 2, "reason": "optimized", "timestamp": "now", "changed_steps": []}],
        )

        d = plan.to_dict()
        self.assertEqual(d["plan_id"], "p-serial")
        self.assertEqual(d["plan_version"], 2)
        self.assertEqual(d["desired_outcome"], "15")
        self.assertEqual(len(d["assumptions"]), 1)
        self.assertEqual(len(d["steps"]), 1)

        restored = AgentPlan.from_dict(d)
        self.assertEqual(restored.plan_id, "p-serial")
        self.assertEqual(restored.plan_version, 2)
        self.assertEqual(restored.replan_count, 1)
        self.assertEqual(len(restored.steps), 1)
        self.assertEqual(restored.steps[0].tool, "calculator")


if __name__ == "__main__":
    unittest.main()
