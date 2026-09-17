# ========== core/v8/telegram_identity.py ==========
# Phase 39 — Universal Telegram Bot ↔ Mikasa User App
# Multi-User Telegram Identity & OTP Account Linking Engine
# Canonical numeric Telegram ID, salted SHA-256 OTP hashing, deep-link token verification

import os
import time
import json
import uuid
import hmac
import hashlib
import secrets
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple, List

from core.v8.events import RemoteEventType, RemoteAuditLogger

logger = logging.getLogger("core.v8.telegram_identity")


@dataclass
class TelegramIdentity:
    """
    Universal Telegram Identity representation.
    Strictly canonicalized by positive integer telegram_user_id.
    Never relies on username as primary identity.
    """
    telegram_user_id: Any
    first_name: Optional[str] = None
    username: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_seen_at: float = field(default_factory=time.time)
    is_verified: bool = False
    is_linked: bool = False
    linked_at: float = field(default_factory=time.time)

    def is_valid(self) -> bool:
        is_valid, _ = self.validate_user_id(self.telegram_user_id)
        return is_valid

    @property
    def user_id(self) -> Optional[int]:
        is_valid, uid = self.validate_user_id(self.telegram_user_id)
        return uid if is_valid else None

    @classmethod
    def validate_user_id(cls, val: Any) -> Tuple[bool, Optional[int]]:
        """Validate and normalize arbitrary Telegram ID input to positive integer."""
        if val is None or isinstance(val, bool):
            return False, None
        try:
            if isinstance(val, int) and val > 0:
                return True, val
            if isinstance(val, str):
                s = val.strip()
                if s.isdigit() and int(s) > 0:
                    return True, int(s)
        except (ValueError, TypeError):
            pass
        return False, None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelegramIdentity":
        return cls(**data)


@dataclass
class TelegramLinkRequest:
    """
    One-time pairing request for account linking.
    Plaintext OTP is NEVER stored. Only salted SHA-256 hash is persisted.
    """
    mikasa_user_id: str
    otp_hash: str
    salt: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    status: str = "PENDING"  # PENDING, VERIFIED, EXPIRED, FAILED
    attempt_count: int = 0
    telegram_user_id: Optional[int] = None
    used_at: Optional[float] = None
    link_token: str = field(default_factory=lambda: secrets.token_urlsafe(24))

    def is_valid(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return self.status == "PENDING" and (now < self.expires_at) and (self.attempt_count < 5)

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return now >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelegramLinkRequest":
        return cls(**data)


@dataclass
class UserTelegramLink:
    """
    Active persistent link between Mikasa User Account and Telegram Numeric ID.
    Enforces 1:1 active mapping between Mikasa user and Telegram account.
    """
    mikasa_user_id: str
    telegram_user_id: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    linked_at: float = field(default_factory=time.time)
    last_verified_at: float = field(default_factory=time.time)
    status: str = "ACTIVE"  # ACTIVE, REVOKED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.telegram_user_id, str):
            clean = self.telegram_user_id.strip()
            if clean.isdigit() and int(clean) > 0:
                self.telegram_user_id = int(clean)
            else:
                raise ValueError(f"Invalid telegram_user_id in link: {self.telegram_user_id}")
        elif not isinstance(self.telegram_user_id, int) or self.telegram_user_id <= 0:
            raise ValueError(f"Invalid telegram_user_id in link: {self.telegram_user_id}")

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserTelegramLink":
        return cls(**data)


class TelegramIdentityManager:
    """
    Central Multi-User Telegram Identity & Account Linking Manager.
    Handles OTP generation, salted SHA-256 hashing, constant-time verification,
    deep-link tokens, rate limiting, and persistence without plaintext secrets.
    """

    DEFAULT_TTL: float = 300.0  # 5 minutes
    MAX_ATTEMPTS: int = 5
    RATE_LIMIT_MAX_REQUESTS: int = 3
    RATE_LIMIT_WINDOW: float = 600.0  # 10 minutes

    _default_instance: Optional["TelegramIdentityManager"] = None

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "v8_telegram_links.json"
        )
        self._links_by_tg: Dict[int, UserTelegramLink] = {}
        self._links_by_mikasa: Dict[str, UserTelegramLink] = {}
        self._identities: Dict[int, TelegramIdentity] = {}
        self._requests: Dict[str, TelegramLinkRequest] = {}  # request_id -> req
        self._requests_by_token: Dict[str, TelegramLinkRequest] = {}  # link_token -> req
        self._generation_history: Dict[str, List[float]] = {}  # mikasa_user_id -> timestamps
        self._audit = RemoteAuditLogger.get_instance()
        self.load()

    @classmethod
    def get_default_instance(cls, storage_path: Optional[str] = None) -> "TelegramIdentityManager":
        if cls._default_instance is None:
            cls._default_instance = cls(storage_path=storage_path)
        return cls._default_instance

    @staticmethod
    def hash_otp(otp: str, salt: str) -> str:
        """Compute salted SHA-256 hash of plaintext OTP."""
        clean_otp = str(otp).strip()
        data = f"{salt}:{clean_otp}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def verify_otp_hash(cls, otp: str, salt: str, expected_hash: str) -> bool:
        """Constant-time verification of candidate OTP against stored salted hash."""
        candidate_hash = cls.hash_otp(otp, salt)
        return hmac.compare_digest(candidate_hash, expected_hash)

    def check_rate_limit(self, mikasa_user_id: str, current_time: Optional[float] = None) -> bool:
        """
        Check if user has exceeded max 3 OTP requests in the last 10 minutes.
        Returns True if request is allowed, False if rate limited.
        """
        now = current_time if current_time is not None else time.time()
        uid = str(mikasa_user_id)
        history = self._generation_history.get(uid, [])
        # Prune older than window
        cutoff = now - self.RATE_LIMIT_WINDOW
        recent = [t for t in history if t > cutoff]
        self._generation_history[uid] = recent
        return len(recent) < self.RATE_LIMIT_MAX_REQUESTS

    def record_rate_limit_attempt(self, mikasa_user_id: str, current_time: Optional[float] = None):
        now = current_time if current_time is not None else time.time()
        uid = str(mikasa_user_id)
        if uid not in self._generation_history:
            self._generation_history[uid] = []
        self._generation_history[uid].append(now)

    def create_link_request(
        self,
        mikasa_user_id: str,
        ttl: Optional[float] = None,
        bot_username: str = "MikasaUniversalBot",
        current_time: Optional[float] = None
    ) -> Tuple[Optional[TelegramLinkRequest], Optional[str], Optional[str], Optional[str]]:
        """
        Generate a new 6-digit OTP and deep link for a Mikasa account.
        Returns (request, plaintext_otp, deep_link, error_message).
        Plaintext OTP is ONLY returned in this call and NEVER stored.
        """
        now = current_time if current_time is not None else time.time()
        uid = str(mikasa_user_id).strip()
        if not uid:
            return None, None, None, "INVALID_USER_ID: Mikasa User ID bo'sh bo'lishi mumkin emas"

        # Rate limit check
        if not self.check_rate_limit(uid, now):
            self._audit.log(
                RemoteEventType.TELEGRAM_LINK_RATE_LIMITED,
                user_id=uid,
                window_seconds=self.RATE_LIMIT_WINDOW,
                max_requests=self.RATE_LIMIT_MAX_REQUESTS
            )
            return None, None, None, "RATE_LIMITED: 10 daqiqa ichida maksimal 3 ta kod so'rash mumkin"

        # Record attempt
        self.record_rate_limit_attempt(uid, now)

        # Generate cryptographically secure 6-digit OTP: [100000, 999999]
        plaintext_otp = f"{secrets.randbelow(900000) + 100000}"
        salt = secrets.token_hex(16)
        otp_hash = self.hash_otp(plaintext_otp, salt)

        req_ttl = ttl if ttl is not None else self.DEFAULT_TTL
        link_token = secrets.token_urlsafe(24)
        clean_bot = bot_username.lstrip("@").strip()
        deep_link = f"https://t.me/{clean_bot}?start={link_token}"

        req = TelegramLinkRequest(
            mikasa_user_id=uid,
            otp_hash=otp_hash,
            salt=salt,
            created_at=now,
            expires_at=now + req_ttl,
            status="PENDING",
            attempt_count=0,
            link_token=link_token
        )

        self._requests[req.request_id] = req
        self._requests_by_token[link_token] = req

        self._audit.log(
            RemoteEventType.TELEGRAM_LINK_REQUEST_CREATED,
            request_id=req.request_id,
            user_id=uid,
            expires_at=req.expires_at,
            ttl=req_ttl
        )

        logger.info(f"[TelegramIdentity] Yangi bog'lanish so'rovi yaratildi: req={req.request_id}, user={uid}, ttl={req_ttl}s")
        return req, plaintext_otp, deep_link, None

    def get_request(self, request_id: str) -> Optional[TelegramLinkRequest]:
        return self._requests.get(str(request_id))

    def get_request_by_token(self, link_token: str) -> Optional[TelegramLinkRequest]:
        return self._requests_by_token.get(str(link_token))

    def verify_otp(
        self,
        otp: str,
        telegram_user_id: Any,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
        request_id: Optional[str] = None,
        current_time: Optional[float] = None
    ) -> Tuple[bool, str, Optional[UserTelegramLink]]:
        """
        Verify candidate 6-digit OTP against pending request(s).
        Enforces single-use, TTL expiration, max 5 attempts lockout, and constant-time match.
        """
        now = current_time if current_time is not None else time.time()
        is_valid_tg, tg_int = TelegramIdentity.validate_user_id(telegram_user_id)
        if not is_valid_tg or tg_int is None:
            return False, "INVALID_TELEGRAM_ID: Telegram ID musbat butun son bo'lishi shart", None

        candidate_otp = str(otp).strip()
        if not candidate_otp.isdigit() or len(candidate_otp) != 6:
            return False, "INVALID_FORMAT: OTP 6 xonali raqam bo'lishi shart", None

        # Resolve candidate request
        req: Optional[TelegramLinkRequest] = None
        if request_id:
            req = self._requests.get(str(request_id))
            if not req:
                return False, "REQUEST_NOT_FOUND: Bog'lanish so'rovi topilmadi", None
        else:
            # First search pending requests matching this OTP
            matching_reqs = [
                r for r in self._requests.values()
                if r.status == "PENDING" and (not r.is_expired(now)) and r.attempt_count < self.MAX_ATTEMPTS
            ]
            for r in sorted(matching_reqs, key=lambda x: x.created_at, reverse=True):
                if self.verify_otp_hash(candidate_otp, r.salt, r.otp_hash):
                    req = r
                    break
            # If no pending match found, check any request matching OTP (e.g. verified, expired, failed)
            if not req:
                all_matching = [
                    r for r in self._requests.values()
                    if self.verify_otp_hash(candidate_otp, r.salt, r.otp_hash)
                ]
                if all_matching:
                    req = sorted(all_matching, key=lambda x: x.created_at, reverse=True)[0]
                elif matching_reqs:
                    # If no hash match at all, take the latest pending request to record failure attempt
                    req = sorted(matching_reqs, key=lambda x: x.created_at, reverse=True)[0]

        if not req:
            return False, "INVALID_OR_EXPIRED_CODE: Bog'lanish kodi topilmadi yoki muddati tugagan", None

        # Check expiration
        if req.is_expired(now):
            req.status = "EXPIRED"
            self._audit.log(
                RemoteEventType.TELEGRAM_LINK_EXPIRED,
                request_id=req.request_id,
                user_id=req.mikasa_user_id,
                telegram_user_id=str(tg_int)
            )
            return False, "CODE_EXPIRED: Tasdiqlash kodining muddati o'tgan (5 daqiqa)", None

        # Check status
        if req.status != "PENDING":
            if req.status == "VERIFIED":
                return False, "CODE_ALREADY_USED: Ushbu kod allaqachon ishlatilgan (Replay blocked)", None
            if req.status == "FAILED":
                return False, "MAX_ATTEMPTS_EXCEEDED: Ushbu so'rov bo'yicha urinishlar soni tugagan (5 ta)", None
            return False, f"REQUEST_INVALID: So'rov holati yaroqsiz: {req.status}", None

        # Check attempts
        if req.attempt_count >= self.MAX_ATTEMPTS:
            req.status = "FAILED"
            return False, "MAX_ATTEMPTS_EXCEEDED: Maksimal 5 ta xato urinish qayd etildi", None

        # Constant-time comparison
        is_match = self.verify_otp_hash(candidate_otp, req.salt, req.otp_hash)
        if not is_match:
            req.attempt_count += 1
            remaining = max(0, self.MAX_ATTEMPTS - req.attempt_count)
            if req.attempt_count >= self.MAX_ATTEMPTS:
                req.status = "FAILED"
            self._audit.log(
                RemoteEventType.TELEGRAM_OTP_VERIFICATION_FAILED,
                request_id=req.request_id,
                user_id=req.mikasa_user_id,
                telegram_user_id=str(tg_int),
                attempt_count=req.attempt_count,
                remaining_attempts=remaining
            )
            return False, f"INVALID_OTP: Kod noto'g'ri. Qolgan urinishlar soni: {remaining}", None

        # Verification Success: mark single-use
        req.status = "VERIFIED"
        req.telegram_user_id = tg_int
        req.used_at = now

        # Revoke any prior active link for this Mikasa user or Telegram user (clean 1:1 mapping)
        self._revoke_existing_links(req.mikasa_user_id, tg_int)

        # Create active link
        meta = {}
        if username:
            meta["username"] = str(username)
        if first_name:
            meta["first_name"] = str(first_name)

        link = UserTelegramLink(
            mikasa_user_id=req.mikasa_user_id,
            telegram_user_id=tg_int,
            linked_at=now,
            last_verified_at=now,
            status="ACTIVE",
            metadata=meta
        )
        self._links_by_tg[tg_int] = link
        self._links_by_mikasa[req.mikasa_user_id] = link

        # Update or register Telegram Identity
        ident = self._identities.get(tg_int)
        if ident is None:
            ident = TelegramIdentity(
                telegram_user_id=tg_int,
                first_name=first_name,
                username=username,
                created_at=now,
                last_seen_at=now,
                is_verified=True,
                is_linked=True
            )
        else:
            ident.first_name = first_name or ident.first_name
            ident.username = username or ident.username
            ident.is_verified = True
            ident.is_linked = True
            ident.last_seen_at = now
        self._identities[tg_int] = ident

        self.save()

        self._audit.log(
            RemoteEventType.TELEGRAM_OTP_VERIFICATION_SUCCESS,
            request_id=req.request_id,
            user_id=req.mikasa_user_id,
            telegram_user_id=str(tg_int)
        )
        self._audit.log(
            RemoteEventType.TELEGRAM_ACCOUNT_LINKED,
            request_id=req.request_id,
            user_id=req.mikasa_user_id,
            telegram_user_id=str(tg_int)
        )

        logger.info(f"[TelegramIdentity] Muvaffaqiyatli bog'landi: tg_id={tg_int} ↔ mikasa_user={req.mikasa_user_id}")
        return True, "OK: Mikasa hisobi Telegram bot bilan muvaffaqiyatli bog'landi", link

    def verify_link_token(
        self,
        link_token: str,
        telegram_user_id: Any,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
        current_time: Optional[float] = None
    ) -> Tuple[bool, str, Optional[UserTelegramLink]]:
        """
        Verify deep-link token (e.g. from t.me/bot?start=<token>).
        Enforces single-use, TTL expiration, and registers link.
        """
        now = current_time if current_time is not None else time.time()
        is_valid_tg, tg_int = TelegramIdentity.validate_user_id(telegram_user_id)
        if not is_valid_tg or tg_int is None:
            return False, "INVALID_TELEGRAM_ID: Telegram ID musbat butun son bo'lishi shart", None

        token_str = str(link_token).strip()
        req = self._requests_by_token.get(token_str)
        if not req:
            return False, "INVALID_LINK_TOKEN: Havola yaroqsiz yoki topilmadi", None

        if req.is_expired(now):
            req.status = "EXPIRED"
            self._audit.log(
                RemoteEventType.TELEGRAM_LINK_EXPIRED,
                request_id=req.request_id,
                user_id=req.mikasa_user_id,
                telegram_user_id=str(tg_int)
            )
            return False, "CODE_EXPIRED: Havolaning muddati o'tgan (5 daqiqa)", None

        if req.status != "PENDING":
            if req.status == "VERIFIED":
                return False, "TOKEN_ALREADY_USED: Ushbu havola allaqachon ishlatilgan (Replay blocked)", None
            return False, f"TOKEN_INVALID: Havola holati yaroqsiz: {req.status}", None

        # Verify success
        req.status = "VERIFIED"
        req.telegram_user_id = tg_int
        req.used_at = now

        self._revoke_existing_links(req.mikasa_user_id, tg_int)

        meta = {}
        if username:
            meta["username"] = str(username)
        if first_name:
            meta["first_name"] = str(first_name)

        link = UserTelegramLink(
            mikasa_user_id=req.mikasa_user_id,
            telegram_user_id=tg_int,
            linked_at=now,
            last_verified_at=now,
            status="ACTIVE",
            metadata=meta
        )
        self._links_by_tg[tg_int] = link
        self._links_by_mikasa[req.mikasa_user_id] = link

        ident = self._identities.get(tg_int)
        if ident is None:
            ident = TelegramIdentity(
                telegram_user_id=tg_int,
                first_name=first_name,
                username=username,
                created_at=now,
                last_seen_at=now,
                is_verified=True,
                is_linked=True
            )
        else:
            ident.first_name = first_name or ident.first_name
            ident.username = username or ident.username
            ident.is_verified = True
            ident.is_linked = True
            ident.last_seen_at = now
        self._identities[tg_int] = ident

        self.save()

        self._audit.log(
            RemoteEventType.TELEGRAM_ACCOUNT_LINKED,
            request_id=req.request_id,
            user_id=req.mikasa_user_id,
            telegram_user_id=str(tg_int)
        )

        logger.info(f"[TelegramIdentity] Havola orqali muvaffaqiyatli bog'landi: tg_id={tg_int} ↔ user={req.mikasa_user_id}")
        return True, "OK: Mikasa hisobi havola orqali Telegram bot bilan muvaffaqiyatli bog'landi", link

    def _revoke_existing_links(self, mikasa_user_id: str, telegram_user_id: int):
        """Internal helper to clean up any prior active links for users being paired."""
        old_by_tg = self._links_by_tg.get(telegram_user_id)
        if old_by_tg and old_by_tg.is_active:
            old_by_tg.status = "REVOKED"
            if old_by_tg.mikasa_user_id in self._links_by_mikasa:
                del self._links_by_mikasa[old_by_tg.mikasa_user_id]

        old_by_mikasa = self._links_by_mikasa.get(mikasa_user_id)
        if old_by_mikasa and old_by_mikasa.is_active:
            old_by_mikasa.status = "REVOKED"
            if old_by_mikasa.telegram_user_id in self._links_by_tg:
                del self._links_by_tg[old_by_mikasa.telegram_user_id]

    def unlink(
        self,
        mikasa_user_id: Optional[str] = None,
        telegram_user_id: Optional[Any] = None
    ) -> bool:
        """
        Revoke active link relationship and cancel pending pairing requests.
        Can be invoked by Mikasa User ID or Telegram User ID.
        """
        link: Optional[UserTelegramLink] = None
        tg_int: Optional[int] = None
        if telegram_user_id is not None:
            _, tg_int = TelegramIdentity.validate_user_id(telegram_user_id)
            if tg_int:
                link = self._links_by_tg.get(tg_int)

        if not link and mikasa_user_id is not None:
            link = self._links_by_mikasa.get(str(mikasa_user_id))

        if link and link.is_active:
            link.status = "REVOKED"
            if link.telegram_user_id in self._links_by_tg:
                del self._links_by_tg[link.telegram_user_id]
            if link.mikasa_user_id in self._links_by_mikasa:
                del self._links_by_mikasa[link.mikasa_user_id]

            # Update identity if present
            ident = self._identities.get(link.telegram_user_id)
            if ident:
                ident.is_linked = False

            # Cancel any pending requests for this user
            for r in self._requests.values():
                if r.mikasa_user_id == link.mikasa_user_id and r.status == "PENDING":
                    r.status = "EXPIRED"

            self.save()

            self._audit.log(
                RemoteEventType.TELEGRAM_ACCOUNT_UNLINKED,
                user_id=link.mikasa_user_id,
                telegram_user_id=str(link.telegram_user_id)
            )
            logger.info(f"[TelegramIdentity] Bog'lanish bekor qilindi: tg={link.telegram_user_id}, mikasa={link.mikasa_user_id}")
            return True

        return False

    def get_link_by_mikasa_user(self, mikasa_user_id: str) -> Optional[UserTelegramLink]:
        link = self._links_by_mikasa.get(str(mikasa_user_id))
        return link if (link and link.is_active) else None

    def get_link_by_telegram_user(self, telegram_user_id: Any) -> Optional[UserTelegramLink]:
        _, tg_int = TelegramIdentity.validate_user_id(telegram_user_id)
        if not tg_int:
            return None
        link = self._links_by_tg.get(tg_int)
        return link if (link and link.is_active) else None

    def get_identity(self, telegram_user_id: Any) -> Optional[TelegramIdentity]:
        _, tg_int = TelegramIdentity.validate_user_id(telegram_user_id)
        if not tg_int:
            return None
        return self._identities.get(tg_int)

    def register_or_update_identity(
        self,
        telegram_user_id: Any,
        first_name: Optional[str] = None,
        username: Optional[str] = None
    ) -> Optional[TelegramIdentity]:
        is_valid, tg_int = TelegramIdentity.validate_user_id(telegram_user_id)
        if not is_valid or tg_int is None:
            return None

        now = time.time()
        ident = self._identities.get(tg_int)
        link = self.get_link_by_telegram_user(tg_int)
        is_linked = link is not None and link.is_active

        if ident is None:
            ident = TelegramIdentity(
                telegram_user_id=tg_int,
                first_name=first_name,
                username=username,
                created_at=now,
                last_seen_at=now,
                is_verified=is_linked,
                is_linked=is_linked
            )
        else:
            if first_name:
                ident.first_name = first_name
            if username:
                ident.username = username
            ident.last_seen_at = now
            ident.is_linked = is_linked

        self._identities[tg_int] = ident
        return ident

    def list_active_links(self) -> List[UserTelegramLink]:
        return [lnk for lnk in self._links_by_tg.values() if lnk.is_active]

    def count_active_links(self) -> int:
        return len(self.list_active_links())

    def count_pending_requests(self, current_time: Optional[float] = None) -> int:
        now = current_time if current_time is not None else time.time()
        return sum(1 for r in self._requests.values() if r.status == "PENDING" and not r.is_expired(now))

    def cleanup_expired_requests(self, current_time: Optional[float] = None) -> int:
        now = current_time if current_time is not None else time.time()
        cleaned = 0
        for r in list(self._requests.values()):
            if r.status == "PENDING" and r.is_expired(now):
                r.status = "EXPIRED"
                cleaned += 1
        return cleaned

    def save(self):
        if not self.storage_path:
            return
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            data = {
                "links": [lnk.to_dict() for lnk in self._links_by_tg.values()],
                "identities": [ident.to_dict() for ident in self._identities.values()],
                "requests": [req.to_dict() for req in self._requests.values()]
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[TelegramIdentity] Saqlashda xatolik: {e}")

    def load(self):
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_links = data.get("links", [])
            for item in raw_links:
                lnk = UserTelegramLink.from_dict(item)
                if lnk.is_active:
                    self._links_by_tg[lnk.telegram_user_id] = lnk
                    self._links_by_mikasa[lnk.mikasa_user_id] = lnk

            raw_idents = data.get("identities", [])
            for item in raw_idents:
                ident = TelegramIdentity.from_dict(item)
                self._identities[ident.telegram_user_id] = ident

            raw_reqs = data.get("requests", [])
            for item in raw_reqs:
                req = TelegramLinkRequest.from_dict(item)
                self._requests[req.request_id] = req
                if req.link_token:
                    self._requests_by_token[req.link_token] = req

            logger.info(f"[TelegramIdentity] Yuklandi: {len(self._links_by_tg)} ta faol link, {len(self._identities)} ta identity.")
        except Exception as e:
            logger.error(f"[TelegramIdentity] Yuklashda xatolik: {e}")
