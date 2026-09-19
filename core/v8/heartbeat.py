# ========== core/v8/heartbeat.py ==========
# Phase 35 — Heartbeat & State Lifecycle Management

import time
import logging
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Callable, List

logger = logging.getLogger("core.v8.heartbeat")


class DeviceState(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WAKING = "waking"
    CONNECTING = "connecting"
    READY = "ready"
    ERROR = "error"


@dataclass
class HeartbeatPayload:
    device_id: str
    timestamp: float
    agent_version: str = "8.0.0"
    state: DeviceState = DeviceState.ONLINE
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(self.state, DeviceState):
            d["state"] = self.state.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HeartbeatPayload":
        state_val = data.get("state", DeviceState.ONLINE)
        if isinstance(state_val, str):
            try:
                state_val = DeviceState(state_val)
            except ValueError:
                state_val = DeviceState.ONLINE
        return cls(
            device_id=data["device_id"],
            timestamp=float(data.get("timestamp", time.time())),
            agent_version=data.get("agent_version", "8.0.0"),
            state=state_val,
            metrics=data.get("metrics", {})
        )


class HeartbeatManager:
    """
    Heartbeat monitoring va qurilma holatini aniqlash (Online / Offline / Waking).
    """
    _default_instance: Optional["HeartbeatManager"] = None

    def __init__(self, stale_timeout: float = 60.0):
        self.stale_timeout = stale_timeout
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._listeners: List[Callable[[str, DeviceState, DeviceState], None]] = []

    @classmethod
    def get_default_instance(cls) -> "HeartbeatManager":
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance

    def register_device(
        self,
        device_id: str,
        initial_state: DeviceState = DeviceState.OFFLINE,
        info: Optional[Dict[str, Any]] = None
    ):
        if device_id not in self._devices:
            self._devices[device_id] = {
                "state": initial_state,
                "last_heartbeat": 0.0,
                "info": info or {},
                "metrics": {},
                "heartbeat_count": 0
            }
        else:
            if info:
                self._devices[device_id]["info"].update(info)

    def record_heartbeat(self, payload: HeartbeatPayload) -> bool:
        dev_id = payload.device_id
        if dev_id not in self._devices:
            self.register_device(dev_id, initial_state=payload.state)

        dev_entry = self._devices[dev_id]
        old_state = dev_entry["state"]
        new_state = payload.state

        dev_entry["last_heartbeat"] = payload.timestamp
        dev_entry["state"] = new_state
        dev_entry["metrics"] = payload.metrics
        dev_entry["heartbeat_count"] += 1

        if old_state != new_state:
            self._notify_state_change(dev_id, old_state, new_state)
        return True

    def set_device_state(self, device_id: str, new_state: DeviceState):
        if device_id in self._devices:
            old_state = self._devices[device_id]["state"]
            self._devices[device_id]["state"] = new_state
            if old_state != new_state:
                self._notify_state_change(device_id, old_state, new_state)

    def check_timeouts(self, current_time: Optional[float] = None) -> List[str]:
        now = current_time if current_time is not None else time.time()
        went_offline = []
        for dev_id, entry in self._devices.items():
            if entry["state"] in (DeviceState.ONLINE, DeviceState.READY, DeviceState.CONNECTING):
                if entry["last_heartbeat"] > 0 and (now - entry["last_heartbeat"]) > self.stale_timeout:
                    old_state = entry["state"]
                    entry["state"] = DeviceState.OFFLINE
                    went_offline.append(dev_id)
                    self._notify_state_change(dev_id, old_state, DeviceState.OFFLINE)
        return went_offline

    def get_device_state(self, device_id: str) -> DeviceState:
        if device_id in self._devices:
            return self._devices[device_id]["state"]
        return DeviceState.OFFLINE

    def is_online(self, device_id: str) -> bool:
        return self.get_device_state(device_id) in (DeviceState.ONLINE, DeviceState.READY)

    def add_state_listener(self, listener: Callable[[str, DeviceState, DeviceState], None]):
        self._listeners.append(listener)

    def _notify_state_change(self, device_id: str, old_state: DeviceState, new_state: DeviceState):
        logger.info(f"[Heartbeat] Qurilma '{device_id}': {old_state.value} -> {new_state.value}")
        for listener in self._listeners:
            try:
                listener(device_id, old_state, new_state)
            except Exception as e:
                logger.error(f"Listener error: {e}")
