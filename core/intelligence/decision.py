# ========== decision.py ==========
# Mikasa AI 7.x — Decision Engine
# Reasoning & Action Routing Decision Layer

import logging
from typing import Dict, Any, Optional
from core.intelligence.types import (
    Decision,
    DecisionType,
    Intent,
    IntentCategory,
    RiskLevel,
    AIResponse,
)
from core.intelligence.permission import PermissionEngine

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Qaror qabul qilish (Decision) dvigateli.
    Aniqlangan niyat va AI javobini PermissionEngine bilan birgalikda baholab,
    tizim qanday harakat qilishi kerakligini hal qiladi (ANSWER, COMMAND, TOOL, CLARIFICATION, CONFIRMATION).
    """

    def __init__(self, permission_engine: Optional[PermissionEngine] = None, tool_registry=None):
        self.permission_engine = permission_engine or PermissionEngine()
        self.tool_registry = tool_registry

    def decide(self, intent: Intent, response: AIResponse) -> Decision:
        """Niyat va AI javobi asosida yakuniy qarorni shakllantirish"""

        # 1. Xatolik holati
        if intent.category == IntentCategory.ERROR or not response.success:
            return Decision(
                type=DecisionType.ERROR,
                content=response.content or "Kutilmagan xatolik yuz berdi.",
                intent=intent
            )

        # 2. Aniqlashtirish talabi (Clarification)
        if intent.category == IntentCategory.CLARIFICATION:
            question = intent.params.get("question") or response.content or "Iltimos, so'rovingizni aniqlashtiring."
            return Decision(
                type=DecisionType.CLARIFICATION,
                content=question,
                clarification_question=question,
                intent=intent
            )

        # 3. Buyruq yoki Tool chaqiruvi (Command / Tool)
        if intent.category in (IntentCategory.COMMAND, IntentCategory.TOOL_REQUEST):
            action_name = intent.name
            params = intent.params

            # Xavf darajasini va tasdiqlash zarurligini baholash
            risk, req_confirm, confirm_prompt = self.permission_engine.evaluate(action_name, params)

            # Agar yuqori xavfli amal bo'lsa -> Darhol CONFIRMATION qaytarish
            if req_confirm:
                logger.info(f"Qaror: Amal '{action_name}' uchun tasdiqlash so'raladi")
                prompt_text = confirm_prompt or f"'{action_name}' amalini bajarishni tasdiqlaysizmi?"
                return Decision(
                    type=DecisionType.CONFIRMATION,
                    content=prompt_text,
                    intent=intent,
                    risk_level=risk,
                    requires_confirmation=True,
                    confirmation_prompt=prompt_text
                )

            # ToolRegistry da mavjud vosita ekanligini tekshirish
            is_tool = False
            if self.tool_registry:
                try:
                    is_tool = bool(self.tool_registry.get(action_name))
                except Exception:
                    pass

            if is_tool:
                return Decision(
                    type=DecisionType.TOOL,
                    content=response.content or f"'{action_name}' vositasi ishlatilmoqda.",
                    intent=intent,
                    tool_name=action_name,
                    tool_params=params,
                    risk_level=risk
                )
            else:
                return Decision(
                    type=DecisionType.COMMAND,
                    content=response.content or f"Buyruq bajarilmoqda: {action_name}",
                    intent=intent,
                    risk_level=risk
                )

        # 4. Tasdiqlash javobi
        if intent.category == IntentCategory.CONFIRMATION:
            prompt_text = intent.params.get("question") or response.content or "Ushbu amalni tasdiqlaysizmi?"
            return Decision(
                type=DecisionType.CONFIRMATION,
                content=prompt_text,
                intent=intent,
                requires_confirmation=True,
                confirmation_prompt=prompt_text
            )

        # 5. Standart javob (Answer)
        return Decision(
            type=DecisionType.ANSWER,
            content=response.content or "Javob tayyorlanmadi.",
            intent=intent
        )
