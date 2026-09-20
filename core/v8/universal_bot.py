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
from core.v8.account_device import AccountDeviceManager

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
        account_device_manager: Optional[AccountDeviceManager] = None,
        bot_username: str = "MikasaUniversalBot"
    ):
        self.transport: TelegramTransport = transport or MockTelegramTransport()
        self.identity_mgr: TelegramIdentityManager = identity_manager or TelegramIdentityManager.get_default_instance()
        self.account_device_mgr: AccountDeviceManager = account_device_manager or AccountDeviceManager.get_default_instance()
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

        # 6. /devices (Phase 40)
        if text.startswith("/devices"):
            return await self._handle_devices(chat_id, tg_user_id)

        # 7. /select <query> (Phase 40)
        if text.startswith("/select"):
            parts = text.split(maxsplit=1)
            query = parts[1].strip() if len(parts) > 1 else ""
            return await self._handle_select(chat_id, tg_user_id, query)

        # 8. /status
        if text.startswith("/status"):
            return await self._handle_status(chat_id, tg_user_id)

        # 9. /session (Phase 40+ remote session inspection)
        if text.startswith("/session"):
            return await self._handle_session(chat_id, tg_user_id)

        # 10. /logout (remote session only — not web Supabase session)
        if text.startswith("/logout"):
            return await self._handle_logout(chat_id, tg_user_id)

        # 11. /access (Phase 47 - Agent Access Status)
        if text.startswith("/access"):
            return await self._handle_access(chat_id, tg_user_id)

        # 12. /permissions (Phase 47 - List all permissions)
        if text.startswith("/permissions"):
            return await self._handle_permissions(chat_id, tg_user_id)

        # 13. /revoke (Phase 47 - Emergency Revoke All)
        if text.startswith("/revoke"):
            return await self._handle_revoke(chat_id, tg_user_id)

        # 14. /help
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
        """Handle /account to inspect linking, identity, and device state."""
        link = self.identity_mgr.get_link_by_telegram_user(tg_user_id)
        ident = self.identity_mgr.get_identity(tg_user_id)

        if link and link.is_active:
            linked_dt = datetime.fromtimestamp(link.linked_at).strftime("%Y-%m-%d %H:%M:%S")
            uname = f"@{ident.username}" if (ident and ident.username) else (f"@{username}" if username else "Mavjud emas")
            devices = self.account_device_mgr.get_devices_for_user(link.mikasa_user_id, include_revoked=False)
            selected = self.account_device_mgr.get_selected_device(link.mikasa_user_id)
            selected_str = f"{selected.name} (`{selected.device_id}`)" if selected else "Tanlanmagan"

            text = (
                "👤 *Mikasa Hisob Ma'lumotlari:*\n\n"
                f"• Mikasa User ID: `{link.mikasa_user_id}`\n"
                f"• Telegram ID: `{tg_user_id}`\n"
                f"• Username: {uname}\n"
                f"• Bog'langan vaqt: `{linked_dt}`\n"
                f"• Holat: 🟢 Faol (Active)\n"
                f"• Ulangan kompyuterlar: {len(devices)} ta\n"
                f"• Faol tanlangan kompyuter: {selected_str}\n\n"
                "Qurilmalar ro'yxati: /devices\n"
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

    async def _handle_devices(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Handle /devices to list user's owned devices and current selection."""
        link = self.identity_mgr.get_link_by_telegram_user(tg_user_id)
        if not link or not link.is_active:
            text = (
                "🔒 *Hisob bog'lanmagan.*\n\n"
                "Qurilmalarni ko'rish uchun avval Mikasa hisobingizni bog'lang:\n"
                "1. Mikasa ilovasidan 6 xonali kod oling.\n"
                "2. Botga `/link <kod>` yuboring."
            )
            return await self._send_reply(chat_id, text)

        devices = self.account_device_mgr.get_devices_for_user(link.mikasa_user_id, include_revoked=False)
        if not devices:
            text = (
                "💻 *Qurilmalar ro'yxati:*\n\n"
                "Sizning hisobingizga hozircha birorta ham kompyuter ulanmagan.\n"
                "Mikasa Desktop ilovasi orqali kompyuteringizni ro'yxatdan o'tkazing."
            )
            return await self._send_reply(chat_id, text)

        selected = self.account_device_mgr.get_selected_device(link.mikasa_user_id)
        selected_dev_id = selected.device_id if selected else None

        lines = ["💻 *Sizning Kompyuterlaringiz:*\n"]
        for idx, dev in enumerate(devices, start=1):
            status_dot = "🟢" if dev.is_online else ("🟡" if dev.status.lower() == "standby" else "⚪")
            selected_badge = " *(Faol)*" if (selected_dev_id and dev.device_id == selected_dev_id) else ""
            lines.append(f"{idx}. {status_dot} *{dev.name}*{selected_badge}")
            lines.append(f"   ID: `{dev.device_id}` | Holat: {dev.status.capitalize()}")

        lines.append("\nQurilmani tanlash uchun:\n`/select <nom_yoki_id>`")
        return await self._send_reply(chat_id, "\n".join(lines))

    async def _handle_select(self, chat_id: Union[int, str], tg_user_id: int, query: str) -> Dict[str, Any]:
        """Handle /select <name_or_id> to set user's active device."""
        link = self.identity_mgr.get_link_by_telegram_user(tg_user_id)
        if not link or not link.is_active:
            text = (
                "🔒 *Hisob bog'lanmagan.*\n\n"
                "Qurilmani tanlash uchun avval hisobingizni bog'lang: /link <kod>"
            )
            return await self._send_reply(chat_id, text)

        if not query:
            text = (
                "ℹ️ *Qurilma nomi yoki ID talab qilinadi.*\n\n"
                "Foydalanish: `/select <nom_yoki_id>`\n"
                "Mavjud qurilmalarni ko'rish uchun: /devices"
            )
            return await self._send_reply(chat_id, text)

        ok, msg, dev = self.account_device_mgr.select_device_by_query(link.mikasa_user_id, query)
        if ok and dev:
            text = (
                f"✅ *Faol qurilma tanlandi:*\n\n"
                f"• Nomi: *{dev.name}*\n"
                f"• Apparat ID: `{dev.device_id}`\n"
                f"• Holat: {dev.status.capitalize()}\n\n"
                "Barcha buyruqlar endi ushbu qurilmaga yo'naltiriladi."
            )
            return await self._send_reply(chat_id, text)
        else:
            text = f"❌ *Xatolik:*\n{msg}\n\nQurilmalar ro'yxati: /devices"
            return await self._send_reply(chat_id, text)

    async def _handle_status(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Handle /status — selected device state for linked users, bot health otherwise."""
        link = self.identity_mgr.get_link_by_telegram_user(tg_user_id)
        if link and link.is_active:
            dev = self.account_device_mgr.get_selected_device(link.mikasa_user_id)
            if not dev:
                text = (
                    "💻 *Qurilma holati:*\n\n"
                    "Faol tanlangan kompyuter yo'q.\n"
                    "Avval qurilmani tanlang: /devices → `/select <nom>`"
                )
                return await self._send_reply(chat_id, text)

            status_upper = dev.status.lower()
            if dev.is_revoked or status_upper == "revoked":
                state_label = "🔴 REVOKED"
            elif status_upper == "online":
                state_label = "🟢 ONLINE"
            elif status_upper in ("standby", "degraded"):
                state_label = "🟡 DEGRADED"
            else:
                state_label = "⚪ OFFLINE"

            last_seen = "Noma'lum"
            if dev.last_seen_at:
                last_seen = datetime.fromtimestamp(dev.last_seen_at).strftime("%Y-%m-%d %H:%M:%S")

            text = (
                "🖥️ *Tanlangan Qurilma Holati:*\n\n"
                f"• Nomi: *{dev.name}*\n"
                f"• Apparat ID: `{dev.device_id}`\n"
                f"• Holat: *{state_label}*\n"
                f"• Platforma: {dev.platform.capitalize()}\n"
                f"• Oxirgi faollik: `{last_seen}`\n\n"
                "Sessiya holati: /session"
            )
            return await self._send_reply(chat_id, text)

        active_links = self.identity_mgr.count_active_links()
        pending_reqs = self.identity_mgr.count_pending_requests()
        text = (
            "🤖 *Mikasa Universal Telegram Bot Holati:*\n\n"
            "• Server: 🟢 Ishlamoqda (Online)\n"
            f"• Bot Username: `@{self.bot_username}`\n"
            f"• Faol ulanishlar: {active_links}\n"
            f"• Kutilayotgan so'rovlar: {pending_reqs}\n"
            "• Versiya: `v8.0.0 Phase 39 / Phase 40`"
        )
        return await self._send_reply(chat_id, text)

    async def _handle_session(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Handle /session — remote control session presence (no secret/token exposure)."""
        link = self.identity_mgr.get_link_by_telegram_user(tg_user_id)
        if not link or not link.is_active:
            return await self._send_reply(
                chat_id,
                "🔒 *Hisob bog'lanmagan.*\n\nAvval hisobingizni bog'lang: /link <kod>"
            )

        dev = self.account_device_mgr.get_selected_device(link.mikasa_user_id)
        if not dev:
            return await self._send_reply(
                chat_id,
                "💻 *Faol qurilma tanlanmagan.*\n\nAvval kompyuteringizni tanlang: /devices"
            )

        from core.v8.auth_session import SessionManager
        session_mgr = SessionManager.get_default_instance()
        session = session_mgr.get_active_session(link.mikasa_user_id, dev.device_id)

        if session and session.is_valid():
            expires = datetime.fromtimestamp(session.expires_at).strftime("%Y-%m-%d %H:%M:%S")
            text = (
                "🔐 *Masofaviy Boshqaruv Sessiyasi:*\n\n"
                f"• Qurilma: *{dev.name}* (`{dev.device_id}`)\n"
                "• Holat: 🟢 *Faol*\n"
                f"• Tugash vaqti: `{expires}`\n\n"
                "Sessiyani yopish: /logout"
            )
        else:
            text = (
                "🔐 *Masofaviy Boshqaruv Sessiyasi:*\n\n"
                f"• Qurilma: *{dev.name}* (`{dev.device_id}`)\n"
                "• Holat: ⚪ *Faol emas*\n\n"
                "Masofaviy boshqaruv Mikasa Desktop/Web ilovasi orqali boshlanadi."
            )
        return await self._send_reply(chat_id, text)

    async def _handle_logout(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Handle /logout — close remote session only (not Supabase web auth)."""
        link = self.identity_mgr.get_link_by_telegram_user(tg_user_id)
        if not link or not link.is_active:
            return await self._send_reply(
                chat_id,
                "🔒 *Hisob bog'lanmagan.*\n\nAvval hisobingizni bog'lang: /link <kod>"
            )

        dev = self.account_device_mgr.get_selected_device(link.mikasa_user_id)
        if not dev:
            return await self._send_reply(
                chat_id,
                "💻 *Faol qurilma tanlanmagan.*\n\nAvval kompyuteringizni tanlang: /devices"
            )

        from core.v8.auth_session import SessionManager
        session_mgr = SessionManager.get_default_instance()
        closed = session_mgr.close_session(link.mikasa_user_id, dev.device_id)

        if closed:
            text = (
                "🔓 *Masofaviy sessiya yopildi.*\n\n"
                f"• Qurilma: *{dev.name}* (`{dev.device_id}`)\n"
                "• Mikasa Web kirish sessiyasi saqlanib qoldi.\n\n"
                "Holatni tekshirish: /session"
            )
        else:
            text = (
                "ℹ️ *Faol masofaviy sessiya topilmadi.*\n\n"
                f"• Qurilma: *{dev.name}* (`{dev.device_id}`)\n"
                "Hech qanday ochiq remote session yo'q."
            )
        return await self._send_reply(chat_id, text)

    async def _handle_access(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Phase 47: Show agent access level for active device."""
        link = self._get_link(tg_user_id)
        if not link:
            return await self._send_reply(chat_id, "❌ Telegram hisobingiz Mikasa'ga bog'lanmagan. /link buyrug'idan foydalaning.")

        dev = self._get_active_device(link)
        if not dev:
            return await self._send_reply(chat_id, "❌ Faol qurilma topilmadi. /select bilan tanlang.")

        from core.v8.agent_access import AgentAccessManager
        access_mgr = AgentAccessManager.get_default_instance()
        status = access_mgr.get_access_status(link.mikasa_user_id, dev.device_id)

        level = status.get("access_level", "LIMITED")
        level_icon = "🟢" if level == "FULL" else ("🟡" if level == "CUSTOM" else "🔴")
        granted = status.get("permissions_granted", 0)
        total = status.get("total_supported_permissions", 15)

        text = (
            f"🛡 *Agent Access Status*\n\n"
            f"• Qurilma: *{dev.name}* (`{dev.device_id}`)\n"
            f"• Daraja: {level_icon} *{level}*\n"
            f"• Ruxsatlar: {granted}/{total}\n"
            f"• Siyosat versiyasi: `{status.get('policy_version', '1.0.0')}`\n\n"
            "Batafsil: /permissions\n"
            "Bekor qilish: /revoke"
        )
        return await self._send_reply(chat_id, text)

    async def _handle_permissions(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Phase 47: List all 15 permissions with status."""
        link = self._get_link(tg_user_id)
        if not link:
            return await self._send_reply(chat_id, "❌ Telegram hisobingiz Mikasa'ga bog'lanmagan.")

        dev = self._get_active_device(link)
        if not dev:
            return await self._send_reply(chat_id, "❌ Faol qurilma topilmadi. /select bilan tanlang.")

        from core.v8.permission_center import PermissionStore, STANDARD_PERMISSIONS
        store = PermissionStore.get_default_instance()
        profile = store.get_profile(link.mikasa_user_id, dev.device_id)

        lines = ["📋 *Ruxsatlar ro'yxati:*\n"]
        for perm in STANDARD_PERMISSIONS:
            granted = profile.is_granted(perm.id) if profile else perm.default_enabled
            icon = "✅" if granted else "❌"
            lines.append(f"  {icon} `{perm.id}` — {perm.label}")

        lines.append(f"\n🛡 Access Level: *{profile.access_level if profile else 'LIMITED'}*")
        return await self._send_reply(chat_id, "\n".join(lines))

    async def _handle_revoke(self, chat_id: Union[int, str], tg_user_id: int) -> Dict[str, Any]:
        """Phase 47: Emergency revoke all agent access."""
        link = self._get_link(tg_user_id)
        if not link:
            return await self._send_reply(chat_id, "❌ Telegram hisobingiz Mikasa'ga bog'lanmagan.")

        dev = self._get_active_device(link)
        if not dev:
            return await self._send_reply(chat_id, "❌ Faol qurilma topilmadi.")

        from core.v8.agent_access import AgentAccessManager
        access_mgr = AgentAccessManager.get_default_instance()
        ok, msg = access_mgr.emergency_revoke(link.mikasa_user_id, dev.device_id)

        if ok:
            text = (
                "🚨 *FAVQULODDA BEKOR QILISH BAJARILDI!*\n\n"
                f"• Qurilma: *{dev.name}*\n"
                "• Access level: LIMITED\n"
                "• Barcha pending buyruqlar bekor qilindi\n"
                "• Barcha confirmation tokenlar bekor qilindi\n\n"
                "Holatni tekshirish: /access"
            )
        else:
            text = f"⚠️ Bekor qilishda xatolik: {msg}"
        return await self._send_reply(chat_id, text)

    async def _handle_help(self, chat_id: Union[int, str], first_name: Optional[str]) -> Dict[str, Any]:
        """Handle /help command catalog."""
        help_text = (
            "📖 *Mikasa Telegram Bot Buyruqlari:*\n\n"
            "• `/start` — Botni ishga tushirish va yo'riqnoma\n"
            "• `/link <kod>` — Mikasa 6 xonali kodi orqali bog'lash\n"
            "• `/unlink` — Telegram hisobini Mikasadan uzish\n"
            "• `/account` — Bog'langan hisob va qurilmalar tafsilotlari\n"
            "• `/devices` — Sizning barcha kompyuterlaringiz ro'yxati\n"
            "• `/select <nom>` — Masofaviy boshqaruv uchun faol kompyuterni tanlash\n"
            "• `/session` — Masofaviy boshqaruv sessiyasi holati\n"
            "• `/logout` — Masofaviy sessiyani yopish (Web kirish saqlanadi)\n"
            "• `/access` — Agent vakolat darajasi (Phase 47)\n"
            "• `/permissions` — Barcha ruxsatlar ro'yxati\n"
            "• `/revoke` — 🚨 Favqulodda barcha vakolatlarni bekor qilish\n"
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
