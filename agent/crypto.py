# ========== agent/crypto.py ==========
# Phase 45 — Windows PC Agent Ed25519 Cryptographic Manager
# DPAPI-backed private key management and canonical challenge signing

import time
import logging
import platform
from typing import Optional, Dict, Any

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from core.v8.device_enrollment import (
    SecureCredentialStore,
    WindowsCredentialStore,
    MockCredentialStore
)
from core.v8.device_auth import DeviceAuthManager

logger = logging.getLogger("mikasa.agent.crypto")


class AgentCrypto:
    """
    Windows PC Agent tomonida asimmetrik Ed25519 kalitlar boshqaruvi.
    - Private key Windows DPAPI (CryptProtectData) orqali shifrlangan saqlanadi.
    - Non-Windows (Linux CI) muhitlarda MockCredentialStore orqali ishlaydi.
    - Backend uchun faqat 32-baytlik ommaviy kalit (public_key_hex) taqdim etiladi.
    - Challenge xabarlarini kanonik formatda imzolaydi.
    - Xotiradan kalitni tozalash (clean_memory) funksiyasiga ega.
    """

    def __init__(
        self,
        device_id: str,
        vault_dir: Optional[str] = None,
        credential_store: Optional[SecureCredentialStore] = None
    ):
        self.device_id = str(device_id).strip()
        self.vault_dir = vault_dir

        if credential_store is not None:
            self.store: SecureCredentialStore = credential_store
        elif platform.system().lower() == "windows":
            self.store = WindowsCredentialStore(base_dir=vault_dir)
        else:
            self.store = MockCredentialStore()

        self._private_key: Optional[ed25519.Ed25519PrivateKey] = None
        self._public_key_hex: Optional[str] = None
        self._init_keypair()

    def _cred_key_name(self) -> str:
        return f"ed25519_agent_key_{self.device_id}"

    def _init_keypair(self):
        """Mavjud kalitni vaultdan yuklash yoki yangisini yaratib saqlash"""
        key_name = self._cred_key_name()
        stored_priv_hex = self.store.load_credential(key_name)

        if stored_priv_hex:
            try:
                priv_bytes = bytes.fromhex(stored_priv_hex)
                self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
                logger.info(f"[AgentCrypto] Mavjud Ed25519 kaliti vaultdan yuklandi: dev={self.device_id}")
            except Exception as e:
                logger.warning(f"[AgentCrypto] Vaultdagi kalitni o'qishda xato: {e}")
                self._private_key = None

        if self._private_key is None:
            self._private_key = ed25519.Ed25519PrivateKey.generate()
            raw_priv = self._private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            self.store.save_credential(key_name, raw_priv.hex())
            logger.info(f"[AgentCrypto] Yangi Ed25519 kaliti yaratildi va saqlandi: dev={self.device_id}")

        pub = self._private_key.public_key()
        pub_bytes = pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self._public_key_hex = pub_bytes.hex().lower()

    @property
    def public_key_hex(self) -> str:
        """64-belgili hex Ed25519 public key"""
        if not self._public_key_hex:
            self._init_keypair()
        return self._public_key_hex or ""

    def sign_challenge(
        self,
        nonce: str,
        timestamp: Optional[float] = None,
        protocol_version: str = "1.0"
    ) -> Dict[str, Any]:
        """
        Backenddan kelgan nonce chaqirig'ini kanonik tartibda imzolash:
        device_id|nonce|timestamp|protocol_version
        """
        if self._private_key is None:
            self._init_keypair()

        if self._private_key is None:
            raise RuntimeError("Ed25519 private key yuklanmadi")

        ts = float(timestamp if timestamp is not None else time.time())
        msg = DeviceAuthManager.canonical_challenge_message(
            device_id=self.device_id,
            nonce=nonce,
            timestamp=ts,
            protocol_version=protocol_version
        )

        signature = self._private_key.sign(msg)
        return {
            "signature": signature.hex(),
            "context": {
                "device_id": self.device_id,
                "nonce": nonce,
                "timestamp": ts,
                "protocol_version": protocol_version
            }
        }

    def regenerate_keypair(self) -> str:
        """Qurilma qayta ulanganda (re-pair) kalitlarni almashtirish"""
        key_name = self._cred_key_name()
        self.store.delete_credential(key_name)
        self._private_key = None
        self._public_key_hex = None
        self._init_keypair()
        return self.public_key_hex

    def clean_memory(self):
        """Shutdown vaqtida maxfiy kalitni xotiradan tozalash"""
        self._private_key = None
        logger.info("[AgentCrypto] Maxfiy kalit xotiradan tozalandi")
