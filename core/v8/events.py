# ========== core/v8/events.py ==========
# Phase 36 — Remote Audit & Structured Event Logging
# Safe, Correlated & Sensitive-Data Redacted

import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger("core.v8.audit")


class RemoteEventType(str, Enum):
    REMOTE_REQUEST_RECEIVED = "REMOTE_REQUEST_RECEIVED"
    REMOTE_REQUEST_AUTHORIZED = "REMOTE_REQUEST_AUTHORIZED"
    REMOTE_REQUEST_DENIED = "REMOTE_REQUEST_DENIED"
    DEVICE_REGISTERED = "DEVICE_REGISTERED"
    DEVICE_AUTH_FAILED = "DEVICE_AUTH_FAILED"
    WOL_REQUESTED = "WOL_REQUESTED"
    WOL_SENT = "WOL_SENT"
    WOL_FAILED = "WOL_FAILED"
    DEVICE_WAKING = "DEVICE_WAKING"
    DEVICE_ONLINE = "DEVICE_ONLINE"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    COMMAND_STARTED = "COMMAND_STARTED"
    COMMAND_COMPLETED = "COMMAND_COMPLETED"
    COMMAND_FAILED = "COMMAND_FAILED"
    COMMAND_TIMEOUT = "COMMAND_TIMEOUT"
    AGENT_CONNECTED = "AGENT_CONNECTED"
    AGENT_DISCONNECTED = "AGENT_DISCONNECTED"


def sanitize_sensitive_string(val: str) -> str:
    """Telegram token, API kalitlar va parollarni xavfsiz niqoblash"""
    if not isinstance(val, str):
        return str(val)
    # Telegram bot token regex-like match: 123456789:ABCdef...
    if ":" in val and len(val) > 20:
        parts = val.split(":")
        if parts[0].isdigit():
            return f"{parts[0]}:***MASKED_TELEGRAM_TOKEN***"
    if val.startswith("sk-") or val.startswith("AIza") or len(val) >= 32:
        return f"{val[:4]}***MASKED_SECRET***{val[-3:] if len(val) > 8 else ''}"
    return val


def sanitize_event_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Tadbir parametrlari ichidagi maxfiy ma'lumotlarni tozalash"""
    cleaned = {}
    sensitive_keys = {"token", "bot_token", "password", "secret", "pairing_token", "auth_header"}
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            cleaned[k] = "***REDACTED***"
        elif isinstance(v, str):
            cleaned[k] = sanitize_sensitive_string(v)
        elif isinstance(v, dict):
            cleaned[k] = sanitize_event_data(v)
        else:
            cleaned[k] = v
    return cleaned


@dataclass
class RemoteAuditEvent:
    event_type: RemoteEventType
    request_id: Optional[str] = None
    device_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "request_id": self.request_id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "details": sanitize_event_data(self.details)
        }


class RemoteAuditLogger:
    """
    Tizimdagi barcha masofaviy amallar auditi.
    Xotirada keshlaydi, loglarga yozadi va xavfsiz formatlaydi.
    """
    _instance: Optional["RemoteAuditLogger"] = None

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._history: List[RemoteAuditEvent] = []
        self._subscribers: List[Callable[[RemoteAuditEvent], None]] = []

    @classmethod
    def get_instance(cls) -> "RemoteAuditLogger":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log(
        self,
        event_type: RemoteEventType,
        request_id: Optional[str] = None,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **details
    ) -> RemoteAuditEvent:
        clean_details = sanitize_event_data(details)
        event = RemoteAuditEvent(
            event_type=event_type,
            request_id=request_id,
            device_id=device_id,
            user_id=user_id,
            timestamp=time.time(),
            details=clean_details
        )
        self._history.append(event)
        if len(self._history) > self.max_history:
            self._history.pop(0)

        log_msg = (
            f"[V8_AUDIT] {event_type.value} | req={request_id or '-'} | "
            f"dev={device_id or '-'} | user={user_id or '-'} | {clean_details}"
        )
        warning_events = (
            RemoteEventType.REMOTE_REQUEST_DENIED,
            RemoteEventType.DEVICE_AUTH_FAILED,
            RemoteEventType.COMMAND_FAILED,
            RemoteEventType.WOL_FAILED
        )
        if event_type in warning_events:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        for sub in self._subscribers:
            try:
                sub(event)
            except Exception as e:
                logger.error(f"Audit subscriber error: {e}")

        return event

    def get_history(
        self,
        event_type: Optional[RemoteEventType] = None,
        device_id: Optional[str] = None,
        limit: int = 50
    ) -> List[RemoteAuditEvent]:
        res = self._history
        if event_type:
            res = [e for e in res if e.event_type == event_type]
        if device_id:
            res = [e for e in res if e.device_id == device_id]
        return res[-limit:]

    def subscribe(self, subscriber: Callable[[RemoteAuditEvent], None]):
        self._subscribers.append(subscriber)

    def clear(self):
        self._history.clear()
