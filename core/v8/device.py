# ========== core/v8/device.py ==========
# Phase 35 — Device Identity & Hardware Grounding

import socket
import getpass
import platform
import uuid
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

from core.v8.heartbeat import DeviceState


@dataclass
class DeviceIdentity:
    """
    Qurilmaning barqaror va deterministik identifikatori.
    """
    device_id: str
    hostname: str
    username: str
    os_name: str
    os_version: str
    os_release: str
    architecture: str
    mac_address: str
    local_ip: str
    fingerprint: str
    agent_version: str = "8.0.0"
    mikasa_version: str = "8.0.0"
    last_seen: Optional[str] = None
    status: DeviceState = DeviceState.OFFLINE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if isinstance(self.status, DeviceState):
            data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceIdentity":
        data = dict(data)
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = DeviceState(data["status"])
            except ValueError:
                data["status"] = DeviceState.OFFLINE
        valid_fields = {
            "device_id", "hostname", "username", "os_name", "os_version",
            "os_release", "architecture", "mac_address", "local_ip",
            "fingerprint", "agent_version", "mikasa_version", "last_seen",
            "status", "metadata"
        }
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class DeviceIdentityManager:
    """
    Qurilma identifikatsiyasini aniqlash va boshqarish.
    """

    @staticmethod
    def get_mac_address() -> str:
        try:
            node = uuid.getnode()
            return ':'.join(['{:02x}'.format((node >> i) & 0xff) for i in range(0, 48, 8)][::-1])
        except Exception:
            return "00:00:00:00:00:00"

    @staticmethod
    def get_local_ip() -> str:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "127.0.0.1"

    @classmethod
    def generate_fingerprint(cls, hostname: str, machine: str, mac: str) -> str:
        raw = f"{hostname.lower().strip()}|{machine.lower().strip()}|{mac.lower().strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def create_local_identity(cls, override_device_id: Optional[str] = None) -> DeviceIdentity:
        hostname = socket.gethostname()
        username = getpass.getuser()
        mac = cls.get_mac_address()
        machine = platform.machine()
        fingerprint = cls.generate_fingerprint(hostname, machine, mac)
        
        dev_id = override_device_id or f"{username}@{hostname}"
        
        return DeviceIdentity(
            device_id=dev_id,
            hostname=hostname,
            username=username,
            os_name=platform.system(),
            os_version=platform.version(),
            os_release=platform.release(),
            architecture=machine,
            mac_address=mac,
            local_ip=cls.get_local_ip(),
            fingerprint=fingerprint,
            agent_version="8.0.0",
            mikasa_version="8.0.0",
            status=DeviceState.ONLINE
        )
