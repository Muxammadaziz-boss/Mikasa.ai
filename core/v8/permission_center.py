# ========== core/v8/permission_center.py ==========
# Phase 38 — User Permission Center & Capability Engine
# Persistent, Per-User, Per-Device Capability-Based Permissions with Instant Propagation

import os
import time
import json
import logging
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Callable

from core.intelligence.types import RiskLevel
from core.v8.events import RemoteEventType, RemoteAuditLogger

logger = logging.getLogger("core.v8.permission")


class PermissionCategory(str, Enum):
    SYSTEM = "SYSTEM"
    APPLICATIONS = "APPLICATIONS"
    FILES = "FILES"
    NETWORK = "NETWORK"
    POWER = "POWER"
    ADVANCED = "ADVANCED"


@dataclass
class PermissionDefinition:
    """Tizimdagi ruxsat elementi ta'rifi"""
    id: str
    name: str
    category: PermissionCategory
    description: str
    default_enabled: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "default_enabled": self.default_enabled,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level),
            "requires_confirmation": self.requires_confirmation
        }


# Standart Ruxsatlar Katalogi (Phase 38 Matrix)
STANDARD_PERMISSIONS: List[PermissionDefinition] = [
    # 1. System
    PermissionDefinition(
        id="system.status",
        name="Kompyuter holati",
        category=PermissionCategory.SYSTEM,
        description="Kompyuterning faol yoki oflayn holatini tekshirish",
        default_enabled=True,
        risk_level=RiskLevel.LOW,
        requires_confirmation=False
    ),
    PermissionDefinition(
        id="system.info",
        name="Tizim ma'lumotlari (CPU/RAM)",
        category=PermissionCategory.SYSTEM,
        description="Operatsion tizim, protsessor va xotira yuklamasini ko'rish",
        default_enabled=True,
        risk_level=RiskLevel.LOW,
        requires_confirmation=False
    ),
    PermissionDefinition(
        id="system.screenshot",
        name="Ekran tasviri (Screenshot)",
        category=PermissionCategory.SYSTEM,
        description="Ishchi stol ekran tasvirini olish va ko'rish",
        default_enabled=True,
        risk_level=RiskLevel.LOW,
        requires_confirmation=False
    ),

    # 2. Applications
    PermissionDefinition(
        id="app.list",
        name="Dasturlar ro'yxati",
        category=PermissionCategory.APPLICATIONS,
        description="Ishlayotgan va o'rnatilgan dasturlarni ko'rish",
        default_enabled=True,
        risk_level=RiskLevel.LOW,
        requires_confirmation=False
    ),
    PermissionDefinition(
        id="app.launch",
        name="Tasdiqlangan dasturni ochish",
        category=PermissionCategory.APPLICATIONS,
        description="Ruxsat etilgan dasturlar ro'yxatidagi ilovani ishga tushirish",
        default_enabled=True,
        risk_level=RiskLevel.MEDIUM,
        requires_confirmation=False
    ),
    PermissionDefinition(
        id="app.close",
        name="Dasturni yopish",
        category=PermissionCategory.APPLICATIONS,
        description="Ishlayotgan ilova yoki jarayonni to'xtatish",
        default_enabled=False,
        risk_level=RiskLevel.MEDIUM,
        requires_confirmation=True
    ),

    # 3. Files
    PermissionDefinition(
        id="file.list",
        name="Fayllar ro'yxatini ko'rish",
        category=PermissionCategory.FILES,
        description="Ruxsat etilgan kataloglardagi fayllarni ko'rish",
        default_enabled=True,
        risk_level=RiskLevel.LOW,
        requires_confirmation=False
    ),
    PermissionDefinition(
        id="file.read",
        name="Faylni o'qish",
        category=PermissionCategory.FILES,
        description="Xavfsiz matnli fayllar tarkibini ko'rish",
        default_enabled=True,
        risk_level=RiskLevel.MEDIUM,
        requires_confirmation=False
    ),
    PermissionDefinition(
        id="file.write",
        name="Fayl yozish / saqlash",
        category=PermissionCategory.FILES,
        description="Fayllarni yaratish yoki yangilash",
        default_enabled=False,
        risk_level=RiskLevel.MEDIUM,
        requires_confirmation=False
    ),
    PermissionDefinition(
        id="file.delete",
        name="Faylni o'chirish",
        category=PermissionCategory.FILES,
        description="Fayllarni xavfsiz o'chirib yuborish",
        default_enabled=False,
        risk_level=RiskLevel.HIGH,
        requires_confirmation=True
    ),

    # 4. Network
    PermissionDefinition(
        id="network.info",
        name="Tarmoq holati",
        category=PermissionCategory.NETWORK,
        description="IP manzillar va tarmoq interfeyslari holatini ko'rish",
        default_enabled=True,
        risk_level=RiskLevel.LOW,
        requires_confirmation=False
    ),

    # 5. Power
    PermissionDefinition(
        id="power.wake",
        name="Kompyuterni uyg'otish (WoL)",
        category=PermissionCategory.POWER,
        description="Wake-on-LAN paketi orqali kompyuterni yoqish",
        default_enabled=True,
        risk_level=RiskLevel.LOW,
        requires_confirmation=False
    ),
    PermissionDefinition(
        id="power.restart",
        name="Qayta ishga tushirish (Restart)",
        category=PermissionCategory.POWER,
        description="Kompyuterni masofadan qayta yuklash",
        default_enabled=True,
        risk_level=RiskLevel.HIGH,
        requires_confirmation=True
    ),
    PermissionDefinition(
        id="power.shutdown",
        name="O'chirish (Shutdown)",
        category=PermissionCategory.POWER,
        description="Kompyuterni masofadan to'liq o'chirish",
        default_enabled=False,
        risk_level=RiskLevel.HIGH,
        requires_confirmation=True
    ),
    PermissionDefinition(
        id="power.sleep",
        name="Kutish rejimiga o'tkazish (Sleep)",
        category=PermissionCategory.POWER,
        description="Kompyuterni uyqu rejimiga kiritish",
        default_enabled=False,
        risk_level=RiskLevel.HIGH,
        requires_confirmation=True
    ),

    # 6. Advanced / Capability
    PermissionDefinition(
        id="admin.tool.access",
        name="Kengaytirilgan boshqaruv asboblari",
        category=PermissionCategory.ADVANCED,
        description="Maxsus ma'muriy vositalar va konfiguratsiyalarga kirish",
        default_enabled=False,
        risk_level=RiskLevel.HIGH,
        requires_confirmation=True
    ),
]

PERMISSIONS_BY_ID: Dict[str, PermissionDefinition] = {p.id: p for p in STANDARD_PERMISSIONS}


@dataclass
class UserPermissionProfile:
    """Foydalanuvchi va Qurilma uchun biriktirilgan faol ruxsatlar profili"""
    user_id: str
    device_id: str
    permissions: Dict[str, bool] = field(default_factory=dict)
    capabilities: Dict[str, bool] = field(default_factory=dict)
    version: int = 1
    updated_at: float = field(default_factory=time.time)

    def is_granted(self, permission_id: str) -> bool:
        """Ruxsat berilganligini tekshirish"""
        clean_id = permission_id.strip()

        # Capability darajasida tekshirish (masalan: ADMIN_FILE_ACCESS)
        if clean_id.startswith("file.") and not self.capabilities.get("ADMIN_FILE_ACCESS", True):
            return False
        if clean_id.startswith("power.") and not self.capabilities.get("ADMIN_POWER_CONTROL", True):
            return False
        if clean_id.startswith("app.") and not self.capabilities.get("ADMIN_APP_CONTROL", True):
            return False

        # To'g'ridan-to'g'ri ruxsat tekshiruvi
        if clean_id in self.permissions:
            return bool(self.permissions[clean_id])

        # Agar ro'yxatda yo'q bo'lsa, standart sozlamani olish
        defn = PERMISSIONS_BY_ID.get(clean_id)
        if defn:
            return defn.default_enabled

        return False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPermissionProfile":
        return cls(**data)


class PermissionStore:
    """
    Foydalanuvchilarning ruxsat profillarini doimiy saqlash va tezkor tekshirish xotirasi.
    O'zgarishlarni zudlik bilan barcha komponentlarga (Telegram Gateway, PermissionEngine)
    qayta ishga tushirishsiz (zero-restart) yetkazadi.
    """

    _default_instance: Optional["PermissionStore"] = None

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "v8_permissions.json"
        )
        self._profiles: Dict[str, UserPermissionProfile] = {}  # f"{user_id}:{device_id}" -> UserPermissionProfile
        self._subscribers: List[Callable[[UserPermissionProfile], None]] = []
        self._audit = RemoteAuditLogger.get_instance()
        self.load()

    @classmethod
    def get_default_instance(cls, storage_path: Optional[str] = None) -> "PermissionStore":
        if cls._default_instance is None:
            cls._default_instance = cls(storage_path=storage_path)
        return cls._default_instance

    def _get_key(self, user_id: str, device_id: str) -> str:
        return f"{str(user_id)}:{str(device_id)}"

    def subscribe(self, callback: Callable[[UserPermissionProfile], None]):
        """Ruxsatlar o'zgarganda xabardor qiluvchi listener ro'yxatga olish"""
        self._subscribers.append(callback)

    def get_catalog(self) -> List[Dict[str, Any]]:
        """Barcha ruxsatlar katalogi (UI uchun)"""
        return [p.to_dict() for p in STANDARD_PERMISSIONS]

    def get_profile(self, user_id: str, device_id: str) -> UserPermissionProfile:
        """Foydalanuvchi profilini olish yoki standart profil yaratish"""
        key = self._get_key(user_id, device_id)
        if key not in self._profiles:
            # Standart ruxsatlar xaritasi
            default_perms = {p.id: p.default_enabled for p in STANDARD_PERMISSIONS}
            default_caps = {
                "ADMIN_SYSTEM_INFO": True,
                "ADMIN_APP_CONTROL": True,
                "ADMIN_FILE_ACCESS": True,
                "ADMIN_POWER_CONTROL": True,
                "ADMIN_NETWORK_CONTROL": True,
                "ADMIN_DEVICE_CONFIGURATION": False
            }
            profile = UserPermissionProfile(
                user_id=str(user_id),
                device_id=str(device_id),
                permissions=default_perms,
                capabilities=default_caps,
                version=1,
                updated_at=time.time()
            )
            self._profiles[key] = profile
            self.save()

        return self._profiles[key]

    def is_granted(self, user_id: str, device_id: str, permission_id: str) -> bool:
        """Muayyan ruxsat yoqilganligini tekshirish"""
        profile = self.get_profile(user_id, device_id)
        return profile.is_granted(permission_id)

    def has_permission(self, user_id: str, device_id: str, permission_id: str) -> bool:
        """Ruxsat mavjudligini tekshirish (is_granted uchun alias)"""
        return self.is_granted(user_id, device_id, permission_id)

    def grant_permission(self, user_id: str, device_id: str, permission_id: str) -> UserPermissionProfile:
        """Muayyan ruxsatni yoqish"""
        return self.update_permissions(user_id, device_id, {permission_id: True})

    def revoke_permission(self, user_id: str, device_id: str, permission_id: str) -> UserPermissionProfile:
        """Muayyan ruxsatni bekor qilish"""
        return self.update_permissions(user_id, device_id, {permission_id: False})

    def get_effective_capabilities(self, user_id: str, device_id: str) -> List[str]:
        """Foydalanuvchi ega bo'lgan faol capabilitylar ro'yxati"""
        profile = self.get_profile(user_id, device_id)
        return [k for k, v in profile.capabilities.items() if v]

    def revoke_device_permissions(self, user_id: str, device_id: str) -> bool:
        """Qurilma o'chirilganda yoki bekor qilinganda uning ruxsat profilini tozalash (Phase 40)"""
        key = self._get_key(user_id, device_id)
        if key in self._profiles:
            del self._profiles[key]
            self.save()
            self._audit.log(
                RemoteEventType.PERMISSION_REVOKED,
                user_id=str(user_id),
                device_id=str(device_id),
                details={"reason": "device_revoked"}
            )
            return True
        return False

    def add_observer(self, callback: Callable):
        """Observer listener qo'shish"""
        self.subscribe(callback)

    def update_permissions(
        self,
        user_id: str,
        device_id: str,
        new_permissions: Dict[str, bool],
        new_capabilities: Optional[Dict[str, bool]] = None
    ) -> UserPermissionProfile:
        """
        Foydalanuvchi ruxsatlarini yangilash.
        Tizimni qayta ishga tushirishsiz Telegram va boshqa xizmatlarda zudlik bilan qo'llaniladi.
        """
        profile = self.get_profile(user_id, device_id)
        old_perms = dict(profile.permissions)

        # Ruxsatlarni yangilash va audit qilish
        for perm_id, is_enabled in new_permissions.items():
            prev_val = old_perms.get(perm_id)
            new_val = bool(is_enabled)
            profile.permissions[perm_id] = new_val

            if prev_val is not None and prev_val != new_val:
                event_type = RemoteEventType.PERMISSION_GRANTED if new_val else RemoteEventType.PERMISSION_REVOKED
                self._audit.log(
                    event_type,
                    user_id=str(user_id),
                    device_id=str(device_id),
                    permission=perm_id,
                    enabled=new_val
                )

        # Capabilities yangilash
        if new_capabilities:
            profile.capabilities.update(new_capabilities)

        # Versiya va vaqt yangilanishi
        profile.version += 1
        profile.updated_at = time.time()
        self.save()

        self._audit.log(
            RemoteEventType.PERMISSION_CHANGED,
            user_id=str(user_id),
            device_id=str(device_id),
            version=profile.version
        )
        logger.info(f"[PermissionStore] Ruxsatlar yangilandi: user={user_id}, dev={device_id}, ver={profile.version}")

        # Barcha obunachilarni (Gateway, Telegram, WebSocket) darhol xabardor qilish
        for sub in self._subscribers:
            try:
                import inspect
                sig = inspect.signature(sub)
                if len(sig.parameters) >= 3:
                    sub(user_id, device_id, profile)
                else:
                    sub(profile)
            except Exception as e:
                logger.error(f"[PermissionStore] Obunachi xatosi: {e}")

        return profile

    def save(self):
        if not self.storage_path:
            return
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            data = {
                "profiles": {k: v.to_dict() for k, v in self._profiles.items()}
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[PermissionStore] Saqlashda xatolik: {e}")

    def load(self):
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            profiles_raw = data.get("profiles", {})
            self._profiles = {k: UserPermissionProfile.from_dict(v) for k, v in profiles_raw.items()}
            logger.info(f"[PermissionStore] {len(self._profiles)} ta ruxsat profili yuklandi.")
        except Exception as e:
            logger.error(f"[PermissionStore] Yuklashda xatolik: {e}")
