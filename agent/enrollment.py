# ========== agent/enrollment.py ==========
# Phase 45 — Windows PC Agent Device Enrollment Client
# 6-digit pairing code verification and Ed25519 public key registration

import time
import logging
from typing import Tuple, Optional, Dict, Any

from core.v8.events import RemoteEventType
from core.v8.device import DeviceIdentity
from agent.crypto import AgentCrypto
from agent.transport import SecureTransport
from agent.audit import AgentAuditLogger

logger = logging.getLogger("mikasa.agent.enrollment")


class AgentEnrollment:
    """
    Qurilmani Mikasa hisobiga ulash (Pairing & Enrollment) mijozi.
    - Foydalanuvchi Mikasa Desktop/Web ilovasidan olgan 6-xonali kod orqali ulanadi.
    - Faqatgina ommaviy kalit (Ed25519 public key) yuboriladi, maxfiy kalit diskda shifrlangan qoladi.
    """

    def __init__(
        self,
        transport: SecureTransport,
        crypto: Optional[AgentCrypto] = None,
        device_id: Optional[str] = None
    ):
        self.transport = transport
        self.crypto = crypto
        self.device_id = device_id or (crypto.device_id if crypto else "")
        self._audit = AgentAuditLogger.get_instance()

    async def complete_pairing(
        self,
        pin: str,
        pairing_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """6 xonali raqamli PIN orqali hisobga bog'lanish"""
        code = str(pin).strip()
        if len(code) != 6 or not code.isdigit():
            return False, "PIN 6 xonali raqamdan iborat bo'lishi shart", None

        p_id = pairing_id or f"pair-{self.device_id}-{int(time.time())}"
        pub_key = self.crypto.public_key_hex if self.crypto else ""

        self._audit.log_event(
            event_type=RemoteEventType.ENROLLMENT_STARTED,
            device_id=self.device_id,
            details={"pin": code, "pairing_id": p_id}
        )

        payload = {
            "pairing_id": p_id,
            "pin": code,
            "code": code,
            "device_id": self.device_id,
            "public_key": pub_key,
        }

        status, resp = await self.transport.post("/api/devices/pairing/complete", data=payload)
        if status == 200 and resp.get("ok"):
            self._audit.log_event(
                event_type=RemoteEventType.ENROLLMENT_COMPLETED,
                device_id=self.device_id,
                details={"device_id": self.device_id, "status": "enrolled"}
            )
            return True, "Muvaffaqiyatli biriktirildi", resp
        else:
            err_msg = resp.get("error") or resp.get("message") or f"HTTP {status}"
            self._audit.log_event(
                event_type=RemoteEventType.ENROLLMENT_FAILED,
                device_id=self.device_id,
                error=err_msg
            )
            return False, err_msg, resp

    async def enroll(
        self,
        pairing_id: str,
        pairing_code: str,
        crypto: AgentCrypto,
        identity: DeviceIdentity
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Qurilmani backendga ro'yxatdan o'tkazish (Enrollment).
        Qaytaradi: (success: bool, message: str, credential_info: Optional[Dict])
        """
        p_id = str(pairing_id).strip()
        code = str(pairing_code).strip()

        if not p_id or not code:
            return False, "pairing_id va pairing_code kiritilishi shart", None

        self._audit.log_event(
            event_type=RemoteEventType.ENROLLMENT_STARTED,
            device_id=identity.device_id,
            details={"pairing_id": p_id}
        )

        payload = {
            "pairing_id": p_id,
            "code": code,
            "public_key": crypto.public_key_hex,
            "device": {
                "device_id": identity.device_id,
                "hostname": identity.hostname,
                "platform": identity.os_name,
                "os_version": f"{identity.os_version} ({identity.os_release})",
                "fingerprint": identity.fingerprint,
                "name": identity.metadata.get("friendly_name") or identity.hostname,
                "metadata": identity.metadata
            }
        }

        status, resp = await self.transport.post("/api/devices/pairing/complete", data=payload)

        if status == 200 and resp.get("ok"):
            self._audit.log_event(
                event_type=RemoteEventType.ENROLLMENT_COMPLETED,
                device_id=identity.device_id,
                details={
                    "pairing_id": p_id,
                    "device_id": identity.device_id,
                    "status": "enrolled"
                }
            )
            logger.info(f"[AgentEnrollment] Qurilma muvaffaqiyatli hisobga biriktirildi: {identity.device_id}")
            return True, resp.get("message", "Muvaffaqiyatli biriktirildi"), resp.get("credential")
        else:
            err_msg = resp.get("error") or resp.get("message") or f"HTTP {status}"
            self._audit.log_event(
                event_type=RemoteEventType.ENROLLMENT_FAILED,
                device_id=identity.device_id,
                details={"pairing_id": p_id},
                error=err_msg
            )
            logger.warning(f"[AgentEnrollment] Enrollment rad etildi: {err_msg}")
            return False, err_msg, None
