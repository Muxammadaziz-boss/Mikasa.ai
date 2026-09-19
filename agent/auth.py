# ========== agent/auth.py ==========
# Phase 45 — Windows PC Agent Cryptographic Authentication Client
# Challenge-Response auth flow with Ed25519 signing and session management

import logging
from typing import Dict, Any, Optional, Tuple

from core.v8.events import RemoteEventType
from agent.audit import AgentAuditLogger
from agent.crypto import AgentCrypto
from agent.transport import SecureTransport

logger = logging.getLogger("mikasa.agent.auth")


class AgentAuth:
    """
    Mikasa Backend bilan kriptografik chaqiriq-javob autentifikatsiyasi.
    1. /api/devices/{device_id}/challenge orqali 32-bayt nonce oladi.
    2. Mahalliy DPAPI/Ed25519 xususiy kalit bilan kanonik xabarni imzolaydi.
    3. /api/devices/{device_id}/authenticate ga imzoni yuborib, DeviceSession tokenini oladi.
    """

    def __init__(
        self,
        transport: SecureTransport,
        crypto: AgentCrypto,
        device_id: str
    ):
        self.transport = transport
        self.crypto = crypto
        self.device_id = device_id
        self._audit = AgentAuditLogger.get_instance()
        self.session_token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.session_expires_at: float = 0.0

    async def authenticate(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        To'liq autentifikatsiya jarayonini amalga oshirish.
        Qaytaradi: (muvaffaqiyat, xabar/xato, sessiya ma'lumotlari)
        """
        self._audit.log_event(
            event_type=RemoteEventType.AUTH_STARTED,
            device_id=self.device_id,
            details={"action": "request_challenge"}
        )

        # 1. Chaqiriq (Challenge) so'rovi
        endpoint_challenge = f"/api/devices/{self.device_id}/challenge"
        status, data = await self.transport.post(endpoint_challenge, {})
        if status != 200 or not data.get("ok"):
            err_msg = data.get("error", f"HTTP {status}")
            logger.error(f"[AgentAuth] Challenge olishda xato: {err_msg}")
            self._audit.log_event(
                event_type=RemoteEventType.AUTH_FAILED,
                device_id=self.device_id,
                details={"step": "challenge", "error": err_msg}
            )
            return False, err_msg, None

        challenge_id = data.get("challenge_id", "")
        nonce = data.get("nonce", "")
        if not challenge_id or not nonce:
            err_msg = "Chaqiriq ma'lumotlari (challenge_id yoki nonce) to'liq emas"
            logger.error(f"[AgentAuth] {err_msg}")
            self._audit.log_event(
                event_type=RemoteEventType.AUTH_FAILED,
                device_id=self.device_id,
                details={"step": "challenge_payload", "error": err_msg}
            )
            return False, err_msg, None

        # 2. Imzolash (Ed25519)
        try:
            signed = self.crypto.sign_challenge(nonce=nonce)
            signature = signed["signature"]
            context = signed["context"]
        except Exception as e:
            err_msg = f"Imzolashda xatolik: {e}"
            logger.error(f"[AgentAuth] {err_msg}")
            self._audit.log_event(
                event_type=RemoteEventType.AUTH_FAILED,
                device_id=self.device_id,
                details={"step": "signing", "error": str(e)}
            )
            return False, err_msg, None

        # 3. Autentifikatsiya so'rovi (Verify Challenge Response)
        endpoint_auth = f"/api/devices/{self.device_id}/authenticate"
        payload = {
            "challenge_id": challenge_id,
            "signature": signature,
            "context": context
        }
        status, auth_data = await self.transport.post(endpoint_auth, payload)
        if status != 200 or not auth_data.get("ok"):
            err_msg = auth_data.get("error", f"HTTP {status}")
            logger.error(f"[AgentAuth] Autentifikatsiya rad etildi: {err_msg}")
            self._audit.log_event(
                event_type=RemoteEventType.AUTH_FAILED,
                device_id=self.device_id,
                details={"step": "verify", "error": err_msg}
            )
            return False, err_msg, None

        # 4. Sessiyani saqlash va transportga o'rnatish
        self.session_token = auth_data.get("session_token")
        self.session_id = auth_data.get("session_id")
        self.session_expires_at = float(auth_data.get("expires_at", 0.0))

        if self.session_token:
            self.transport.set_session_token(self.session_token)

        self._audit.log_event(
            event_type=RemoteEventType.AUTH_SUCCESS,
            device_id=self.device_id,
            details={
                "session_id": self.session_id,
                "expires_at": self.session_expires_at,
                "protocol_version": auth_data.get("protocol_version")
            }
        )
        logger.info(f"[AgentAuth] Autentifikatsiya muvaffaqiyatli! Session ID={self.session_id}")
        return True, "Autentifikatsiya muvaffaqiyatli", auth_data
