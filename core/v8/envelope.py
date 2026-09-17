# ========== core/v8/envelope.py ==========
# Phase 35/36 — Remote Command Envelope, Replay Defense, Rate Limiter & Idempotency

import time
import uuid
import secrets
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple, Set, List

from core.v8.events import RemoteEventType, RemoteAuditLogger


@dataclass
class RemoteCommandEnvelope:
    """
    Masofaviy buyruq xavfsiz konverti (Envelope).
    Idempotentlik, replay attack himoyasi va ruxsatlar versiyasi bilan ta'minlangan.
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
    # Phase 38 Qo'shimcha maydonlar
    command_id: Optional[str] = None
    telegram_user_id: Optional[str] = None
    session_id: Optional[str] = None
    tool_id: Optional[str] = None
    permission_version: int = 1

    def __post_init__(self):
        if self.expires_at == 0.0:
            self.expires_at = self.created_at + 300.0  # 5 daqiqa amal qiladi
        if self.command_id is None:
            self.command_id = self.request_id
        if self.tool_id is None:
            self.tool_id = self.action

    @property
    def timestamp(self) -> float:
        return self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteCommandEnvelope":
        valid_keys = {
            "request_id", "device_id", "action", "params", "origin", "user_id",
            "created_at", "expires_at", "nonce", "confirmation_required", "signature",
            "command_id", "telegram_user_id", "session_id", "tool_id", "permission_version"
        }
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


class RateLimiter:
    """
    So'rovlar chastotasini cheklovchi (Sliding Window).
    Hujumlar va cheksiz yuklanishlarning oldini oladi.
    """

    def __init__(self, max_requests: int = 20, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def check_limit(self, key: str, current_time: Optional[float] = None) -> Tuple[bool, str]:
        if not key:
            return True, "OK"
        now = current_time if current_time is not None else time.time()
        window_start = now - self.window_seconds

        # O'tgan vaqt oynasidan eski vaqtlarni tozalash
        timestamps = [t for t in self._requests[key] if t > window_start]
        self._requests[key] = timestamps

        if len(timestamps) >= self.max_requests:
            return False, f"RATE_LIMIT_EXCEEDED: Qisqa vaqt ichida juda ko'p so'rov ({len(timestamps)}/{self.max_requests}). Iltimos, kuting."

        self._requests[key].append(now)
        return True, "OK"

    def reset(self, key: Optional[str] = None):
        if key:
            if key in self._requests:
                del self._requests[key]
        else:
            self._requests.clear()


class EnvelopeManager:
    """
    Buyruq konvertlarini yaratish, tekshirish, replay attack himoyasi,
    idempotentlik va rate limiting dvigateli.
    """

    def __init__(
        self,
        authorized_user_id: Optional[str] = None,
        authorized_user_ids: Optional[Set[str]] = None,
        default_ttl: float = 300.0,
        rate_limiter: Optional[RateLimiter] = None
    ):
        self.authorized_user_id = str(authorized_user_id) if authorized_user_id is not None else None
        self.authorized_user_ids: Set[str] = set(authorized_user_ids or [])
        if self.authorized_user_id:
            self.authorized_user_ids.add(self.authorized_user_id)

        self.default_ttl = default_ttl
        self.rate_limiter = rate_limiter or RateLimiter(max_requests=30, window_seconds=60.0)
        self._seen_nonces: Dict[str, float] = {}  # nonce -> expires_at
        self._executed_results: Dict[str, Dict[str, Any]] = {}  # request_id -> result dict
        self._audit = RemoteAuditLogger.get_instance()

    def create_envelope(
        self,
        device_id: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        user_id: str = "",
        origin: str = "telegram",
        confirmation_required: bool = False,
        telegram_user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        permission_version: int = 1
    ) -> RemoteCommandEnvelope:
        now = time.time()
        req_id = str(uuid.uuid4())
        return RemoteCommandEnvelope(
            request_id=req_id,
            device_id=device_id,
            action=action,
            params=params or {},
            origin=origin,
            user_id=str(user_id),
            created_at=now,
            expires_at=now + self.default_ttl,
            nonce=secrets.token_hex(8),
            confirmation_required=confirmation_required,
            command_id=req_id,
            telegram_user_id=telegram_user_id,
            session_id=session_id,
            tool_id=tool_id or action,
            permission_version=permission_version
        )

    def validate_envelope(self, envelope: RemoteCommandEnvelope, current_time: Optional[float] = None) -> Tuple[bool, str]:
        now = current_time if current_time is not None else time.time()

        # 0. Malformed envelope tekshiruvi
        if not envelope.request_id or not envelope.device_id or not envelope.action:
            return False, "MALFORMED_ENVELOPE: request_id, device_id yoki action maydoni bo'sh"
        if not envelope.nonce:
            return False, "INVALID_NONCE: Nonce bo'sh bo'lishi mumkin emas"

        # 1. Muddati o'tganligini tekshirish (Expiration)
        if now > envelope.expires_at:
            return False, "REQUEST_EXPIRED: Buyruqning amal qilish muddati tugagan"

        # 2. Ruxsat tekshiruvi (Authorization)
        if self.authorized_user_ids:
            uid_ok = (str(envelope.user_id) in self.authorized_user_ids) or (
                bool(envelope.telegram_user_id) and str(envelope.telegram_user_id) in self.authorized_user_ids
            )
            if not uid_ok:
                self._audit.log(
                    RemoteEventType.REMOTE_REQUEST_DENIED,
                    request_id=envelope.request_id,
                    user_id=envelope.user_id,
                    reason="Unauthorized user"
                )
                return False, f"UNAUTHORIZED: Foydalanuvchi {envelope.user_id} ruxsatga ega emas"
        elif self.authorized_user_id is not None:
            uid_ok = (str(envelope.user_id) == self.authorized_user_id) or (
                bool(envelope.telegram_user_id) and str(envelope.telegram_user_id) == self.authorized_user_id
            )
            if not uid_ok:
                self._audit.log(
                    RemoteEventType.REMOTE_REQUEST_DENIED,
                    request_id=envelope.request_id,
                    user_id=envelope.user_id,
                    reason="Unauthorized user"
                )
                return False, f"UNAUTHORIZED: Foydalanuvchi {envelope.user_id} ruxsatga ega emas"

        # 3. Rate Limiting tekshiruvi
        if envelope.user_id:
            ok_rate, rate_msg = self.rate_limiter.check_limit(f"user:{envelope.user_id}", now)
            if not ok_rate:
                return False, rate_msg

        # 4. Idempotentlik tekshiruvi (agar bir xil request_id avval bajarilgan bo'lsa)
        if envelope.request_id in self._executed_results:
            return False, "DUPLICATE_REQUEST: Ushbu request_id allaqachon qabul qilingan va bajarilgan"

        # 5. Nonce va Replay Attack tekshiruvi
        self._purge_old_nonces(now)
        if envelope.nonce in self._seen_nonces:
            return False, "REPLAY_ATTACK_DETECTED: Ushbu buyruq allaqachon bajarilgan (duplicate nonce)"

        self._seen_nonces[envelope.nonce] = envelope.expires_at
        return True, "OK"

    def record_execution_result(self, request_id: str, result: Dict[str, Any]):
        """Idempotentlik uchun natijani saqlab qo'yish"""
        self._executed_results[request_id] = result

    def get_cached_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        return self._executed_results.get(request_id)

    def is_executed(self, request_id: str) -> bool:
        return request_id in self._executed_results

    def _purge_old_nonces(self, now: float):
        expired = [nonce for nonce, exp in self._seen_nonces.items() if now > exp]
        for n in expired:
            del self._seen_nonces[n]
