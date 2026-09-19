# ========== core/v8/device_enrollment.py ==========
# Phase 42 — Device Enrollment & Secure Credential Management
# Cryptographic Ed25519 public key enrollment, Windows DPAPI secure storage,
# safe default permissions, and credential revocation

import os
import time
import json
import uuid
import logging
import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple

from core.v8.events import RemoteEventType, RemoteAuditLogger
from core.v8.account_device import Device, AccountDeviceManager

logger = logging.getLogger("core.v8.device_enrollment")


# =====================================================================
# 1. DEVICE CREDENTIAL MODEL
# =====================================================================

@dataclass
class DeviceCredential:
    """
    Qurilmaning backendda saqlanuvchi ommaviy (public) kriptografik identifikatori.
    DIQQAT: Maxfiy kalit (private key) hech qachon backendda saqlanmaydi!
    Backendda faqat 32-baytlik Ed25519 ommaviy kaliti (public_key) saqlanadi.
    """
    id: str  # UUID
    user_id: str  # auth.users.id / MikasaUser UUID
    device_id: str  # Hardware device_id
    public_key: str  # 64-belgili hex satr (32-bayt Ed25519 public key)
    algorithm: str = "ed25519"
    is_revoked: bool = False
    enrolled_at: float = field(default_factory=time.time)
    revoked_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return not self.is_revoked

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceCredential":
        valid_fields = {
            "id", "user_id", "device_id", "public_key",
            "algorithm", "is_revoked", "enrolled_at",
            "revoked_at", "metadata"
        }
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# =====================================================================
# 2. SECURE CREDENTIAL STORE (OS / LOCAL STORAGE ABSTRACTION)
# =====================================================================

class SecureCredentialStore(ABC):
    """
    Mijoz / Agent tomonida maxfiy kalitlarni xavfsiz saqlash interfeysi.
    Private key hech qachon ochiq matnda log yoki oddiy JSON faylda saqlanmasligi shart.
    """
    @abstractmethod
    def save_credential(self, key: str, secret_data: str) -> bool:
        """Maxfiy ma'lumotni xavfsiz saqlash"""
        pass

    @abstractmethod
    def load_credential(self, key: str) -> Optional[str]:
        """Maxfiy ma'lumotni o'qish"""
        pass

    @abstractmethod
    def delete_credential(self, key: str) -> bool:
        """Maxfiy ma'lumotni o'chirish"""
        pass


class MockCredentialStore(SecureCredentialStore):
    """Sinovlar va xotiradagi vaqtinchalik agentlar uchun mock xotira"""
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir
        self._store: Dict[str, str] = {}

    def save_credential(self, key: str, secret_data: str) -> bool:
        self._store[key] = str(secret_data)
        return True

    def store_credential(self, key: str, secret_data: str) -> bool:
        return self.save_credential(key, secret_data)

    def load_credential(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def delete_credential(self, key: str) -> bool:
        return self._store.pop(key, None) is not None


class WindowsCredentialStore(SecureCredentialStore):
    """
    Windows operatsion tizimida DPAPI (Data Protection API) orqali
    foydalanuvchining login kaliti bilan shifrlangan saqlash.
    """
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = base_dir
        else:
            appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
            self.base_dir = os.path.join(appdata, "MikasaAI", "secure_vault")
        os.makedirs(self.base_dir, exist_ok=True)
        self._is_windows = platform.system().lower() == "windows"

    def _get_file_path(self, key: str) -> str:
        safe_key = "".join(c for c in key if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.base_dir, f"{safe_key}.vault")

    def _dpapi_protect(self, data: bytes) -> bytes:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ('cbData', wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_byte))
            ]

        cb = len(data)
        buf = (ctypes.c_byte * cb).from_buffer_copy(data)
        in_blob = DATA_BLOB(cb, buf)
        out_blob = DATA_BLOB()
        if not ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(in_blob), 'MikasaDeviceKey', None, None, None, 0, ctypes.byref(out_blob)
        ):
            raise ctypes.WinError()
        res = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        return res

    def _dpapi_unprotect(self, data: bytes) -> bytes:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ('cbData', wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_byte))
            ]

        cb = len(data)
        buf = (ctypes.c_byte * cb).from_buffer_copy(data)
        in_blob = DATA_BLOB(cb, buf)
        out_blob = DATA_BLOB()
        if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
        ):
            raise ctypes.WinError()
        res = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        return res

    def save_credential(self, key: str, secret_data: str) -> bool:
        try:
            raw_bytes = secret_data.encode("utf-8")
            if self._is_windows:
                blob = self._dpapi_protect(raw_bytes)
            else:
                # Unix/Fallback dev storage
                blob = raw_bytes

            fpath = self._get_file_path(key)
            with open(fpath, "wb") as f:
                f.write(blob)
            return True
        except Exception as e:
            logger.warning(f"[WindowsCredentialStore] Kalitni saqlashda xato: {e}")
            return False

    def load_credential(self, key: str) -> Optional[str]:
        try:
            fpath = self._get_file_path(key)
            if not os.path.exists(fpath):
                return None
            with open(fpath, "rb") as f:
                blob = f.read()
            if self._is_windows:
                raw_bytes = self._dpapi_unprotect(blob)
            else:
                raw_bytes = blob
            return raw_bytes.decode("utf-8")
        except Exception as e:
            logger.warning(f"[WindowsCredentialStore] Kalitni o'qishda xato: {e}")
            return None

    def delete_credential(self, key: str) -> bool:
        try:
            fpath = self._get_file_path(key)
            if os.path.exists(fpath):
                os.remove(fpath)
                return True
            return False
        except Exception as e:
            logger.warning(f"[WindowsCredentialStore] Kalitni o'chirishda xato: {e}")
            return False


# =====================================================================
# 3. DEVICE ENROLLMENT MANAGER
# =====================================================================

class DeviceEnrollmentManager:
    """
    Qurilmalarni ro'yxatga olish, ommaviy kalitlarini biriktirish
    va xavfsiz boshlang'ich ruxsatlarni o'rnatish menejeri.
    """
    DEFAULT_SAFE_PERMISSIONS = {
        "allowed_commands": ["system.status", "system.info", "heartbeat", "telemetry.read"],
        "require_confirmation": ["app.launch", "window.focus"],
        "denied_commands": [
            "system.shutdown", "system.reboot", "filesystem.delete", "process.kill",
            "power.shutdown", "power.restart", "file.delete", "terminal.execute"
        ]
    }

    _default_instance: Optional["DeviceEnrollmentManager"] = None
    _instance: Optional["DeviceEnrollmentManager"] = None

    def __init__(
        self,
        account_device_mgr: Optional[AccountDeviceManager] = None,
        storage_path: Optional[str] = None
    ):
        self.account_device_mgr = account_device_mgr or AccountDeviceManager.get_default_instance()
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "v8_device_credentials.json"
        )
        self._credentials: Dict[str, DeviceCredential] = {}
        self._audit = RemoteAuditLogger.get_instance()
        self.load()

    @classmethod
    def get_default_instance(
        cls,
        account_device_mgr: Optional[AccountDeviceManager] = None,
        storage_path: Optional[str] = None
    ) -> "DeviceEnrollmentManager":
        inst = getattr(cls, "_instance", None) or cls._default_instance
        if inst is None:
            cls._default_instance = cls(
                account_device_mgr=account_device_mgr,
                storage_path=storage_path
            )
            return cls._default_instance
        return inst

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "DeviceEnrollmentManager":
        return cls.get_default_instance(*args, **kwargs)

    def _cred_key(self, user_id: str, device_id: str) -> str:
        return f"{user_id.strip()}:{device_id.strip()}"

    def enroll_device(
        self,
        user_id: str,
        device_id: str,
        public_key: str,
        name: str,
        hostname: str = "",
        platform_name: str = "Windows",
        os_version: str = "",
        fingerprint: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[DeviceCredential], Optional[Device]]:
        """
        Qurilmani hisobga muvaffaqiyatli biriktirish (Enrollment):
        1. Ommaviy kalit formatini tekshirish (32-bayt / 64-belgili hex).
        2. AccountDeviceManager orqali qurilmani ro'yxatdan o'tkazish / tiklash.
        3. Standart XAVFSIZ ruxsatlar profilini o'rnatish (xavfli amallar bloklangan).
        4. DeviceCredential yozuvini yaratish va saqlash.
        5. Audit hodisalarini qayd qilish.
        """
        uid = str(user_id).strip()
        dev_id = str(device_id).strip()
        clean_pub = str(public_key).strip().lower()

        if not uid or not dev_id:
            return False, "INVALID_ARGS: user_id va device_id kiritilishi shart", None, None

        # Ed25519 ommaviy kaliti uzunligi va formati (32 bayt = 64 hex)
        if len(clean_pub) != 64 or not all(c in "0123456789abcdef" for c in clean_pub):
            return False, "INVALID_PUBLIC_KEY: Ed25519 public key 64 belgili hex satr bo'lishi shart", None, None

        # 1. Qurilmani AccountDeviceManager ga qo'shish / yangilash
        existing_dev = self.account_device_mgr.get_device(dev_id, user_id=uid)
        is_reenroll = False

        if existing_dev:
            # Agar mavjud bo'lsa va bekor qilingan (revoked) bo'lsa, qayta jonlantiramiz
            if existing_dev.is_revoked:
                is_reenroll = True
                existing_dev.status = "online"
                existing_dev.name = name or existing_dev.name
                existing_dev.hostname = hostname or existing_dev.hostname
                existing_dev.last_seen_at = time.time()
                self.account_device_mgr.save()
                device = existing_dev
            else:
                existing_dev.name = name or existing_dev.name
                existing_dev.hostname = hostname or existing_dev.hostname
                existing_dev.last_seen_at = time.time()
                self.account_device_mgr.save()
                device = existing_dev
        else:
            device = self.account_device_mgr.register_device(
                user_id=uid,
                device_id=dev_id,
                name=name or hostname or "Mening Kompyuterim",
                hostname=hostname,
                platform=platform_name.lower(),
                agent_version="8.0.0",
                status="online"
            )

        # 2. Xavfsiz standart ruxsatlarni belgilash (PermissionStore)
        try:
            from core.v8.permission_center import PermissionStore
            perm_store = PermissionStore.get_default_instance()
            # Standart ruxsat: Faqat status va heartbeat xavfsiz o'qiladi,
            # Xavfli amallar (power.shutdown, file.delete) ruxsatsiz qoladi
            profile = perm_store.get_profile(uid, dev_id)
            profile.allowed_categories = ["system.status", "system.info", "heartbeat"]
            profile.require_confirmation_categories = ["app.launch", "window.focus"]
            profile.blocked_commands = ["power.shutdown", "power.restart", "file.delete", "terminal.execute"]
            perm_store.save()
        except Exception as e:
            logger.warning(f"[DeviceEnrollment] Standart ruxsatlarni belgilashda ogohlantirish: {e}")

        # 3. Eski kredensialni bekor qilish (agar bo'lsa) va yangi yaratish
        cred_key = self._cred_key(uid, dev_id)
        cred_id = str(uuid.uuid4())
        meta = dict(metadata or {})
        if fingerprint:
            meta["fingerprint"] = fingerprint
        cred = DeviceCredential(
            id=cred_id,
            user_id=uid,
            device_id=dev_id,
            public_key=clean_pub,
            algorithm="ed25519",
            is_revoked=False,
            enrolled_at=time.time(),
            metadata=meta
        )
        self._credentials[cred_key] = cred
        self.save()

        # 4. Audit
        event_type = RemoteEventType.DEVICE_REENROLLED if is_reenroll else RemoteEventType.DEVICE_ENROLLED
        self._audit.log(
            event_type,
            device_id=dev_id,
            user_id=uid,
            hostname=hostname,
            name=device.name
        )
        self._audit.log(
            RemoteEventType.DEVICE_CREDENTIAL_CREATED,
            device_id=dev_id,
            user_id=uid,
            algorithm="ed25519"
        )
        logger.info(f"[DeviceEnrollment] Qurilma enroll qilindi: dev={dev_id}, user={uid}, reenroll={is_reenroll}")
        return True, "OK", cred, device

    def get_credential(
        self,
        device_id: str,
        user_id: Optional[str] = None,
        include_revoked: bool = False
    ) -> Optional[DeviceCredential]:
        """Qurilmaning kredensialini olish"""
        dev_id = str(device_id).strip()
        if user_id:
            cred = self._credentials.get(self._cred_key(user_id, dev_id))
            if cred and (include_revoked or not cred.is_revoked):
                return cred
            return None

        # Agar user_id ko'rsatilmagan bo'lsa, device_id bo'yicha kredensialni qidirish
        for cred in self._credentials.values():
            if cred.device_id == dev_id and (include_revoked or not cred.is_revoked):
                return cred
        return None

    def revoke_credential(self, device_id: str, user_id: Optional[str] = None) -> bool:
        """Qurilma kredensialini bekor qilish (kaskadli o'chirish uchun)"""
        dev_id = str(device_id).strip()
        revoked_any = False
        now = time.time()

        for key, cred in list(self._credentials.items()):
            if cred.device_id == dev_id:
                if user_id and cred.user_id != str(user_id).strip():
                    continue
                cred.is_revoked = True
                cred.revoked_at = now
                revoked_any = True

        if revoked_any:
            self.save()
            logger.info(f"[DeviceEnrollment] Qurilma kredensiali bekor qilindi: dev={dev_id}")
        return revoked_any

    def is_device_credential_valid(self, device_id: str, user_id: Optional[str] = None) -> bool:
        cred = self.get_credential(device_id, user_id=user_id)
        return cred is not None and not cred.is_revoked

    # ========================================================
    # 4. PERSISTENCE
    # ========================================================

    def save(self):
        if not self.storage_path or self.storage_path == ":memory:":
            return
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            temp_path = f"{self.storage_path}.tmp.{os.getpid()}"
            data = {
                "credentials": {k: c.to_dict() for k, c in self._credentials.items()}
            }
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.storage_path):
                os.replace(temp_path, self.storage_path)
            else:
                os.rename(temp_path, self.storage_path)
        except Exception as e:
            logger.warning(f"[DeviceEnrollment] Saqlashda xatolik: {e}")

    def load(self):
        if not self.storage_path or self.storage_path == ":memory:" or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            creds = data.get("credentials", {})
            for k, cdata in creds.items():
                self._credentials[k] = DeviceCredential.from_dict(cdata)
        except Exception as e:
            logger.warning(f"[DeviceEnrollment] Yuklashda xatolik: {e}")
