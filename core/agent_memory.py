# ========== agent_memory.py ==========
# Agent uzoq muddatli xotira tizimi
# Suhbat tarixi + Foydalanuvchi profili + Bilimlar bazasi

import os
import json
import logging
import datetime
from collections import deque
from threading import RLock
from typing import Optional, List, Dict, Any

from core.intelligence.memory_types import (
    MemoryItem,
    MemoryType,
    MemorySource,
    MemoryConfidence,
)
from core.intelligence.memory_policy import MemoryPolicy
from core.intelligence.memory_retriever import MemoryRetriever

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Loyiha ildizi


class AgentMemory:
    """Agent xotirasi — 3 darajali:

    1. Qisqa muddatli (RAM) — joriy suhbat konteksti
    2. O'rta muddatli (fayl) — suhbat tarixi
    3. Uzoq muddatli (fayl) — foydalanuvchi profili va bilimlar
    """

    def __init__(self, max_short_term=20, max_conversations=100):
        self._lock = RLock()

        # Qisqa muddatli xotira (RAM)
        self._short_term = deque(maxlen=max_short_term)

        # Fayl yo'llari
        self._conversations_file = os.path.join(
            BASE_DIR, "data", "agent_conversations.json"
        )
        self._profile_file = os.path.join(BASE_DIR, "data", "agent_profile.json")
        self._knowledge_file = os.path.join(BASE_DIR, "data", "agent_knowledge.json")

        self._max_conversations = max_conversations

        # Yuklash
        self._profile = self._load_json(
            self._profile_file,
            {
                "ism": "",
                "ovoz_turi": "erkak",
                "til": "uz",
                "qiziqishlar": [],
                "yoqtirgan_platformalar": [],
                "yaratilgan": datetime.datetime.now().isoformat(),
            },
        )
        self._knowledge = self._load_json(self._knowledge_file, {})
        self._conversations = self._load_json(self._conversations_file, [])

        logger.info(
            f"AgentMemory yuklandi: {len(self._conversations)} suhbat, {len(self._knowledge)} bilim"
        )

    # ========== QISQA MUDDATLI XOTIRA ==========

    def add_to_context(self, role: str, content: str):
        """Joriy suhbatga xabar qo'shish"""
        with self._lock:
            self._short_term.append(
                {
                    "role": role,
                    "content": content,
                    "time": datetime.datetime.now().isoformat(),
                }
            )

    def get_context(self, last_n: int = 10) -> list:
        """Joriy suhbat kontekstini olish"""
        with self._lock:
            items = list(self._short_term)
            return items[-last_n:]

    def clear_context(self):
        """Joriy suhbatni tozalash"""
        with self._lock:
            self._short_term.clear()

    # ========== SUHBAT TARIXI ==========

    def add_conversation(self, user_input: str, agent_response: str):
        """Suhbatni tarixga qo'shish"""
        should_save = False
        with self._lock:
            self._conversations.append(
                {
                    "user": user_input,
                    "agent": agent_response,
                    "time": datetime.datetime.now().isoformat(),
                }
            )

            # Cheklanishdan oshsa eski suhbatlarni o'chirish
            while len(self._conversations) > self._max_conversations:
                self._conversations.pop(0)

            # Har 5 ta suhbatda faylga saqlash (flag)
            if len(self._conversations) % 5 == 0:
                should_save = True

        # Fayl I/O — lock tashqarisida (boshqa threadlar bloklanmaydi)
        if should_save:
            self._save_conversations()

    def get_conversations(self, last_n: int = 20) -> list:
        """Oxirgi N ta suhbat"""
        with self._lock:
            return self._conversations[-last_n:]

    def search_conversations(self, query: str, limit: int = 5) -> list:
        """Suhbatlardan qidirish"""
        with self._lock:
            query_lower = query.lower()
            results = []
            for conv in reversed(self._conversations):
                if (
                    query_lower in conv["user"].lower()
                    or query_lower in conv["agent"].lower()
                ):
                    results.append(conv)
                    if len(results) >= limit:
                        break
            return results

    def get_history_for_ai(self, last_n: int = 6) -> list:
        """AI uchun suhbat tarixi formatda"""
        conversations = self.get_conversations(last_n)
        history = []
        for conv in conversations:
            history.append({"role": "user", "content": conv["user"]})
            history.append({"role": "assistant", "content": conv["agent"]})
        return history

    def clear_conversations(self):
        """Barcha suhbatlar tarixini tozalash"""
        with self._lock:
            self._conversations.clear()
            self._save_conversations()

    # ========== FOYDALANUVCHI PROFILI ==========

    def set_profile(self, key: str, value):
        """Profil ma'lumotini o'zgartirish"""
        with self._lock:
            self._profile[key] = value
            self._save_json(self._profile_file, self._profile)
            logger.debug(f"Profil yangilandi: {key} = {value}")

    def get_profile(self, key: str = None, default=None):
        """Profil ma'lumotini olish"""
        with self._lock:
            if key:
                return self._profile.get(key, default)
            return self._profile.copy()

    # ========== BILIMLAR BAZASI ==========

    def save_knowledge(
        self,
        key: str,
        value: str,
        memory_type: Optional[MemoryType] = None,
        source: MemorySource = MemorySource.USER,
        confidence: float = 1.0,
        importance: float = 0.5,
    ) -> bool:
        """Yangi bilim saqlash (MemoryPolicy xavfsizlik va deduplikatsiya bilan)"""
        with self._lock:
            decision = MemoryPolicy.evaluate_write(
                key=key,
                content=value,
                source=source,
                existing_knowledge=self._knowledge,
            )

            if not decision.allowed:
                logger.warning(
                    f"Bilim saqlash rad etildi: key='{key}', sabab='{decision.reason}'"
                )
                return False

            if memory_type is None:
                memory_type = MemoryPolicy.classify_type(key, decision.sanitized_content)

            # Duplikat bo'lsa: mavjud xotirani yangilaymiz
            if decision.is_duplicate and decision.existing_key:
                target_key = decision.existing_key
                if target_key in self._knowledge:
                    existing = self._knowledge[target_key]
                    if isinstance(existing, dict):
                        existing["access_count"] = existing.get("access_count", 0) + 1
                        existing["updated_at"] = datetime.datetime.now().isoformat()
                        self._save_json(self._knowledge_file, self._knowledge)
                        return True

            # Yangi xotira yaratish
            item = MemoryItem(
                key=key,
                content=decision.sanitized_content,
                type=memory_type if isinstance(memory_type, MemoryType) else MemoryType(memory_type),
                source=source if isinstance(source, MemorySource) else MemorySource(source),
                importance=importance,
                confidence=confidence,
            )

            # Ziddiyatli xotiralar tekshiruvi va yangilanishi
            existing_items = self.get_memory_items()
            MemoryPolicy.resolve_conflict(item, existing_items)
            for ex in existing_items:
                if ex.key in self._knowledge and not ex.is_active():
                    self._knowledge[ex.key]["superseded_by"] = ex.superseded_by

            self._knowledge[key] = item.to_dict()
            self._save_json(self._knowledge_file, self._knowledge)
            logger.debug(f"Bilim saqlandi ({item.type.value}): {key} = {decision.sanitized_content}")
            return True

    def get_memory_items(self) -> List[MemoryItem]:
        """Barcha bilimlarni normalizatsiya qilingan MemoryItem ro'yxati sifatida olish"""
        with self._lock:
            items = []
            for k, v in self._knowledge.items():
                try:
                    items.append(MemoryItem.from_dict(k, v))
                except Exception as e:
                    logger.warning(f"MemoryItem yaratishda xatolik ({k}): {e}")
            return items

    def retrieve_relevant(
        self,
        query: str,
        limit: int = 6,
        task_entities: Optional[List[str]] = None,
    ) -> List[MemoryItem]:
        """So'rov bo'yicha eng mos xotiralarni saralab qaytarish"""
        with self._lock:
            items = self.get_memory_items()
            retrieved = MemoryRetriever.retrieve(
                query=query,
                items=items,
                limit=limit,
                task_entities=task_entities,
            )
            for item in retrieved:
                if item.key in self._knowledge and isinstance(self._knowledge[item.key], dict):
                    self._knowledge[item.key]["access_count"] = item.access_count
                    self._knowledge[item.key]["last_used_at"] = item.last_used_at
            return retrieved

    def get_knowledge(self, key: str = None) -> dict:
        """Bilim olish"""
        with self._lock:
            if key:
                if key in self._knowledge:
                    self._knowledge[key]["access_count"] += 1
                    return self._knowledge[key]
                return None
            return self._knowledge.copy()

    def get_knowledge_summary(self) -> str:
        """AI prompt uchun bilimlar xulosasi"""
        with self._lock:
            if not self._knowledge:
                return ""

            lines = []
            for key, data in self._knowledge.items():
                lines.append(f"- {key}: {data['value']}")
            return "\n".join(lines)

    def delete_knowledge(self, key: str) -> bool:
        """Bilimni o'chirish"""
        with self._lock:
            if key in self._knowledge:
                del self._knowledge[key]
                self._save_json(self._knowledge_file, self._knowledge)
                return True
            return False

    def clear_knowledge(self):
        """Barcha saqlangan bilimlarni tozalash"""
        with self._lock:
            self._knowledge.clear()
            self._save_json(self._knowledge_file, self._knowledge)

    # ========== STATISTIKA ==========

    @property
    def stats(self) -> dict:
        """Xotira statistikasi"""
        with self._lock:
            return {
                "kontekst_hajmi": len(self._short_term),
                "suhbatlar_soni": len(self._conversations),
                "bilimlar_soni": len(self._knowledge),
                "profil_toliq": bool(self._profile.get("ism")),
            }

    # ========== ICHKI FUNKSIYALAR ==========

    def _load_json(self, path: str, default):
        """JSON faylni yuklash"""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"JSON yuklash xatolik ({path}): {e}")
        return default

    def _save_json(self, path: str, data):
        """JSON faylga saqlash"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"JSON saqlash xatolik ({path}): {e}")

    def _save_conversations(self):
        """Suhbatlarni faylga saqlash"""
        self._save_json(self._conversations_file, self._conversations)

    def save_all(self):
        """Barchasini faylga saqlash"""
        with self._lock:
            self._save_conversations()
            self._save_json(self._profile_file, self._profile)
            self._save_json(self._knowledge_file, self._knowledge)
            logger.info("AgentMemory: barcha ma'lumotlar saqlandi")


# Global singleton
_memory = None


def get_memory() -> AgentMemory:
    """Global AgentMemory olish (singleton — duplikat yaratmaydi)"""
    global _memory
    if _memory is None:
        _memory = AgentMemory()
    return _memory
