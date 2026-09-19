# ========== agent/identity.py ==========
# Phase 45 — Windows PC Agent Deterministic Device Identity
# Cross-restart stable, hardware-fingerprinted device identity

import os
import json
import socket
import getpass
import platform
import time
import logging
from typing import Dict, Any, Optional

from core.v8.device import DeviceIdentity, DeviceIdentityManager
from core.v8.heartbeat import DeviceState

logger = logging.getLogger("mikasa.agent.identity")


class AgentIdentityManager:
    """
    Windows PC Agent uchun apparat darajasidagi deterministik va barqaror identifikator boshqaruvchisi.
    - Apparat xeshi (fingerprint): MAC, arxitektura va mashina identifikatori orqali hosil qilinadi.
    - Qurilma ID si bir marta generatsiya qilinadi va mahalliy vaultda saqlanadi.
    - Foydalanuvchi nomi yoki kompyuter nomi o'zgarganda ham barqaror saqlanib qoladi.
    """

    def __init__(self, vault_dir: Optional[str] = None):
        self.vault_dir = vault_dir or os.path.join(os.path.expanduser("~"), ".mikasa_agent", "vault")

    def compute_hardware_fingerprint(self) -> str:
        """Apparat xeshini hisoblash (instansiya metodi)"""
        return self.compute_fingerprint()

    def get_or_create_identity(self, friendly_name: Optional[str] = None) -> DeviceIdentity:
        """Qurilma identifikatsiyasini olish yoki yaratish (instansiya metodi)"""
        return self.load_or_create_identity(self.vault_dir, friendly_name=friendly_name)

    @classmethod
    def compute_fingerprint(cls) -> str:
        """Apparat xeshini hisoblash"""
        hostname = socket.gethostname()
        machine = platform.machine()
        mac = DeviceIdentityManager.get_mac_address()
        return DeviceIdentityManager.compute_fingerprint(
            hostname=hostname,
            machine=machine,
            mac=mac
        )

    @classmethod
    def load_or_create_identity(
        cls,
        vault_dir: str,
        override_device_id: Optional[str] = None,
        friendly_name: Optional[str] = None
    ) -> DeviceIdentity:
        """
        Qurilma identifikatsiyasini mahalliy diskdan yuklash yoki yangisini yaratib saqlash.
        """
        os.makedirs(vault_dir, exist_ok=True)
        identity_file = os.path.join(vault_dir, "device_identity.json")

        hostname = socket.gethostname()
        username = getpass.getuser()
        mac = DeviceIdentityManager.get_mac_address()
        machine = platform.machine()
        fingerprint = cls.compute_fingerprint()

        saved_data: Dict[str, Any] = {}
        if os.path.exists(identity_file):
            try:
                with open(identity_file, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
            except Exception as e:
                logger.warning(f"[AgentIdentity] Faylni o'qishda xato: {e}")

        # Deterministic device_id:
        # 1. Override berilgan bo'lsa (masalan testlarda yoki CLI dan)
        # 2. Avval saqlangan device_id bo'lsa
        # 3. Aks holda barqaror apparat xeshi asosida 'win-{fingerprint[:16]}'
        if override_device_id:
            dev_id = str(override_device_id).strip()
        elif saved_data.get("device_id"):
            dev_id = str(saved_data["device_id"]).strip()
        else:
            dev_id = f"win-{fingerprint[:16]}"

        identity = DeviceIdentity(
            device_id=dev_id,
            hostname=hostname,
            username=username,
            os_name=platform.system(),
            os_version=platform.version(),
            os_release=platform.release(),
            architecture=machine,
            mac_address=mac,
            local_ip=DeviceIdentityManager.get_local_ip(),
            fingerprint=fingerprint,
            agent_version="8.0.0",
            mikasa_version="8.0.0",
            status=DeviceState.ONLINE,
            metadata={
                "friendly_name": friendly_name or hostname,
                "platform_type": "windows_pc" if platform.system().lower() == "windows" else "pc"
            }
        )

        # Barqarorlik uchun saqlab qo'yish
        dump_data = identity.to_dict()
        dump_data["hardware_fingerprint"] = fingerprint
        dump_data["enrolled_at"] = saved_data.get("enrolled_at", time.time())
        try:
            with open(identity_file, "w", encoding="utf-8") as f:
                json.dump(dump_data, f, indent=2)
        except Exception as e:
            logger.error(f"[AgentIdentity] Identifikatsiyani saqlashda xato: {e}")

        return identity
