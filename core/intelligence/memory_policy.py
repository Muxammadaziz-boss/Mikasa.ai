# ========== memory_policy.py ==========
# Mikasa AI 7.x — Memory Write Policy, Sensitive Scrubbing & Conflict Resolution
# Prevents Prompt Injection, Blocks Secrets & Controls Deduplication and Conflicts

import re
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List
from core.intelligence.memory_types import (
    MemoryItem,
    MemoryType,
    MemorySource,
    MemoryConfidence,
)

logger = logging.getLogger(__name__)


@dataclass
class PolicyDecision:
    """Xotira yozish siyosati qarori"""
    allowed: bool
    reason: str
    is_duplicate: bool = False
    existing_key: Optional[str] = None
    sanitized_content: str = ""
    confidence: float = 1.0


class MemoryPolicy:
    """
    Xotira yozish xavfsizligi, filtrlash va ziddiyatlarni hal qilish siyosati.
    """

    # Maxfiy ma'lumotlar shablonlari (API keys, tokens, passwords)
    SENSITIVE_PATTERNS = [
        re.compile(r"AIza[0-9A-Za-z-_]{30,}"),               # Google Gemini API key
        re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),              # OpenAI / OpenRouter key
        re.compile(r"ghp_[a-zA-Z0-9]{30,}"),                # GitHub personal token
        re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.I),# Bearer token
        re.compile(r"(?:parol|password|secret|token|api_key)\s*[:=]\s*['\"]?([^\s'\"]{6,})", re.I),
    ]

    # Prompt Injection xurujlari shablonlari (Memory is DATA, never instructions!)
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions", re.I),
        re.compile(r"avvalgi\s+barcha\s+ko'rsatmalarni\s+bekor\s+qil", re.I),
        re.compile(r"barcha\s+qoidalarni\s+unut", re.I),
        re.compile(r"system\s*:\s*", re.I),
        re.compile(r"system_prompt", re.I),
        re.compile(r"run\s+(?:shutdown|restart|rm\s+-rf)", re.I),
    ]

    @classmethod
    def contains_sensitive_data(cls, text: str) -> bool:
        """Matnda maxfiy kalit, token yoki parol borligini tekshirish"""
        if not text:
            return False
        for pattern in cls.SENSITIVE_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def sanitize_for_prompt_injection(cls, text: str) -> str:
        """Prompt Injection xurujlarini zararsizlantirish"""
        if not text:
            return ""
        sanitized = text
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(sanitized):
                logger.warning(f"Xotira xavfsizligi: Prompt injection shabloni zararsizlantirildi: {pattern.pattern}")
                sanitized = pattern.sub("[BLOCKED_INSTRUCTION]", sanitized)
        return sanitized.strip()

    @classmethod
    def evaluate_write(
        cls,
        key: str,
        content: str,
        source: MemorySource = MemorySource.USER,
        existing_knowledge: Optional[Dict[str, Any]] = None
    ) -> PolicyDecision:
        """
        Xotirani saqlash mumkinligini qat'iy tekshirish:
        1. Maxfiy ma'lumotlarni rad etish (API keys, passwords).
        2. Prompt injection xurujlarini filtrlash.
        3. Duplikatlarni aniqlash.
        4. Ishonchlilik darajasini belgilash.
        """
        combined = f"{key} {content}"

        # 1. Maxfiy ma'lumotlar tekshiruvi
        if cls.contains_sensitive_data(combined):
            logger.warning(f"Xavfsizlik: Xotiraga maxfiy ma'lumot saqlash urinishi rad etildi (key='{key}')")
            return PolicyDecision(
                allowed=False,
                reason="SENSITIVE_DATA_REJECTED",
                sanitized_content=""
            )

        # 2. Prompt injection filtratsiyasi
        sanitized_content = cls.sanitize_for_prompt_injection(content)
        sanitized_key = cls.sanitize_for_prompt_injection(key)

        # 3. Bo'sh qiymatlarni rad etish
        if not sanitized_key.strip() or not sanitized_content.strip():
            return PolicyDecision(
                allowed=False,
                reason="EMPTY_CONTENT",
                sanitized_content=""
            )

        # 4. Duplikat va ziddiyat tekshiruvi
        is_duplicate = False
        duplicate_key = None

        if existing_knowledge:
            norm_key = sanitized_key.lower().strip()
            norm_content = sanitized_content.lower().strip()

            for ex_key, ex_val in existing_knowledge.items():
                val_text = ex_val.get("value", "") if isinstance(ex_val, dict) else str(ex_val)
                norm_ex_key = str(ex_key).lower().strip()
                norm_ex_val = val_text.lower().strip()

                # Aniq bir xil kalit va bir xil mazmun
                if norm_key == norm_ex_key and norm_content == norm_ex_val:
                    is_duplicate = True
                    duplicate_key = ex_key
                    break

                # Mazmuni bir xil bo'lgan yaqin kalitlar (masalan: "sevimli_rang" va "yoqtirgan_rang")
                if norm_content == norm_ex_val and (norm_key in norm_ex_key or norm_ex_key in norm_key):
                    is_duplicate = True
                    duplicate_key = ex_key
                    break

        confidence = MemoryConfidence.HIGH.value if source == MemorySource.USER else MemoryConfidence.MEDIUM.value

        return PolicyDecision(
            allowed=True,
            reason="ALLOWED",
            is_duplicate=is_duplicate,
            existing_key=duplicate_key,
            sanitized_content=sanitized_content,
            confidence=confidence
        )

    @classmethod
    def resolve_conflict(
        cls,
        new_item: MemoryItem,
        existing_items: List[MemoryItem]
    ) -> List[MemoryItem]:
        """
        Ziddiyatli xotiralarni xavfsiz hal qilish:
        Agar yangi aniq foydalanuvchi ma'lumoti kelgan bo'lsa (masalan: oldin 'dark mode', endi 'light mode'),
        yangi ma'lumot g'olib bo'ladi va eski ma'lumot superseded_by bilan belgilanadi.
        """
        updated_list = []
        norm_new_key = new_item.key.lower().strip()

        for old in existing_items:
            norm_old_key = old.key.lower().strip()
            # Bir xil yoki o'zaro qarama-qarshi kalit
            if norm_new_key == norm_old_key and old.id != new_item.id:
                if new_item.confidence >= old.confidence:
                    logger.info(f"Xotira ziddiyati hal qilindi: '{old.key}' ({old.content}) yangi qiymat ({new_item.content}) bilan almashtirildi")
                    old.superseded_by = new_item.id
            updated_list.append(old)

        return updated_list

    @classmethod
    def classify_type(cls, key: str, content: str) -> MemoryType:
        """Kalit va mazmunga qarab xotira turini avtomatik aniqlash"""
        combined = f"{key} {content}".lower()

        # Preference patterns
        pref_keywords = ["yoqtir", "sevaman", "afzal", "ishlataman", "mavzu", "tema", "dizayn", "uslub", "preference"]
        if any(k in combined for k in pref_keywords):
            return MemoryType.PREFERENCE

        # Task patterns
        task_keywords = ["vazifa", "loyiha", "maqsad", "qilyapman", "ishlayapman", "task", "progress", "jarayon"]
        if any(k in combined for k in task_keywords):
            return MemoryType.TASK

        # Note patterns
        note_keywords = ["eslatma", "eslat", "eslab_qol", "eslab qol", "yodda tut", "note"]
        if any(k in combined for k in note_keywords):
            return MemoryType.NOTE

        # Conversation patterns
        conv_keywords = ["suhbat", "mavzusi", "muhokama", "xulosa", "gaplashdik"]
        if any(k in combined for k in conv_keywords):
            return MemoryType.CONVERSATION

        return MemoryType.FACT

