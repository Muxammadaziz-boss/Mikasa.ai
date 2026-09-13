# ========== context.py ==========
# Mikasa AI 7.x — Context Engine
# Selective, Bounded, and Safe Context Assembly for AI Reasoning

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from core.intelligence.types import AIRequest

logger = logging.getLogger(__name__)


class ContextEngine:
    """
    Kontekstni tanlab va xavfsiz yig'ish dvigateli.
    Har bir so'rov uchun ortiqcha og'ir ma'lumotlarni tiqishtirmasdan,
    zaruriy va cheklangan (bounded) kontekstni yig'adi.
    """

    def __init__(self, memory=None, tool_registry=None, app_detector=None):
        self._memory = memory
        self._tool_registry = tool_registry
        self._app_detector = app_detector

    def _get_memory(self):
        if self._memory is None:
            try:
                from core.agent_memory import get_memory
                self._memory = get_memory()
            except Exception as e:
                logger.warning(f"AgentMemory yuklanmadi: {e}")
        return self._memory

    def _get_tool_registry(self):
        if self._tool_registry is None:
            try:
                from core.agent_tools import get_registry
                self._tool_registry = get_registry()
            except Exception as e:
                logger.warning(f"ToolRegistry yuklanmadi: {e}")
        return self._tool_registry

    def _get_app_detector(self):
        if self._app_detector is None:
            try:
                from core.app_detector import get_app_detector
                self._app_detector = get_app_detector()
            except Exception as e:
                logger.warning(f"AppDetector yuklanmadi: {e}")
        return self._app_detector

    def should_include_system_specs(self, message: str) -> bool:
        """So'rov kompyuter parametrlari yoki o'rnatilgan ilovalar haqida ekanligini aniqlash"""
        lowered = message.lower()
        spec_keywords = [
            "kompyuter", "pc", "tizim", "sistema", "parametr", "xususiyat",
            "ram", "protsessor", "disk", "gpu", "videokarta", "dastur", "ilova",
            "o'rnatilganmi", "bormi", "mavjudmi", "windows"
        ]
        return any(kw in lowered for kw in spec_keywords)

    def assemble(
        self,
        message: str,
        user_name: str = "Foydalanuvchi",
        max_history_turns: int = 6,
        include_tools: bool = True
    ) -> AIRequest:
        """
        AIRequest obyektini to'liq va xavfsiz tarzda shakllantirish
        """
        system_context: Dict[str, Any] = {}
        conversation_history: List[Dict[str, str]] = []
        memory_data: Dict[str, Any] = {}
        tools_summary: List[Dict[str, Any]] = []

        mem = self._get_memory()
        reg = self._get_tool_registry()

        # 1. Bounded Suhbat Tarixi
        if mem:
            try:
                raw_convs = mem.get_conversations(last_n=max_history_turns)
                for c in raw_convs:
                    u = c.get("user", "").strip()
                    a = c.get("agent", "").strip()
                    if u:
                        conversation_history.append({"role": "user", "content": u})
                    if a:
                        conversation_history.append({"role": "assistant", "content": a})
            except Exception as e:
                logger.warning(f"Suhbat tarixini olishda xatolik: {e}")

        # 2. Bounded Foydalanuvchi Bilimlari va Profili
        if mem:
            try:
                knowledge = mem.get_knowledge()
                if knowledge:
                    # Maksimal 8 ta eng muhim bilim
                    memory_data["knowledge"] = {
                        k: v.get("value", v) if isinstance(v, dict) else v
                        for k, v in list(knowledge.items())[:8]
                    }
                profile = mem.get_profile()
                if profile:
                    memory_data["profile"] = {
                        "ism": profile.get("ism") or user_name,
                        "til": profile.get("til", "uz"),
                        "ovoz_turi": profile.get("ovoz_turi", "erkak")
                    }
            except Exception as e:
                logger.warning(f"Bilimlar bazasini olishda xatolik: {e}")

        # 3. Tanlangan Tizim va Dasturlar Konteksti
        system_specs_text = ""
        if self.should_include_system_specs(message):
            detector = self._get_app_detector()
            if detector:
                try:
                    specs = detector.get_realtime_system_specs()
                    inv = detector.get_realtime_inventory_summary()
                    system_specs_text = f"KOMPYUTER VA ILOVALAR PARAMETRLARI:\n{specs}\nAniqlangan dasturlar:\n{inv}"
                    system_context["specs"] = specs
                except Exception as e:
                    logger.warning(f"Tizim parametrlarini olishda xatolik: {e}")

        # 4. Asboblar (Tools) xulosasi
        tools_prompt_text = ""
        if include_tools and reg:
            try:
                tools_summary = reg.list_tools()
                tools_lines = []
                for t in tools_summary:
                    name = t.get("name")
                    desc = t.get("description")
                    params = t.get("parameters", {})
                    p_str = ", ".join(f"{k}: {v.get('type')}" for k, v in params.items())
                    tools_lines.append(f"- {name}({p_str}): {desc}")
                tools_prompt_text = "MAVJUD ASBOBLAR (TOOLS):\n" + "\n".join(tools_lines)
            except Exception as e:
                logger.warning(f"Toollar ro'yxatini olishda xatolik: {e}")

        # 5. Yagona Tizim Ko'rsatmasini (System Prompt) Shakllantirish
        prompt_parts = [
            f"""Sen — "Mikasa AI", foydalanuvchining shaxsiy aqlli yordamchisi va do'stisan.
Foydalanuvchi ismi: {user_name}.
Tiling: O'ZBEK tili. Javoblaring samimiy, aniq, lo'nda va do'stona bo'lsin.

MUHIM QOIDALAR:
1. Har doim O'ZBEK tilida javob ber.
2. Qisqa va tabiiy gaplash (1-3 gap).
3. Foydalanuvchi biror buyruq bajarishni yoki asbob ishlatishni so'rasa, javobni FAQAT quyidagi JSON formatda ber:
   {{"type": "command", "intent": "<buyruq_yoki_tool_nomi>", "params": {{}}, "response": "<qisqa javob>"}}
4. Agar noaniq bo'lsa, aniqlashtirish so'ra:
   {{"type": "clarification", "question": "<aniqlashtiruvchi savol>"}}
5. Agar tizimga jiddiy ta'sir ko'rsatuvchi xavfli amal (o'chirish, restart) bo'lsa:
   {{"type": "confirmation", "intent": "<intent>", "question": "<tasdiqlash savoli>"}}
6. Agar oddiy savol yoki suhbat bo'lsa:
   {{"type": "answer", "response": "<javob matni>"}}
"""
        ]

        if system_specs_text:
            prompt_parts.append(f"\n{system_specs_text}")

        if memory_data.get("knowledge"):
            k_lines = [f"- {k}: {v}" for k, v in memory_data["knowledge"].items()]
            prompt_parts.append("\nFOYDALANUVCHI BILIMLARI:\n" + "\n".join(k_lines))

        if tools_prompt_text:
            prompt_parts.append(f"\n{tools_prompt_text}")

        full_system_prompt = "\n".join(prompt_parts)
        system_context["prompt"] = full_system_prompt

        return AIRequest(
            message=message,
            system_context=system_context,
            conversation=conversation_history,
            memory=memory_data,
            tools=tools_summary,
            metadata={"user_name": user_name}
        )
