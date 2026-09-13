# ========== orchestrator.py ==========
# Mikasa AI 7.x — Intelligence Orchestrator
# Central Cognitive Controller: Pipeline Coordinator from Context to Verified Response

import time
import logging
from typing import Optional, Dict, Any

from core.intelligence.types import (
    AIRequest,
    AIResponse,
    Intent,
    Decision,
    DecisionType,
    RiskLevel,
    IntelligenceResponse,
)
from core.intelligence.provider import ProviderManager
from core.intelligence.gemini_provider import GeminiProvider
from core.intelligence.openrouter_provider import OpenRouterProvider
from core.intelligence.context import ContextEngine
from core.intelligence.intent import IntentEngine
from core.intelligence.decision import DecisionEngine
from core.intelligence.permission import PermissionEngine

logger = logging.getLogger(__name__)


class IntelligenceOrchestrator:
    """
    Mikasa AI Intelligence Core orkestratori.
    Barcha intellektual bosqichlarni (Kontekst -> Niyat -> Fikrlash -> Qaror -> Vosita -> Tasdiqlash -> Javob)
    birlashtiruvchi markaziy boshqaruvchi.
    """

    def __init__(
        self,
        provider_manager: Optional[ProviderManager] = None,
        context_engine: Optional[ContextEngine] = None,
        intent_engine: Optional[IntentEngine] = None,
        decision_engine: Optional[DecisionEngine] = None,
        permission_engine: Optional[PermissionEngine] = None,
        tool_registry=None,
        command_dispatcher=None,
    ):
        self.permission_engine = permission_engine or PermissionEngine()
        self.intent_engine = intent_engine or IntentEngine()
        self.tool_registry = tool_registry
        self.command_dispatcher = command_dispatcher

        # Provayder menejeri
        if provider_manager is None:
            gemini = GeminiProvider()
            openrouter = OpenRouterProvider()
            self.provider_manager = ProviderManager([gemini, openrouter])
        else:
            self.provider_manager = provider_manager

        # Kontekst dvigateli
        self.context_engine = context_engine or ContextEngine(tool_registry=tool_registry)

        # Qaror dvigateli
        self.decision_engine = decision_engine or DecisionEngine(
            permission_engine=self.permission_engine,
            tool_registry=self.tool_registry
        )

    def handle(
        self,
        message: str,
        user_name: str = "Foydalanuvchi",
        confirmed_action: Optional[str] = None
    ) -> IntelligenceResponse:
        """
        Xabarni to'liq intellektual quvur (pipeline) orqali qayta ishlash:
        1. Qabul qilish
        2. Kontekstni yig'ish (ContextEngine)
        3. AI provayderini chaqirish (ProviderManager)
        4. Niyatni aniqlash (IntentEngine)
        5. Ruxsat va xavfni baholash (PermissionEngine)
        6. Qaror qabul qilish (DecisionEngine)
        7. Tasdiqlash talab etilsa to'xtatish
        8. Asbobni bajarish (Tool execution)
        9. Natijani tekshirish (Verification)
        10. Yakuniy javobni qaytarish (IntelligenceResponse)
        """
        start_time = time.time()
        clean_message = (message or "").strip()

        if not clean_message:
            return IntelligenceResponse(
                type="answer",
                content="Bo'sh xabar kiritildi.",
                verified=True,
                metadata={"latency_ms": 0}
            )

        logger.info(f"[IntelligenceOrchestrator] Xabar qabul qilindi: '{clean_message[:80]}'")

        # 1. Tezkor Mahalliy Buyruqlar tekshiruvi (agar dispatcher mavjud bo'lsa)
        if self.command_dispatcher:
            try:
                handled, local_msg = self.command_dispatcher.dispatch_local(clean_message)
                if handled and local_msg:
                    latency = round((time.time() - start_time) * 1000, 2)
                    logger.info(f"[IntelligenceOrchestrator] Tezkor mahalliy dispatcher bajardi ({latency}ms)")
                    return IntelligenceResponse(
                        type="command",
                        content=local_msg,
                        intent="local_dispatch",
                        verified=True,
                        provider="local",
                        model="command_dispatcher",
                        metadata={"latency_ms": latency}
                    )
            except Exception as e:
                logger.warning(f"Mahalliy dispatcherda xatolik: {e}")

        # 2. Kontekst yig'ish (Context Assembly)
        request = self.context_engine.assemble(
            message=clean_message,
            user_name=user_name,
            include_tools=(self.tool_registry is not None)
        )

        # 3. AI Provayderidan javob olish (Fallback bilan)
        ai_response: AIResponse = self.provider_manager.generate_with_fallback(request)

        # 4. Niyatni aniqlash (Intent Resolution)
        intent: Intent = self.intent_engine.resolve_intent_from_response(ai_response)

        # 5. Qaror qabul qilish (Decision Layer)
        decision: Decision = self.decision_engine.decide(intent, ai_response)
        latency = round((time.time() - start_time) * 1000, 2)

        # 6. Tasdiqlash (Confirmation) tekshiruvi
        if decision.type == DecisionType.CONFIRMATION:
            # Agar foydalanuvchi ushbu amalni allaqachon tasdiqlagan bo'lsa -> davom etish
            if confirmed_action and confirmed_action == intent.name:
                logger.info(f"Foydalanuvchi amalni oldindan tasdiqlagan: '{confirmed_action}'")
                decision.type = DecisionType.COMMAND
            else:
                return IntelligenceResponse(
                    type="confirmation",
                    content=decision.content,
                    intent=intent.name,
                    params=intent.params,
                    verified=True,
                    provider=ai_response.provider,
                    model=ai_response.model,
                    metadata={"latency_ms": latency, "risk_level": decision.risk_level.value}
                )

        # 7. Aniqlashtirish (Clarification) talabi
        if decision.type == DecisionType.CLARIFICATION:
            return IntelligenceResponse(
                type="clarification",
                content=decision.content,
                intent=intent.name if intent else None,
                verified=True,
                provider=ai_response.provider,
                model=ai_response.model,
                metadata={"latency_ms": latency}
            )

        # 8. Asbobni ijro etish va Natijani tekshirish (Tool Execution & Verification)
        if decision.type == DecisionType.TOOL and decision.tool_name and self.tool_registry:
            tool_name = decision.tool_name
            tool_params = decision.tool_params

            logger.info(f"[IntelligenceOrchestrator] Asbob ijro etilmoqda: '{tool_name}', parametrlar={tool_params}")
            try:
                tool_call_res = self.tool_registry.call(tool_name, **tool_params)
                is_success = bool(tool_call_res.get("success", False))

                if is_success:
                    raw_result = tool_call_res.get("result")
                    formatted_content = self._format_tool_output(tool_name, raw_result, decision.content)
                    logger.info(f"[IntelligenceOrchestrator] Asbob muvaffaqiyatli bajarildi: '{tool_name}'")
                    return IntelligenceResponse(
                        type="tool",
                        content=formatted_content,
                        intent=intent.name,
                        params=tool_params,
                        tool_executed=tool_name,
                        tool_result=raw_result,
                        verified=True,
                        provider=ai_response.provider,
                        model=ai_response.model,
                        metadata={"latency_ms": latency}
                    )
                else:
                    err = tool_call_res.get("error", "Noma'lum xatolik")
                    logger.warning(f"[IntelligenceOrchestrator] Asbob bajarilmadi: '{tool_name}', xato: {err}")
                    return IntelligenceResponse(
                        type="error",
                        content=f"Asbobni bajarishda xatolik yuz berdi ({tool_name}): {err}",
                        intent=intent.name,
                        params=tool_params,
                        tool_executed=tool_name,
                        tool_result=tool_call_res,
                        verified=False,
                        provider=ai_response.provider,
                        model=ai_response.model,
                        metadata={"latency_ms": latency}
                    )
            except Exception as e:
                logger.error(f"Asbob ijrosida istisno: {e}", exc_info=True)
                return IntelligenceResponse(
                    type="error",
                    content=f"Asbob ijro etilmadi: {e}",
                    intent=intent.name,
                    params=tool_params,
                    tool_executed=tool_name,
                    verified=False,
                    provider=ai_response.provider,
                    model=ai_response.model,
                    metadata={"latency_ms": latency}
                )

        # 9. Buyruq (Command)
        if decision.type == DecisionType.COMMAND:
            return IntelligenceResponse(
                type="command",
                content=decision.content,
                intent=intent.name,
                params=intent.params,
                verified=True,
                provider=ai_response.provider,
                model=ai_response.model,
                metadata={"latency_ms": latency}
            )

        # 10. Xatolik (Error)
        if decision.type == DecisionType.ERROR:
            return IntelligenceResponse(
                type="error",
                content=decision.content,
                intent=intent.name,
                verified=False,
                provider=ai_response.provider,
                model=ai_response.model,
                error_code=ai_response.error_code,
                metadata={"latency_ms": latency}
            )

        # 11. Standart Suhbat Javobi (Answer)
        return IntelligenceResponse(
            type="answer",
            content=decision.content,
            intent=intent.name,
            verified=True,
            provider=ai_response.provider,
            model=ai_response.model,
            metadata={"latency_ms": latency}
        )

    def _format_tool_output(self, tool_name: str, result: Any, default_text: str) -> str:
        """Asbob natijasini foydalanuvchiga tushunarli matnga aylantirish"""
        if isinstance(result, dict):
            if "message" in result:
                return str(result["message"])
            if "response" in result:
                return str(result["response"])
            if "info" in result and isinstance(result["info"], dict):
                lines = [f"• {k}: {v}" for k, v in result["info"].items()]
                return "Ma'lumotlar:\n" + "\n".join(lines)
        if isinstance(result, str) and result.strip():
            return result.strip()
        return default_text or f"'{tool_name}' vositasi muvaffaqiyatli bajarildi."
