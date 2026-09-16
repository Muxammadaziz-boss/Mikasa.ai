# ========== core/v8/wol.py ==========
# Phase 35 — Wake-on-LAN Manager & Magic Packet Constructor

import re
import socket
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger("core.v8.wol")


def create_magic_packet(mac_address: str) -> bytes:
    """
    Standart WoL Magic Packet (6 ta 0xFF baytlari ketidan 16 marta 6-baytli MAC takrorlanadi).
    Jami 102 bayt.
    """
    clean_mac = re.sub(r"[^0-9A-Fa-f]", "", mac_address)
    if len(clean_mac) != 12:
        raise ValueError(f"Noto'g'ri MAC manzil formati: {mac_address} (12 ta hex belgidan iborat bo'lishi kerak)")

    mac_bytes = bytes.fromhex(clean_mac)
    magic_packet = b"\xff" * 6 + mac_bytes * 16
    return magic_packet


class WakeRelay(ABC):
    """
    Tarmoq ichida WoL paketini yetkazib beruvchi relay interfeysi.
    """

    @abstractmethod
    async def send_wake(self, mac_address: str, broadcast_ip: str = "255.255.255.255", port: int = 9) -> bool:
        pass


class LocalBroadcastRelay(WakeRelay):
    """
    Mahalliy tarmoqda to'g'ridan-to'g'ri UDP broadcast orqali yuborish.
    """

    async def send_wake(self, mac_address: str, broadcast_ip: str = "255.255.255.255", port: int = 9) -> bool:
        packet = create_magic_packet(mac_address)
        loop = asyncio.get_running_loop()

        def _broadcast():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:
                sock.sendto(packet, (broadcast_ip, port))
                return True
            finally:
                sock.close()

        return await loop.run_in_executor(None, _broadcast)


class WakeOnLanManager:
    """
    Wake-on-LAN jo'natish, qayta urinish va holat monitoringini boshqaradi.
    """

    def __init__(self, relay: Optional[WakeRelay] = None, retry_count: int = 3, retry_delay: float = 0.5):
        self.relay = relay or LocalBroadcastRelay()
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    async def wake_device(
        self,
        mac_address: str,
        broadcast_ip: str = "255.255.255.255",
        port: int = 9
    ) -> Dict[str, Any]:
        """
        Qurilmaga bir nechta urinish bilan WoL paketini yuboradi.
        """
        try:
            packet = create_magic_packet(mac_address)
        except Exception as e:
            logger.error(f"[WoL] Magic packet yaratishda xato: {e}")
            return {
                "success": False,
                "attempts": 0,
                "packet_size": 0,
                "error": str(e)
            }

        successful_attempts = 0
        last_err = None

        for attempt in range(1, self.retry_count + 1):
            try:
                res = await self.relay.send_wake(mac_address, broadcast_ip=broadcast_ip, port=port)
                if res:
                    successful_attempts += 1
                    logger.info(f"[WoL] Magic packet muvaffaqiyatli yuborildi ({attempt}/{self.retry_count}) -> {mac_address}")
            except Exception as e:
                last_err = str(e)
                logger.warning(f"[WoL] Urinish {attempt} muvaffaqiyatsiz: {e}")

            if attempt < self.retry_count and self.retry_delay > 0:
                await asyncio.sleep(self.retry_delay)

        return {
            "success": successful_attempts > 0,
            "attempts": successful_attempts,
            "packet_size": len(packet),
            "error": last_err if successful_attempts == 0 else None
        }
