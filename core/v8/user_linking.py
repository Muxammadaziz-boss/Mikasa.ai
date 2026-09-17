# ========== core/v8/user_linking.py ==========
# Phase 38 — User Account ↔ Telegram Linking & One-Time Pairing Engine
# Links Mikasa User ID, Telegram numeric ID, and Paired PC Device IDs

import os
import time
import json
import secrets
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple, List

from core.v8.events import RemoteEventType, RemoteAuditLogger

logger = logging.getLogger("core.v8.user_linking")


@dataclass
class TelegramIdentity:
    """Telegram foydalanuvchisi identifikatsiyasi (Faqat raqamli ID asosida)"""
    telegram_user_id: str
    first_name: Optional[str] = None
    username: Optional[str] = None
    linked_at: float = field(default_factory=time.time)

    def is_valid(self) -> bool:
        return str(self.telegram_user_id).isdigit() and int(self.telegram_user_id) > 0

    @property
    def user_id(self) -> Optional[int]:
        return int(self.telegram_user_id) if self.is_valid() else None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelegramIdentity":
        return cls(**data)


@dataclass
class PairingToken:
    """Bir martalik, qisqa muddatli (5 daqiqa) pairing kodi (MK-XXXXXX)"""
    code: str
    mikasa_user_id: str
    device_id: str
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    is_used: bool = False

    def is_valid(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return (not self.is_used) and (now < self.expires_at)

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return now >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PairingToken":
        return cls(**data)


@dataclass
class UserDeviceLink:
    """Mikasa foydalanuvchisi, Telegram raqamli ID va PC qurilmasi o'rtasidagi bog'lanish"""
    mikasa_user_id: str
    telegram_user_id: str
    device_id: str
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserDeviceLink":
        return cls(**data)


class UserLinkingStore:
    """
    Foydalanuvchi hisobi va Telegram raqamli ID o'rtasida xavfsiz bog'lanishlar registratori.
    Bir martalik pairing kodlari, replay himoyasi va doimiy fayl saqlashni boshqaradi.
    """

    CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # O, 0, 1, I chiqarib tashlangan (adashmaslik uchun)
    DEFAULT_TOKEN_TTL = 300.0  # 5 daqiqa

    _default_instance: Optional["UserLinkingStore"] = None

    def __init__(self, storage_path: Optional[str] = None, tokens_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "v8_user_links.json"
        )
        self.tokens_path = tokens_path
        self._links: Dict[str, UserDeviceLink] = {}  # device_id -> UserDeviceLink
        self._pending_tokens: Dict[str, PairingToken] = {}  # code -> PairingToken
        self._audit = RemoteAuditLogger.get_instance()
        self.load()

    @classmethod
    def get_default_instance(cls, storage_path: Optional[str] = None) -> "UserLinkingStore":
        if cls._default_instance is None:
            cls._default_instance = cls(storage_path=storage_path)
        return cls._default_instance

    def generate_pairing_code(
        self,
        mikasa_user_id: str,
        device_id: str,
        ttl: Optional[float] = None
    ) -> str:
        """
        Mikasa ilovasi uchun bir martalik MK-XXXXXX kodi yaratish.
        Standart yaroqlilik muddati: 5 daqiqa (300 soniya).
        """
        token_ttl = ttl if ttl is not None else self.DEFAULT_TOKEN_TTL
        now = time.time()

        # Tasodifiy 6 xonali kod
        raw_code = "".join(secrets.choice(self.CODE_ALPHABET) for _ in range(6))
        code = f"MK-{raw_code}"

        token = PairingToken(
            code=code,
            mikasa_user_id=str(mikasa_user_id),
            device_id=str(device_id),
            created_at=now,
            expires_at=now + token_ttl,
            is_used=False
        )
        self._pending_tokens[code] = token
        logger.info(f"[UserLinking] Yangi pairing kodi yaratildi: dev={device_id}, user={mikasa_user_id}, ttl={token_ttl}s")
        return code

    def get_token(self, code: str) -> Optional[PairingToken]:
        """Kodni qidirish (mavjud bo'lsa)"""
        return self._pending_tokens.get(str(code).strip().upper())

    def redeem_pairing_code(
        self,
        code: str,
        telegram_user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        current_time: Optional[float] = None
    ) -> Tuple[bool, str, Optional[UserDeviceLink]]:
        """
        Telegram foydalanuvchisi /pair MK-XXXXXX kiritganda tekshirish va bog'lash.
        - Kod mavjudligi va muddati tekshiriladi
        - Replay himoyasi (bir martalik foydalanish)
        - Telegram numeric ID tekshiruvi
        """
        clean_code = str(code).strip().upper()
        tg_id_str = str(telegram_user_id).strip()
        now = current_time if current_time is not None else time.time()

        # Raqamli Telegram ID tekshiruvi (faqat raqamlar bo'lishi kerak)
        if not tg_id_str.isdigit():
            return False, "INVALID_TELEGRAM_ID: Telegram ID faqat raqamlardan iborat bo'lishi shart", None

        token = self._pending_tokens.get(clean_code)
        if not token:
            return False, "INVALID_PAIRING_CODE: Bog'lanish kodi topilmadi yoki noto'g'ri kiritildi", None

        if token.is_used:
            return False, "CODE_ALREADY_USED: Ushbu kod allaqachon ishlatilgan (Replay blocked)", None

        if now >= token.expires_at:
            return False, "CODE_EXPIRED: Ushbu kodning muddati o'tgan (5 daqiqa)", None

        # Kodni ishlatilgan deb belgilash (Single-use)
        token.is_used = True

        meta_dict = metadata if isinstance(metadata, dict) else ({"username": str(metadata)} if metadata else {})
        link = UserDeviceLink(
            mikasa_user_id=token.mikasa_user_id,
            telegram_user_id=tg_id_str,
            device_id=token.device_id,
            created_at=now,
            last_active_at=now,
            is_active=True,
            metadata=meta_dict
        )
        self._links[token.device_id] = link
        self.save()

        self._audit.log(
            RemoteEventType.ACCOUNT_LINKED,
            user_id=token.mikasa_user_id,
            device_id=token.device_id,
            telegram_user_id=tg_id_str
        )
        self._audit.log(
            RemoteEventType.DEVICE_PAIRED,
            user_id=token.mikasa_user_id,
            device_id=token.device_id,
            telegram_user_id=tg_id_str
        )
        logger.info(f"[UserLinking] Bog'lanish muvaffaqiyatli: tg={tg_id_str} ↔ dev={token.device_id}")
        return True, "OK: Qurilma va Telegram hisobi muvaffaqiyatli bog'landi", link

    def unlink_telegram(self, device_id: str, telegram_user_id: Optional[str] = None) -> bool:
        """Qurilma va Telegram o'rtasidagi bog'lanishni bekor qilish (Unpair)"""
        dev_id = str(device_id)
        link = self._links.get(dev_id)
        if link and link.is_active:
            if telegram_user_id and str(telegram_user_id) != link.telegram_user_id:
                return False
            link.is_active = False
            self.save()
            self._audit.log(
                RemoteEventType.ACCOUNT_UNLINKED,
                user_id=link.mikasa_user_id,
                device_id=dev_id,
                telegram_user_id=link.telegram_user_id
            )
            self._audit.log(
                RemoteEventType.DEVICE_UNPAIRED,
                user_id=link.mikasa_user_id,
                device_id=dev_id,
                telegram_user_id=link.telegram_user_id
            )
            logger.info(f"[UserLinking] Bog'lanish bekor qilindi: dev={dev_id}")
            return True
        return False

    def get_link_by_telegram(self, telegram_user_id: str) -> Optional[UserDeviceLink]:
        """Telegram numeric ID bo'yicha faol bog'lanishni topish"""
        tg_str = str(telegram_user_id).strip()
        for link in self._links.values():
            if link.telegram_user_id == tg_str and link.is_active:
                return link
        return None

    def get_link_by_device(self, device_id: str) -> Optional[UserDeviceLink]:
        """Qurilma ID bo'yicha faol bog'lanishni topish"""
        link = self._links.get(str(device_id))
        return link if (link and link.is_active) else None

    def list_linked_devices(self, telegram_user_id: str) -> List[UserDeviceLink]:
        """Foydalanuvchiga tegishli barcha faol qurilmalar ro'yxati"""
        tg_str = str(telegram_user_id).strip()
        return [link for link in self._links.values() if link.telegram_user_id == tg_str and link.is_active]

    def is_telegram_linked(self, telegram_user_id: str) -> bool:
        return self.get_link_by_telegram(telegram_user_id) is not None

    def save(self):
        if not self.storage_path:
            return
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            data = {
                "links": {k: v.to_dict() for k, v in self._links.items()}
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[UserLinking] Saqlashda xatolik: {e}")

    def load(self):
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            links_raw = data.get("links", {})
            self._links = {k: UserDeviceLink.from_dict(v) for k, v in links_raw.items()}
            logger.info(f"[UserLinking] {len(self._links)} ta bog'lanish yuklandi.")
        except Exception as e:
            logger.error(f"[UserLinking] Yuklashda xatolik: {e}")
