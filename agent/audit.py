# ========== agent/audit.py ==========
# Phase 45 — Windows PC Agent Audit Logger
# Sensitive-data-scrubbed lifecycle audit logging

import time
import logging
from typing import Dict, Any, Optional, List, Callable

from core.v8.events import (
    RemoteEventType,
    RemoteAuditEvent,
    RemoteAuditLogger,
    sanitize_event_data
)

logger = logging.getLogger("mikasa.agent.audit")


class AgentAuditLogger:
    """
    Windows PC Agent tadbirlarini xavfsiz va tozalangan holda qayd qilish.
    Maxfiy kalitlar, tokenlar yoki pairing kodlari aslo loglarga tushmaydi.
    """
    _instance: Optional["AgentAuditLogger"] = None

    def __init__(self):
        self._core_logger = RemoteAuditLogger.get_instance()
        self._listeners: List[Callable[[RemoteAuditEvent], None]] = []
        self._events: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> "AgentAuditLogger":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_listener(self, listener: Callable[[RemoteAuditEvent], None]):
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[RemoteAuditEvent], None]):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def get_events(self) -> List[Dict[str, Any]]:
        """Qayd etilgan tadbirlar nusxasini olish"""
        return list(self._events)

    def clear(self):
        """Xotiradagi tadbirlarni tozalash (testlar uchun)"""
        self._events.clear()

    def log_event(
        self,
        event_type: RemoteEventType,
        device_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> RemoteAuditEvent:
        """Tadbirni tozalash va logga yozish"""
        merged_details = dict(details or {})
        if error:
            merged_details["error"] = error
        safe_details = sanitize_event_data(merged_details)
        event = RemoteAuditEvent(
            event_type=event_type,
            device_id=device_id,
            details=safe_details,
            timestamp=time.time()
        )

        event_dict = {
            "event_type": event_type,
            "device_id": device_id,
            "details": safe_details,
            "error": error,
            "timestamp": event.timestamp
        }
        self._events.append(event_dict)

        if hasattr(self._core_logger, "log_event"):
            self._core_logger.log_event(event)

        for cb in self._listeners:
            try:
                cb(event)
            except Exception:
                pass

        log_level = logging.WARNING if error else logging.INFO
        logger.log(log_level, f"[AgentAudit] {event_type.value}: dev={device_id} | err={error}")
        return event
