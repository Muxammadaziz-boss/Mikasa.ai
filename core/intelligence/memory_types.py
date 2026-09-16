# ========== memory_types.py ==========
# Mikasa AI 7.x — Memory & Context Intelligence Types
# Normalized Memory Item, Categories, Confidence & Active Task Context

import uuid
import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class MemoryType(str, Enum):
    FACT = "fact"                  # Foydalanuvchi taqdim etgan barqaror faktlar
    PREFERENCE = "preference"      # Foydalanuvchi xohish-istaklari va didi
    CONVERSATION = "conversation"  # Suhbatdagi muhim mavzu yoki xulosa
    TASK = "task"                  # Davom etayotgan yoki faol vazifa ma'lumotlari
    NOTE = "note"                  # Foydalanuvchi eslab qolishni so'ragan eslatma
    WORK_CONTEXT = "work_context"  # Ish va loyiha muhiti konteksti


class MemorySource(str, Enum):
    USER = "user"                  # Foydalanuvchi tomonidan to'g'ridan-to'g'ri aytilgan
    CONVERSATION = "conversation"  # Suhbat mantiqidan ajratib olingan
    SYSTEM = "system"              # Tizim tomonidan qayd etilgan


class MemoryConfidence(float, Enum):
    HIGH = 1.0                     # Aniq, bevosita foydalanuvchi bayonoti
    MEDIUM = 0.6                   # Mantiqiy xulosa qilingan xohish/afzallik
    LOW = 0.3                      # Model taxmini (saqlanmasligi kerak)


@dataclass
class MemoryItem:
    """Normalizatsiya qilingan xotira birligi"""
    key: str
    content: str
    type: MemoryType = MemoryType.FACT
    source: MemorySource = MemorySource.USER
    importance: float = 0.5        # 0.0 dan 1.0 gacha
    confidence: float = 1.0        # 0.0 dan 1.0 gacha
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    last_used_at: Optional[str] = None
    access_count: int = 0
    superseded_by: Optional[str] = None   # Ziddiyatli yangi xotira bilan almashtirilgan bo'lsa
    pinned: bool = False                  # Foydalanuvchi tomonidan qadalgan/muhim belgilangan
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_active(self) -> bool:
        """Xotira faolmi (bekor qilinmaganmi)? Ziddiyatli xotiralar superseded_by ga ega"""
        return self.superseded_by is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "content": self.content,
            "value": self.content,  # AgentMemory bilan 100% orqaga qaytuvchanlik
            "type": self.type.value if isinstance(self.type, MemoryType) else str(self.type),
            "source": self.source.value if isinstance(self.source, MemorySource) else str(self.source),
            "importance": self.importance,
            "confidence": self.confidence,
            "is_active": self.is_active(),
            "created_at": self.created_at,
            "saved_at": self.created_at,  # Legacy field
            "updated_at": self.updated_at,
            "last_used_at": self.last_used_at,
            "access_count": self.access_count,
            "superseded_by": self.superseded_by,
            "pinned": self.pinned,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, key_or_data: Any, data: Any = None) -> "MemoryItem":
        """Mavjud agent_knowledge.json yoki yangi formatdan MemoryItem yaratish"""
        if data is None and isinstance(key_or_data, dict):
            data = key_or_data
            key = str(data.get("key", ""))
        else:
            key = str(key_or_data)

        if isinstance(data, str):
            return cls(key=key, content=data)

        if not isinstance(data, dict):
            return cls(key=key, content=str(data))

        content = data.get("content") or data.get("value") or ""
        type_str = data.get("type", "fact")
        try:
            m_type = MemoryType(type_str)
        except ValueError:
            m_type = MemoryType.FACT

        src_str = data.get("source", "user")
        try:
            m_src = MemorySource(src_str)
        except ValueError:
            m_src = MemorySource.USER

        return cls(
            key=key,
            content=content,
            type=m_type,
            source=m_src,
            importance=float(data.get("importance", 0.5)),
            confidence=float(data.get("confidence", 1.0)),
            id=data.get("id") or str(uuid.uuid4())[:8],
            created_at=data.get("created_at") or data.get("saved_at") or datetime.datetime.now().isoformat(),
            updated_at=data.get("updated_at") or datetime.datetime.now().isoformat(),
            last_used_at=data.get("last_used_at"),
            access_count=int(data.get("access_count", 0)),
            superseded_by=data.get("superseded_by"),
            pinned=bool(data.get("pinned", False)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ActiveTaskContext:
    """Faol ko'p qadamli vazifa konteksti (suhbat davomiyligi uchun)"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: str = ""
    entities: List[str] = field(default_factory=list)  # Masalan: ["telegram", "github", "python"]
    last_action: Optional[str] = None
    last_result: Optional[str] = None
    status: str = "active"  # "active", "completed", "idle"
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "entities": self.entities,
            "last_action": self.last_action,
            "last_result": self.last_result,
            "status": self.status,
            "updated_at": self.updated_at,
        }
