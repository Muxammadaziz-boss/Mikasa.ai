# ========== test_goal_decomposition.py ==========
# Mikasa AI 7.x — Unit Tests for Goal Decomposition 2.0 (GoalDecomposer)

import unittest
from unittest.mock import MagicMock

from core.intelligence.types import (
    RiskLevel,
    StepStatus,
    AIRequest,
    AIResponse,
)
from core.intelligence.planner import GoalDecomposer


class TestGoalDecomposition(unittest.TestCase):
    """GoalDecomposer sinovi: oddiy vs murakkab maqsadlar va dekompozitsiya qoidalari"""

    def setUp(self):
        self.decomposer = GoalDecomposer()

    def test_simple_goal_detection_math(self):
        """Matematik hisob-kitoblar oddiy (simple) maqsad deb aniqlanadi"""
        self.assertTrue(self.decomposer.is_simple_goal("25 * 4"))
        self.assertTrue(self.decomposer.is_simple_goal("100 / 5 ni hisobla"))
        self.assertTrue(self.decomposer.is_simple_goal("hisobla: 12 + 88"))
        self.assertTrue(self.decomposer.is_simple_goal("2 + 2"))

    def test_simple_goal_detection_time(self):
        """Vaqt va sana so'rovlari oddiy maqsad deb aniqlanadi"""
        self.assertTrue(self.decomposer.is_simple_goal("soat necha"))
        self.assertTrue(self.decomposer.is_simple_goal("hozirgi vaqt"))
        self.assertTrue(self.decomposer.is_simple_goal("bugun qaysi kun"))

    def test_simple_goal_detection_single_app(self):
        """Yagona ilovani ochish oddiy maqsad deb aniqlanadi"""
        self.assertTrue(self.decomposer.is_simple_goal("youtube ni och"))
        self.assertTrue(self.decomposer.is_simple_goal("chrome"))
        self.assertTrue(self.decomposer.is_simple_goal("telegramni och"))

    def test_complex_goal_detection(self):
        """Bog'lovchilar ('va', 'keyin', 'agar') bo'lgan maqsadlar murakkab deb aniqlanadi"""
        self.assertFalse(self.decomposer.is_simple_goal("ob-havoni ko'r va hisobla"))
        self.assertFalse(self.decomposer.is_simple_goal("brauzerni och keyin youtube ga kir"))
        self.assertFalse(self.decomposer.is_simple_goal("tizimni tekshir hamda hisobot ber"))

    def test_decompose_simple_goal_zero_overplanning(self):
        """Oddiy maqsad uchun aynan 1 qadamli minimal reja tuziladi (ortiqcha qadamsiz)"""
        plan = self.decomposer.decompose("25 * 4 ni hisobla")
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].tool, "calculator")
        self.assertEqual(plan.execution_order, [plan.steps[0].step_id])
        self.assertEqual(plan.dependencies, {})
        self.assertEqual(plan.metadata.get("complexity"), "simple")

    def test_decompose_conjunction_va(self):
        """'va' bog'lovchisi bilan 2 qadamli mustaqil yoki ketma-ket reja tuziladi"""
        plan = self.decomposer.decompose("toshkent ob-havosini bil va valyuta kursini ko'r")
        self.assertEqual(len(plan.steps), 2)
        tools = [s.tool for s in plan.steps]
        self.assertIn("weather", tools)
        self.assertIn("currency", tools)
        self.assertEqual(len(plan.execution_order), 2)

    def test_decompose_conjunction_keyin(self):
        """'keyin' bog'lovchisi ketma-ket qaramlik (dependency) hosil qiladi"""
        plan = self.decomposer.decompose("youtube ni och keyin chrome ni och")
        self.assertEqual(len(plan.steps), 2)
        s1, s2 = plan.steps[0], plan.steps[1]
        self.assertEqual(s1.tool, "open_youtube")
        self.assertEqual(s2.tool, "open_chrome")
        # 2-qadam 1-qadamga bog'langan
        self.assertIn(s1.step_id, plan.dependencies.get(s2.step_id, []))
        self.assertEqual(plan.execution_order, [s1.step_id, s2.step_id])

    def test_decompose_diagnostics_pipeline(self):
        """Diagnostika va tekshiruv shablonlari tahlil qilinadi"""
        plan = self.decomposer.decompose("tizim holatini tekshir va tavsiya ber")
        self.assertGreaterEqual(len(plan.steps), 1)
        tools = [s.tool for s in plan.steps]
        self.assertTrue("system_info" in tools or "app_check" in tools or "search" in tools)

    def test_decompose_llm_fallback(self):
        """Noma'lum yoki murakkab iboralar uchun LLM orqali JSON reja tuzish"""
        mock_provider = MagicMock()
        mock_provider.generate_with_fallback.return_value = AIResponse(
            provider="gemini",
            model="gemini-2.5-flash",
            content='''{
              "goal": "Murakkab loyiha yarat",
              "steps": [
                {"intent": "open_code", "tool": "open_code", "parameters": {}, "expected_result": "VS Code ochildi"},
                {"intent": "search", "tool": "search", "parameters": {"query": "python fastapi template"}, "expected_result": "Qidiruv natijasi"}
              ]
            }'''
        )
        decomposer = GoalDecomposer(provider_manager=mock_provider)
        req = AIRequest(message="Murakkab loyiha yarat")
        plan = decomposer.decompose("Murakkab loyiha yarat", request=req)
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].tool, "open_code")
        self.assertEqual(plan.steps[1].tool, "search")
        self.assertEqual(plan.metadata.get("planner"), "llm_structured")


if __name__ == "__main__":
    unittest.main()
