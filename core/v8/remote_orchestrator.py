# ========== core/v8/remote_orchestrator.py ==========
# Phase 36/37/38 — Remote PC Control Master Orchestrator
# Coordinates Telegram Gateway ↔ User Linking ↔ Permission Center ↔ Auth Engine ↔ DeviceRegistry ↔ WoL ↔ Heartbeat ↔ Tool System 2.0 ↔ PCAgent

import time
import logging
import asyncio
from typing import Dict, Any, Optional, Union

from core.v8.device import DeviceIdentity, DeviceRegistry
from core.v8.heartbeat import DeviceState, HeartbeatManager
from core.v8.wol import WakeOnLanManager
from core.v8.envelope import EnvelopeManager, RemoteCommandEnvelope
from core.v8.telegram_gateway import TelegramRemoteGateway
from core.v8.pc_agent import MikasaPCAgent
from core.v8.planning_remote import create_remote_wake_and_verify_dag
from core.v8.events import RemoteEventType, RemoteAuditLogger
from core.v8.auth_session import RemoteAuthEngine, SessionManager
from core.v8.user_linking import UserLinkingStore
from core.v8.permission_center import PermissionStore
from core.v8.remote_tools import RemoteToolRegistry

logger = logging.getLogger("core.v8.orchestrator")


class RemoteOrchestrator:
    """
    Mikasa AI v8.0.0 Masofaviy Boshqaruv Markaziy Koordinatori.
    Barcha qatlamlarni birlashtiradi va xavfsiz boshqaradi:
    Telegram -> User Linking -> Permission Center -> Session Auth -> Envelope/RateLimit -> Intent/DAG -> WoL -> Tool System 2.0 -> PC Agent.
    """

    def __init__(
        self,
        gateway: Optional[TelegramRemoteGateway] = None,
        heartbeat_manager: Optional[HeartbeatManager] = None,
        wol_manager: Optional[WakeOnLanManager] = None,
        envelope_manager: Optional[EnvelopeManager] = None,
        device_registry: Optional[DeviceRegistry] = None,
        pc_agent: Optional[MikasaPCAgent] = None,
        session_manager: Optional[SessionManager] = None,
        auth_engine: Optional[RemoteAuthEngine] = None,
        user_linking: Optional[UserLinkingStore] = None,
        permission_store: Optional[PermissionStore] = None,
        tool_registry: Optional[RemoteToolRegistry] = None,
        agent_loop=None,
        require_session_auth: bool = True,
        telegram_gateway: Optional[TelegramRemoteGateway] = None,
        user_linking_store: Optional[UserLinkingStore] = None
    ):
        self.device_registry = device_registry or DeviceRegistry.get_default_instance()
        self.heartbeat_manager = heartbeat_manager or HeartbeatManager()
        self.wol_manager = wol_manager or WakeOnLanManager()
        self.envelope_manager = envelope_manager or EnvelopeManager()
        self.gateway = gateway or telegram_gateway or TelegramRemoteGateway(
            admin_id="admin",
            envelope_manager=self.envelope_manager,
            wol_manager=self.wol_manager
        )
        self.pc_agent = pc_agent or MikasaPCAgent(
            heartbeat_manager=self.heartbeat_manager,
            envelope_manager=self.envelope_manager,
            device_registry=self.device_registry
        )
        self.session_manager = session_manager or SessionManager()
        self.auth_engine = auth_engine or RemoteAuthEngine(session_manager=self.session_manager)
        self.user_linking = user_linking or user_linking_store or UserLinkingStore.get_default_instance()
        self.permission_store = permission_store
        self.tool_registry = tool_registry or RemoteToolRegistry.get_default_instance()
        self.agent_loop = agent_loop
        self.require_session_auth = require_session_auth
        self._audit = RemoteAuditLogger.get_instance()

    @property
    def pending_confirmations(self):
        """Gateway ichidagi kutilayotgan tasdiqlar xaritasi"""
        return getattr(self.gateway, "_pending_confirmations", {})

    def pop_pending_confirmation(self, request_id: str):
        return self.gateway.pop_pending_confirmation(request_id)

    def cancel_confirmation(self, request_id: str):
        return self.gateway.cancel_confirmation(request_id)

    def resolve_target_device(self, user_id: Union[str, int]) -> Optional[DeviceIdentity]:
        """Foydalanuvchiga bog'langan qurilmani aniqlash"""
        user_str = str(user_id)

        # 1. UserLinkingStore orqali tekshirish
        link = self.user_linking.get_link_by_telegram(user_str)
        if link:
            dev = self.device_registry.get_device(link.device_id)
            if dev:
                return dev

        # 2. DeviceRegistry pairing
        paired = self.device_registry.get_paired_device_for_user(user_str)
        if paired:
            return paired

        # 3. Agar pairing topilmasa, mavjud birinchi qurilmani yoki pc_agent identity'sini olish
        all_devs = self.device_registry.list_devices()
        if all_devs:
            return all_devs[0]

        return self.pc_agent.identity if self.pc_agent else None

    async def process_telegram_message(
        self,
        user_id: Union[str, int],
        text: str,
        chat_id: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """Telegram xabarini qayta ishlash uchun qulay usul"""
        cid = chat_id if chat_id is not None else user_id
        return await self.handle_message(cid, user_id, text)

    async def handle_message(
        self,
        chat_id: Union[str, int],
        user_id: Union[str, int],
        text: str
    ) -> Dict[str, Any]:
        """
        Telegram foydalanuvchidan kelgan xabarni qabul qilish va boshqaruv ssenariysiga yo'naltirish.
        """
        user_str = str(user_id)
        clean_text = text.strip()

        # Parol yoki PIN kiritilayotgan bo'lsa logda maxfiy qilish
        is_secret_input = self.auth_engine.is_auth_pending(user_str) and not clean_text.startswith("/")
        log_text = "***PASSWORD_INPUT***" if is_secret_input else clean_text

        self._audit.log(RemoteEventType.REMOTE_REQUEST_RECEIVED, user_id=user_str, text=log_text)

        # 1. Buyruqni tahlil qilish (Uzbek NLP + slash commands)
        parsed = self.gateway.parse_command(clean_text)
        action = parsed["action"]
        params = parsed.get("params", {})

        # 2. Avtorizatsiya tekshiruvi (Telegram ID allowlist yoki UserLinkingStore)
        is_user_authorized = self.gateway.is_authorized(user_str) or self.user_linking.is_telegram_linked(user_str)
        is_pairing_command = action in ("pair", "link") or clean_text.lower().startswith(("/pair", "/link"))

        if not is_user_authorized and not is_pairing_command:
            self._audit.log(RemoteEventType.REMOTE_REQUEST_DENIED, user_id=user_str, reason="Unauthorized")
            await self.gateway.transport.send_message(
                chat_id,
                "⛔ **Ruxsat berilmadi!**\nSizning Telegram hisobingiz Mikasa tizimiga bog'lanmagan. "
                "Ilovada 'Telegram ulash' tugmasini bosing va `/pair MK-XXXXXX` kodini yuboring."
            )
            return {"success": False, "error": "UNAUTHORIZED", "user_id": user_str}

        self._audit.log(RemoteEventType.REMOTE_REQUEST_AUTHORIZED, user_id=user_str)

        # 3. Qurilmani va Mikasa hisobini aniqlash
        link = self.user_linking.get_link_by_telegram(user_str)
        effective_user_id = link.mikasa_user_id if link else (
            "admin" if self.gateway.is_authorized(user_str) else user_str
        )
        device = self.resolve_target_device(user_str)
        dev_id = device.device_id if device else (self.pc_agent.identity.device_id if self.pc_agent else "pc")
        mac_addr = getattr(device, "mac_address", "") or "AA:BB:CC:DD:EE:FF"

        # 4. Foydalanuvchi bog'lanish amallari (/pair, /unpair, /devices, /account)
        if action == "pair":
            token_code = params.get("pairing_token") or ""
            if not token_code and len(clean_text.split()) > 1:
                token_code = clean_text.split()[1]

            if not token_code:
                await self.gateway.transport.send_message(
                    chat_id,
                    "ℹ️ **Telegram ulash:**\nIlovadagi 6 xonali kodni yuboring:\nMasalan: `/pair MK-A7F92B`"
                )
                return {"success": False, "action": "pair", "error": "MISSING_CODE"}

            ok, msg, link = self.user_linking.redeem_pairing_code(token_code, user_str)
            if ok and link:
                self.gateway.add_allowed_user(user_str)
                dev = self.device_registry.get_device(link.device_id)
                dev_host = dev.hostname if dev else link.device_id
                self.device_registry.pair_device(
                    device_id=link.device_id,
                    user_id=user_str,
                    fingerprint=getattr(dev, "fingerprint", "fp") or "fp",
                    mac_address=getattr(dev, "mac_address", "") or ""
                )
                await self.gateway.transport.send_message(
                    chat_id,
                    f"✅ **Qurilma muvaffaqiyatli bog'landi!**\n\n"
                    f"🖥️ Qurilma: `{dev_host}`\n"
                    f"🆔 Device ID: `{link.device_id}`\n"
                    f"👤 Telegram ID: `{user_str}`\n\n"
                    f"Endi kompyuterni boshqarishingiz mumkin."
                )
                return {"success": True, "action": "pair", "device_id": link.device_id}
            else:
                await self.gateway.transport.send_message(
                    chat_id,
                    f"❌ **Bog'lanishda xatolik:**\n{msg}"
                )
                return {"success": False, "action": "pair", "error": msg}

        elif action == "unpair":
            ok = self.user_linking.unlink_telegram(dev_id, user_str)
            self.device_registry.unpair_device(dev_id)
            await self.gateway.transport.send_message(
                chat_id,
                f"🔒 **Qurilma bilan bog'lanish bekor qilindi.** (`{dev_id}`)"
            )
            return {"success": True, "action": "unpair", "unpaired": ok}

        elif action == "devices":
            links = self.user_linking.list_linked_devices(user_str)
            if not links:
                p_dev = self.device_registry.get_paired_device_for_user(user_str)
                if p_dev:
                    msg = f"📱 **Bog'langan qurilmalar:**\n• `{p_dev.hostname}` (`{p_dev.device_id}`) — `{p_dev.status.value}`"
                else:
                    msg = "ℹ️ Bog'langan qurilmalar topilmadi. Bog'lash uchun: `/pair MK-XXXXXX`"
            else:
                lines = ["📱 **Bog'langan qurilmalar:**"]
                for link_item in links:
                    dev = self.device_registry.get_device(link_item.device_id)
                    hname = dev.hostname if dev else link_item.device_id
                    st = self.heartbeat_manager.get_device_state(link_item.device_id).value
                    lines.append(f"• `{hname}` (`{link_item.device_id}`) — `{st}`")
                msg = "\n".join(lines)
            await self.gateway.transport.send_message(chat_id, msg)
            return {"success": True, "action": "devices"}

        elif action == "account":
            linked = self.user_linking.get_link_by_telegram(user_str)
            dev_str = f"`{linked.device_id}`" if linked else "Bog'lanmagan"
            msg = (
                f"👤 **Mikasa Foydalanuvchi Hisobi:**\n"
                f"• Telegram Numeric ID: `{user_str}`\n"
                f"• Bog'langan qurilma: {dev_str}\n"
                f"• Telegram Gateway: Faol"
            )
            await self.gateway.transport.send_message(chat_id, msg)
            return {"success": True, "action": "account"}

        # 5. Kutilayotgan Autentifikatsiya (Authentication Challenge) ni qayta ishlash
        if self.auth_engine.is_auth_pending(user_str):
            if clean_text.lower() in ("/cancel", "cancel", "bekor qilish"):
                self.auth_engine.clear_auth_pending(user_str)
                await self.gateway.transport.send_message(chat_id, "❌ **Autentifikatsiya bekor qilindi.**")
                return {"success": True, "action": "auth_cancelled"}

            pending_device = self.auth_engine.get_pending_device(user_str) or dev_id
            ok, msg, session = self.auth_engine.verify_secret(user_str, pending_device, clean_text)

            if ok and session:
                await self.gateway.transport.send_message(
                    chat_id,
                    "✅ **Parol tasdiqlandi! Masofaviy sessiya ochildi.**\n\n"
                    "⏱️ Sessiya muddati: 15 daqiqa.\n"
                    "🤖 Mikasa Agent: READY\n\n"
                    "Masofaviy buyruqlarni yuborishingiz mumkin."
                )
                return {
                    "success": True,
                    "action": "auth_success",
                    "session_id": session.session_id,
                    "device_id": pending_device
                }
            else:
                if "COOLDOWN" in msg:
                    await self.gateway.transport.send_message(
                        chat_id,
                        "🚫 **Xavfsizlik blokirovkasi!**\n"
                        "Ketma-ket 3 marta noto'g'ri parol kiritildi. "
                        "Tizim 5 daqiqaga bloklandi. Iltimos, keyinroq qayta urining."
                    )
                else:
                    remaining = self.auth_engine.get_remaining_attempts(user_str)
                    await self.gateway.transport.send_message(
                        chat_id,
                        f"❌ **Noto'g'ri parol yoki PIN kod!**\n"
                        f"Qolgan urinishlar: `{remaining}` ta. Qayta urinib ko'ring:"
                    )
                return {"success": False, "action": "auth_failed", "error": msg}

        # 6. Sessiyani boshqarish buyruqlari (/logout, /lock, /session)
        if action == "logout":
            closed = self.session_manager.close_session(user_str, dev_id)
            if closed:
                await self.gateway.transport.send_message(
                    chat_id,
                    "🔒 **Sessiya yopildi.** Masofaviy boshqaruv bloklandi."
                )
            else:
                await self.gateway.transport.send_message(
                    chat_id,
                    "ℹ️ Faol sessiya topilmadi."
                )
            return {"success": True, "action": "logout", "closed": closed}

        elif action == "session":
            active_sess = self.session_manager.get_active_session(user_str, dev_id)
            if active_sess:
                rem = int(max(0, active_sess.expires_at - time.time()))
                await self.gateway.transport.send_message(
                    chat_id,
                    f"🟢 **Sessiya faol!**\n"
                    f"• ID: `{active_sess.session_id[:8]}...`\n"
                    f"• Qolgan vaqt: `{rem}` soniya\n"
                    f"• Qurilma: `{dev_id}`"
                )
                return {"success": True, "action": "session_status", "active": True, "remaining": rem}
            else:
                await self.gateway.transport.send_message(
                    chat_id,
                    "🔴 **Faol sessiya mavjud emas.**\nBuyruq bajarish uchun parolni tasdiqlang."
                )
                return {"success": True, "action": "session_status", "active": False}

        # 7. Tasdiqlash (/confirm) va Bekor qilish (/cancel)
        if action in ("confirm", "yes") or clean_text.lower() in ("/confirm", "confirm", "ha", "yes"):
            found_req_id = None
            for req_id, entry in list(self.pending_confirmations.items()):
                env = entry.get("envelope")
                if (env and (env.user_id == effective_user_id or getattr(env, "telegram_user_id", None) == user_str)) or entry.get("chat_id") == chat_id:
                    found_req_id = req_id
                    break
            if not found_req_id and self.pending_confirmations:
                found_req_id = list(self.pending_confirmations.keys())[-1]

            if found_req_id:
                envelope = self.pop_pending_confirmation(found_req_id)
                if envelope:
                    if self.require_session_auth:
                        active_sess = (
                            self.session_manager.get_active_session(effective_user_id, dev_id)
                            or self.session_manager.get_active_session(user_str, dev_id)
                        )
                        if not active_sess:
                            self.auth_engine.set_auth_pending(user_str, dev_id, True, chat_id=chat_id)
                            # Re-store pending confirmation so it's not lost
                            self.gateway.store_pending_confirmation(found_req_id, envelope, ttl=60.0, chat_id=chat_id)
                            await self.gateway.transport.send_message(
                                chat_id,
                                "🔐 **Parolni tasdiqlang!**\n"
                                "Masofaviy buyruqni bajarish uchun parol yoki PIN kodni kiriting:"
                            )
                            return {
                                "success": False,
                                "error": "SESSION_REQUIRED",
                                "auth_required": True
                            }
                        envelope.session_id = active_sess.session_id

                    envelope.confirmation_required = False
                    exec_res = await self.execute_command(envelope)
                    action_name = envelope.action.split(".")[-1]
                    await self.gateway.transport.send_message(
                        chat_id,
                        f"✅ **Amal muvaffaqiyatli bajarildi!** (`{envelope.action}`)\nKompyuterda {action_name} holati qo'llanildi."
                    )
                    return {"success": True, "action": "confirm", "result": exec_res}

            await self.gateway.transport.send_message(chat_id, "ℹ️ Tasdiqlash uchun kutilayotgan buyruq topilmadi.")
            return {"success": False, "error": "NO_PENDING_CONFIRMATION"}

        elif action in ("cancel", "no") or clean_text.lower() in ("/cancel", "cancel", "yo'q", "no", "bekor qilish"):
            cleared = False
            for req_id in list(self.pending_confirmations.keys()):
                self.cancel_confirmation(req_id)
                cleared = True
            await self.gateway.transport.send_message(chat_id, "❌ **Amal bekor qilindi.**")
            return {"success": True, "action": "cancel", "cancelled": cleared}

        # 8. Ruxsatlarni xaritalash va tekshirish (User Permission Center)
        ACTION_TO_PERMISSION = {
            "status": "system.status",
            "wake": "power.wake",
            "info": "system.info",
            "sys": "system.info",
            "system_info": "system.info",
            "system.info": "system.info",
            "system.screenshot": "system.screenshot",
            "screenshot": "system.screenshot",
            "app.list": "app.list",
            "apps": "app.list",
            "app.launch": "app.launch",
            "app.close": "app.close",
            "file.list": "file.list",
            "files": "file.list",
            "file.read": "file.read",
            "network.info": "network.info",
            "network": "network.info",
            "restart": "power.restart",
            "power.restart": "power.restart",
            "shutdown": "power.shutdown",
            "power.shutdown": "power.shutdown",
            "sleep": "power.sleep",
            "power.sleep": "power.sleep",
        }
        required_perm = ACTION_TO_PERMISSION.get(action, action)

        if self.permission_store is not None and not self.permission_store.is_granted(effective_user_id, dev_id, required_perm):
            self._audit.log(
                RemoteEventType.COMMAND_DENIED,
                user_id=user_str,
                device_id=dev_id,
                action=action,
                permission=required_perm,
                reason="Permission not granted"
            )
            if action in ("wake", "power.wake"):
                err_msg = "❌ **Kompyuterni uyg'otish (WoL) uchun ruxsat berilmagan.**"
            else:
                err_msg = "❌ **Bu amal uchun ruxsat berilmagan.**"
            await self.gateway.transport.send_message(
                chat_id,
                err_msg
            )
            return {"success": False, "error": "PERMISSION_DENIED", "permission": required_perm}

        # 9. Standart buyruqlar
        if action == "status":
            current_state = self.heartbeat_manager.get_device_state(dev_id)
            info = device.to_dict() if device and hasattr(device, "to_dict") else {}
            msg = self.gateway.format_status_message(info, current_state)
            await self.gateway.transport.send_message(
                chat_id,
                msg,
                reply_markup={"inline_keyboard": self.gateway.build_keyboard()}
            )
            return {
                "success": True,
                "action": "status",
                "device_id": dev_id,
                "state": current_state.value
            }

        elif action == "wake":
            return await self.execute_wake_pipeline(
                device_id=dev_id,
                mac_address=mac_addr,
                chat_id=chat_id,
                user_id=user_str
            )

        # 10. Yuqori xavfli amallar: Confirmation talab etiladi
        if action in ("restart", "shutdown", "sleep", "power.restart", "power.shutdown", "power.sleep", "app.close"):
            envelope = self.envelope_manager.create_envelope(
                device_id=dev_id,
                action=action,
                params=params,
                user_id=effective_user_id,
                confirmation_required=True,
                telegram_user_id=user_str,
                session_id=None,
                tool_id=required_perm,
                permission_version=self.permission_store.get_profile(effective_user_id, dev_id).version if self.permission_store else 1
            )
            self.gateway.store_pending_confirmation(
                request_id=envelope.request_id,
                envelope=envelope,
                ttl=60.0,
                chat_id=chat_id,
                prompt=f"Kompyuterni {action} qilish"
            )
            action_desc_map = {
                "restart": "qayta ishga tushiradi",
                "power.restart": "qayta ishga tushiradi",
                "shutdown": "o'chiradi",
                "power.shutdown": "o'chiradi",
                "sleep": "kutish rejimiga o'tkazadi",
                "power.sleep": "kutish rejimiga o'tkazadi",
                "app.close": "dasturni yopadi"
            }
            action_desc = action_desc_map.get(action, action)
            prompt_text = (
                f"⚠️ **TASDIQLASH TALAB ETILADI!**\n\n"
                f"Ushbu amal kompyuterni `{action_desc}`.\n"
                f"Tasdiqlash uchun `/confirm` deb yuboring yoki inline tugmani bosing."
            )
            await self.gateway.transport.send_message(
                chat_id,
                prompt_text,
                reply_markup={"inline_keyboard": self.gateway.build_confirmation_keyboard(envelope.request_id)}
            )
            return {
                "success": True,
                "action": action,
                "confirmation_required": True,
                "request_id": envelope.request_id
            }

        # 11. Sessiya ruxsati tekshiruvi (Amallar faol sessiya talab qiladi)
        active_sess = None
        if self.require_session_auth:
            active_sess = self.session_manager.get_active_session(effective_user_id, dev_id) or self.session_manager.get_active_session(user_str, dev_id)
            if not active_sess:
                self.auth_engine.set_auth_pending(user_str, dev_id, True, chat_id=chat_id)
                await self.gateway.transport.send_message(
                    chat_id,
                    "🔐 **Parolni tasdiqlang!**\n"
                    "Masofaviy buyruqni bajarish uchun parol yoki PIN kodni kiriting:"
                )
                return {
                    "success": False,
                    "error": "SESSION_REQUIRED",
                    "auth_required": True
                }

        # 11. Standart asboblarni bajarish (system.screenshot, app.list, file.list, network.info, va boshqalar)
        envelope = self.envelope_manager.create_envelope(
            device_id=dev_id,
            action=required_perm,
            params=params,
            user_id=effective_user_id,
            telegram_user_id=user_str,
            session_id=active_sess.session_id if active_sess else None,
            tool_id=required_perm,
            permission_version=self.permission_store.get_profile(effective_user_id, dev_id).version if self.permission_store else 1
        )
        exec_res = await self.execute_command(envelope)
        if exec_res.get("success"):
            res_val = exec_res.get("result")
            await self.gateway.transport.send_message(
                chat_id,
                f"✅ **Buyruq bajarildi:** `{action}`\n\nNatija: `{res_val}`"
            )
        else:
            err_msg = exec_res.get("error", "Noma'lum xatolik")
            await self.gateway.transport.send_message(
                chat_id,
                f"❌ **Xatolik:** {err_msg}"
            )
        return exec_res

    async def handle_callback_query(
        self,
        callback_query_id: str,
        chat_id: Union[str, int],
        user_id: Union[str, int],
        data: str
    ) -> Dict[str, Any]:
        """
        Inline tugmalar (callbacks) bosilishini boshqarish.
        """
        user_str = str(user_id)
        await self.gateway.transport.answer_callback_query(callback_query_id)

        if not self.gateway.is_authorized(user_str) and not self.user_linking.is_telegram_linked(user_str):
            await self.gateway.transport.send_message(
                chat_id,
                "⛔ **Ruxsat yo'q!** Ushbu amalni faqat vakolatli administrator bajara oladi."
            )
            return {"success": False, "error": "UNAUTHORIZED"}

        # Tasdiqlash tugmalari
        if data.startswith("confirm_yes:"):
            req_id = data.split(":", 1)[1]
            envelope = self.gateway.pop_pending_confirmation(req_id)
            if not envelope:
                await self.gateway.transport.send_message(
                    chat_id,
                    "⚠️ **Tasdiqlash muddati o'tgan yoki bekor qilingan.**"
                )
                return {"success": False, "error": "CONFIRMATION_EXPIRED"}

            envelope.confirmation_required = False  # Endi ruxsat etildi
            await self.gateway.transport.send_message(
                chat_id,
                f"✅ **Amal tasdiqlandi:** `{envelope.action}` bajarilmoqda..."
            )
            return await self.execute_command(envelope)

        elif data.startswith("confirm_no:"):
            req_id = data.split(":", 1)[1]
            self.gateway.cancel_confirmation(req_id)
            await self.gateway.transport.send_message(chat_id, "❌ **Xavfli amal bekor qilindi.**")
            return {"success": True, "action": "cancelled", "request_id": req_id}

        # Standart tugmalar
        device = self.resolve_target_device(user_str)
        dev_id = device.device_id if device else "pc"
        mac_addr = getattr(device, "mac_address", "") or "AA:BB:CC:DD:EE:FF"

        if data in ("btn_status", "btn_refresh"):
            current_state = self.heartbeat_manager.get_device_state(dev_id)
            info = device.to_dict() if device and hasattr(device, "to_dict") else {}
            msg = self.gateway.format_status_message(info, current_state)
            await self.gateway.transport.send_message(
                chat_id,
                msg,
                reply_markup={"inline_keyboard": self.gateway.build_keyboard()}
            )
            return {"success": True, "action": "status", "state": current_state.value}

        elif data == "btn_wake":
            return await self.execute_wake_pipeline(
                device_id=dev_id,
                mac_address=mac_addr,
                chat_id=chat_id,
                user_id=user_str
            )

        elif data == "btn_sys":
            if self.permission_store is not None and not self.permission_store.is_granted(user_str, dev_id, "system.info"):
                await self.gateway.transport.send_message(chat_id, "❌ **Bu amal uchun ruxsat berilmagan.**")
                return {"success": False, "error": "PERMISSION_DENIED"}

            envelope = self.envelope_manager.create_envelope(
                device_id=dev_id,
                action="system_info",
                user_id=user_str,
                tool_id="system.info"
            )
            return await self.execute_command(envelope)

        elif data == "btn_cancel":
            await self.gateway.transport.send_message(chat_id, "❌ **Amal bekor qilindi.**")
            return {"success": True, "action": "cancel"}

        return {"success": False, "error": f"UNKNOWN_CALLBACK: {data}"}

    async def execute_wake_pipeline(
        self,
        device_id: str,
        mac_address: str,
        chat_id: Optional[Union[str, int]] = None,
        user_id: Optional[Union[str, int]] = None,
        wait_timeout: float = 10.0,
        poll_interval: float = 0.1
    ) -> Dict[str, Any]:
        """
        Masofadan kompyuterni uyg'otish va tekshirish E2E pipeline (Planning 2.0 DAG asosida):
        CHECK_PERMISSION -> CHECK_DEVICE -> WAKE_DEVICE -> WAIT_HEARTBEAT -> VERIFY_ONLINE -> AUTH_CHALLENGE -> GET_STATUS
        """
        user_str = str(user_id) if user_id is not None else ""
        link = self.user_linking.get_link_by_telegram(user_str)
        effective_user_id = link.mikasa_user_id if link else (
            "admin" if self.gateway.is_authorized(user_str) else user_str
        )
        self._audit.log(RemoteEventType.WOL_REQUESTED, device_id=device_id, user_id=user_str)

        # [0/5] Ruxsat tekshiruvi (power.wake)
        if self.permission_store is not None and effective_user_id and not self.permission_store.is_granted(effective_user_id, device_id, "power.wake"):
            self._audit.log(
                RemoteEventType.COMMAND_DENIED,
                user_id=user_str,
                device_id=device_id,
                action="wake",
                permission="power.wake",
                reason="Permission not granted"
            )
            if chat_id:
                await self.gateway.transport.send_message(
                    chat_id,
                    "❌ **Kompyuterni uyg'otish (WoL) uchun ruxsat berilmagan.**"
                )
            return {"success": False, "error": "PERMISSION_DENIED", "permission": "power.wake"}

        # [1/5] Qurilma holatini tekshirish
        current_state = self.heartbeat_manager.get_device_state(device_id)
        if chat_id:
            await self.gateway.send_progress(chat_id, 1, 5, "Device holati tekshirilmoqda...")

        if current_state in (DeviceState.ONLINE, DeviceState.READY):
            if chat_id:
                await self.gateway.transport.send_message(
                    chat_id,
                    "🟢 **Kompyuter allaqachon yoqilgan va faol holatda!**"
                )
            return {"success": True, "state": "online", "message": "Already online"}

        # [2/5] Wake-on-LAN Magic Packet yuborish
        dag = create_remote_wake_and_verify_dag(device_id, mac_address)
        if chat_id:
            await self.gateway.send_progress(chat_id, 2, 5, "Wake-on-LAN yuborilmoqda...")

        self.heartbeat_manager.set_device_state(device_id, DeviceState.WAKING)
        self._audit.log(RemoteEventType.WOL_SENT, device_id=device_id)
        self._audit.log(RemoteEventType.DEVICE_WAKING, device_id=device_id)

        wol_res = await self.wol_manager.wake_device(mac_address)
        if not wol_res.get("success"):
            self.heartbeat_manager.set_device_state(device_id, DeviceState.OFFLINE)
            self._audit.log(RemoteEventType.WOL_FAILED, device_id=device_id, reason=wol_res.get("error"))
            if chat_id:
                await self.gateway.transport.send_message(
                    chat_id,
                    f"⚠️ **WoL paketi yuborishda xatolik:** {wol_res.get('error')}"
                )
            return {"success": False, "error": "WOL_SEND_FAILED", "detail": wol_res}

        # [3/5] Heartbeat kutilmoqda (Bounded wait)
        if chat_id:
            await self.gateway.send_progress(chat_id, 3, 5, "Heartbeat kutilmoqda...")

        start_wait = time.time()
        is_awake = False

        while (time.time() - start_wait) < wait_timeout:
            state = self.heartbeat_manager.get_device_state(device_id)
            if state in (DeviceState.ONLINE, DeviceState.READY):
                is_awake = True
                break
            await asyncio.sleep(poll_interval)

        if not is_awake:
            self.heartbeat_manager.set_device_state(device_id, DeviceState.OFFLINE)
            self._audit.log(RemoteEventType.WOL_FAILED, device_id=device_id, reason="Heartbeat timeout")
            self._audit.log(RemoteEventType.DEVICE_OFFLINE, device_id=device_id)
            if chat_id:
                await self.gateway.transport.send_message(
                    chat_id,
                    "⚠️ **Kompyuter uyg'onmadi.**\n\n**Sabab:** PC Agent heartbeat qaytmadi."
                )
            return {
                "success": False,
                "error": "HEARTBEAT_TIMEOUT",
                "state": "offline",
                "device_id": device_id
            }

        # [4/5] Device online tasdiqlanmoqda
        if chat_id:
            await self.gateway.send_progress(chat_id, 4, 5, "Device online tasdiqlanmoqda...")

        self._audit.log(RemoteEventType.DEVICE_ONLINE, device_id=device_id)

        # [5/5] Status olinmoqda va yakun
        if chat_id:
            await self.gateway.send_progress(chat_id, 5, 5, "Status olinmoqda...")

        # Phase 37: Sessiya autentifikatsiyasi so'rovi (Challenge)
        has_active_sess = bool(user_str and self.session_manager.get_active_session(user_str, device_id))
        auth_pending = False

        if not has_active_sess and user_str:
            self.auth_engine.set_auth_pending(user_str, device_id, True, chat_id=chat_id)
            auth_pending = True

        if chat_id:
            remaining = self.auth_engine.get_remaining_attempts(user_str) if user_str else 3
            final_text = (
                "⚡ **Kompyuterni uyg'otish boshlandi.**\n\n"
                "⏳ Mikasa PC Agent kutilmoqda...\n\n"
                "🟢 **Kompyuter online bo'ldi.**\n"
                "🤖 **Mikasa Agent:** READY\n\n"
                "🔐 **Parolni tasdiqlang!**\n"
                "Masofaviy sessiyani ochish uchun maxfiy parol yoki PIN kodni yuboring.\n"
                f"⏳ Qolgan urinishlar: `{remaining}` ta\n\n"
                "✅ **Masofaviy boshqaruv tayyor.**"
            )
            await self.gateway.transport.send_message(chat_id, final_text)

        return {
            "success": True,
            "device_id": device_id,
            "state": "online",
            "auth_required": auth_pending,
            "dag_id": dag.plan_id
        }

    async def execute_command(self, envelope: RemoteCommandEnvelope) -> Dict[str, Any]:
        """Buyruqni PC Agent orqali xavfsiz bajarish"""
        return await self.pc_agent.handle_remote_command(envelope)
