# ========== intent.py ==========
# Mikasa AI 7.x — Intent Engine
# Normalized Intent Representation & Intent Categorization

import logging
from typing import Dict, Any, Optional
from core.intelligence.types import Intent, IntentCategory, AIResponse

logger = logging.getLogger(__name__)


class IntentEngine:
    """
    Niyatlarni (Intent) tahlil qilish va normalizatsiya qilish dvigateli.
    AI modeli javobi yoki mahalliy qoidalardan niyatni ajratib oladi.
    """

    def resolve_intent_from_response(self, response: AIResponse) -> Intent:
        """AIResponse obyektidan normalizatsiya qilingan Intent hosil qilish"""
        if not response.success or response.type == "error":
            return Intent(
                name="error",
                category=IntentCategory.ERROR,
                confidence=0.0,
                params={"error_code": response.error_code, "message": response.content},
                source="llm"
            )

        resp_type = response.type.lower()
        intent_name = response.intent or ""

        if resp_type == "confirmation":
            return Intent(
                name=intent_name or "confirmation",
                category=IntentCategory.CONFIRMATION,
                confidence=0.95,
                params={"question": response.content, **response.params},
                source="llm"
            )
        elif resp_type == "clarification":
            return Intent(
                name="clarification",
                category=IntentCategory.CLARIFICATION,
                confidence=0.9,
                params={"question": response.content, **response.params},
                source="llm",
                requires_context=True
            )
        elif resp_type == "tool":
            return Intent(
                name=intent_name or "tool_call",
                category=IntentCategory.TOOL_REQUEST,
                confidence=0.95,
                params=response.params,
                source="llm"
            )
        elif resp_type == "command" or (intent_name and resp_type != "answer"):
            return Intent(
                name=intent_name or "unknown_command",
                category=IntentCategory.COMMAND,
                confidence=0.95,
                params=response.params,
                source="llm"
            )
        else:
            # Standart suhbat javobi
            return Intent(
                name="conversation",
                category=IntentCategory.CONVERSATION,
                confidence=1.0,
                params={"content": response.content},
                source="llm"
            )

    def create_local_intent(self, name: str, params: Optional[Dict[str, Any]] = None) -> Intent:
        """Mahalliy qoidalar yoki CommandDispatcher aniqlagan niyatni yaratish"""
        return Intent(
            name=name,
            category=IntentCategory.COMMAND,
            confidence=1.0,
            params=params or {},
            source="local"
        )
