# ========== memory_retriever.py ==========
# Mikasa AI 7.x — Deterministic Memory Retrieval & Multi-Factor Ranking
# High-Relevance Context Scoring without Heavy External Vector Databases

import re
import datetime
import logging
from typing import List, Optional, Dict, Any, Tuple
from core.intelligence.memory_types import MemoryItem, MemoryType

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """
    Xotiralarni deterministik va ko'p omilli (multi-factor) tartiblash asosida
    eng mos (relevant) ma'lumotlarni ajratib oluvchi dvigatel.
    """

    # Xotira turlari bo'yicha koeffitsiyentlar
    TYPE_WEIGHTS = {
        MemoryType.TASK: 1.25,
        MemoryType.PREFERENCE: 1.15,
        MemoryType.FACT: 1.00,
        MemoryType.NOTE: 0.95,
        MemoryType.CONVERSATION: 0.80,
    }

    @staticmethod
    def _tokenize(text: str) -> set:
        """Matnni tozalangan so'zlar to'plamiga ajratish"""
        if not text:
            return set()
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        return {w for w in clean.split() if len(w) > 1}

    @classmethod
    def calculate_relevance_score(
        cls,
        query_tokens: set,
        item: MemoryItem,
        task_entities: Optional[List[str]] = None
    ) -> float:
        """
        Bitta xotira birligi uchun kompozit reyting (0.0 dan 1.0+ gacha) hisoblash:
        1. Leksik moslik (Lexical overlap) — 40%
        2. Muhimlik (Importance) — 20%
        3. Ishonchlilik (Confidence) — 15%
        4. Yangilik / Vaqt omili (Recency) — 15%
        5. Xotira turi og'irligi (Type weight) — 10%
        6. Faol vazifa bog'liqligi (Task entity bonus)
        7. Qadalganlik bonusi (Pinned bonus: +0.35)
        """
        # Faol bo'lmagan (ziddiyatda yutqazgan) xotiralar o'tkazib yuboriladi
        active = item.is_active() if callable(getattr(item, "is_active", None)) else bool(getattr(item, "is_active", True))
        if not active:
            return -1.0

        if isinstance(query_tokens, str):
            query_tokens = cls._tokenize(query_tokens)

        item_text = f"{item.key} {item.content}"
        item_tokens = cls._tokenize(item_text)

        if not query_tokens:
            lexical_sim = 0.2  # Agar so'rov bo'sh bo'lsa umumiy fond
        else:
            intersection = query_tokens.intersection(item_tokens)
            lexical_sim = len(intersection) / max(1, len(query_tokens))

        # Faol vazifa ob'ektlari (entities) bonusi
        task_bonus = 0.0
        if task_entities:
            for ent in task_entities:
                if ent.lower() in item_text.lower():
                    task_bonus += 0.25

        # Pinned memory bonusi
        pinned_bonus = 0.35 if getattr(item, "pinned", False) else 0.0

        # Recency (vaqt) omili: 30 kun ichida yaratilgan/ishlatilgan bo'lsa yuqori ball
        recency_score = 0.5
        try:
            timestamp_str = item.last_used_at or item.updated_at or item.created_at
            item_time = datetime.datetime.fromisoformat(timestamp_str)
            now = datetime.datetime.now()
            age_days = (now - item_time).total_seconds() / 86400.0
            recency_score = max(0.1, min(1.0, 1.0 - (age_days / 30.0)))
        except Exception:
            pass

        # Xotira turi og'irligi
        type_w = cls.TYPE_WEIGHTS.get(item.type, 1.0)

        # Kompozit ball hisoblash
        base_score = (
            (lexical_sim * 0.40) +
            (item.importance * 0.20) +
            (item.confidence * 0.15) +
            (recency_score * 0.15)
        ) * type_w

        final_score = base_score + task_bonus + pinned_bonus
        return round(final_score, 4)

    @classmethod
    def retrieve_with_explanation(
        cls,
        query: str,
        items: List[MemoryItem],
        limit: int = 6,
        task_entities: Optional[List[str]] = None,
        min_score: float = 0.05
    ) -> Tuple[List[MemoryItem], List[Dict[str, Any]]]:
        """
        Eng mos xotiralarni ajratish va har biri uchun tushunarli sabab (explainability) qaytarish
        """
        if not items:
            return [], []

        query_tokens = cls._tokenize(query)
        scored_items = []

        for item in items:
            if not item.is_active():
                continue

            item_text = f"{item.key} {item.content}"
            item_tokens = cls._tokenize(item_text)
            matched_terms = query_tokens.intersection(item_tokens) if query_tokens else set()

            task_bonus = 0.0
            matched_entities = []
            if task_entities:
                for ent in task_entities:
                    if ent.lower() in item_text.lower():
                        task_bonus += 0.25
                        matched_entities.append(ent)

            pinned_bonus = 0.35 if getattr(item, "pinned", False) else 0.0

            recency_score = 0.5
            try:
                timestamp_str = item.last_used_at or item.updated_at or item.created_at
                item_time = datetime.datetime.fromisoformat(timestamp_str)
                now = datetime.datetime.now()
                age_days = (now - item_time).total_seconds() / 86400.0
                recency_score = max(0.1, min(1.0, 1.0 - (age_days / 30.0)))
            except Exception:
                pass

            lexical_sim = (len(matched_terms) / max(1, len(query_tokens))) if query_tokens else 0.2
            type_w = cls.TYPE_WEIGHTS.get(item.type, 1.0)

            base_score = (
                (lexical_sim * 0.40) +
                (item.importance * 0.20) +
                (item.confidence * 0.15) +
                (recency_score * 0.15)
            ) * type_w

            final_score = round(base_score + task_bonus + pinned_bonus, 4)

            if final_score >= min_score:
                reasons = []
                if matched_terms:
                    reasons.append(f"So'rovingizdagi so'zlar mos keldi: {', '.join(sorted(list(matched_terms))[:3])}")
                if matched_entities:
                    reasons.append(f"Faol vazifadagi '{matched_entities[0]}' ob'ektiga bog'liq")
                if pinned_bonus > 0:
                    reasons.append("Siz tomondan muhim deb qadalgan (pinned)")
                if not reasons:
                    reasons.append("Umumiy ahamiyat va yangilik ko'rsatkichi yuqori")

                user_reason = "; ".join(reasons)

                details_dict = {
                    "matched_terms": list(matched_terms),
                    "task_bonus": task_bonus,
                    "pinned": bool(getattr(item, "pinned", False)),
                    "lexical_sim": round(lexical_sim, 3),
                    "importance": item.importance,
                    "confidence": item.confidence,
                    "recency": round(recency_score, 3),
                    "type_weight": type_w,
                }
                explanation = {
                    "memory_id": item.id,
                    "key": item.key,
                    "score": final_score,
                    "type": item.type.value if hasattr(item.type, "value") else str(item.type),
                    "matched_terms": list(matched_terms),
                    "task_bonus": task_bonus > 0,
                    "pinned": bool(getattr(item, "pinned", False)),
                    "reason": user_reason,
                    "details": details_dict,
                    "debug_details": details_dict,
                }
                scored_items.append((final_score, item, explanation))

        scored_items.sort(key=lambda x: x[0], reverse=True)

        selected_items = [item for _, item, _ in scored_items[:limit]]
        selected_explanations = [exp for _, _, exp in scored_items[:limit]]

        now_iso = datetime.datetime.now().isoformat()
        for item in selected_items:
            item.last_used_at = now_iso
            item.access_count += 1

        logger.debug(f"MemoryRetriever: {len(items)} ta xotiradan {len(selected_items)} ta ajratildi (limit={limit})")
        return selected_items, selected_explanations

    @classmethod
    def retrieve(
        cls,
        query: str,
        items: List[MemoryItem],
        limit: int = 6,
        task_entities: Optional[List[str]] = None,
        min_score: float = 0.05
    ) -> List[MemoryItem]:
        """So'rov bo'yicha eng mos xotiralarni saralash va chegaralangan sonda qaytarish"""
        selected, _ = cls.retrieve_with_explanation(
            query=query,
            items=items,
            limit=limit,
            task_entities=task_entities,
            min_score=min_score
        )
        return selected

