# ========== core/v8/device_auth.py ==========
# Phase 42 — Cryptographic Device Authentication Engine
# Asymmetric Ed25519 challenge-response with replay protection & protocol versioning
# Distinct from SupabaseSessionClaims (user auth) and RemoteAuthSession (remote control)

import time
import uuid
import secrets
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple, List

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

from core.v8.events import RemoteEventType, RemoteAuditLogger
from core.v8.device_enrollment import DeviceEnrollmentManager

logger = logging.getLogger("core.v8.device_auth")


# =====================================================================
# 1. CHALLENGE & SESSION MODELS
# =====================================================================

@dataclass
class DeviceAuthChallenge:
    """
    Agentga yuboriladigan bir martalik tasodifiy chaqiriq (nonce).
    Replay hujumlarining oldini olish uchun faqat bir marta ishlatilishi mumkin.
    """
    id: str  # UUID
    device_id: str
    nonce: str  # 64-belgili hex satr (32-bayt tasodifiy ma'lumot)
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    is_used: bool = False

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return (not self.is_used) and (not self.is_expired)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeviceSession:
    """
    Autentifikatsiyadan o'tgan Agent ↔ Backend kanali sessiyasi.
    SupabaseSessionClaims (veb-foydalanuvchi) va RemoteAuthSession
    (foydalanuvchi bergan masofaviy kompyuter boshqaruvi) dan to'liq ajratilgan.
    """
    session_id: str
    device_id: str
    user_id: str
    token: str  # 64-belgili xavfsiz sessiya tokeni
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    is_active: bool = True
    protocol_version: str = "1.0"
    last_heartbeat_at: float = field(default_factory=time.time)

    @property
    def is_valid(self) -> bool:
        return self.is_active and (time.time() < self.expires_at)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================================
# 2. DEVICE AUTH MANAGER
# =====================================================================

class DeviceAuthManager:
    """
    Qurilmalarni Ed25519 asimmetrik imzo orqali autentifikatsiya qilish menejeri.
    1. Chaqiriq (Challenge) so'rovi -> 32-bayt bir martalik tasodifiy nonce va 60s TTL.
    2. Chaqiriq javobi (Response) -> Imzo tekshiruvi va replay himoyasi.
    3. Muvaffaqiyatli autentifikatsiyadan so'ng DeviceSession beriladi.
    """
    DEFAULT_CHALLENGE_TTL = 60.0  # 60 soniya
    DEFAULT_SESSION_TTL = 86400.0  # 24 soat
    SUPPORTED_PROTOCOL_VERSIONS = {"1.0"}

    _default_instance: Optional["DeviceAuthManager"] = None
    _instance: Optional["DeviceAuthManager"] = None

    def __init__(
        self,
        enrollment_mgr: Optional[DeviceEnrollmentManager] = None,
        storage_path: Optional[str] = None
    ):
        self.enrollment_mgr = enrollment_mgr or DeviceEnrollmentManager.get_default_instance()
        self.storage_path = storage_path
        self._challenges: Dict[str, DeviceAuthChallenge] = {}
        self._sessions: Dict[str, DeviceSession] = {}
        self._audit = RemoteAuditLogger.get_instance()

    @classmethod
    def get_default_instance(
        cls,
        enrollment_mgr: Optional[DeviceEnrollmentManager] = None,
        storage_path: Optional[str] = None
    ) -> "DeviceAuthManager":
        inst = getattr(cls, "_instance", None) or cls._default_instance
        if inst is None:
            cls._default_instance = cls(
                enrollment_mgr=enrollment_mgr,
                storage_path=storage_path
            )
            return cls._default_instance
        return inst

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "DeviceAuthManager":
        return cls.get_default_instance(*args, **kwargs)

    # ========================================================
    # 1. CHALLENGE ISSUANCE
    # ========================================================

    def issue_challenge(self, device_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Agent uchun bir martalik autentifikatsiya chaqirig'ini (nonce) yaratish.
        Qurilma avval hisobga enroll qilingan va revoked bo'lmagan bo'lishi shart.
        """
        dev_id = str(device_id).strip()
        cred = self.enrollment_mgr.get_credential(dev_id)

        if not cred or cred.is_revoked:
            return False, "NOT_ENROLLED: Qurilma hisobga biriktirilmagan yoki bekor qilingan (revoked)", None

        now = time.time()
        nonce = secrets.token_hex(32)  # 32 bayt = 64 hex belgilar
        challenge_id = str(uuid.uuid4())

        challenge = DeviceAuthChallenge(
            id=challenge_id,
            device_id=dev_id,
            nonce=nonce,
            created_at=now,
            expires_at=now + self.DEFAULT_CHALLENGE_TTL,
            is_used=False
        )
        self._challenges[challenge_id] = challenge

        self._audit.log(
            RemoteEventType.AUTH_CHALLENGE_ISSUED,
            request_id=challenge_id,
            device_id=dev_id,
            user_id=cred.user_id,
            ttl=self.DEFAULT_CHALLENGE_TTL
        )
        logger.info(f"[DeviceAuth] Yangi challenge yaratildi: challenge_id={challenge_id}, dev={dev_id}")

        return True, "OK", {
            "challenge_id": challenge_id,
            "nonce": nonce,
            "expires_at": challenge.expires_at,
            "ttl": self.DEFAULT_CHALLENGE_TTL
        }

    # ========================================================
    # 2. CHALLENGE VERIFICATION & AUTHENTICATION
    # ========================================================

    @staticmethod
    def canonical_challenge_message(
        device_id: str,
        nonce: str,
        timestamp: float,
        protocol_version: str = "1.0"
    ) -> bytes:
        """Imzolanishi shart bo'lgan kanonik xabar formati"""
        # Standartlashtirilgan deterministik satr
        raw = f"{str(device_id).strip()}|{str(nonce).strip()}|{float(timestamp):.3f}|{str(protocol_version).strip()}"
        return raw.encode("utf-8")

    def verify_challenge_response(
        self,
        device_id: str,
        challenge_id: str,
        signature_hex: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[DeviceSession]]:
        """
        Agent tomonidan yuborilgan Ed25519 imzoni tekshirish.
        1. Protokol versiyasini tekshirish.
        2. Chaqiriqning (nonce) mavjudligi, muddati va ISHLATILMAGANLIGINI (Replay protection) tekshirish.
        3. Darhol chaqiriqni is_used=True qilish (takroriy foydalanishni to'sish).
        4. Ommaviy kalit orqali imzoni verifikatsiya qilish.
        5. Agar to'g'ri bo'lsa, DeviceSession berish va holatni ONLINE qilish.
        """
        dev_id = str(device_id).strip()
        proto_ver = str(context.get("protocol_version", "1.0")).strip()

        # 1. Protokol versiyasi tekshiruvi
        if proto_ver not in self.SUPPORTED_PROTOCOL_VERSIONS:
            logger.warning(f"[DeviceAuth] Noma'lum protokol versiyasi: {proto_ver}")
            return False, f"UNSUPPORTED_PROTOCOL: Protokol versiyasi '{proto_ver}' qo'llab-quvvatlanmaydi", None

        # 2. Challenge tekshiruvi
        challenge = self._challenges.get(challenge_id)
        if not challenge:
            return False, "INVALID_CHALLENGE: Chaqiriq (challenge) topilmadi", None

        if challenge.device_id != dev_id:
            return False, "DEVICE_MISMATCH: Chaqiriq boshqa qurilma uchun berilgan", None

        if challenge.is_used:
            self._audit.log(
                RemoteEventType.DEVICE_AUTH_FAILED,
                request_id=challenge_id,
                device_id=dev_id,
                reason="replay_attack_detected"
            )
            logger.warning(f"[DeviceAuth] Replay hujumi aniqlandi! Nonce allaqachon ishlatilgan: id={challenge_id}")
            return False, "REPLAY_DETECTED: Ushbu chaqiriq (nonce) allaqachon ishlatilgan", None

        if challenge.is_expired:
            challenge.is_used = True
            return False, "CHALLENGE_EXPIRED: Chaqiriq muddati o'tgan (60 soniyadan oshdi)", None

        # 3. REPLAY HIMOYA: Nonceni darhol ishlatilgan deb belgilaymiz!
        challenge.is_used = True

        # 4. Kredensial va Ommaviy kalit tekshiruvi
        cred = self.enrollment_mgr.get_credential(dev_id)
        if not cred or cred.is_revoked:
            return False, "NOT_ENROLLED: Qurilma kredensiali topilmadi yoki bekor qilingan", None

        # 5. Kanonik xabarni tuzish
        ts = float(context.get("timestamp", challenge.created_at))
        expected_msg = self.canonical_challenge_message(
            device_id=dev_id,
            nonce=challenge.nonce,
            timestamp=ts,
            protocol_version=proto_ver
        )

        # 6. Ed25519 Imzosini tekshirish
        try:
            pub_bytes = bytes.fromhex(cred.public_key)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            sig_bytes = bytes.fromhex(signature_hex)
            public_key.verify(sig_bytes, expected_msg)
        except InvalidSignature:
            self._audit.log(
                RemoteEventType.DEVICE_AUTH_FAILED,
                request_id=challenge_id,
                device_id=dev_id,
                reason="invalid_signature"
            )
            logger.warning(f"[DeviceAuth] Noto'g'ri Ed25519 imzo: dev={dev_id}")
            return False, "INVALID_SIGNATURE: Ed25519 raqamli imzosi noto'g'ri", None
        except Exception as e:
            self._audit.log(
                RemoteEventType.DEVICE_AUTH_FAILED,
                request_id=challenge_id,
                device_id=dev_id,
                reason="crypto_error"
            )
            logger.warning(f"[DeviceAuth] Kriptografik xatolik: {e}")
            return False, f"CRYPTO_ERROR: Imzoni tekshirishda xatolik ({e})", None

        # 7. DeviceSession yaratish
        now = time.time()
        session_token = secrets.token_hex(32)
        dev_session = DeviceSession(
            session_id=str(uuid.uuid4()),
            device_id=dev_id,
            user_id=cred.user_id,
            token=session_token,
            created_at=now,
            expires_at=now + self.DEFAULT_SESSION_TTL,
            is_active=True,
            protocol_version=proto_ver,
            last_heartbeat_at=now
        )
        self._sessions[session_token] = dev_session

        # 8. Device holatini yangilash (Online)
        try:
            dev = self.enrollment_mgr.account_device_mgr.get_device(dev_id, user_id=cred.user_id)
            if dev:
                dev.status = "online"
                dev.last_seen_at = now
                dev.last_heartbeat_at = now
                self.enrollment_mgr.account_device_mgr.save()
        except Exception as e:
            logger.debug(f"[DeviceAuth] Device holatini yangilashda xato: {e}")

        self._audit.log(
            RemoteEventType.DEVICE_AUTH_SUCCESS,
            request_id=dev_session.session_id,
            device_id=dev_id,
            user_id=cred.user_id,
            protocol_version=proto_ver
        )
        logger.info(f"[DeviceAuth] Qurilma autentifikatsiyadan o'tdi: dev={dev_id}, sess={dev_session.session_id}")
        return True, "OK", dev_session

    def get_session(self, session_token: str) -> Optional[DeviceSession]:
        """Faol DeviceSession ni olish"""
        sess = self._sessions.get(session_token)
        if sess and sess.is_valid:
            return sess
        return None

    def get_active_sessions_for_device(self, device_id: str) -> List[DeviceSession]:
        """Qurilmaning barcha faol sessiyalari ro'yxatini olish"""
        dev_id = str(device_id).strip()
        return [s for s in self._sessions.values() if s.device_id == dev_id and s.is_valid]

    def terminate_device_sessions(self, device_id: str) -> int:
        """Qurilmaning barcha faol sessiyalarini bekor qilish (Revocation kaskadi)"""
        dev_id = str(device_id).strip()
        count = 0
        for sess in self._sessions.values():
            if sess.device_id == dev_id and sess.is_active:
                sess.is_active = False
                count += 1
        return count
