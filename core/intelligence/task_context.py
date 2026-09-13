# ========== task_context.py ==========
# Mikasa AI 7.x — Active Task Context & Conversation Reference Continuity
# Contextual Coreferencing for Uzbek Pronouns ("shunga", "undagi", "o'sha")

import re
import logging
from typing import Optional, List, Dict, Any
from core.intelligence.memory_types import ActiveTaskContext

logger = logging.getLogger(__name__)


class TaskContextManager:
    """
    Faol vazifalar kontekstini boshqarish va suhbatdagi olmoshlar/havolalarni
    (coreferences) yechish xizmati.
    """

    REFERENCE_MARKERS = [
        "shunga", "shunda", "shundagi", "shuni",
        "unga", "unda", "undagi", "uni",
        "bunga", "bunda", "bundagi", "buni",
        "o'sha", "o'shani", "o'shanda",
        "o'xshash", "oxshash", "muqobil", "boshqa", "yana",
    ]

    KNOWN_ENTITY_PATTERNS = [
        ("telegram", ["telegram", "tg", "ayugram"]),
        ("youtube", ["youtube", "yutub"]),
        ("chrome", ["chrome", "brauzer", "google chrome"]),
        ("vscode", ["vs code", "vscode", "code"]),
        ("discord", ["discord", "diskord"]),
        ("github", ["github", "git", "repo", "loyiha"]),
        ("python", ["python", "payton"]),
    ]

    def __init__(self):
        self._current_task: Optional[ActiveTaskContext] = None

    def get_active_task(self) -> Optional[ActiveTaskContext]:
        """Faol vazifani olish"""
        if self._current_task and self._current_task.status == "active":
            return self._current_task
        return None

    def set_active_task(self, goal: str, entities: Optional[List[str]] = None) -> ActiveTaskContext:
        """Yangi faol vazifani o'rnatish"""
        task = ActiveTaskContext(
            goal=goal,
            entities=entities or self.extract_entities(goal),
            status="active"
        )
        self._current_task = task
        logger.info(f"Yangi faol vazifa belgilandi: '{goal}' (entities={task.entities})")
        return task

    def update_task_progress(
        self,
        action: Optional[str] = None,
        result: Optional[str] = None,
        new_entities: Optional[List[str]] = None
    ):
        """Faol vazifa holatini yangilash"""
        if self._current_task:
            if action:
                self._current_task.last_action = action
            if result:
                self._current_task.last_result = result
            if new_entities:
                for ent in new_entities:
                    if ent not in self._current_task.entities:
                        self._current_task.entities.append(ent)

    def complete_task(self):
        """Vazifani yakunlash"""
        if self._current_task:
            self._current_task.status = "completed"
            logger.info(f"Faol vazifa yakunlandi: '{self._current_task.goal}'")
            self._current_task = None

    def extract_entities(self, text: str) -> List[str]:
        """Matndan asosiy ilovalar va ob'ektlarni aniqlash"""
        if not text:
            return []
        lowered = text.lower()
        found = []
        for canonical, aliases in self.KNOWN_ENTITY_PATTERNS:
            if any(re.search(rf"\b{re.escape(alias)}\b", lowered) for alias in aliases):
                if canonical not in found:
                    found.append(canonical)
        return found

    def resolve_reference_hint(
        self,
        current_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Optional[str]:
        """
        Agar xabarda 'shunga', 'undagi', 'o'xshash' kabi nisbiy havolalar bo'lsa,
        avvalgi suhbat yoki faol vazifadan ob'ektni aniqlab, AI uchun yordamchi ko'rsatma beradi.
        """
        lowered_msg = current_message.lower()
        has_reference = any(re.search(rf"\b{re.escape(marker)}\b", lowered_msg) for marker in self.REFERENCE_MARKERS)

        if not has_reference:
            return None

        # 1. Faol vazifa ob'ektlaridan tekshirish
        if self._current_task and self._current_task.entities:
            main_entity = self._current_task.entities[0]
            return f"KONTEKSTUAL BOG'LANISH: Foydalanuvchining havolasi ('shunga/undagi') joriy faol vazifadagi '{main_entity}' ob'ektiga tegishli."

        # 2. Oxirgi suhbat xabarlaridan ob'ektni qidirish (orqadan oldinga)
        if conversation_history:
            for turn in reversed(conversation_history[-4:]):
                content = turn.get("content") or turn.get("text") or ""
                entities = self.extract_entities(content)
                if entities:
                    target = entities[0]
                    return f"KONTEKSTUAL BOG'LANISH: Foydalanuvchining havolasi ('shunga/undagi/o'xshash') avvalgi suhbatdagi '{target}' mavzusiga tegishli."

        return None


# Global singleton
_task_manager = None


def get_task_context_manager() -> TaskContextManager:
    """Global TaskContextManager singleton instansiyasini olish"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskContextManager()
    return _task_manager
