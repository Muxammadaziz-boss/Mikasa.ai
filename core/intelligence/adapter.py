# ========== adapter.py ==========
# Mikasa AI 7.x — Compatibility Adapter
# Bridges Intelligence Core with Existing Frontend & Legacy AI Engine Contracts

import datetime
from typing import Dict, Any, Optional
from core.intelligence.types import IntelligenceResponse


class CompatibilityAdapter:
    """
    Yangi Intelligence Core javoblarini (IntelligenceResponse)
    mavjud frontend va legacy tizimlar kutayotgan formatga o'giruvchi adapter.
    """

    @staticmethod
    def to_frontend_response(
        intel_resp: IntelligenceResponse,
        user_name: str = "Foydalanuvchi",
        mode: str = "ask"
    ) -> Dict[str, Any]:
        """
        Frontend REST API (/api/chat) va WebSocket uchun to'liq mos keluvchi javob
        """
        is_ok = intel_resp.verified if intel_resp.type != "error" else False
        
        return {
            "ok": is_ok,
            "response": intel_resp.content,
            "type": intel_resp.type,
            "intent": intel_resp.intent,
            "params": intel_resp.params or {},
            "user": user_name,
            "mode": mode,
            "verified": intel_resp.verified,
            "provider": intel_resp.provider,
            "model": intel_resp.model,
            "timestamp": datetime.datetime.now().isoformat(),
            "error": intel_resp.content if not is_ok else None,
        }

    @staticmethod
    def to_legacy_ai_engine_dict(intel_resp: IntelligenceResponse) -> Optional[Dict[str, Any]]:
        """
        Eski `core/ai_engine.py` dagi `ai_savol_yuborish` funksiyasi kutgan format:
        - {"type": "command", "intent": "...", "params": {...}, "response": "..."}
        - {"type": "answer", "response": "..."}
        - {"type": "confirmation", "question": "..."}
        - {"type": "clarification", "question": "..."}
        """
        if not intel_resp:
            return None

        if intel_resp.type == "command":
            return {
                "type": "command",
                "intent": intel_resp.intent,
                "params": intel_resp.params or {},
                "response": intel_resp.content,
            }
        elif intel_resp.type == "confirmation":
            return {
                "type": "confirmation",
                "intent": intel_resp.intent,
                "question": intel_resp.content,
                "response": intel_resp.content,
                "params": intel_resp.params or {},
            }
        elif intel_resp.type == "clarification":
            return {
                "type": "clarification",
                "question": intel_resp.content,
                "response": intel_resp.content,
                "params": intel_resp.params or {},
            }
        elif intel_resp.type == "tool":
            return {
                "type": "command",
                "intent": intel_resp.tool_executed or intel_resp.intent,
                "params": intel_resp.params or {},
                "response": intel_resp.content,
            }
        elif intel_resp.type == "error":
            return {
                "type": "answer",
                "response": intel_resp.content,
                "error": True,
            }
        else:
            return {
                "type": "answer",
                "response": intel_resp.content,
            }
