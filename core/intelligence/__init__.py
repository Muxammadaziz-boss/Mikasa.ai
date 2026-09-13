# ========== __init__.py ==========
# Mikasa AI 7.x — Intelligence Core Package
# Modular Intelligence Architecture (Context -> Intent -> Reasoning -> Decision -> Tool -> Verification -> Response)

from core.intelligence.types import (
    RiskLevel,
    IntentCategory,
    DecisionType,
    AIRequest,
    AIResponse,
    Intent,
    Decision,
    IntelligenceResponse,
)
from core.intelligence.provider import (
    AIProvider,
    ProviderManager,
)
from core.intelligence.gemini_provider import GeminiProvider
from core.intelligence.openrouter_provider import OpenRouterProvider
from core.intelligence.context import ContextEngine
from core.intelligence.intent import IntentEngine
from core.intelligence.decision import DecisionEngine
from core.intelligence.permission import PermissionEngine
from core.intelligence.orchestrator import IntelligenceOrchestrator
from core.intelligence.adapter import CompatibilityAdapter

__all__ = [
    "RiskLevel",
    "IntentCategory",
    "DecisionType",
    "AIRequest",
    "AIResponse",
    "Intent",
    "Decision",
    "IntelligenceResponse",
    "AIProvider",
    "ProviderManager",
    "GeminiProvider",
    "OpenRouterProvider",
    "ContextEngine",
    "IntentEngine",
    "DecisionEngine",
    "PermissionEngine",
    "IntelligenceOrchestrator",
    "CompatibilityAdapter",
    "get_orchestrator",
]

_orchestrator = None


def get_orchestrator() -> IntelligenceOrchestrator:
    """Global IntelligenceOrchestrator singleton instansiyasini olish"""
    global _orchestrator
    if _orchestrator is None:
        from core.agent_tools import get_registry
        from core.command_dispatcher import CommandDispatcher

        registry = get_registry()
        dispatcher = CommandDispatcher()

        _orchestrator = IntelligenceOrchestrator(
            tool_registry=registry,
            command_dispatcher=dispatcher
        )
    return _orchestrator
