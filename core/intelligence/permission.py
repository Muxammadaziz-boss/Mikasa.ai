# ========== permission.py ==========
# Mikasa AI 7.x — Permission & Risk Model
# Action Authorization & Confirmation Requirements

import logging
from typing import Dict, Any, Tuple, Optional
from core.intelligence.types import RiskLevel

logger = logging.getLogger(__name__)


class PermissionEngine:
    """
    Xavfsizlik va ruxsatlar boshqaruvi dvigateli.
    Har qanday buyruq yoki asbob chaqiruvining xavf darajasini (LOW, MEDIUM, HIGH)
    baholaydi va tasdiqlash (confirmation) talablarini belgilaydi.
    """

    HIGH_RISK_ACTIONS = {
        "shutdown": "Kompyuterni o'chirishni tasdiqlaysizmi?",
        "restart": "Kompyuterni qayta yuklashni tasdiqlaysizmi?",
        "system_shutdown": "Tizimni o'chirishni xohlaysizmi?",
        "delete_all_reminders": "Barcha eslatmalarni o'chirib yuborishni tasdiqlaysizmi?",
        "clear_memory": "Barcha xotira va bilimlarni tozalashni tasdiqlaysizmi?",
        "delete_plugin": "Ushbu plaginni butunlay o'chirishni tasdiqlaysizmi?",
        "destructive_file_op": "Faylni butunlay o'chirishni tasdiqlaysizmi?",
    }

    MEDIUM_RISK_ACTIONS = {
        "process_kill": "Jarayonni to'xtatish",
        "close_window": "Hozirgi oynani yopish",
        "close_chrome": "Brauzerni yopish",
        "lock": "Ekranni qulflash",
        "scheduler_edit": "Vazifani o'zgartirish",
        "scheduler_remove": "Vazifani o'chirish",
    }

    def __init__(self):
        self._custom_risk_overrides: Dict[str, RiskLevel] = {}
        self._custom_confirmation_prompts: Dict[str, str] = {}

    def register_risk_level(self, action_name: str, level: RiskLevel, confirmation_prompt: Optional[str] = None):
        """Amal uchun maxsus xavf darajasini belgilash"""
        self._custom_risk_overrides[action_name] = level
        if confirmation_prompt:
            self._custom_confirmation_prompts[action_name] = confirmation_prompt

    def evaluate(self, action_name: str, params: Optional[Dict[str, Any]] = None) -> Tuple[RiskLevel, bool, Optional[str]]:
        """
        Amalni baholash.
        Qaytaradi: (RiskLevel, requires_confirmation, confirmation_prompt)
        """
        clean_name = (action_name or "").lower().strip()

        # 1. Maxsus kiritilgan sozlamalar
        if clean_name in self._custom_risk_overrides:
            level = self._custom_risk_overrides[clean_name]
            prompt = self._custom_confirmation_prompts.get(clean_name)
            req_confirm = (level == RiskLevel.HIGH)
            return level, req_confirm, prompt

        # 2. Yuqori xavfli amallar (HIGH)
        if clean_name in self.HIGH_RISK_ACTIONS:
            prompt = self.HIGH_RISK_ACTIONS[clean_name]
            logger.warning(f"Xavfsizlik: Yuqori xavfli amal aniqlandi: '{clean_name}' (tasdiqlash talab etiladi)")
            return RiskLevel.HIGH, True, prompt

        # 3. O'rta xavfli amallar (MEDIUM)
        if clean_name in self.MEDIUM_RISK_ACTIONS:
            return RiskLevel.MEDIUM, False, None

        # 4. Qolgan barcha standart amallar (LOW) — ochish, qidiruv, hisoblash, ma'lumot olish
        return RiskLevel.LOW, False, None
