# ========== agent_lessons.py ==========
# Agent xatolardan o'rganish tizimi
# Murakkab vazifalarda bir xil xatoni takrorlamaslik uchun

import os
import json
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AgentLessons:
    """Agent saboqlarini saqlash va yuklab olish"""

    def __init__(self, max_lessons: int = 100):
        self._file = os.path.join(BASE_DIR, "data", "agent_lessons.json")
        self._max_lessons = max_lessons
        self._lessons = self._load()

    def _load(self) -> List[dict]:
        """Saboqlarni fayldan yuklash"""
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Agent lessons loaded: {len(data)} ta")
                    return data
            except Exception as e:
                logger.error(f"Lessons yuklab bo'lmadi: {e}")
        return []

    def _save(self):
        """Saboqlarni faylga saqlash"""
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(
                    self._lessons[-self._max_lessons :], f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"Lessons saqlab bo'lmadi: {e}")

    def save_lesson(
        self, situation: str, wrong_action: str, correct_action: str, tool: str = ""
    ):
        """Yangi saboq saqlash"""
        self._lessons.append(
            {
                "situation": situation,
                "wrong": wrong_action,
                "correct": correct_action,
                "tool": tool,
                "time": datetime.now().isoformat(),
            }
        )
        if len(self._lessons) > self._max_lessons:
            self._lessons = self._lessons[-self._max_lessons :]
        self._save()
        logger.info(f"Lesson saved: {situation[:50]}")

    def get_relevant(self, task: str, limit: int = 3) -> List[dict]:
        """Vazifa bo'yicha tegishli saboqlarni olish"""
        if not task or not self._lessons:
            return []

        task_lower = task.lower()
        words = set(task_lower.split())

        scored = []
        for lesson in self._lessons:
            situation = lesson.get("situation", "").lower()
            situation_words = set(situation.split())

            common = words & situation_words
            if common:
                scored.append((len(common), lesson))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [l for _, l in scored[:limit]]

    def format_for_prompt(self, task: str) -> str:
        """Prompt uchun formatlangan matn"""
        lessons = self.get_relevant(task)
        if not lessons:
            return ""

        lines = ["\n\n=== OLDINGI SABOQLAR (xatolardan o'rganilgan) ==="]
        for i, l in enumerate(lessons, 1):
            lines.append(f"{i}. Vazifa: {l['situation']}")
            lines.append(f"   XATO: {l['wrong']}")
            lines.append(f"   TO'G'RI: {l['correct']}")
            if l.get("tool"):
                lines.append(f"   Tool: {l['tool']}")
        lines.append("=========================================\n")
        return "\n".join(lines)

    def clear(self):
        """Barcha saboqlarni o'chirish"""
        self._lessons = []
        self._save()
        logger.info("Barcha lessons o'chirildi")


_lesson_instance: Optional[AgentLessons] = None


def get_lessons() -> AgentLessons:
    """Global lessons instance"""
    global _lesson_instance
    if _lesson_instance is None:
        _lesson_instance = AgentLessons()
    return _lesson_instance
