# ========== core/v8/auth_session.py ==========
# Phase 37 — Secure Remote Session Authentication Engine
# Session Lifecycle, PBKDF2 Password/PIN Verification, 3-Attempts & 5-Min Cooldown

import os
import time
import uuid
import secrets
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple, List

from core.v8.events import RemoteEventType, RemoteAuditLogger

logger = logging.getLogger("core.v8.auth")


@dataclass
class RemoteAuthSession:
    """
    Masofaviy faol boshqaruv sessiyasi.
    Vaqt chegaralangan (TTL), audit qilingan va yagona identifikatorga ega.
    """
    user_id: str
    device_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    is_active: bool = True
    permissions: List[str] = field(default_factory=lambda: ["all"])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self, current_time: Optional[float] = None) -> bool:
        """Sessiyaning faolligi va muddati o'tmaganligini tekshirish"""
        now = current_time if current_time is not None else time.time()
        return self.is_active and (now < self.expires_at)

    def extend_ttl(self, seconds: float = 900.0, current_time: Optional[float] = None):
        """Sessiya muddatini uzaytirish"""
        now = current_time if current_time is not None else time.time()
        self.expires_at = now + seconds

    def close(self):
        """Sessiyani xavfsiz yakunlash"""
        self.is_active = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteAuthSession":
        return cls(**data)


class SessionManager:
    """
    Faol masofaviy sessiyalar registratori va muddati o'tgan sessiyalarni tozalash dvigateli.
    """

    def __init__(self, default_ttl: float = 900.0):
        self.default_ttl = default_ttl  # Standart: 15 daqiqa (900s)
        self._sessions: Dict[str, RemoteAuthSession] = {}  # f"{user_id}:{device_id}" -> session
        self._audit = RemoteAuditLogger.get_instance()

    def _get_key(self, user_id: str, device_id: str) -> str:
        return f"{str(user_id)}:{str(device_id)}"

    def create_session(
        self,
        user_id: str,
        device_id: str,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RemoteAuthSession:
        """Yangi sessiya yaratish (oldingi faol sessiyani yopadi)"""
        key = self._get_key(user_id, device_id)
        now = time.time()
        session_ttl = ttl if ttl is not None else self.default_ttl

        # Agar eski sessiya mavjud bo'lsa, uni yopish
        if key in self._sessions and self._sessions[key].is_active:
            self._sessions[key].close()

        session = RemoteAuthSession(
            user_id=str(user_id),
            device_id=str(device_id),
            created_at=now,
            expires_at=now + session_ttl,
            is_active=True,
            metadata=metadata or {}
        )
        self._sessions[key] = session

        self._audit.log(
            RemoteEventType.SESSION_OPENED,
            user_id=str(user_id),
            device_id=str(device_id),
            session_id=session.session_id,
            ttl=session_ttl
        )
        logger.info(f"[SessionManager] Yangi sessiya ochildi: user={user_id}, dev={device_id}, ttl={session_ttl}s")
        return session

    def get_active_session(
        self,
        user_id: str,
        device_id: str,
        current_time: Optional[float] = None
    ) -> Optional[RemoteAuthSession]:
        """Faol sessiyani olish (muddati o'tgan bo'lsa avtomatik yopiladi)"""
        key = self._get_key(user_id, device_id)
        session = self._sessions.get(key)
        if not session:
            return None

        now = current_time if current_time is not None else time.time()
        if not session.is_valid(now):
            session.close()
            self._audit.log(
                RemoteEventType.SESSION_EXPIRED,
                user_id=str(user_id),
                device_id=str(device_id),
                session_id=session.session_id
            )
            return None

        return session

    def close_session(self, user_id: str, device_id: str) -> bool:
        """Sessiyani foydalanuvchi xohishi bilan yopish (Logout)"""
        key = self._get_key(user_id, device_id)
        session = self._sessions.get(key)
        if session and session.is_active:
            session.close()
            self._audit.log(
                RemoteEventType.SESSION_CLOSED,
                user_id=str(user_id),
                device_id=str(device_id),
                session_id=session.session_id
            )
            logger.info(f"[SessionManager] Sessiya yopildi: user={user_id}, dev={device_id}")
            return True
        return False

    def cleanup_expired_sessions(self, current_time: Optional[float] = None) -> int:
        """Barcha muddati o'tgan sessiyalarni tozalash"""
        now = current_time if current_time is not None else time.time()
        closed_count = 0
        for session in list(self._sessions.values()):
            if session.is_active and not session.is_valid(now):
                session.close()
                closed_count += 1
        return closed_count


class RemoteAuthEngine:
    """
    Masofaviy autentifikatsiya dvigateli.
    PBKDF2-HMAC-SHA256 xeshlash, 3 ta urinish chegarasi, 5 daqiqalik cooldown
    va doimiy vaqtli (constant-time) solishtirish bilan to'liq himoyalangan.
    """

    PBKDF2_ITERATIONS = 100_000

    def __init__(
        self,
        default_password: Optional[str] = None,
        default_pin: Optional[str] = None,
        max_attempts: int = 3,
        cooldown_seconds: float = 300.0,  # 5 daqiqa
        session_manager: Optional[SessionManager] = None
    ):
        self.max_attempts = max_attempts
        self.cooldown_seconds = cooldown_seconds
        self.session_manager = session_manager or SessionManager()
        self._audit = RemoteAuditLogger.get_instance()

        self._password_hash: Optional[str] = None
        self._pin_hash: Optional[str] = None

        # Urinishlar va cooldown holati: user_id -> qiymat
        self._failed_attempts: Dict[str, int] = {}
        self._cooldown_until: Dict[str, float] = {}
        self._pending_challenges: Dict[str, Dict[str, Any]] = {}  # user_id -> challenge info

        # Boshlang'ich parollarni o'rnatish
        env_pw = os.environ.get("REMOTE_AUTH_PASSWORD") or os.environ.get("ADMIN_PAROL") or default_password or "mikasa2026"
        env_pin = os.environ.get("REMOTE_AUTH_PIN") or default_pin or "1234"
        self.set_password(env_pw)
        self.set_pin(env_pin)

    @classmethod
    def hash_secret(cls, secret: str, salt: Optional[bytes] = None) -> str:
        """Tuzlangan (salted) PBKDF2-HMAC-SHA256 xesh yaratish"""
        use_salt = salt if salt is not None else secrets.token_bytes(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            secret.encode("utf-8"),
            use_salt,
            cls.PBKDF2_ITERATIONS
        )
        return f"pbkdf2:sha256:{cls.PBKDF2_ITERATIONS}:{use_salt.hex()}:{key.hex()}"

    @classmethod
    def verify_hash(cls, secret: str, stored_hash: str) -> bool:
        """Constant-time xesh tekshiruvi (Timing Attack lardan himoya)"""
        if not stored_hash or not isinstance(stored_hash, str):
            return False
        parts = stored_hash.split(":")
        if len(parts) != 5 or parts[0] != "pbkdf2" or parts[1] != "sha256":
            return False
        try:
            iterations = int(parts[2])
            salt = bytes.fromhex(parts[3])
            expected_key = bytes.fromhex(parts[4])
            actual_key = hashlib.pbkdf2_hmac(
                "sha256",
                secret.encode("utf-8"),
                salt,
                iterations
            )
            return secrets.compare_digest(actual_key, expected_key)
        except Exception as e:
            logger.error(f"[RemoteAuthEngine] Hash verifikatsiyasida xatolik: {e}")
            return False

    def set_password(self, password: str):
        """Yangi asosiy parolni o'rnatish"""
        self._password_hash = self.hash_secret(str(password))

    def set_pin(self, pin: str):
        """Yangi raqamli PIN kodni o'rnatish"""
        self._pin_hash = self.hash_secret(str(pin))

    # ========================================================
    # CHALLENGE LIFECYCLE (WAKE -> PROMPT -> AUTH)
    # ========================================================

    def set_auth_pending(
        self,
        user_id: str,
        device_id: str,
        pending: bool = True,
        chat_id: Optional[int] = None
    ):
        """Foydalanuvchi uchun autentifikatsiya kutish holatini yoqish/o'chirish"""
        uid = str(user_id)
        if pending:
            self._pending_challenges[uid] = {
                "device_id": str(device_id),
                "chat_id": chat_id,
                "issued_at": time.time()
            }
            self._audit.log(
                RemoteEventType.AUTH_CHALLENGE_ISSUED,
                user_id=uid,
                device_id=str(device_id)
            )
        else:
            self._pending_challenges.pop(uid, None)

    def is_auth_pending(self, user_id: str) -> bool:
        return str(user_id) in self._pending_challenges

    def get_pending_device(self, user_id: str) -> Optional[str]:
        entry = self._pending_challenges.get(str(user_id))
        return entry.get("device_id") if entry else None

    def clear_auth_pending(self, user_id: str):
        self._pending_challenges.pop(str(user_id), None)

    # ========================================================
    # ATTEMPTS & 5-MINUTE COOLDOWN
    # ========================================================

    def is_in_cooldown(self, user_id: str, current_time: Optional[float] = None) -> Tuple[bool, float]:
        """Foydalanuvchi cooldown blokirovkasida ekanligini va qolgan soniyalarni tekshirish"""
        uid = str(user_id)
        now = current_time if current_time is not None else time.time()
        until = self._cooldown_until.get(uid, 0.0)

        if now < until:
            remaining = until - now
            return True, remaining

        # Cooldown tugagan bo'lsa, holatni tiklash
        if uid in self._cooldown_until:
            del self._cooldown_until[uid]
            self._failed_attempts[uid] = 0

        return False, 0.0

    def get_remaining_attempts(self, user_id: str) -> int:
        """Qolgan urinishlar sonini olish (maksimal: 3)"""
        uid = str(user_id)
        failed = self._failed_attempts.get(uid, 0)
        return max(0, self.max_attempts - failed)

    def reset_cooldown(self, user_id: Optional[str] = None):
        """Cooldown va urinishlar hisoblagichini tozalash (Admin override / Test)"""
        if user_id:
            uid = str(user_id)
            self._failed_attempts[uid] = 0
            self._cooldown_until.pop(uid, None)
        else:
            self._failed_attempts.clear()
            self._cooldown_until.clear()

    # ========================================================
    # SECRET VERIFICATION & SESSION CREATION
    # ========================================================

    def verify_secret(
        self,
        user_id: str,
        device_id: str,
        input_secret: str,
        current_time: Optional[float] = None
    ) -> Tuple[bool, str, Optional[RemoteAuthSession]]:
        """
        Kiritilgan parol yoki PIN kodni tekshirish:
        - Cooldown tekshiruvi
        - Xesh solishtiruvi (parol yoki pin bilan)
        - To'g'ri bo'lsa: urinishlarni tiklash, sessiyani ochish
        - Noto'g'ri bo'lsa: urinishni oshirish, 3 taga yetsa 5-daqiqa cooldown yoqish
        """
        uid = str(user_id)
        dev = str(device_id)
        now = current_time if current_time is not None else time.time()

        # 1. Cooldown tekshiruvi
        in_cd, rem_cd = self.is_in_cooldown(uid, now)
        if in_cd:
            rem_sec = int(rem_cd)
            logger.warning(f"[RemoteAuthEngine] Cooldown faol: user={uid}, qolgan vaqt={rem_sec}s")
            return (
                False,
                f"COOLDOWN_ACTIVE: Xavfsizlik blokirovkasi faol. Qolgan vaqt: {rem_sec} soniya.",
                None
            )

        clean_secret = str(input_secret).strip()

        # 2. Xeshlar bilan tekshirish (parol yoki pin mos kelishi kerak)
        match_password = bool(self._password_hash and self.verify_hash(clean_secret, self._password_hash))
        match_pin = bool(self._pin_hash and self.verify_hash(clean_secret, self._pin_hash))

        if match_password or match_pin:
            # MUVOFAQIYATLI AUTENTIFIKATSIYA
            self._failed_attempts[uid] = 0
            self.clear_auth_pending(uid)

            # Yangi sessiya yaratish
            session = self.session_manager.create_session(uid, dev)

            self._audit.log(
                RemoteEventType.AUTH_ATTEMPT_SUCCESS,
                user_id=uid,
                device_id=dev,
                session_id=session.session_id,
                auth_method="password" if match_password else "pin"
            )
            return (
                True,
                "OK: Autentifikatsiya muvaffaqiyatli yakunlandi. Sessiya ochildi.",
                session
            )

        # XATO AUTENTIFIKATSIYA
        self._failed_attempts[uid] = self._failed_attempts.get(uid, 0) + 1
        failed_count = self._failed_attempts[uid]
        remaining = max(0, self.max_attempts - failed_count)

        self._audit.log(
            RemoteEventType.AUTH_ATTEMPT_FAILED,
            user_id=uid,
            device_id=dev,
            failed_count=failed_count,
            remaining_attempts=remaining
        )

        # 3. 3-marta xato qilinganda 5 daqiqalik cooldown blokirovkasi
        if failed_count >= self.max_attempts:
            cooldown_end = now + self.cooldown_seconds
            self._cooldown_until[uid] = cooldown_end
            self._audit.log(
                RemoteEventType.AUTH_COOLDOWN_ACTIVATED,
                user_id=uid,
                device_id=dev,
                cooldown_seconds=self.cooldown_seconds
            )
            logger.warning(f"[RemoteAuthEngine] 3 ta xato urinish! Cooldown faollashdi: user={uid}, {self.cooldown_seconds}s")
            return (
                False,
                f"COOLDOWN_ACTIVATED: Ketma-ket 3 marta noto'g'ri parol kiritildi. "
                f"Tizim {int(self.cooldown_seconds / 60)} daqiqaga bloklandi.",
                None
            )

        return (
            False,
            f"INVALID_CREDENTIALS: Noto'g'ri parol yoki PIN kod! Qolgan urinishlar: {remaining} ta.",
            None
        )
