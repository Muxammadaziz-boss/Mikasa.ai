# ========== core/v8/__init__.py ==========
# Mikasa AI v8.0.0 — Phase 38: Mikasa Online Remote Control + User Permission Center
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
from core.v8.user_linking import (
    PairingToken,
    UserDeviceLink,
    UserLinkingStore
)
from core.v8.telegram_identity import (
    TelegramIdentity,
    TelegramLinkRequest,
    UserTelegramLink,
    TelegramIdentityManager
)
from core.v8.universal_bot import UniversalTelegramBot
from core.v8.account_device import (
    MikasaUser,
    Device,
    UserDeviceLink as AccountUserDeviceLink,
    UserDeviceContext,
    AccountDeviceManager
)
from core.v8.account_auth import (
    AccountAuthManager,
    AccountSession,
    PasswordManager,
    VerificationToken,
    AuthRateLimiter,
    EmailVerificationProvider,
    MockEmailVerificationProvider
)
from core.v8.permission_center import (
    PermissionCategory,
    PermissionDefinition,
    UserPermissionProfile,
    PermissionStore,
    STANDARD_PERMISSIONS
)
from core.v8.remote_tools import (
    RemoteToolDefinition,
    RemoteToolRegistry
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
PHASE = 41

__all__ = [
    "__version__",
    "PHASE",
    # Account & Auth (Phase 41)
    "AccountAuthManager",
    "AccountSession",
    "PasswordManager",
    "VerificationToken",
    "AuthRateLimiter",
    "EmailVerificationProvider",
    "MockEmailVerificationProvider",
    # Device & Accounts (Phase 40)
    "MikasaUser",
    "Device",
    "AccountDeviceManager",
    "UserDeviceContext",
    # Device (Phase 35)
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
    # User Linking & Permission Center (Phase 38)
    "TelegramIdentity",
    "PairingToken",
    "UserDeviceLink",
    "UserLinkingStore",
    "PermissionCategory",
    "PermissionDefinition",
    "UserPermissionProfile",
    "PermissionStore",
    "STANDARD_PERMISSIONS",
    # Universal Telegram Bot & Identity (Phase 39)
    "TelegramLinkRequest",
    "UserTelegramLink",
    "TelegramIdentityManager",
    "UniversalTelegramBot",
    # Remote Tools (Phase 38)
    "RemoteToolDefinition",
    "RemoteToolRegistry",
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
