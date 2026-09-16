# ========== test_intelligence_core.py ==========
# Mikasa AI 7.x — Phase 28 Intelligence Core Comprehensive Unit & Integration Tests
# Verifies Provider Abstraction, Context, Intent, Decision, Permission, Orchestrator and Compatibility

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.intelligence.types import (
    RiskLevel,
    IntentCategory,
    DecisionType,
    AIRequest,
    AIResponse,
    Intent,
    Decision,
    IntelligenceResponse,
)
from core.intelligence.provider import AIProvider, ProviderManager
from core.intelligence.gemini_provider import GeminiProvider
from core.intelligence.openrouter_provider import OpenRouterProvider
from core.intelligence.context import ContextEngine
from core.intelligence.intent import IntentEngine
from core.intelligence.permission import PermissionEngine
from core.intelligence.decision import DecisionEngine
from core.intelligence.orchestrator import IntelligenceOrchestrator
from core.intelligence.adapter import CompatibilityAdapter


class MockProvider(AIProvider):
    """Testlar uchun soxta (mock) provayder"""
    def __init__(self, name="mock", available=True, return_response=None, raise_exc=False):
        self._name = name
        self._available = available
        self._return_response = return_response
        self._raise_exc = raise_exc

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._available

    def generate(self, request: AIRequest) -> AIResponse:
        if self._raise_exc:
            raise RuntimeError(f"Mock failure in {self._name}")
        return self._return_response or AIResponse(
            provider=self._name,
            model="mock-v1",
            type="answer",
            content="Mock javob",
            success=True
        )


class TestAIProvider(unittest.TestCase):
    """1. Provider Abstraction, Normalization and Fallback Tests"""

    def test_gemini_normalization_answer(self):
        prov = GeminiProvider(api_key="test_key")
        normalized = prov._normalize_response(
            '{"type": "answer", "response": "Python - dasturlash tili."}',
            model="gemini-2.5-flash",
            usage={},
            grounding={}
        )
        self.assertEqual(normalized.type, "answer")
        self.assertEqual(normalized.content, "Python - dasturlash tili.")
        self.assertTrue(normalized.success)
        self.assertEqual(normalized.provider, "gemini")

    def test_gemini_normalization_command(self):
        prov = GeminiProvider(api_key="test_key")
        normalized = prov._normalize_response(
            '{"type": "command", "intent": "open_youtube", "params": {}, "response": "YouTube ochilmoqda"}',
            model="gemini-2.5-flash",
            usage={},
            grounding={}
        )
        self.assertEqual(normalized.type, "command")
        self.assertEqual(normalized.intent, "open_youtube")
        self.assertEqual(normalized.content, "YouTube ochilmoqda")

    def test_gemini_normalization_clarification(self):
        prov = GeminiProvider(api_key="test_key")
        normalized = prov._normalize_response(
            '{"type": "clarification", "question": "Qaysi dasturni ochish kerak?"}',
            model="gemini-2.5-flash",
            usage={},
            grounding={}
        )
        self.assertEqual(normalized.type, "clarification")
        self.assertEqual(normalized.content, "Qaysi dasturni ochish kerak?")

    def test_gemini_normalization_confirmation(self):
        prov = GeminiProvider(api_key="test_key")
        normalized = prov._normalize_response(
            '{"type": "confirmation", "intent": "shutdown", "question": "Kompyuterni o‘chirishni tasdiqlaysizmi?"}',
            model="gemini-2.5-flash",
            usage={},
            grounding={}
        )
        self.assertEqual(normalized.type, "confirmation")
        self.assertEqual(normalized.intent, "shutdown")
        self.assertEqual(normalized.content, "Kompyuterni o‘chirishni tasdiqlaysizmi?")

    def test_openrouter_normalization(self):
        prov = OpenRouterProvider(api_key="test_key")
        normalized = prov._normalize_response(
            '{"type": "command", "intent": "open_telegram", "response": "Telegram ochildi"}',
            model="openrouter/test",
            usage={}
        )
        self.assertEqual(normalized.type, "command")
        self.assertEqual(normalized.intent, "open_telegram")
        self.assertEqual(normalized.content, "Telegram ochildi")
        self.assertEqual(normalized.provider, "openrouter")

    def test_provider_fallback_success(self):
        # Gemini xato beradi, OpenRouter muvaffaqiyatli ishlaydi
        p1 = MockProvider(name="gemini", available=True, raise_exc=True)
        p2 = MockProvider(name="openrouter", available=True, return_response=AIResponse(
            provider="openrouter",
            model="or-model",
            type="answer",
            content="OpenRouter orqali olingan javob",
            success=True
        ))

        manager = ProviderManager([p1, p2])
        req = AIRequest(message="Salom")
        res = manager.generate_with_fallback(req)

        self.assertTrue(res.success)
        self.assertEqual(res.provider, "openrouter")
        self.assertEqual(res.content, "OpenRouter orqali olingan javob")

    def test_provider_all_unavailable(self):
        # Ikkala provayder ham nosoz
        p1 = MockProvider(name="gemini", available=True, raise_exc=True)
        p2 = MockProvider(name="openrouter", available=True, raise_exc=True)

        manager = ProviderManager([p1, p2])
        req = AIRequest(message="Salom")
        res = manager.generate_with_fallback(req)

        self.assertFalse(res.success)
        self.assertEqual(res.type, "error")
        self.assertEqual(res.error_code, "AI_PROVIDER_UNAVAILABLE")


class TestContextEngine(unittest.TestCase):
    """2. Context Engine Selective & Bounded Assembly Tests"""

    def setUp(self):
        self.mock_memory = MagicMock()
        self.mock_memory.get_conversations.return_value = [
            {"user": "Salom", "agent": "Salom! Qanday yordam bera olaman?"},
            {"user": "Ob-havo qanday?", "agent": "Havo quyoshli."}
        ]
        self.mock_memory.get_knowledge.return_value = {
            "sevimli_rang": "ko'k",
            "kasb": "dasturchi"
        }
        self.mock_memory.get_profile.return_value = {"ism": "Aziz"}
        self.engine = ContextEngine(memory=self.mock_memory)

    def test_context_assembly_bounded_history(self):
        req = self.engine.assemble("Yana nima qila olasan?", user_name="Aziz", max_history_turns=2)
        self.assertEqual(len(req.conversation), 4)  # 2 juft: 2 user, 2 assistant
        self.assertIn("prompt", req.system_context)
        self.assertIn("Aziz", req.system_context["prompt"])
        self.assertIn("sevimli_rang", req.memory["knowledge"])

    def test_context_selective_specs_inclusion(self):
        # Specs faqat zarur bo'lganda qo'shiladi
        self.assertFalse(self.engine.should_include_system_specs("Musiqa qo'y"))
        self.assertTrue(self.engine.should_include_system_specs("Menda telegram bormi?"))
        self.assertTrue(self.engine.should_include_system_specs("Kompyuter parametrlari"))

    def test_context_resilience_on_memory_failure(self):
        bad_memory = MagicMock()
        bad_memory.get_conversations.side_effect = RuntimeError("Disk error")
        bad_memory.get_knowledge.side_effect = RuntimeError("Knowledge error")
        engine = ContextEngine(memory=bad_memory)

        # Xatolik yuz berganda ham assembler qulamasligi kerak
        req = engine.assemble("Test xabar", user_name="User")
        self.assertEqual(req.message, "Test xabar")
        self.assertIn("prompt", req.system_context)


class TestIntentEngine(unittest.TestCase):
    """3. Intent Engine Tests"""

    def setUp(self):
        self.engine = IntentEngine()

    def test_resolve_conversation_intent(self):
        resp = AIResponse(provider="gemini", model="gemini-2.5-flash", type="answer", content="Salom do'stim!")
        intent = self.engine.resolve_intent_from_response(resp)
        self.assertEqual(intent.category, IntentCategory.CONVERSATION)
        self.assertEqual(intent.name, "conversation")

    def test_resolve_command_intent(self):
        resp = AIResponse(provider="gemini", model="gemini-2.5-flash", type="command", intent="open_youtube", params={"query": "music"})
        intent = self.engine.resolve_intent_from_response(resp)
        self.assertEqual(intent.category, IntentCategory.COMMAND)
        self.assertEqual(intent.name, "open_youtube")
        self.assertEqual(intent.params.get("query"), "music")

    def test_resolve_clarification_intent(self):
        resp = AIResponse(provider="gemini", model="gemini-2.5-flash", type="clarification", content="Qaysi brauzerni nazarda tutdingiz?")
        intent = self.engine.resolve_intent_from_response(resp)
        self.assertEqual(intent.category, IntentCategory.CLARIFICATION)
        self.assertTrue(intent.requires_context)

    def test_resolve_confirmation_intent(self):
        resp = AIResponse(provider="gemini", model="gemini-2.5-flash", type="confirmation", intent="shutdown", content="Kompyuterni o'chirishni tasdiqlaysizmi?")
        intent = self.engine.resolve_intent_from_response(resp)
        self.assertEqual(intent.category, IntentCategory.CONFIRMATION)


class TestPermissionEngine(unittest.TestCase):
    """4. Permission & Risk Model Tests"""

    def setUp(self):
        self.perm = PermissionEngine()

    def test_low_risk_actions(self):
        risk, req_confirm, prompt = self.perm.evaluate("open_youtube")
        self.assertEqual(risk, RiskLevel.LOW)
        self.assertFalse(req_confirm)

        risk2, req_confirm2, _ = self.perm.evaluate("weather")
        self.assertEqual(risk2, RiskLevel.LOW)
        self.assertFalse(req_confirm2)

    def test_medium_risk_actions(self):
        risk, req_confirm, _ = self.perm.evaluate("close_window")
        self.assertEqual(risk, RiskLevel.MEDIUM)
        self.assertFalse(req_confirm)

    def test_high_risk_actions(self):
        risk, req_confirm, prompt = self.perm.evaluate("shutdown")
        self.assertEqual(risk, RiskLevel.HIGH)
        self.assertTrue(req_confirm)
        self.assertIn("o'chirishni tasdiqlaysizmi", prompt)

        risk2, req_confirm2, prompt2 = self.perm.evaluate("restart")
        self.assertEqual(risk2, RiskLevel.HIGH)
        self.assertTrue(req_confirm2)

    def test_custom_risk_override(self):
        self.perm.register_risk_level("custom_dangerous_op", RiskLevel.HIGH, "Ushbu xavfli amalni tasdiqlaysizmi?")
        risk, req_confirm, prompt = self.perm.evaluate("custom_dangerous_op")
        self.assertEqual(risk, RiskLevel.HIGH)
        self.assertTrue(req_confirm)
        self.assertEqual(prompt, "Ushbu xavfli amalni tasdiqlaysizmi?")


class TestDecisionEngine(unittest.TestCase):
    """5. Decision Engine Tests"""

    def setUp(self):
        self.mock_registry = MagicMock()
        self.mock_registry.get.side_effect = lambda name: MagicMock() if name == "calculator" else None
        self.decision_engine = DecisionEngine(tool_registry=self.mock_registry)

    def test_decide_answer(self):
        intent = Intent(name="conversation", category=IntentCategory.CONVERSATION)
        resp = AIResponse(provider="gemini", model="gemini-2.5-flash", type="answer", content="Salom!")
        dec = self.decision_engine.decide(intent, resp)
        self.assertEqual(dec.type, DecisionType.ANSWER)
        self.assertEqual(dec.content, "Salom!")

    def test_decide_registered_tool(self):
        intent = Intent(name="calculator", category=IntentCategory.COMMAND, params={"expression": "12 * 12"})
        resp = AIResponse(provider="gemini", model="gemini-2.5-flash", type="command", intent="calculator", params={"expression": "12 * 12"})
        dec = self.decision_engine.decide(intent, resp)
        self.assertEqual(dec.type, DecisionType.TOOL)
        self.assertEqual(dec.tool_name, "calculator")

    def test_decide_high_risk_confirmation(self):
        intent = Intent(name="shutdown", category=IntentCategory.COMMAND)
        resp = AIResponse(provider="gemini", model="gemini-2.5-flash", type="command", intent="shutdown")
        dec = self.decision_engine.decide(intent, resp)
        self.assertEqual(dec.type, DecisionType.CONFIRMATION)
        self.assertTrue(dec.requires_confirmation)
        self.assertIn("o'chirishni tasdiqlaysizmi", dec.content)


class TestIntelligenceOrchestrator(unittest.TestCase):
    """6. Intelligence Orchestrator Full Pipeline Tests"""

    def test_orchestrator_answer_path(self):
        provider = MockProvider(return_response=AIResponse(
            provider="gemini",
            model="gemini-2.5-flash",
            type="answer",
            content="Antarktida - eng sovuq qit'a."
        ))
        orch = IntelligenceOrchestrator(provider_manager=ProviderManager([provider]))
        result = orch.handle("Antarktida haqida ayt", user_name="Aziz")

        self.assertEqual(result.type, "answer")
        self.assertEqual(result.content, "Antarktida - eng sovuq qit'a.")
        self.assertTrue(result.verified)

    def test_orchestrator_tool_success_verification(self):
        # Muvaffaqiyatli asbob ijrosi va tasdiqlangan javob
        mock_registry = MagicMock()
        mock_tool = MagicMock()
        mock_tool.call.return_value = {"success": True, "result": {"message": "15 * 10 = 150"}}
        mock_registry.get.return_value = mock_tool
        mock_registry.call.return_value = {"success": True, "result": {"message": "15 * 10 = 150"}}

        provider = MockProvider(return_response=AIResponse(
            provider="gemini",
            model="gemini-2.5-flash",
            type="command",
            intent="calculator",
            params={"expression": "15 * 10"},
            content="Hisoblanmoqda"
        ))

        orch = IntelligenceOrchestrator(
            provider_manager=ProviderManager([provider]),
            tool_registry=mock_registry
        )
        result = orch.handle("15 ni 10 ga ko'paytir")

        self.assertEqual(result.type, "tool")
        self.assertEqual(result.tool_executed, "calculator")
        self.assertEqual(result.content, "15 * 10 = 150")
        self.assertTrue(result.verified)

    def test_orchestrator_tool_failure_no_fake_success(self):
        # Agar tool xato bersa, soxta 'muvaffaqiyat' javobi berilmasligi kerak
        mock_registry = MagicMock()
        mock_registry.get.return_value = MagicMock()
        mock_registry.call.return_value = {"success": False, "error": "Bo'lishda nolga bo'lish mumkin emas"}

        provider = MockProvider(return_response=AIResponse(
            provider="gemini",
            model="gemini-2.5-flash",
            type="command",
            intent="calculator",
            params={"expression": "10 / 0"},
            content="Hisoblandi"
        ))

        orch = IntelligenceOrchestrator(
            provider_manager=ProviderManager([provider]),
            tool_registry=mock_registry
        )
        result = orch.handle("10 ni 0 ga bo'l")

        self.assertEqual(result.type, "error")
        self.assertFalse(result.verified)
        self.assertIn("nolga bo'lish mumkin emas", result.content)

    def test_orchestrator_confirmation_path(self):
        # Tasdiqlash talab etilishi
        provider = MockProvider(return_response=AIResponse(
            provider="gemini",
            model="gemini-2.5-flash",
            type="command",
            intent="shutdown"
        ))

        orch = IntelligenceOrchestrator(provider_manager=ProviderManager([provider]))
        result = orch.handle("Kompyuterni o'chir")

        self.assertEqual(result.type, "confirmation")
        self.assertEqual(result.intent, "shutdown")
        self.assertIn("o'chirishni tasdiqlaysizmi", result.content)

        # Agar foydalanuvchi tasdiqlagan bo'lsa -> command ga o'tishi kerak
        confirmed_result = orch.handle("Kompyuterni o'chir", confirmed_action="shutdown")
        self.assertEqual(confirmed_result.type, "command")


class TestCompatibilityAdapter(unittest.TestCase):
    """7. Compatibility Adapter Tests"""

    def test_to_frontend_response(self):
        resp = IntelligenceResponse(
            type="command",
            content="YouTube ochilmoqda",
            intent="open_youtube",
            params={"target": "trending"},
            verified=True,
            provider="gemini",
            model="gemini-2.5-flash"
        )
        fe_dict = CompatibilityAdapter.to_frontend_response(resp, user_name="Aziz", mode="ask")
        self.assertTrue(fe_dict["ok"])
        self.assertEqual(fe_dict["response"], "YouTube ochilmoqda")
        self.assertEqual(fe_dict["intent"], "open_youtube")
        self.assertEqual(fe_dict["user"], "Aziz")
        self.assertIn("timestamp", fe_dict)

    def test_to_legacy_ai_engine_dict(self):
        resp = IntelligenceResponse(
            type="command",
            content="YouTube ochilmoqda",
            intent="open_youtube",
            params={"target": "music"}
        )
        legacy = CompatibilityAdapter.to_legacy_ai_engine_dict(resp)
        self.assertEqual(legacy["type"], "command")
        self.assertEqual(legacy["intent"], "open_youtube")
        self.assertEqual(legacy["response"], "YouTube ochilmoqda")


if __name__ == "__main__":
    unittest.main()
