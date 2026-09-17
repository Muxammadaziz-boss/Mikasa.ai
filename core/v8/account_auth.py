# ========== core/v8/account_auth.py ==========
# Phase 41 — Supabase Auth Integration & Token Verification
# Central Identity Provider: Supabase Auth (auth.users)
# Application Profiles: public.profiles (1:1 with auth.users.id UUID)
# Strict Separation: Supabase Auth Session vs RemoteAuthSession (PC Agent control)
# Zero Backend Password Storage: Mikasa never receives or stores passwords.

import os
import time
import base64
import hmac
import hashlib
import json
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List

from core.v8.events import RemoteAuditLogger
from core.v8.account_device import MikasaUser, Device, AccountDeviceManager

logger = logging.getLogger("core.v8.account_auth")


# =====================================================================
# 1. INPUT VALIDATION RULES
# =====================================================================

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
# 2. SUPABASE SESSION MODEL
# =====================================================================

@dataclass
class SupabaseSessionClaims:
    """
    Supabase Auth JWT claims modeli.
    Web va mijoz ilovalari autentifikatsiyasi uchun xizmat qiladi.
    RemoteAuthSession (kompyuter masofaviy boshqaruvi) dan to'liq ajratilgan.
    """
    user_id: str  # sub (auth.users.id)
    email: str = ""
    role: str = "authenticated"
    exp: float = 0.0
    iat: float = field(default_factory=time.time)
    username: str = ""
    display_name: str = ""
    avatar_url: str = ""
    raw_claims: Dict[str, Any] = field(default_factory=dict)
    token: str = ""

    @property
    def is_valid(self) -> bool:
        return time.time() < self.exp if self.exp else True

    @property
    def id(self) -> str:
        return self.user_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "exp": self.exp,
            "is_valid": self.is_valid,
            "username": self.username,
            "display_name": self.display_name
        }


# Backward-compatible alias
AccountSession = SupabaseSessionClaims


# =====================================================================
# 3. RATE LIMITER
# =====================================================================

class AuthRateLimiter:
    """
    API so'rovlarini brute-force va suiiste'mollikdan himoya qiluvchi hisoblagich.
    """
    COOLDOWN_SECONDS = 300.0  # 5 daqiqa
    MAX_ATTEMPTS = 5

    def __init__(self):
        self._failures: Dict[str, List[float]] = {}
        self._cooldowns: Dict[str, float] = {}

    def is_rate_limited(self, identifier: str) -> Tuple[bool, float]:
        now = time.time()
        cd = self._cooldowns.get(identifier, 0.0)
        if now < cd:
            return True, cd - now
        return False, 0.0

    def record_failure(self, identifier: str):
        now = time.time()
        history = [t for t in self._failures.get(identifier, []) if now - t < self.COOLDOWN_SECONDS]
        history.append(now)
        self._failures[identifier] = history
        if len(history) >= self.MAX_ATTEMPTS:
            self._cooldowns[identifier] = now + self.COOLDOWN_SECONDS
            self._failures.pop(identifier, None)

    def record_success(self, identifier: str):
        self._failures.pop(identifier, None)
        self._cooldowns.pop(identifier, None)


# =====================================================================
# 4. SUPABASE AUTH MANAGER
# =====================================================================

class SupabaseAuthManager:
    """
    Mikasa AI Supabase Auth integratsiya va JWT verifikatsiya dvigateli.
    Supabase auth.users.id ni asosiy identity sifatida tekshiradi va
    Mikasa public.profiles bilan 1:1 bog'laydi.
    """
    _default_instance: Optional["SupabaseAuthManager"] = None
    _instance: Optional["SupabaseAuthManager"] = None

    def __init__(
        self,
        account_device_mgr: Optional[AccountDeviceManager] = None,
        supabase_url: Optional[str] = None,
        supabase_anon_key: Optional[str] = None,
        supabase_jwt_secret: Optional[str] = None,
        storage_path: Optional[str] = None
    ):
        self.account_device_mgr = account_device_mgr or AccountDeviceManager.get_default_instance()
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL", "")
        self.supabase_anon_key = supabase_anon_key or os.environ.get("SUPABASE_ANON_KEY", "")
        self.supabase_jwt_secret = (
            supabase_jwt_secret if supabase_jwt_secret is not None
            else os.environ.get("SUPABASE_JWT_SECRET", "mikasa-default-test-secret")
        )
        self.rate_limiter = AuthRateLimiter()
        self._audit = RemoteAuditLogger.get_instance()
        self.storage_path = storage_path

    @classmethod
    def get_default_instance(cls, storage_path: Optional[str] = None) -> "SupabaseAuthManager":
        inst = getattr(cls, "_instance", None) or cls._default_instance
        if inst is None:
            cls._default_instance = cls(storage_path=storage_path)
            return cls._default_instance
        return inst

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "SupabaseAuthManager":
        return cls.get_default_instance(*args, **kwargs)

    # ========================================================
    # A. JWT VERIFICATION (RFC 7519 / Supabase Auth Contract)
    # ========================================================

    @staticmethod
    def _base64url_decode(data: str) -> bytes:
        """Base64URL satrni to'g'ri padding bilan baytlarga o'tkazish"""
        rem = len(data) % 4
        if rem > 0:
            data += "=" * (4 - rem)
        return base64.urlsafe_b64decode(data.encode("utf-8"))

    @staticmethod
    def _base64url_encode(data: bytes) -> str:
        """Baytlarni Base64URL satriga aylantirish"""
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    def verify_supabase_jwt(self, token: str) -> Tuple[bool, str, Optional[SupabaseSessionClaims]]:
        """
        Supabase access token (JWT) ni tekshirish.
        1. Strukturaviy tekshiruv (header.payload.signature).
        2. Imzo (HMAC-SHA256) tekshiruvi (agar secret mavjud bo'lsa).
        3. Muddati (exp), sub (UUID), role tekshiruvi.
        """
        if not token or not isinstance(token, str):
            return False, "Token kiritilmadi", None

        clean_token = token.strip()
        parts = clean_token.split(".")
        if len(parts) != 3:
            return False, "Noto'g'ri JWT token formati", None

        header_b64, payload_b64, signature_b64 = parts

        # 1. Payload dekodlash
        try:
            payload_bytes = self._base64url_decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            return False, f"JWT payload dekodlashda xatolik: {e}", None

        # 2. Imzo tekshiruvi (agar secret bo'lsa)
        if self.supabase_jwt_secret:
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_sig = hmac.new(
                self.supabase_jwt_secret.encode("utf-8"),
                signing_input,
                hashlib.sha256
            ).digest()
            try:
                actual_sig = self._base64url_decode(signature_b64)
                if not hmac.compare_digest(expected_sig, actual_sig):
                    return False, "Yaroqsiz JWT imzosi", None
            except Exception:
                return False, "Yaroqsiz JWT imzosi", None

        # 3. Expiration tekshiruvi
        now = time.time()
        exp = payload.get("exp")
        if exp is not None and float(exp) < now:
            return False, "Token muddati o'tgan (expired)", None

        # 4. Foydalanuvchi identifikatori (sub)
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id or not isinstance(user_id, str):
            return False, "Token ichida foydalanuvchi identifikatori (sub) topilmadi", None

        email = payload.get("email", "")
        role = payload.get("role", "authenticated")
        user_meta = payload.get("user_metadata", {}) or {}
        username = user_meta.get("username", "") or email.split("@")[0] if email else user_id
        display_name = user_meta.get("display_name", "") or username
        avatar_url = user_meta.get("avatar_url", "")

        claims = SupabaseSessionClaims(
            user_id=str(user_id).strip(),
            email=str(email).strip().lower(),
            role=str(role),
            exp=float(exp) if exp else 0.0,
            iat=float(payload.get("iat", now)),
            username=str(username).strip(),
            display_name=str(display_name).strip(),
            avatar_url=str(avatar_url).strip(),
            raw_claims=payload,
            token=clean_token
        )
        return True, "OK", claims

    # ========================================================
    # B. AUTHENTICATION & PROFILE RESOLUTION
    # ========================================================

    def authenticate_token(self, token: str) -> Tuple[Optional[SupabaseSessionClaims], Optional[MikasaUser]]:
        """
        Tokenni tekshirish va unga mos MikasaProfile (public.profiles) ni olish.
        Qaytaradi: (claims, profile) yoki (None, None).
        """
        ok, msg, claims = self.verify_supabase_jwt(token)
        if not ok or not claims:
            logger.debug(f"[SupabaseAuth] Token verifikatsiyasi muvaffaqiyatsiz: {msg}")
            return None, None

        # Supabase auth.users -> Mikasa public.profiles avtomatik sinxronizatsiyasi
        profile = self.account_device_mgr.upsert_profile_from_supabase(
            user_id=claims.user_id,
            email=claims.email,
            username=claims.username,
            display_name=claims.display_name,
            avatar_url=claims.avatar_url,
            is_verified=True
        )

        return claims, profile

    # ========================================================
    # C. TEST & LOCAL TOKEN GENERATOR
    # ========================================================

    def create_mock_jwt(
        self,
        user_id: str,
        email: str = "",
        username: str = "",
        display_name: str = "",
        role: str = "authenticated",
        exp_seconds: int = 3600,
        secret: Optional[str] = None
    ) -> str:
        """
        Sinovlar va lokal muhit uchun haqiqiy Supabase formatidagi HS256 JWT yaratish.
        """
        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": str(user_id),
            "email": str(email).lower(),
            "role": role,
            "aud": "authenticated",
            "iat": now,
            "exp": now + exp_seconds,
            "user_metadata": {
                "username": username or (email.split("@")[0] if email else user_id),
                "display_name": display_name or username or (email.split("@")[0] if email else user_id)
            }
        }

        header_b64 = self._base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = self._base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        sec = secret or self.supabase_jwt_secret
        sig = hmac.new(sec.encode("utf-8"), signing_input, hashlib.sha256).digest()
        sig_b64 = self._base64url_encode(sig)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    # ========================================================
    # D. MULTI-TENANT ISOLATION HELPERS
    # ========================================================

    def get_user_profile(self, user_id: str) -> Optional[MikasaUser]:
        """Foydalanuvchi profilini Supabase UUID orqali olish"""
        return self.account_device_mgr.get_user(user_id)

    def get_user_devices(self, user_id: str) -> List[Device]:
        """Foydalanuvchiga tegishli kompyuter qurilmalari ro'yxati (Row-Level Security)"""
        return self.account_device_mgr.get_devices_for_user(user_id)


# Backward compatibility alias
AccountAuthManager = SupabaseAuthManager
