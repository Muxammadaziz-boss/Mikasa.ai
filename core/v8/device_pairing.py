# ========== core/v8/device_pairing.py ==========
# Phase 42 — Secure PC Agent Pairing Engine
# Short-lived (5 min), single-use, rate-limited pairing sessions
# Plaintext pairing code is NEVER stored in database or audit logs

import os
import time
import json
import uuid
import secrets
import hashlib
import hmac
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List

from core.v8.events import RemoteEventType, RemoteAuditLogger

logger = logging.getLogger("core.v8.device_pairing")


@dataclass
class DevicePairingSession:
    """
    Qurilmani hisobga ulash (enrollment) uchun vaqtinchalik sessiya modeli.
    Faqatgina dastlabki ulanish (enrollment) uchun ishlatiladi.
    Doimiy autentifikatsiya yoki masofaviy boshqaruv huquqini bermaydi.
    """
    id: str  # UUID
    user_id: str  # auth.users.id / MikasaUser UUID
    pairing_code_hash: str  # SHA-256(salt + ":" + code)
    pairing_code_salt: str  # 16-bayt random salt (hex)
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    used_at: Optional[float] = None
    status: str = "PENDING"  # PENDING, VERIFIED, COMPLETED, EXPIRED, REVOKED, FAILED
    attempt_count: int = 0
    max_attempts: int = 5
    device_id: Optional[str] = None
    request_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def is_active(self) -> bool:
        return (
            self.status == "PENDING"
            and not self.is_expired
            and self.attempt_count < self.max_attempts
        )

    @property
    def can_attempt(self) -> bool:
        return self.is_active

    @property
    def remaining_seconds(self) -> float:
        return max(0.0, self.expires_at - time.time())

    def to_dict(self, include_security_metadata: bool = False) -> Dict[str, Any]:
        """User-facing yoki API uchun xavfsiz lug'at (raw code va hashlar chiqarilmaydi)"""
        d = {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "used_at": self.used_at,
            "status": self.status,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "device_id": self.device_id,
            "remaining_seconds": round(self.remaining_seconds, 1),
            "is_active": self.is_active,
            "request_metadata": self.request_metadata,
        }
        if include_security_metadata:
            d["pairing_code_hash"] = self.pairing_code_hash
            d["pairing_code_salt"] = self.pairing_code_salt
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DevicePairingSession":
        valid_fields = {
            "id", "user_id", "pairing_code_hash", "pairing_code_salt",
            "created_at", "expires_at", "used_at", "status",
            "attempt_count", "max_attempts", "device_id", "request_metadata"
        }
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class DevicePairingManager:
    """
    Qurilmalarni xavfsiz juftlash (pairing) menejeri.
    - 6-xonali kriptografik tasodifiy kod generatsiyasi.
    - Plaintext kod faqat response orqali bir marta qaytariladi (bazada faqat xesh saqlanadi).
    - 5 daqiqalik TTL va 5 urinish limiti (Brute-force himoyasi).
    - Bir martalik foydalanish (Single-use) va multi-tenant izolyatsiya.
    """
    DEFAULT_TTL = 300.0  # 5 daqiqa (soniyalarda)
    MAX_ATTEMPTS = 5
    _default_instance: Optional["DevicePairingManager"] = None
    _instance: Optional["DevicePairingManager"] = None

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "v8_device_pairing.json"
        )
        self._sessions: Dict[str, DevicePairingSession] = {}
        self._audit = RemoteAuditLogger.get_instance()
        self.load()

    @classmethod
    def get_default_instance(cls, storage_path: Optional[str] = None) -> "DevicePairingManager":
        inst = getattr(cls, "_instance", None) or cls._default_instance
        if inst is None:
            cls._default_instance = cls(storage_path=storage_path)
            return cls._default_instance
        return inst

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "DevicePairingManager":
        return cls.get_default_instance(*args, **kwargs)

    # ========================================================
    # 1. CODE & HASH GENERATION
    # ========================================================

    @staticmethod
    def generate_pairing_code() -> str:
        """Kriptografik xavfsiz 6 xonali raqamli kod generatsiya qilish"""
        digits = [secrets.choice("0123456789") for _ in range(6)]
        return "".join(digits)

    @staticmethod
    def hash_code(code: str, salt: str) -> str:
        """HMAC-SHA256 / Salted SHA-256 xeshini hisoblash"""
        clean_code = str(code).strip().replace(" ", "").replace("-", "")
        payload = f"{salt}:{clean_code}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    # ========================================================
    # 2. PAIRING LIFECYCLE
    # ========================================================

    def start_pairing(
        self,
        user_id: str,
        ttl_seconds: Optional[float] = None,
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[DevicePairingSession, str]:
        """
        Yangi juftlash sessiyasini yaratish.
        Qaytaradi: (session, raw_pairing_code).
        DIQQAT: raw_pairing_code hech qachon bazada yoki audit loglarida saqlanmaydi!
        """
        uid = str(user_id).strip()
        if not uid:
            raise ValueError("user_id kiritilishi shart")

        self.cleanup_expired_sessions()

        ttl = float(ttl_seconds if ttl_seconds is not None else self.DEFAULT_TTL)
        now = time.time()
        expires_at = now + ttl

        raw_code = self.generate_pairing_code()
        salt = secrets.token_hex(16)
        code_hash = self.hash_code(raw_code, salt)

        session_id = str(uuid.uuid4())
        session = DevicePairingSession(
            id=session_id,
            user_id=uid,
            pairing_code_hash=code_hash,
            pairing_code_salt=salt,
            created_at=now,
            expires_at=expires_at,
            status="PENDING",
            max_attempts=self.MAX_ATTEMPTS,
            request_metadata=dict(request_metadata or {})
        )

        self._sessions[session_id] = session
        self.save()

        # Audit log (Maxfiy raw_code ni HECH QACHON kiritmaymiz!)
        self._audit.log(
            RemoteEventType.DEVICE_PAIRING_STARTED,
            request_id=session_id,
            user_id=uid,
            ttl=ttl,
            status="PENDING"
        )
        logger.info(f"[DevicePairing] Yangi pairing sessiyasi boshlandi: id={session_id}, user={uid}, ttl={ttl}s")
        return session, raw_code

    def get_session(self, pairing_id: str) -> Optional[DevicePairingSession]:
        """Sessiyani olish (muddati o'tgan bo'lsa holatini yangilaydi)"""
        pid = str(pairing_id).strip()
        sess = self._sessions.get(pid)
        if sess and sess.status == "PENDING" and sess.is_expired:
            sess.status = "EXPIRED"
            self.save()
        return sess

    def get_sessions_for_user(self, user_id: str) -> List[DevicePairingSession]:
        """Foydalanuvchiga tegishli barcha pairing sessiyalari"""
        uid = str(user_id).strip()
        return [s for s in self._sessions.values() if s.user_id == uid]

    def verify_code(
        self,
        pairing_id: str,
        code: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[DevicePairingSession]]:
        """
        Kiritilgan juftlash kodini tekshirish.
        Vaqt hujumlariga qarshi hmac.compare_digest bilan tekshiriladi.
        """
        sess = self.get_session(pairing_id)
        if not sess:
            return False, "NOT_FOUND: Juftlash sessiyasi topilmadi", None

        if user_id and sess.user_id != str(user_id).strip():
            logger.warning(f"[DevicePairing] Ruxsatsiz urinish: sess_user={sess.user_id} != req_user={user_id}")
            return False, "UNAUTHORIZED: Sessiya sizning hisobingizga tegishli emas", None

        if sess.status == "COMPLETED":
            return False, "ALREADY_COMPLETED: Ushbu juftlash sessiyasi allaqachon ishlatilgan", None

        if sess.status in ("REVOKED", "FAILED"):
            return False, f"STATUS_INVALID: Sessiya holati yaroqsiz ({sess.status})", None

        if sess.is_expired:
            sess.status = "EXPIRED"
            self.save()
            self._audit.log(
                RemoteEventType.DEVICE_PAIRING_EXPIRED,
                request_id=sess.id,
                user_id=sess.user_id
            )
            return False, "EXPIRED: Kod muddati tugagan (5 daqiqadan oshdi)", None

        if sess.attempt_count >= sess.max_attempts:
            sess.status = "FAILED"
            self.save()
            return False, "MAX_ATTEMPTS: Noto'g'ri kod kiritish cheklovidan oshdi", None

        # Urinishni oshirish
        sess.attempt_count += 1

        expected_hash = sess.pairing_code_hash
        actual_hash = self.hash_code(code, sess.pairing_code_salt)

        if not hmac.compare_digest(expected_hash, actual_hash):
            if sess.attempt_count >= sess.max_attempts:
                sess.status = "FAILED"
                self._audit.log(
                    RemoteEventType.DEVICE_PAIRING_FAILED,
                    request_id=sess.id,
                    user_id=sess.user_id,
                    reason="max_attempts_exceeded"
                )
            self.save()
            return False, f"INVALID_CODE: Kod noto'g'ri (Qolgan urinishlar: {max(0, sess.max_attempts - sess.attempt_count)})", None

        sess.status = "VERIFIED"
        self.save()
        return True, "OK", sess

    def complete_pairing(
        self,
        pairing_id: str,
        code: str,
        device_id: str,
        device_info: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[DevicePairingSession]]:
        """
        Kodni tekshirish va sessiyani COMPLETED holatiga o'tkazish.
        Single-use kafolatlanadi.
        """
        ok, msg, sess = self.verify_code(pairing_id, code, user_id=user_id)
        if not ok or not sess:
            return False, msg, None

        sess.device_id = str(device_id).strip()
        sess.status = "COMPLETED"
        sess.used_at = time.time()
        if device_info:
            sess.request_metadata.update(device_info)
        self.save()

        self._audit.log(
            RemoteEventType.DEVICE_PAIRING_COMPLETED,
            request_id=sess.id,
            device_id=sess.device_id,
            user_id=sess.user_id
        )
        logger.info(f"[DevicePairing] Pairing muvaffaqiyatli yakunlandi: id={sess.id}, dev={device_id}, user={sess.user_id}")
        return True, "OK", sess

    def cancel_pairing(self, pairing_id: str, user_id: str) -> Tuple[bool, str]:
        """Foydalanuvchi tomonidan juftlash sessiyasini bekor qilish"""
        sess = self.get_session(pairing_id)
        if not sess:
            return False, "NOT_FOUND: Juftlash sessiyasi topilmadi"

        if sess.user_id != str(user_id).strip():
            return False, "UNAUTHORIZED: Sessiya sizning hisobingizga tegishli emas"

        if sess.status in ("COMPLETED", "REVOKED"):
            return True, f"Sessiya allaqachon {sess.status}"

        sess.status = "REVOKED"
        self.save()
        logger.info(f"[DevicePairing] Sessiya bekor qilindi: id={pairing_id}, user={user_id}")
        return True, "Sessiya muvaffaqiyatli bekor qilindi"

    def revoke_sessions_for_device(self, device_id: str, user_id: Optional[str] = None) -> int:
        """Qurilma o'chirilganda unga bog'liq pairing sessiyalarini bekor qilish"""
        count = 0
        dev_id = str(device_id).strip()
        for sess in self._sessions.values():
            if sess.device_id == dev_id:
                if user_id and sess.user_id != str(user_id).strip():
                    continue
                if sess.status != "REVOKED":
                    sess.status = "REVOKED"
                    count += 1
        if count > 0:
            self.save()
        return count

    def cleanup_expired_sessions(self):
        """Muddati o'tgan PENDING sessiyalarni EXPIRED qilish"""
        changed = False
        now = time.time()
        for s in self._sessions.values():
            if s.status == "PENDING" and s.expires_at < now:
                s.status = "EXPIRED"
                changed = True
        if changed:
            self.save()

    # ========================================================
    # 3. PERSISTENCE
    # ========================================================

    def save(self):
        if not self.storage_path or self.storage_path == ":memory:":
            return
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            temp_path = f"{self.storage_path}.tmp.{os.getpid()}"
            data = {
                "sessions": {sid: s.to_dict(include_security_metadata=True) for sid, s in self._sessions.items()}
            }
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.storage_path):
                os.replace(temp_path, self.storage_path)
            else:
                os.rename(temp_path, self.storage_path)
        except Exception as e:
            logger.warning(f"[DevicePairing] Saqlashda xatolik: {e}")

    def load(self):
        if not self.storage_path or self.storage_path == ":memory:" or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions_data = data.get("sessions", {})
            for sid, sdata in sessions_data.items():
                self._sessions[sid] = DevicePairingSession.from_dict(sdata)
        except Exception as e:
            logger.warning(f"[DevicePairing] Yuklashda xatolik: {e}")
