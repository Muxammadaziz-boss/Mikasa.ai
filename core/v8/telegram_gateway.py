# ========== core/v8/telegram_gateway.py ==========
# Phase 35/36 — Real Telegram Remote Gateway Transport
# Async Telegram Bot API Client, Callbacks, Confirmation, Uzbek NLP & Progress Reporting

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Set

from core.v8.heartbeat import DeviceState
from core.v8.envelope import EnvelopeManager, RemoteCommandEnvelope
from core.v8.wol import WakeOnLanManager
from core.v8.events import RemoteEventType, RemoteAuditLogger, sanitize_sensitive_string

logger = logging.getLogger("core.v8.telegram")


class TelegramTransport(ABC):
    """
    Telegram Bot API transport interfeysi.
    Real network yoki test mock implementatsiyalari uchun ochiq.
    """

    @abstractmethod
    async def send_message(
        self,
        chat_id: Union[str, int],
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def edit_message_text(
        self,
        chat_id: Union[str, int],
        message_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> bool:
        pass

    @abstractmethod
    async def get_updates(
        self,
        offset: Optional[int] = None,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        pass


class MockTelegramTransport(TelegramTransport):
    """
    Testlar va offlayn muhit uchun to'liq mock transport.
    Haqiqiy Telegram tokeni yoki internet talab qilinmaydi.
    """

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []
        self.edited_messages: List[Dict[str, Any]] = []
        self.answered_callbacks: List[Dict[str, Any]] = []
        self.queued_updates: List[Dict[str, Any]] = []
        self._message_counter = 100

    async def send_message(
        self,
        chat_id: Union[str, int],
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        self._message_counter += 1
        msg = {
            "message_id": self._message_counter,
            "chat": {"id": chat_id},
            "text": text,
            "reply_markup": reply_markup,
            "parse_mode": parse_mode,
            "date": int(time.time())
        }
        self.sent_messages.append(msg)
        return {"ok": True, "result": msg}

    async def edit_message_text(
        self,
        chat_id: Union[str, int],
        message_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        msg = {
            "message_id": message_id,
            "chat": {"id": chat_id},
            "text": text,
            "reply_markup": reply_markup,
            "parse_mode": parse_mode,
            "date": int(time.time())
        }
        self.edited_messages.append(msg)
        return {"ok": True, "result": msg}

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> bool:
        self.answered_callbacks.append({
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert
        })
        return True

    async def get_updates(
        self,
        offset: Optional[int] = None,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        updates = list(self.queued_updates)
        self.queued_updates.clear()
        return updates


class AiohttpTelegramTransport(TelegramTransport):
    """
    Haqiqiy aiohttp orqali Telegram Bot API bilan to'g'ridan-to'g'ri bog'lanuvchi transport.
    Hech qanday tashqi telethon/aiogram kutubxonalarisiz ishlaydi.
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._session = None

    async def _get_session(self):
        import aiohttp
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def send_message(
        self,
        chat_id: Union[str, int],
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        session = await self._get_session()
        url = f"{self.base_url}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            return data

    async def edit_message_text(
        self,
        chat_id: Union[str, int],
        message_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        session = await self._get_session()
        url = f"{self.base_url}/editMessageText"
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            return data

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> bool:
        session = await self._get_session()
        url = f"{self.base_url}/answerCallbackQuery"
        payload: Dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        if show_alert:
            payload["show_alert"] = show_alert

        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            return bool(data.get("ok", False))

    async def get_updates(
        self,
        offset: Optional[int] = None,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        session = await self._get_session()
        url = f"{self.base_url}/getUpdates"
        params: Dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("result", [])

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class TelegramRemoteGateway:
    """
    Telegram bot transport qatlami.
    Faqat transport/gateway vazifasini bajaradi, to'g'ridan-to'g'ri shell executor EMAS.
    """

    def __init__(
        self,
        admin_id: Union[str, int],
        bot_token: str = "",
        allowed_user_ids: Optional[Set[Union[str, int]]] = None,
        envelope_manager: Optional[EnvelopeManager] = None,
        wol_manager: Optional[WakeOnLanManager] = None,
        transport: Optional[TelegramTransport] = None
    ):
        self.admin_id = str(admin_id)
        self.bot_token = bot_token
        self.allowed_user_ids: Set[str] = {self.admin_id}
        if allowed_user_ids:
            for uid in allowed_user_ids:
                self.allowed_user_ids.add(str(uid))

        self.envelope_manager = envelope_manager or EnvelopeManager(
            authorized_user_id=self.admin_id,
            authorized_user_ids=self.allowed_user_ids
        )
        self.wol_manager = wol_manager or WakeOnLanManager()
        self.transport = transport or (
            AiohttpTelegramTransport(bot_token) if bot_token else MockTelegramTransport()
        )
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self._audit = RemoteAuditLogger.get_instance()

        masked_token = sanitize_sensitive_string(self.bot_token) if self.bot_token else "NONE"
        logger.info(f"[TelegramGateway] Initsializatsiya qilindi. Admin={self.admin_id}, Token={masked_token}")

    def is_authorized(self, user_id: Union[str, int]) -> bool:
        return str(user_id) in self.allowed_user_ids

    def is_admin(self, user_id: Union[str, int]) -> bool:
        return str(user_id) == self.admin_id

    def add_allowed_user(self, user_id: Union[str, int]):
        self.allowed_user_ids.add(str(user_id))
        self.envelope_manager.authorized_user_ids.add(str(user_id))

    def parse_command(self, text: str) -> Dict[str, Any]:
        """
        Telegram xabarini tahlil qilib, amal va parametrlarga ajratish.
        Uzbek tabiiy tili ham to'liq tushuniladi.
        """
        raw = text.strip()
        lower = raw.lower()

        # Buyruqlar: Status
        if (
            lower.startswith("/pc")
            or lower.startswith("/status")
            or lower == "🟢 pc status"
            or lower == "🟢 status"
            or "kompyuterim yoqilganmi" in lower
            or "kompyuter holati" in lower
            or "pc status" in lower
        ):
            return {"action": "status", "params": {}}

        # Buyruqlar: Wake
        elif (
            lower.startswith("/wake")
            or lower == "⚡ wake pc"
            or "kompyuterni yoq" in lower
            or "kompyuterni uyg'ot" in lower
            or "kompyuterni uygot" in lower
            or "pc ni yoq" in lower
        ):
            return {"action": "wake", "params": {}}

        # Buyruqlar: System info
        elif (
            lower.startswith("/system_info")
            or lower.startswith("/sys")
            or lower == "system_info"
            or lower == "system info"
            or lower == "📊 system status"
            or lower == "📊 tizim holati"
            or "tizim holati" in lower
            or "system info" in lower
            or "system_info" in lower
        ):
            return {"action": "system_info", "params": {}}

        # Buyruqlar: Restart
        elif lower.startswith("/restart") or "kompyuterni qayta ishga tushir" in lower:
            return {"action": "restart", "params": {}, "high_risk": True}

        # Buyruqlar: Shutdown
        elif (
            lower.startswith("/shutdown")
            or "kompyuterni o'chir" in lower
            or "kompyuterni ochir" in lower
        ):
            return {"action": "shutdown", "params": {}, "high_risk": True}

        # Buyruqlar: Pairing
        elif lower.startswith("/pair"):
            parts = raw.split(maxsplit=1)
            token = parts[1].strip() if len(parts) > 1 else ""
            return {"action": "pair", "params": {"pairing_token": token}}

        # Buyruqlar: Session / Logout / Lock
        elif lower.startswith("/logout") or lower.startswith("/lock") or "sessiyani yop" in lower:
            return {"action": "logout", "params": {}}

        elif lower.startswith("/session") or "sessiya holati" in lower:
            return {"action": "session", "params": {}}

        # Buyruqlar: Cancel
        elif lower.startswith("/cancel") or lower == "❌ cancel" or lower == "bekor qilish":
            return {"action": "cancel", "params": {}}

        # Umumiy chat / NLP
        return {"action": "chat", "params": {"query": raw}}

    def build_keyboard(self) -> List[List[Dict[str, str]]]:
        """
        Asosiy boshqaruv inline tugmalari.
        """
        return [
            [
                {"text": "🟢 PC Status", "callback_data": "btn_status"},
                {"text": "⚡ Wake PC", "callback_data": "btn_wake"}
            ],
            [
                {"text": "📊 System Status", "callback_data": "btn_sys"},
                {"text": "🔄 Refresh", "callback_data": "btn_refresh"}
            ],
            [
                {"text": "❌ Cancel", "callback_data": "btn_cancel"}
            ]
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

    # ========================================================
    # CONFIRMATION MANAGEMENT (TTL-enabled)
    # ========================================================

    def store_pending_confirmation(
        self,
        request_id: str,
        envelope: RemoteCommandEnvelope,
        ttl: float = 60.0,
        chat_id: Optional[Union[str, int]] = None,
        prompt: Optional[str] = None
    ):
        """Xavfli amal uchun tasdiqlash so'rovini saqlash (default TTL: 60s)"""
        now = time.time()
        self._pending_confirmations[request_id] = {
            "envelope": envelope,
            "created_at": now,
            "expires_at": now + ttl,
            "chat_id": chat_id,
            "prompt": prompt
        }
        logger.info(f"[TelegramGateway] Pending confirmation yaratildi: req={request_id}, action={envelope.action}, ttl={ttl}s")

    def get_pending_confirmation(self, request_id: str) -> Optional[RemoteCommandEnvelope]:
        entry = self._pending_confirmations.get(request_id)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._pending_confirmations[request_id]
            return None
        return entry["envelope"]

    def pop_pending_confirmation(self, request_id: str) -> Optional[RemoteCommandEnvelope]:
        entry = self._pending_confirmations.pop(request_id, None)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            return None
        return entry["envelope"]

    def cancel_confirmation(self, request_id: str) -> bool:
        if request_id in self._pending_confirmations:
            del self._pending_confirmations[request_id]
            return True
        return False

    # ========================================================
    # TELEGRAM PROGRESS UX
    # ========================================================

    async def send_progress(
        self,
        chat_id: Union[str, int],
        current_step: int,
        total_steps: int,
        message: str,
        message_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Telegramda bosqichma-bosqich progress ko'rsatish (progress bar bilan).
        Yangi xabar yuborishi yoki mavjud xabarni yangilashi (edit) mumkin.
        """
        pct = int((current_step / max(total_steps, 1)) * 100)
        filled = int(pct / 10)
        unfilled = 10 - filled
        bar = "█" * filled + "░" * unfilled

        text = (
            f"⚡ **Mikasa Masofaviy Boshqaruv**\n"
            f"`[{bar}] {pct}%`\n\n"
            f"[{current_step}/{total_steps}] {message}"
        )

        try:
            if message_id:
                await self.transport.edit_message_text(chat_id, message_id, text)
                return message_id
            else:
                resp = await self.transport.send_message(chat_id, text)
                if isinstance(resp, dict) and resp.get("result"):
                    return resp["result"].get("message_id")
        except Exception as e:
            logger.warning(f"[TelegramGateway] Progress yuborishda xato: {e}")
        return None

    # ========================================================
    # UPDATE ROUTING (MESSAGES & CALLBACKS)
    # ========================================================

    async def handle_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Telegramdan kelgan Update obyektini tahlil qilish va qayta ishlash.
        Ruxsat, xavfsizlik va audit tekshiruvlarini o'z ichiga oladi.
        """
        # 1. Message Update
        if "message" in update:
            msg = update["message"]
            chat_id = msg.get("chat", {}).get("id")
            from_user = msg.get("from", {})
            user_id = str(from_user.get("id", chat_id))
            text = msg.get("text", "").strip()

            self._audit.log(
                RemoteEventType.REMOTE_REQUEST_RECEIVED,
                user_id=user_id,
                text=text
            )

            # Ruxsat tekshiruvi (Authorization)
            if not self.is_authorized(user_id):
                self._audit.log(
                    RemoteEventType.REMOTE_REQUEST_DENIED,
                    user_id=user_id,
                    reason="Unauthorized user"
                )
                await self.transport.send_message(
                    chat_id,
                    "⛔ **Ruxsat berilmadi!**\nSizda ushbu kompyuterni masofadan boshqarish huquqi yo'q."
                )
                return {
                    "handled": True,
                    "authorized": False,
                    "action": "denied",
                    "user_id": user_id
                }

            self._audit.log(
                RemoteEventType.REMOTE_REQUEST_AUTHORIZED,
                user_id=user_id,
                action="authorized"
            )

            parsed = self.parse_command(text)
            action = parsed["action"]

            if action == "status":
                await self.transport.send_message(
                    chat_id,
                    "🔍 **Kompyuter holati tekshirilmoqda...**",
                    reply_markup={"inline_keyboard": self.build_keyboard()}
                )
            elif action == "wake":
                await self.transport.send_message(
                    chat_id,
                    "⚡ **Kompyuterni uyg'otish boshlandi...**\nMagic packet yuborilmoqda."
                )
            elif action == "cancel":
                await self.transport.send_message(
                    chat_id,
                    "❌ **Amal bekor qilindi.**"
                )

            return {
                "handled": True,
                "authorized": True,
                "action": action,
                "parsed": parsed,
                "user_id": user_id,
                "chat_id": chat_id
            }

        # 2. Callback Query Update (Inline Buttons)
        elif "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb.get("id")
            from_user = cb.get("from", {})
            user_id = str(from_user.get("id"))
            data = cb.get("data", "")
            message = cb.get("message", {})
            chat_id = message.get("chat", {}).get("id")

            # Callback javob berish (loading to'xtatish)
            await self.transport.answer_callback_query(cb_id)

            if not self.is_authorized(user_id):
                self._audit.log(
                    RemoteEventType.REMOTE_REQUEST_DENIED,
                    user_id=user_id,
                    reason="Unauthorized callback query"
                )
                if chat_id:
                    await self.transport.send_message(
                        chat_id,
                        "⛔ **Ruxsat yo'q!** Ushbu amalni faqat vakolatli administrator bajara oladi."
                    )
                return {
                    "handled": True,
                    "authorized": False,
                    "action": "callback_denied"
                }

            # Confirmation javoblari: confirm_yes:<req_id> yoki confirm_no:<req_id>
            if data.startswith("confirm_yes:"):
                req_id = data.split(":", 1)[1]
                envelope = self.pop_pending_confirmation(req_id)
                if not envelope:
                    if chat_id:
                        await self.transport.send_message(
                            chat_id,
                            "⚠️ **Tasdiqlash muddati o'tgan yoki bekor qilingan.**"
                        )
                    return {"handled": True, "action": "confirmation_expired", "request_id": req_id}

                envelope.confirmation_required = False  # Endi tasdiqlandi
                if chat_id:
                    await self.transport.send_message(
                        chat_id,
                        f"✅ **Amal tasdiqlandi:** `{envelope.action}` bajarilmoqda..."
                    )
                return {
                    "handled": True,
                    "action": "confirmation_approved",
                    "request_id": req_id,
                    "envelope": envelope
                }

            elif data.startswith("confirm_no:"):
                req_id = data.split(":", 1)[1]
                self.cancel_confirmation(req_id)
                if chat_id:
                    await self.transport.send_message(
                        chat_id,
                        "❌ **Xavfli amal bekor qilindi.**"
                    )
                return {"handled": True, "action": "confirmation_cancelled", "request_id": req_id}

            # Standart inline tugmalar
            return {
                "handled": True,
                "authorized": True,
                "action": "callback_button",
                "button_key": data,
                "chat_id": chat_id,
                "user_id": user_id
            }

        return {"handled": False, "reason": "Unknown update type"}
