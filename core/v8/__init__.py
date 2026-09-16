# ========== core/v8/__init__.py ==========
# Mikasa AI v8.0.0 — Phase 35: Remote PC Control Architecture
# Package initialization, versioning & exports

__version__ = "8.0.0"
PHASE = 35

from core.v8.device import DeviceIdentity, DeviceIdentityManager
from core.v8.heartbeat import DeviceState, HeartbeatPayload, HeartbeatManager
from core.v8.wol import WakeOnLanManager, create_magic_packet, WakeRelay, LocalBroadcastRelay
from core.v8.envelope import RemoteCommandEnvelope, EnvelopeManager
from core.v8.pc_agent import MikasaPCAgent
from core.v8.telegram_gateway import TelegramRemoteGateway
from core.v8.planning_remote import create_remote_wake_and_verify_dag

__all__ = [
    "__version__",
    "PHASE",
    "DeviceIdentity",
    "DeviceIdentityManager",
    "DeviceState",
    "HeartbeatPayload",
    "HeartbeatManager",
    "WakeOnLanManager",
    "create_magic_packet",
    "WakeRelay",
    "LocalBroadcastRelay",
    "RemoteCommandEnvelope",
    "EnvelopeManager",
    "MikasaPCAgent",
    "TelegramRemoteGateway",
    "create_remote_wake_and_verify_dag",
]
