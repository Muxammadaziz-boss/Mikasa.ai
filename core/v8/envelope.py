# ========== core/v8/envelope.py ==========
# Phase 35 — Remote Command Envelope & Replay Attack Defense

import time
import uuid
import secrets
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple


@dataclass
class RemoteCommandEnvelope:
    """
    Masofaviy buyruq xavfsiz konverti (Envelope).
    """
    request_id: str
    device_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    origin: str = "telegram"
    user_id: str = ""
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    nonce: str = field(default_factory=lambda: secrets.token_hex(8))
    confirmation_required: bool = False
    signature: Optional[str] = None

    def __post_init__(self):
        if self.expires_at == 0.0:
            self.expires_at = self.created_at + 300.0  # 5 daqiqa amal qiladi

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteCommandEnvelope":
        return cls(**data)


class EnvelopeManager:
    """
    Buyruq konvertlarini yaratish, tekshirish va replay attack himoyasi.
    """

    def __init__(self, authorized_user_id: Optional[str] = None, default_ttl: float = 300.0):
        self.authorized_user_id = str(authorized_user_id) if authorized_user_id is not None else None
        self.default_ttl = default_ttl
        self._seen_nonces: Dict[str, float] = {}  # nonce -> expires_at

    def create_envelope(
        self,
        device_id: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        user_id: str = "",
        origin: str = "telegram",
        confirmation_required: bool = False
    ) -> RemoteCommandEnvelope:
        now = time.time()
        return RemoteCommandEnvelope(
            request_id=str(uuid.uuid4()),
            device_id=device_id,
            action=action,
            params=params or {},
            origin=origin,
            user_id=str(user_id),
            created_at=now,
            expires_at=now + self.default_ttl,
            nonce=secrets.token_hex(8),
            confirmation_required=confirmation_required
        )

    def validate_envelope(self, envelope: RemoteCommandEnvelope, current_time: Optional[float] = None) -> Tuple[bool, str]:
        now = current_time if current_time is not None else time.time()

        # 1. Muddati o'tganligini tekshirish (Expiration)
        if now > envelope.expires_at:
            return False, "REQUEST_EXPIRED: Buyruqning amal qilish muddati tugagan"

        # 2. Ruxsat tekshiruvi (Authorization)
        if self.authorized_user_id is not None:
            if str(envelope.user_id) != self.authorized_user_id:
                return False, f"UNAUTHORIZED: Foydalanuvchi {envelope.user_id} ruxsatga ega emas"

        # 3. Nonce va Replay Attack tekshiruvi
        self._purge_old_nonces(now)
        if envelope.nonce in self._seen_nonces:
            return False, "REPLAY_ATTACK_DETECTED: Ushbu buyruq allaqachon bajarilgan (duplicate nonce)"

        self._seen_nonces[envelope.nonce] = envelope.expires_at
        return True, "OK"

    def _purge_old_nonces(self, now: float):
        expired = [nonce for nonce, exp in self._seen_nonces.items() if now > exp]
        for n in expired:
            del self._seen_nonces[n]
