# ========== core/v8/telegram_gateway.py ==========
# Phase 35 — Telegram Remote Gateway Transport

import logging
from typing import Dict, Any, Optional, List, Union

from core.v8.heartbeat import DeviceState
from core.v8.envelope import EnvelopeManager, RemoteCommandEnvelope
from core.v8.wol import WakeOnLanManager

logger = logging.getLogger("core.v8.telegram")


class TelegramRemoteGateway:
    """
    Telegram bot transport qatlami.
    Faqat transport/gateway vazifasini bajaradi, to'g'ridan-to'g'ri shell executor EMAS.
    """

    def __init__(
        self,
        admin_id: Union[str, int],
        bot_token: str = "",
        envelope_manager: Optional[EnvelopeManager] = None,
        wol_manager: Optional[WakeOnLanManager] = None
    ):
        self.admin_id = str(admin_id)
        self.bot_token = bot_token
        self.envelope_manager = envelope_manager or EnvelopeManager(authorized_user_id=self.admin_id)
        self.wol_manager = wol_manager or WakeOnLanManager()
        self._pending_confirmations: Dict[str, RemoteCommandEnvelope] = {}

    def is_authorized(self, user_id: Union[str, int]) -> bool:
        return str(user_id) == self.admin_id

    def parse_command(self, text: str) -> Dict[str, Any]:
        """
        Telegram xabarini tahlil qilib, amal va parametrlarga ajratish.
        Uzbek tabiiy tili ham tushuniladi.
        """
        raw = text.strip()
        lower = raw.lower()

        # Buyruqlar
        if lower.startswith("/pc") or lower == "🟢 pc status" or "kompyuterim yoqilganmi" in lower or "kompyuter holati" in lower:
            return {"action": "status", "params": {}}
        elif lower.startswith("/wake") or lower == "⚡ wake pc" or "kompyuterni yoq" in lower:
            return {"action": "wake", "params": {}}
        elif lower == "📊 system status" or "tizim holati" in lower:
            return {"action": "system_info", "params": {}}
        elif lower.startswith("/restart") or "kompyuterni qayta ishga tushir" in lower:
            return {"action": "restart", "params": {}, "high_risk": True}
        elif lower.startswith("/shutdown") or "kompyuterni o'chir" in lower:
            return {"action": "shutdown", "params": {}, "high_risk": True}

        return {"action": "chat", "params": {"query": raw}}

    def build_keyboard(self) -> List[List[Dict[str, str]]]:
        """
        Asosiy boshqaruv tugmalari.
        """
        return [
            [{"text": "🟢 PC Status", "callback_data": "btn_status"}, {"text": "⚡ Wake PC", "callback_data": "btn_wake"}],
            [{"text": "📊 System Status", "callback_data": "btn_sys"}, {"text": "🔄 Refresh", "callback_data": "btn_refresh"}],
            [{"text": "❌ Cancel", "callback_data": "btn_cancel"}]
        ]

    def build_confirmation_keyboard(self, request_id: str) -> List[List[Dict[str, str]]]:
        return [
            [
                {"text": "✅ Ha, bajarilsin", "callback_data": f"confirm_yes:{request_id}"},
                {"text": "❌ Bekor qilish", "callback_data": f"confirm_no:{request_id}"}
            ]
        ]

    def format_status_message(self, device_info: Dict[str, Any], state: DeviceState) -> str:
        state_emojis = {
            DeviceState.ONLINE: "🟢 ONLINE (Faol)",
            DeviceState.OFFLINE: "🔴 OFFLINE (O'chiq)",
            DeviceState.WAKING: "⚡ WAKING (Uyg'onmoqda)",
            DeviceState.CONNECTING: "🔄 CONNECTING (Ulanmoqda)",
            DeviceState.READY: "✅ READY (Tayyor)",
            DeviceState.ERROR: "⚠️ ERROR (Xatolik)"
        }
        state_str = state_emojis.get(state, state.value)
        hostname = device_info.get("hostname", "Noma'lum")
        os_info = f"{device_info.get('os_name', '')} {device_info.get('os_release', '')}".strip() or "Windows"
        last_seen = device_info.get("last_seen", "Hozirgina")

        return (
            f"🖥️ **MIKASA AI — Kompyuter Holati**\n\n"
            f"• **Holat:** {state_str}\n"
            f"• **Qurilma:** `{hostname}`\n"
            f"• **Tizim:** {os_info}\n"
            f"• **IP / MAC:** `{device_info.get('local_ip', '127.0.0.1')}` / `{device_info.get('mac_address', 'N/A')}`\n"
            f"• **Oxirgi faollik:** `{last_seen}`\n"
            f"• **Versiya:** Mikasa v8.0.0"
        )
