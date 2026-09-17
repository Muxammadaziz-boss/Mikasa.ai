# ========== core/v8/device_agent_crypto.py ==========
# Phase 42 — PC Agent Cryptographic Client Helper
# Client-side Ed25519 keypair generation, OS DPAPI secure private key storage,
# and challenge signing. Private key NEVER leaves this module.

import time
import logging
from typing import Optional, Dict, Any

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from core.v8.device_enrollment import SecureCredentialStore, WindowsCredentialStore
from core.v8.device_auth import DeviceAuthManager

logger = logging.getLogger("core.v8.device_agent_crypto")


class DeviceAgentCrypto:
    """
    PC Agent tomonida ishlovchi kriptografik yordamchi.
    - Ed25519 kalitlar juftligini yaratadi yoki SecureCredentialStore orqali yuklaydi.
    - Private key hech qachon tashqariga chiqarilmaydi, faqat ommaviy kalit (public_key) yuboriladi.
    - Challenge xabarlarini kanonik formatda imzolaydi.
    """

    def __init__(
        self,
        device_id: str,
        credential_store: Optional[SecureCredentialStore] = None
    ):
        self.device_id = str(device_id).strip()
        self.store = credential_store or WindowsCredentialStore()
        self._private_key: Optional[ed25519.Ed25519PrivateKey] = None
        self._public_key_hex: Optional[str] = None
        self._init_keypair()

    def _cred_key_name(self) -> str:
        return f"ed25519_key_{self.device_id}"

    def _init_keypair(self):
        """Mavjud kalitni yuklash yoki yangisini yaratib saqlash"""
        key_name = self._cred_key_name()
        stored_priv_hex = self.store.load_credential(key_name)

        if stored_priv_hex:
            try:
                priv_bytes = bytes.fromhex(stored_priv_hex)
                self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
            except Exception as e:
                logger.warning(f"[DeviceAgentCrypto] Saqlangan kalitni yuklashda xato: {e}")
                self._private_key = None

        if self._private_key is None:
            # Yangi Ed25519 kalitini yaratish
            self._private_key = ed25519.Ed25519PrivateKey.generate()
            raw_priv = self._private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            self.store.save_credential(key_name, raw_priv.hex())
            logger.info(f"[DeviceAgentCrypto] Yangi Ed25519 kaliti yaratildi va saqlandi: dev={self.device_id}")

        # Ommaviy kalitni hisoblash
        pub = self._private_key.public_key()
        pub_bytes = pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self._public_key_hex = pub_bytes.hex().lower()

    @property
    def public_key_hex(self) -> str:
        """64 belgili hex Ed25519 public key (enrollment so'rovi uchun xavfsiz)"""
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
        Backenddan kelgan chaqiriqni (nonce) kanonik tartibda imzolash.
        Qaytaradi: {
            "signature": hex_string,
            "context": {
                "device_id": self.device_id,
                "nonce": nonce,
                "timestamp": ts,
                "protocol_version": protocol_version
            }
        }
        """
        if self._private_key is None:
            raise RuntimeError("Private key mavjud emas")

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
        """Qurilma qayta enroll (re-pair) qilinganda yangi kalit yaratish"""
        key_name = self._cred_key_name()
        self.store.delete_credential(key_name)
        self._private_key = None
        self._public_key_hex = None
        self._init_keypair()
        return self.public_key_hex
