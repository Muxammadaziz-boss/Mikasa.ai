# ========== core/v8/universal_bot.py ==========
# Phase 39 — Universal Telegram Bot ↔ Mikasa User App
# Multi-User Universal Telegram Bot Dispatcher
# Strict isolation by numeric telegram_user_id, zero PC connection in Phase 39

import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union

from core.v8.telegram_gateway import TelegramTransport, MockTelegramTransport
from core.v8.telegram_identity import TelegramIdentityManager, TelegramIdentity

logger = logging.getLogger("core.v8.universal_bot")


class UniversalTelegramBot:
    """
    Universal Telegram Bot for multi-user identity resolution & account linking.
    One bot serving many Telegram users and many Mikasa accounts.
    Strictly isolated by canonical numeric Telegram user ID.
    """

    OTP_REGEX = re.compile(r"^\s*(\d{6})\s*$")

    def __init__(
        self,
        transport: Optional[TelegramTransport] = None,
        identity_manager: Optional[TelegramIdentityManager] = None,
        bot_username: str = "MikasaUniversalBot"
    ):
        self.transport: TelegramTransport = transport or MockTelegramTransport()
        self.identity_mgr: TelegramIdentityManager = identity_manager or TelegramIdentityManager.get_default_instance()
        self.bot_username: str = bot_username.lstrip("@").strip()

    async def process_update(self, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ingest and process a single Telegram update dictionary.
        Extracts user metadata, canonical numeric ID, and dispatches to handler.
        """
        message = update.get("message") or update.get("edited_message")
        if not message:
            return None

        chat = message.get("chat", {})
        chat_id = chat.get("id")
        from_user = message.get("from", {})
        raw_tg_id = from_user.get("id") or chat_id

        # Validate positive numeric Telegram User ID
        is_valid_id, tg_user_id = TelegramIdentity.validate_user_id(raw_tg_id)
        if not is_valid_id or tg_user_id is None:
            logger.warning(f"[UniversalBot] Rad etildi: yaroqsiz Telegram ID '{raw_tg_id}'")
            return None

        first_name = from_user.get("first_name")
        username = from_user.get("username")
        text = str(message.get("text", "")).strip()

        # Update or register identity
        self.identity_mgr.register_or_update_identity(
            telegram_user_id=tg_user_id,
            first_name=first_name,
            username=username
        )

        return await self.handle_message(
            chat_id=chat_id or tg_user_id,
            tg_user_id=tg_user_id,
            first_name=first_name,
            username=username,
            text=text
        )

    async def handle_message(
        self,
        chat_id: Union[int, str],
        tg_user_id: int,
        first_name: Optional[str],
        username: Optional[str],
        text: str
    ) -> Dict[str, Any]:
        """
        Route message according to commands, raw OTP, or natural text.
        Multi-user isolated: state and context strictly keyed by tg_user_id.
        """
        if not text:
            return await self._send_reply(chat_id, "Iltimos, matnli buyruq yoki tasdiqlash kodini yuboring.")

        # 1. /start [token]
        if text.startswith("/start"):
            parts = text.split(maxsplit=1)
            token = parts[1].strip() if len(parts) > 1 else ""
            return await self._handle_start(chat_id, tg_user_id, first_name, username, token)

        # 2. /link [code]
        if text.startswith("/link"):
            parts = text.split(maxsplit=1)
            code = parts[1].strip() if len(parts) > 1 else ""
            return await self._handle_link(chat_id, tg_user_id, first_name, username, code)

        # 3. Raw 6-digit numeric OTP entry (e.g. 583921)
        match_otp = self.OTP_REGEX.match(text)
        if match_otp:
            code = match_otp.group(1)
            return await self._handle_link(chat_id, tg_user_id, first_name, username, code)

        # 4. /unlink
        if text.startswith("/unlink"):
            return await self._handle_unlink(chat_id, tg_user_id)

        # 5. /account
        if text.startswith("/account"):
            return await self._handle_account(chat_id, tg_user_id, first_name, username)

        # 6. /status
        if text.startswith("/status"):
            return await self._handle_status(chat_id, tg_user_id)

        # 7. /help
        if text.startswith("/help"):
            return await self._handle_help(chat_id, first_name)

        # Fallback for unrecognized text
        return await self._send_reply(
            chat_id,
            "Tushunarsiz buyruq. Mikasa hisobingizni bog'lash uchun 6 xonali kodni yuboring yoki /help buyrug'idan foydalaning."
        )

    async def _handle_start(
        self,
        chat_id: Union[int, str],
        tg_user_id: int,
        first_name: Optional[str],
        username: Optional[str],
        token: str
    ) -> Dict[str, Any]:
        """Handle /start or deep link /start <link_token>."""
        if token:
            ok, msg, link = self.identity_mgr.verify_link_token(
                link_token=token,
                telegram_user_id=tg_user_id,
                first_name=first_name,
                username=username
            )
            if ok and link:
                text = (
                    "🎉 *Tabriklaymiz!*\n\n"
                    f"Sizning Telegram hisobingiz Mikasa hisobingiz (`{link.mikasa_user_id}`) bilan "
                    "muvaffaqiyatli bog'landi.\n\n"
                    "Holatni tekshirish uchun: /account"
                )
                return await self._send_reply(chat_id, text)
            else:
                text = f"❌ *Bog'lanishda xatolik:*\n{msg}\n\nIltimos, yangi havola oling yoki 6 xonali koddan foydalaning."
                return await self._send_reply(chat_id, text)

        # Standard /start welcome message
        name = first_name or "foydalanuvchi"
        welcome_text = (
            f"👋 *Assalomu alaykum, {name}!*\n\n"
            "Mikasa AI Universal Telegram Botiga xush kelibsiz.\n\n"
            "Ushbu bot orqali Mikasa profilingizni xavfsiz bog'lashingiz mumkin.\n\n"
            "📱 *Bog'lash uchun:*\n"
            "1. Mikasa ilovasida 'Telegram' bo'limiga o'ting.\n"
            "2. 6 xonali ulanish kodini oling.\n"
            "3. Kodni ushbu botga to'g'ridan-to'g'ri yuboring (masalan: `123456`) "
            "yoki `/link 123456` buyrug'idan foydalaning.\n\n"
            "Yordam uchun: /help"
        )
        return await self._send_reply(chat_id, welcome_text)

    async def _handle_link(
        self,
        chat_id: Union[int, str],
        tg_user_id: int,
        first_name: Optional[str],
        username: Optional[str],
        code: str
    ) -> Dict[str, Any]:
        """Handle /link <code> or raw OTP."""
        if not code:
            prompt_text = (
                "ℹ️ *Tasdiqlash kodi talab qilinadi.*\n\n"
                "Iltimos, Mikasa ilovasida ko'rsatilgan 6 xonali tasdiqlash kodini kiriting:\n"
                "Misol: `/link 583921` yoki shunchaki `583921`"
            )
            return await self._send_reply(chat_id, prompt_text)

        ok, msg, link = self.identity_mgr.verify_otp(
            otp=code,
            telegram_user_id=tg_user_id,
            first_name=first_name,
            username=username
        )

        if ok and link:
            reply_text = (
                "✅ *Hisob muvaffaqiyatli bog'landi!*\n\n"
                f"👤 Mikasa User ID: `{link.mikasa_user_id}`\n"
                f"🆔 Telegram ID: `{tg_user_id}`\n"
                "🔒 Ulanish xavfsizlandi.\n\n"
                "Hisob tafsilotlari: /account"
            )
            return await self._send_reply(chat_id, reply_text)
        else:
            reply_text = (
                f"❌ *Bog'lanish muvaffaqiyatsiz:*\n{msg}\n\n"
                "Iltimos, kodni tekshirib qayta kiriting yoki yangi kod generatsiya qiling."
            )
            return await self._send_reply(chat_id, reply_text)

    async def _handle_unlink(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Handle /unlink to revoke Telegram account link."""
        unlinked = self.identity_mgr.unlink(telegram_user_id=tg_user_id)
        if unlinked:
            reply_text = (
                "🔓 *Hisob uzildi.*\n\n"
                "Sizning Telegram hisobingiz Mikasa ilovasidan muvaffaqiyatli uzildi.\n"
                "Qayta ulash uchun: /link <kod>"
            )
        else:
            reply_text = (
                "ℹ️ *Bog'lanish topilmadi.*\n\n"
                "Sizning Telegram hisobingiz Mikasa bilan bog'lanmagan."
            )
        return await self._send_reply(chat_id, reply_text)

    async def _handle_account(
        self,
        chat_id: Union[int, str],
        tg_user_id: int,
        first_name: Optional[str],
        username: Optional[str]
    ) -> Dict[str, Any]:
        """Handle /account to inspect linking and identity state."""
        link = self.identity_mgr.get_link_by_telegram_user(tg_user_id)
        ident = self.identity_mgr.get_identity(tg_user_id)

        if link and link.is_active:
            linked_dt = datetime.fromtimestamp(link.linked_at).strftime("%Y-%m-%d %H:%M:%S")
            uname = f"@{ident.username}" if (ident and ident.username) else (f"@{username}" if username else "Mavjud emas")
            text = (
                "👤 *Mikasa Hisob Ma'lumotlari:*\n\n"
                f"• Mikasa User ID: `{link.mikasa_user_id}`\n"
                f"• Telegram ID: `{tg_user_id}`\n"
                f"• Username: {uname}\n"
                f"• Bog'langan vaqt: `{linked_dt}`\n"
                f"• Holat: 🟢 Faol (Active)\n\n"
                "Hisobni uzish uchun: /unlink"
            )
        else:
            text = (
                "👤 *Telegram Identifikatsiyasi:*\n\n"
                f"• Telegram ID: `{tg_user_id}`\n"
                f"• Holat: ⚪ Bog'lanmagan (Not Linked)\n\n"
                "Mikasa ilovangiz bilan bog'lash uchun:\n"
                "1. Mikasa ilovasida kod oling.\n"
                "2. Botga `/link <kod>` yuboring."
            )
        return await self._send_reply(chat_id, text)

    async def _handle_status(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Handle /status for system health check."""
        active_links = self.identity_mgr.count_active_links()
        pending_reqs = self.identity_mgr.count_pending_requests()
        text = (
            "🤖 *Mikasa Universal Telegram Bot Holati:*\n\n"
            "• Server: 🟢 Ishlamoqda (Online)\n"
            f"• Bot Username: `@{self.bot_username}`\n"
            f"• Faol ulanishlar: {active_links}\n"
            f"• Kutilayotgan so'rovlar: {pending_reqs}\n"
            "• Versiya: `v8.0.0 Phase 39`"
        )
        return await self._send_reply(chat_id, text)

    async def _handle_help(self, chat_id: Union[int, str], first_name: Optional[str]) -> Dict[str, Any]:
        """Handle /help command catalog."""
        help_text = (
            "📖 *Mikasa Telegram Bot Buyruqlari:*\n\n"
            "• `/start` — Botni ishga tushirish va yo'riqnoma\n"
            "• `/link <kod>` — Mikasa 6 xonali kodi orqali bog'lash\n"
            "• `/unlink` — Telegram hisobini Mikasadan uzish\n"
            "• `/account` — Bog'langan hisob tafsilotlarini ko'rish\n"
            "• `/status` — Bot va server holatini tekshirish\n"
            "• `/help` — Ushbu yordam menyusi\n\n"
            "💡 *Maslahat:* 6 xonali tasdiqlash kodini to'g'ridan-to'g'ri xabar sifatida ham yuborishingiz mumkin (masalan: `583921`)."
        )
        return await self._send_reply(chat_id, help_text)

    async def _send_reply(self, chat_id: Union[int, str], text: str) -> Dict[str, Any]:
        """Internal helper to dispatch message via transport."""
        return await self.transport.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown"
        )
