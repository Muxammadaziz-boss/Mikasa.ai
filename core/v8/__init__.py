# ========== core/v8/__init__.py ==========
# Mikasa AI v8.0.0 — Phase 37: Secure Remote Session Authentication
# Package initialization, versioning & exports

from core.v8.device import (
    DeviceIdentity,
    DeviceIdentityManager,
    DevicePairingRecord,
    DeviceRegistry
)
from core.v8.heartbeat import DeviceState, HeartbeatPayload, HeartbeatManager
from core.v8.wol import (
    WakeOnLanManager,
    create_magic_packet,
    WakeRelay,
    LocalBroadcastRelay
)
from core.v8.envelope import (
    RemoteCommandEnvelope,
    EnvelopeManager,
    RateLimiter
)
from core.v8.pc_agent import MikasaPCAgent
from core.v8.telegram_gateway import (
    TelegramRemoteGateway,
    TelegramTransport,
    MockTelegramTransport,
    AiohttpTelegramTransport
)
from core.v8.auth_session import (
    RemoteAuthSession,
    SessionManager,
    RemoteAuthEngine
)
from core.v8.remote_orchestrator import RemoteOrchestrator
from core.v8.planning_remote import create_remote_wake_and_verify_dag
from core.v8.events import (
    RemoteEventType,
    RemoteAuditLogger,
    RemoteAuditEvent,
    sanitize_sensitive_string,
    sanitize_event_data
)

__version__ = "8.0.0"
PHASE = 37

__all__ = [
    "__version__",
    "PHASE",
    # Device
    "DeviceIdentity",
    "DeviceIdentityManager",
    "DevicePairingRecord",
    "DeviceRegistry",
    # Heartbeat
    "DeviceState",
    "HeartbeatPayload",
    "HeartbeatManager",
    # Wake-on-LAN
    "WakeOnLanManager",
    "create_magic_packet",
    "WakeRelay",
    "LocalBroadcastRelay",
    # Envelope & Security
    "RemoteCommandEnvelope",
    "EnvelopeManager",
    "RateLimiter",
    # Agent & Gateway
    "MikasaPCAgent",
    "TelegramRemoteGateway",
    "TelegramTransport",
    "MockTelegramTransport",
    "AiohttpTelegramTransport",
    # Session & Authentication
    "RemoteAuthSession",
    "SessionManager",
    "RemoteAuthEngine",
    # Orchestrator & DAG
    "RemoteOrchestrator",
    "create_remote_wake_and_verify_dag",
    # Audit & Events
    "RemoteEventType",
    "RemoteAuditLogger",
    "RemoteAuditEvent",
    "sanitize_sensitive_string",
    "sanitize_event_data",
]
