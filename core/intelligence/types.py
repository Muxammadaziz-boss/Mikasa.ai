# ========== types.py ==========
# Mikasa AI 7.x — Intelligence Core Types
# Normalized Data Structures for Context, Provider, Intent, Decision and Response

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IntentCategory(str, Enum):
    CONVERSATION = "conversation"
    COMMAND = "command"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    TOOL_REQUEST = "tool_request"
    ERROR = "error"


class DecisionType(str, Enum):
    ANSWER = "answer"
    COMMAND = "command"
    TOOL = "tool"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    ERROR = "error"


@dataclass
class AIRequest:
    """Providerga yuboriladigan normalizatsiya qilingan so'rov"""
    message: str
    system_context: Dict[str, Any] = field(default_factory=dict)
    conversation: List[Dict[str, str]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "system_context": self.system_context,
            "conversation": self.conversation,
            "memory": self.memory,
            "tools": self.tools,
            "metadata": self.metadata,
        }


@dataclass
class AIResponse:
    """AI provayderidan qaytadigan normalizatsiya qilingan javob"""
    provider: str
    model: str
    type: str = "answer"  # answer, command, clarification, confirmation, error
    content: str = ""
    intent: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    success: bool = True
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "type": self.type,
            "content": self.content,
            "intent": self.intent,
            "params": self.params,
            "usage": self.usage,
            "metadata": self.metadata,
            "success": self.success,
            "error_code": self.error_code,
        }


@dataclass
class Intent:
    """Aniqlangan niyat (Intent) ifodasi"""
    name: str
    category: IntentCategory = IntentCategory.CONVERSATION
    confidence: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)
    source: str = "llm"  # "llm", "local", "heuristic"
    requires_context: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value if isinstance(self.category, IntentCategory) else str(self.category),
            "confidence": self.confidence,
            "params": self.params,
            "source": self.source,
            "requires_context": self.requires_context,
        }


@dataclass
class Decision:
    """Qaror qabul qilish (Decision) qatlami chiqishi"""
    type: DecisionType
    content: str = ""
    intent: Optional[Intent] = None
    tool_name: Optional[str] = None
    tool_params: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    clarification_question: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value if isinstance(self.type, DecisionType) else str(self.type),
            "content": self.content,
            "intent": self.intent.to_dict() if self.intent else None,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level),
            "requires_confirmation": self.requires_confirmation,
            "confirmation_prompt": self.confirmation_prompt,
            "clarification_question": self.clarification_question,
        }


@dataclass
class IntelligenceResponse:
    """Intelligence Core ning yakuniy xulosaviy javobi"""
    type: str  # "answer", "command", "tool", "clarification", "confirmation", "error"
    content: str
    intent: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    tool_executed: Optional[str] = None
    tool_result: Optional[Any] = None
    verified: bool = True
    provider: str = "local"
    model: str = "none"
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "intent": self.intent,
            "params": self.params,
            "tool_executed": self.tool_executed,
            "tool_result": self.tool_result,
            "verified": self.verified,
            "provider": self.provider,
            "model": self.model,
            "metadata": self.metadata,
            "error_code": self.error_code,
        }
