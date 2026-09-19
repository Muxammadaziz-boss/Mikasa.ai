# ========== agent/__init__.py ==========
# Phase 45 — Production Windows PC Agent Package
"""
Mikasa AI v8.0.0 — Production-Grade Windows PC Agent
Cryptographic authentication, persistent identity, secure transport, and heartbeat management.
"""

from agent.config import AgentConfig, load_config
from agent.identity import AgentIdentityManager
from agent.crypto import AgentCrypto, WindowsCredentialStore, MockCredentialStore
from agent.audit import AgentAuditLogger
from agent.recovery import CrashRecoveryManager
from agent.transport import SecureTransport
from agent.enrollment import AgentEnrollment
from agent.auth import AgentAuth
from agent.heartbeat import AgentHeartbeat, AgentState
from agent.startup import WindowsStartupManager
from agent.lifecycle import AgentLifecycleManager, calculate_backoff
from agent.windows_agent import WindowsAgent

__all__ = [
    "AgentConfig",
    "load_config",
    "AgentIdentityManager",
    "AgentCrypto",
    "WindowsCredentialStore",
    "MockCredentialStore",
    "AgentAuditLogger",
    "CrashRecoveryManager",
    "SecureTransport",
    "AgentEnrollment",
    "AgentAuth",
    "AgentHeartbeat",
    "AgentState",
    "WindowsStartupManager",
    "AgentLifecycleManager",
    "calculate_backoff",
    "WindowsAgent",
]
