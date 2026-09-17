# ========== core/v8/account_auth.py ==========
# Phase 41 — Account Registration & Authentication System
# Secure Multi-Tenant Identity, Session Issuance & Token Management
# Strictly separated from device RemoteAuthSession

import os
import time
import uuid
import secrets
import hashlib
import hmac
import re
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple, List

from core.v8.events import RemoteEventType, RemoteAuditLogger
from core.v8.account_device import MikasaUser, AccountDeviceManager

logger = logging.getLogger("core.v8.account_auth")


# =====================================================================
# 1. PASSWORD SECURITY & VALIDATION
# =====================================================================

class PasswordManager:
    """
    PBKDF2-HMAC-SHA256 password hashing and constant-time verification.
    OWASP recommended minimum 600,000 iterations and 16-byte random salt.
    """
    ALGORITHM = "pbkdf2_sha256"
    ITERATIONS = 600_000
    SALT_BYTES = 16

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Parolni PBKDF2-HMAC-SHA256 algoritmi va xavfsiz salt bilan heshlash"""
        if not isinstance(password, str) or not password:
            raise ValueError("Parol bo'sh bo'lishi mumkin emas")
        salt = secrets.token_bytes(cls.SALT_BYTES)
        key = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=cls.ITERATIONS
        )
        return f"{cls.ALGORITHM}${cls.ITERATIONS}${salt.hex()}${key.hex()}"

    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        """Kiritilgan parolni heshlangan parol bilan constant-time taqqoslash"""
        if not password or not password_hash or not isinstance(password_hash, str):
            return False
        sep = "$" if "$" in password_hash else ":"
        parts = password_hash.split(sep)
        if len(parts) != 4:
            return False
        algo, iter_str, salt_hex, expected_hash_hex = parts
        if algo not in ("pbkdf2", "pbkdf2:sha256", "pbkdf2_sha256"):
            return False
        try:
            iterations = int(iter_str)
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(expected_hash_hex)
        except Exception:
            return False

        computed_key = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=iterations
        )
        return hmac.compare_digest(computed_key, expected_key)

    @classmethod
    def validate_password_strength(
        cls,
        password: str,
        confirmation: Optional[str] = None,
        confirm_password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Parol xavfsizlik mezonlari va tasdiq mosligini tekshirish"""
        if not password or not isinstance(password, str):
            return False, "Parol kiritilishi shart"
        if len(password) < 8:
            return False, "Parol kamida 8 ta belgidan iborat bo'lishi kerak"
        if len(password) > 128:
            return False, "Parol 128 belgidan oshmasligi kerak"
        if not re.search(r"[a-zA-Z]", password):
            return False, "Parolda kamida bitta harf bo'lishi kerak"
        if not re.search(r"[0-9]", password):
            return False, "Parolda kamida bitta raqam bo'lishi kerak"
        conf = confirmation if confirmation is not None else confirm_password
        if conf is not None and password != conf:
            return False, "Parollar bir-biriga mos kelmadi"
        return True, "OK"

    validate_strength = validate_password_strength


def validate_username(username: str) -> Tuple[bool, str]:
    """Username tekshiruvi: 3-32 belgi, faqat a-z, A-Z, 0-9, _, -"""
    if not username or not isinstance(username, str):
        return False, "Username kiritilishi shart"
    clean = username.strip()
    if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", clean):
        return False, "Username 3-32 belgidan iborat bo'lishi va faqat harf, raqam, '_' yoki '-' dan iborat bo'lishi kerak"
    return True, clean


def validate_email(email: Optional[str], allow_empty: bool = True) -> Tuple[bool, str]:
    """Email formati tekshiruvi va lowercase canonical formatga keltirish"""
    if email is None or (isinstance(email, str) and not email.strip()):
        if allow_empty:
            return True, ""
        return False, "Email kiritilishi shart"
    if not isinstance(email, str):
        return False, "Email satr bo'lishi kerak"
    clean = email.strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, clean) or len(clean) > 254:
        return False, "Noto'g'ri email formati"
    return True, clean


# =====================================================================
# 2. SESSION & TOKEN MODELS
# =====================================================================

@dataclass
class AccountSession:
    """
    Foydalanuvchi veb/mijoz autentifikatsiya sessiyasi.
    RemoteAuthSession (kompyuter masofaviy boshqaruvi) dan to'liq ajratilgan.
    """
    id: str
    user_id: str
    token_hash: str
    token: str = ""
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 7 * 86400.0)  # 7 kun
    last_activity_at: float = field(default_factory=time.time)
    ip_hash: str = ""
    user_agent: str = ""
    revoked_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.is_valid()

    def is_valid(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return (self.revoked_at is None) and (now < self.expires_at)

    def revoke(self):
        self.revoked_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Tashqi API uchun xavfsiz lug'at (token_hash chiqarilmaydi)"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_activity_at": self.last_activity_at,
            "is_active": self.is_active,
            "user_agent": self.user_agent
        }

    def to_storage_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AccountSession":
        return cls(**data)


@dataclass
class VerificationToken:
    """
    Email tasdiqlash yoki parolni tiklash uchun bir martalik token modeli.
    Plaintext token hech qachon saqlanmaydi, faqat token_hash saqlanadi.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    token_hash: str = ""
    token_type: str = "EMAIL_VERIFICATION"  # "EMAIL_VERIFICATION", "PASSWORD_RESET"
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    is_used: bool = False
    used_at: Optional[float] = None
    token: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.token_hash and self.token:
            self.token_hash = hashlib.sha256(self.token.encode("utf-8")).hexdigest()

    def is_valid(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return (not self.is_used) and (now < self.expires_at)

    def mark_used(self):
        self.is_used = True
        self.used_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("token", None)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationToken":
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)


# =====================================================================
# 3. EMAIL VERIFICATION PROVIDERS
# =====================================================================

class EmailVerificationProvider(ABC):
    """Email xabarnomalarini yuborish uchun abstrakt interfeys"""
    @abstractmethod
    def send_verification_email(self, email: str, raw_token: str, username: str) -> bool:
        pass

    @abstractmethod
    def send_password_reset_email(self, email: str, raw_token: str, username: str) -> bool:
        pass


class MockEmailVerificationProvider(EmailVerificationProvider):
    """Testlar va lokal ishlab chiqish uchun xotirada saqlovchi email provayderi"""
    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []

    def send_verification_email(self, email: str, raw_token: str, username: str) -> bool:
        self.sent_emails.append({
            "type": "EMAIL_VERIFICATION",
            "email": email,
            "username": username,
            "raw_token": raw_token,
            "token": raw_token,
            "sent_at": time.time()
        })
        logger.info(f"[MockEmail] Email tasdiqlash xabari yuborildi: to={email}")
        return True

    def send_password_reset_email(self, email: str, raw_token: str, username: str) -> bool:
        self.sent_emails.append({
            "type": "PASSWORD_RESET",
            "email": email,
            "username": username,
            "raw_token": raw_token,
            "token": raw_token,
            "sent_at": time.time()
        })
        logger.info(f"[MockEmail] Parolni tiklash xabari yuborildi: to={email}")
        return True


# =====================================================================
# 4. RATE LIMITER
# =====================================================================

class AuthRateLimiter:
    """
    Login urinishlari va ro'yxatdan o'tish himoyasi (Brute-force protection).
    5 ta muvaffaqiyatsiz urinish -> 5 daqiqa cooldown.
    """
    MAX_FAILED_ATTEMPTS = 5
    COOLDOWN_SECONDS = 300.0  # 5 daqiqa
    REGISTRATION_LIMIT_PER_HOUR = 15

    def __init__(self):
        self._failed_logins: Dict[str, List[float]] = {}  # key -> list of failure timestamps
        self._registrations: Dict[str, List[float]] = {}  # ip -> list of timestamps

    def _hash_key(self, identifier: str) -> str:
        return hashlib.sha256(str(identifier).strip().lower().encode("utf-8")).hexdigest()[:16]

    def record_login_failure(self, identifier: str, ip: Optional[str] = None):
        now = time.time()
        key_id = f"id:{self._hash_key(identifier)}"
        self._failed_logins.setdefault(key_id, []).append(now)
        if ip:
            key_ip = f"ip:{self._hash_key(ip)}"
            self._failed_logins.setdefault(key_ip, []).append(now)

    def record_login_success(self, identifier: str, ip: Optional[str] = None):
        key_id = f"id:{self._hash_key(identifier)}"
        self._failed_logins.pop(key_id, None)

    def is_login_rate_limited(self, identifier: str, ip: Optional[str] = None) -> Tuple[bool, float]:
        now = time.time()
        cutoff = now - self.COOLDOWN_SECONDS

        keys_to_check = [f"id:{self._hash_key(identifier)}"]
        if ip:
            keys_to_check.append(f"ip:{self._hash_key(ip)}")

        for key in keys_to_check:
            timestamps = self._failed_logins.get(key, [])
            recent = [t for t in timestamps if t > cutoff]
            self._failed_logins[key] = recent
            if len(recent) >= self.MAX_FAILED_ATTEMPTS:
                remaining = (recent[0] + self.COOLDOWN_SECONDS) - now
                return True, max(1.0, remaining)

        return False, 0.0

    def record_registration(self, ip: Optional[str]):
        if not ip:
            return
        now = time.time()
        key = f"reg:{self._hash_key(ip)}"
        self._registrations.setdefault(key, []).append(now)

    def is_registration_rate_limited(self, ip: Optional[str]) -> bool:
        if not ip:
            return False
        now = time.time()
        cutoff = now - 3600.0  # 1 soat
        key = f"reg:{self._hash_key(ip)}"
        timestamps = self._registrations.get(key, [])
        recent = [t for t in timestamps if t > cutoff]
        self._registrations[key] = recent
        return len(recent) >= self.REGISTRATION_LIMIT_PER_HOUR


# =====================================================================
# 5. ACCOUNT AUTH MANAGER
# =====================================================================

class AccountAuthManager:
    """
    Mikasa AI markaziy autentifikatsiya, hisob yaratish va sessiya dvigateli.
    """
    _default_instance: Optional["AccountAuthManager"] = None

    SESSION_TTL = 7 * 86400.0       # 7 kun
    EMAIL_VERIFY_TTL = 86400.0      # 24 soat
    PASSWORD_RESET_TTL = 900.0      # 15 daqiqa

    def __init__(
        self,
        account_device_manager: Optional[AccountDeviceManager] = None,
        account_device_mgr: Optional[AccountDeviceManager] = None,
        email_provider: Optional[EmailVerificationProvider] = None,
        storage_path: Optional[str] = None
    ):
        self.account_device_mgr = account_device_manager or account_device_mgr or AccountDeviceManager.get_default_instance()
        self.email_provider = email_provider or MockEmailVerificationProvider()
        self.rate_limiter = AuthRateLimiter()
        self._audit = RemoteAuditLogger.get_instance()

        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "v8_account_auth.json"
        )

        self._sessions: Dict[str, AccountSession] = {}           # session_id -> AccountSession
        self._sessions_by_hash: Dict[str, str] = {}              # token_hash -> session_id
        self._user_sessions: Dict[str, List[str]] = {}           # user_id -> List[session_id]
        self._tokens: Dict[str, VerificationToken] = {}          # token_id -> VerificationToken
        self._tokens_by_hash: Dict[str, str] = {}                # token_hash -> token_id

        self.load()

    @classmethod
    def get_default_instance(cls, storage_path: Optional[str] = None) -> "AccountAuthManager":
        inst = getattr(cls, "_instance", None) or cls._default_instance
        if inst is None:
            cls._default_instance = cls(storage_path=storage_path)
            return cls._default_instance
        return inst

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "AccountAuthManager":
        return cls.get_default_instance(*args, **kwargs)

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        """Kriptografik tokenning SHA-256 heshini hisoblash"""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # ========================================================
    # A. REGISTRATION
    # ========================================================

    def register(
        self,
        username: str,
        arg2: Optional[str] = None,
        arg3: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        password_confirmation: Optional[str] = None,
        confirm_password: Optional[str] = None,
        ip: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[MikasaUser], Optional[AccountSession]]:
        """
        Yangi Mikasa foydalanuvchi hisobini ro'yxatdan o'tkazish.
        Returns (success, message, user_object, session_object).
        """
        effective_email = email
        effective_pwd = password
        effective_conf = password_confirmation or confirm_password
        effective_ip = ip or client_ip

        if arg2 is not None:
            if "@" in arg2:
                effective_email = arg2
                if arg3 is not None:
                    effective_pwd = arg3
            else:
                effective_pwd = arg2
                if arg3 is not None:
                    effective_email = arg3

        if not effective_pwd:
            return False, "Parol kiritilishi shart", None, None

        # 1. Registration abuse check
        if self.rate_limiter.is_registration_rate_limited(effective_ip):
            return False, "Juda ko'p ro'yxatdan o'tish so'rovlari yuborildi. Iltimos, keyinroq urinib ko'ring.", None, None

        # 2. Username validation
        is_u_ok, uname_or_err = validate_username(username)
        if not is_u_ok:
            return False, uname_or_err, None, None
        clean_username = uname_or_err

        # 3. Email validation (optional)
        is_e_ok, email_or_err = validate_email(effective_email, allow_empty=True)
        if not is_e_ok:
            return False, email_or_err, None, None
        clean_email = email_or_err

        # 4. Password validation
        is_p_ok, p_err = PasswordManager.validate_password_strength(effective_pwd, effective_conf)
        if not is_p_ok:
            return False, p_err, None, None

        # 5. Uniqueness checks (case-insensitive)
        if self.account_device_mgr.get_user_by_username(clean_username):
            return False, "Ushbu username allaqachon mavjud yoki band qilingan", None, None

        if clean_email and self.account_device_mgr.get_user_by_email(clean_email):
            return False, "Ushbu email allaqachon mavjud yoki ro'yxatdan o'tilgan", None, None

        # 6. Hash password
        pwd_hash = PasswordManager.hash_password(effective_pwd)

        # 7. Create user in AccountDeviceManager
        user = self.account_device_mgr.create_user(
            username=clean_username,
            email=clean_email,
            password_hash=pwd_hash,
            is_verified=False
        )
        self.rate_limiter.record_registration(effective_ip)

        # 8. Generate Email Verification Token
        raw_vtoken, token_obj = self._create_verification_token(user.id, "EMAIL_VERIFICATION", self.EMAIL_VERIFY_TTL)
        if user.email:
            self.email_provider.send_verification_email(user.email, raw_vtoken, user.username)

        # 9. Create initial AccountSession for immediate authenticated state
        raw_stoken, session = self._create_account_session(
            user_id=user.id,
            ip=effective_ip,
            user_agent=user_agent or "Mikasa App"
        )
        session.token = raw_stoken

        # 10. Audit Event
        self._audit.log(
            RemoteEventType.ACCOUNT_REGISTERED,
            user_id=user.id,
            details={"username": user.username, "email": user.email}
        )
        logger.info(f"[AccountAuth] Yangi foydalanuvchi muvaffaqiyatli ro'yxatga olindi: id={user.id}, username={user.username}")
        return True, "Akkaunt muvaffaqiyatli yaratildi", user, session

    # ========================================================
    # B. LOGIN & SESSION ISSUANCE
    # ========================================================

    def login(
        self,
        identifier: Optional[str] = None,
        password: Optional[str] = None,
        username_or_email: Optional[str] = None,
        ip: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[MikasaUser], Optional[AccountSession]]:
        """
        Foydalanuvchi tizimga kirishi (Username yoki Email orqali).
        Returns (success, message, user_object, session_object).
        """
        clean_id = str(identifier or username_or_email or "").strip()
        effective_ip = ip or client_ip
        generic_error = "Noto'g'ri username/email yoki parol (Invalid username/email or password)"
        if not clean_id or not password:
            return False, generic_error, None, None

        # 1. Rate Limiter check
        is_limited, sec_left = self.rate_limiter.is_login_rate_limited(clean_id, effective_ip)
        if is_limited:
            return False, f"Juda ko'p xato urinishlar. Iltimos, {int(sec_left)} soniya kuting.", None, None

        # 2. Resolve User by username OR email
        user = self.account_device_mgr.get_user_by_username(clean_id)
        if not user:
            user = self.account_device_mgr.get_user_by_email(clean_id)

        # 3. Check credentials (Generic error on failure)
        generic_error = "Noto'g'ri username/email yoki parol (Invalid username/email or password)"
        if not user or not user.password_hash:
            self.rate_limiter.record_login_failure(clean_id, effective_ip)
            self._audit.log(RemoteEventType.ACCOUNT_LOGIN_FAILED, details={"identifier": clean_id, "reason": "User not found"})
            return False, generic_error, None, None

        if not PasswordManager.verify_password(password, user.password_hash):
            self.rate_limiter.record_login_failure(clean_id, effective_ip)
            self._audit.log(RemoteEventType.ACCOUNT_LOGIN_FAILED, user_id=user.id, details={"reason": "Bad password"})
            return False, generic_error, None, None

        if not user.is_active:
            return False, "Ushbu hisob bloklangan yoki bekor qilingan", None, None

        # 4. Successful login
        self.rate_limiter.record_login_success(clean_id, effective_ip)
        user.last_login_at = time.time()
        self.account_device_mgr.update_user(user)

        # 5. Issue new AccountSession
        raw_token, session = self._create_account_session(
            user_id=user.id,
            ip=effective_ip,
            user_agent=user_agent or "Mikasa Desktop"
        )
        session.token = raw_token

        self._audit.log(
            RemoteEventType.ACCOUNT_LOGIN_SUCCESS,
            user_id=user.id,
            details={"session_id": session.id}
        )
        logger.info(f"[AccountAuth] Foydalanuvchi tizimga kirdi: user={user.username}, session={session.id}")
        return True, "Muvaffaqiyatli kirildi", user, session

    def _create_account_session(
        self,
        user_id: str,
        ip: Optional[str] = None,
        user_agent: str = ""
    ) -> Tuple[str, AccountSession]:
        """Kriptografik random token va yangi AccountSession yaratish"""
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)
        session_id = str(uuid.uuid4())
        ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16] if ip else ""

        session = AccountSession(
            id=session_id,
            user_id=user_id,
            token_hash=token_hash,
            token=raw_token,
            created_at=time.time(),
            expires_at=time.time() + self.SESSION_TTL,
            last_activity_at=time.time(),
            ip_hash=ip_hash,
            user_agent=user_agent
        )
        self._sessions[session_id] = session
        self._sessions_by_hash[token_hash] = session_id
        self._user_sessions.setdefault(user_id, []).append(session_id)
        self.save()
        return raw_token, session

    def authenticate_token(self, raw_token: str) -> Tuple[Optional[AccountSession], Optional[MikasaUser]]:
        """
        So'rovdan kelgan Bearer tokenni tekshirish va foydalanuvchini aniqlash.
        Muddati o'tgan yoki bekor qilingan bo'lsa (None, None) qaytaradi.
        """
        if not raw_token or not isinstance(raw_token, str):
            return None, None
        token_hash = self._hash_token(raw_token.strip())
        session_id = self._sessions_by_hash.get(token_hash)
        if not session_id:
            return None, None
        session = self._sessions.get(session_id)
        if not session or not session.is_valid():
            return None, None

        # Update last activity
        session.last_activity_at = time.time()
        session.token = raw_token.strip()
        user = self.account_device_mgr.get_user(session.user_id)
        if not user or not user.is_active:
            return None, None
        return session, user

    # ========================================================
    # C. LOGOUT & LOGOUT-ALL
    # ========================================================

    def logout(self, raw_token: str) -> bool:
        """Joriy sessiyani bekor qilish"""
        if not raw_token:
            return False
        token_hash = self._hash_token(raw_token.strip())
        session_id = self._sessions_by_hash.get(token_hash)
        if not session_id:
            return False
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.revoke()
        self.save()

        self._audit.log(
            RemoteEventType.ACCOUNT_LOGOUT,
            user_id=session.user_id,
            details={"session_id": session.id}
        )
        return True

    def logout_all(self, user_id: str) -> int:
        """Foydalanuvchining barcha faol autentifikatsiya sessiyalarini bekor qilish"""
        uid = str(user_id).strip()
        count = 0
        now = time.time()
        for session_id in self._user_sessions.get(uid, []):
            sess = self._sessions.get(session_id)
            if sess and sess.is_valid(now):
                sess.revoke()
                count += 1

        self.save()
        self._audit.log(
            RemoteEventType.ACCOUNT_LOGOUT_ALL,
            user_id=uid,
            details={"revoked_count": count}
        )
        logger.info(f"[AccountAuth] Barcha sessiyalar bekor qilindi: user={uid}, count={count}")
        return count

    def get_active_sessions_for_user(self, user_id: str) -> List[AccountSession]:
        """Foydalanuvchining faol sessiyalari ro'yxati"""
        uid = str(user_id).strip()
        result = []
        now = time.time()
        for s_id in self._user_sessions.get(uid, []):
            sess = self._sessions.get(s_id)
            if sess and sess.is_valid(now):
                result.append(sess)
        return result

    # ========================================================
    # D. EMAIL VERIFICATION
    # ========================================================

    def _create_verification_token(
        self,
        user_id: str,
        token_type: str,
        ttl_seconds: float
    ) -> Tuple[str, VerificationToken]:
        """Kriptografik random token va uning heshlangan modelini yaratish"""
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)
        token_id = str(uuid.uuid4())

        tok = VerificationToken(
            id=token_id,
            user_id=user_id,
            token_hash=token_hash,
            token_type=token_type,
            created_at=time.time(),
            expires_at=time.time() + ttl_seconds
        )
        self._tokens[token_id] = tok
        self._tokens_by_hash[token_hash] = token_id
        self.save()
        return raw_token, tok

    def verify_email(self, raw_token: str) -> Tuple[bool, str]:
        """Email tasdiqlash tokenini tekshirish va hisobni tasdiqlangan qilish"""
        if not raw_token or not isinstance(raw_token, str):
            return False, "Tasdiqlash kodi ko'rsatilmadi"
        token_hash = self._hash_token(raw_token.strip())
        token_id = self._tokens_by_hash.get(token_hash)
        if not token_id:
            tok = self._tokens.get(raw_token.strip()) or self._tokens.get(token_hash)
            if not tok:
                return False, "Yaroqsiz yoki muddati o'tgan tasdiqlash kodi"
        else:
            tok = self._tokens.get(token_id)

        if not tok or tok.token_type.upper() != "EMAIL_VERIFICATION":
            return False, "Yaroqsiz tasdiqlash kodi"

        if tok.is_used:
            return False, "Ushbu tasdiqlash kodi allaqachon ishlatilgan"

        if not tok.is_valid():
            return False, "Tasdiqlash kodining muddati o'tgan"

        user = self.account_device_mgr.get_user(tok.user_id)
        if not user:
            return False, "Foydalanuvchi hisobi topilmadi"

        tok.mark_used()
        user.is_verified = True
        self.account_device_mgr.update_user(user)
        self.save()

        self._audit.log(RemoteEventType.EMAIL_VERIFIED, user_id=user.id)
        logger.info(f"[AccountAuth] Email tasdiqlandi: user={user.username}, email={user.email}")
        return True, "Email manzilingiz muvaffaqiyatli tasdiqlandi"

    # ========================================================
    # E. FORGOT & RESET PASSWORD
    # ========================================================

    def request_password_reset(self, identifier: str) -> Tuple[bool, str, Optional[str]]:
        """
        Parolni tiklash so'rovi.
        Foydalanuvchi mavjudligini oshkor qilmaslik uchun har doim bir xil generic xabar qaytariladi.
        """
        clean_id = str(identifier).strip()
        generic_msg = "If account exists, a reset message has been sent."
        if not clean_id:
            return True, generic_msg, None

        user = self.account_device_mgr.get_user_by_username(clean_id)
        if not user:
            user = self.account_device_mgr.get_user_by_email(clean_id)

        if not user or not user.email:
            # Prevent user enumeration
            return True, generic_msg, None

        raw_token, tok = self._create_verification_token(user.id, "PASSWORD_RESET", self.PASSWORD_RESET_TTL)
        self.email_provider.send_password_reset_email(user.email, raw_token, user.username)

        self._audit.log(RemoteEventType.PASSWORD_RESET_REQUESTED, user_id=user.id)
        logger.info(f"[AccountAuth] Parolni tiklash so'raldi: user={user.username}")
        return True, generic_msg, raw_token

    def reset_password(
        self,
        raw_token: str,
        new_password: str,
        new_password_confirmation: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Tiklash kodi orqali yangi parol o'rnatish"""
        if not raw_token or not isinstance(raw_token, str):
            return False, "Tiklash kodi kiritilishi shart"

        token_hash = self._hash_token(raw_token.strip())
        token_id = self._tokens_by_hash.get(token_hash)
        if not token_id:
            tok = self._tokens.get(raw_token.strip()) or self._tokens.get(token_hash)
            if not tok:
                return False, "Yaroqsiz yoki muddati o'tgan tiklash kodi (topilmadi)"
        else:
            tok = self._tokens.get(token_id)

        if not tok or tok.token_type.upper() != "PASSWORD_RESET":
            return False, "Yaroqsiz tiklash kodi (topilmadi)"

        if tok.is_used:
            return False, "Ushbu tiklash kodi allaqachon ishlatilgan"

        if not tok.is_valid():
            return False, "Tiklash kodining muddati o'tgan"

        is_p_ok, p_err = PasswordManager.validate_password_strength(new_password, new_password_confirmation)
        if not is_p_ok:
            return False, p_err

        user = self.account_device_mgr.get_user(tok.user_id)
        if not user:
            return False, "Foydalanuvchi hisobi topilmadi"

        tok.mark_used()
        user.password_hash = PasswordManager.hash_password(new_password)
        self.account_device_mgr.update_user(user)

        # Revoke all old sessions for security
        self.logout_all(user.id)
        self.save()

        self._audit.log(RemoteEventType.PASSWORD_RESET_COMPLETED, user_id=user.id)
        self._audit.log(RemoteEventType.PASSWORD_CHANGED, user_id=user.id)
        logger.info(f"[AccountAuth] Parol tiklash orqali yangilandi: user={user.username}")
        return True, "Parol muvaffaqiyatli yangilandi. Yangi parol bilan tizimga kiring."

    # ========================================================
    # F. CHANGE PASSWORD (AUTHENTICATED)
    # ========================================================

    def change_password(
        self,
        user_id: str,
        current_password: Optional[str] = None,
        new_password: Optional[str] = None,
        old_password: Optional[str] = None,
        new_password_confirmation: Optional[str] = None,
        confirm_password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Autentifikatsiyadan o'tgan foydalanuvchining parolini o'zgartirish"""
        effective_old = current_password or old_password or ""
        effective_new = new_password or ""
        effective_conf = new_password_confirmation or confirm_password

        uid = str(user_id).strip()
        user = self.account_device_mgr.get_user(uid)
        if not user:
            return False, "Foydalanuvchi topilmadi"

        if not PasswordManager.verify_password(effective_old, user.password_hash):
            return False, "Joriy parol noto'g'ri kiritildi"

        is_p_ok, p_err = PasswordManager.validate_password_strength(effective_new, effective_conf)
        if not is_p_ok:
            return False, p_err

        user.password_hash = PasswordManager.hash_password(new_password)
        self.account_device_mgr.update_user(user)

        # Revoke all other sessions
        self.logout_all(user.id)
        self.save()

        self._audit.log(RemoteEventType.PASSWORD_CHANGED, user_id=user.id)
        logger.info(f"[AccountAuth] Parol o'zgartirildi: user={user.username}")
        return True, "Parol muvaffaqiyatli o'zgartirildi. Barcha boshqa sessiyalar to'xtatildi."

    # ========================================================
    # G. PERSISTENCE
    # ========================================================

    def save(self):
        """Sessiyalar va tokenlarni xavfsiz JSON faylga atomik saqlash"""
        if not self.storage_path:
            return
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            data = {
                "sessions": {k: v.to_storage_dict() for k, v in self._sessions.items()},
                "sessions_by_hash": self._sessions_by_hash,
                "user_sessions": self._user_sessions,
                "tokens": {k: v.to_dict() for k, v in self._tokens.items()},
                "tokens_by_hash": self._tokens_by_hash
            }
            tmp_path = f"{self.storage_path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.storage_path):
                os.replace(tmp_path, self.storage_path)
            else:
                os.rename(tmp_path, self.storage_path)
        except Exception as e:
            logger.error(f"[AccountAuthManager] Saqlashda xatolik: {e}")

    def load(self):
        """Fayldan saqlangan sessiyalar va tokenlarni tiklash"""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            sessions_raw = data.get("sessions", {})
            self._sessions = {k: AccountSession.from_dict(v) for k, v in sessions_raw.items()}
            self._sessions_by_hash = data.get("sessions_by_hash", {})
            self._user_sessions = data.get("user_sessions", {})

            tokens_raw = data.get("tokens", {})
            self._tokens = {k: VerificationToken.from_dict(v) for k, v in tokens_raw.items()}
            self._tokens_by_hash = data.get("tokens_by_hash", {})

            logger.info(f"[AccountAuthManager] Yuklandi: {len(self._sessions)} ta sessiya, {len(self._tokens)} ta token")
        except Exception as e:
            logger.error(f"[AccountAuthManager] Yuklashda xatolik: {e}")
