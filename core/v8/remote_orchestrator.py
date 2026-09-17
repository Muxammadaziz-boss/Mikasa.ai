# ========== core/v8/remote_orchestrator.py ==========
# Phase 36/37 — Remote PC Control Master Orchestrator
# Coordinates Telegram Gateway ↔ Auth Engine ↔ DeviceRegistry ↔ WoL ↔ Heartbeat ↔ AgentLoop ↔ PCAgent

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

logger = logging.getLogger("core.v8.orchestrator")


class RemoteOrchestrator:
    """
    Mikasa AI v8.0.0 Masofaviy Boshqaruv Markaziy Koordinatori.
    Barcha qatlamlarni birlashtiradi va xavfsiz boshqaradi:
    Telegram -> Auth -> RateLimit -> Intent/DAG -> WoL -> Heartbeat -> Session Auth -> AgentLoop -> PC.
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
        agent_loop=None,
        require_session_auth: bool = True
    ):
        self.device_registry = device_registry or DeviceRegistry.get_default_instance()
        self.heartbeat_manager = heartbeat_manager or HeartbeatManager()
        self.wol_manager = wol_manager or WakeOnLanManager()
        self.envelope_manager = envelope_manager or EnvelopeManager()
        self.gateway = gateway or TelegramRemoteGateway(
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
        self.agent_loop = agent_loop
        self.require_session_auth = require_session_auth
        self._audit = RemoteAuditLogger.get_instance()

    def resolve_target_device(self, user_id: Union[str, int]) -> Optional[DeviceIdentity]:
        """Foydalanuvchiga bog'langan qurilmani aniqlash"""
        paired = self.device_registry.get_paired_device_for_user(str(user_id))
        if paired:
            return paired

        # Agar pairing topilmasa, mavjud birinchi qurilmani yoki pc_agent identity'sini olish
        all_devs = self.device_registry.list_devices()
        if all_devs:
            return all_devs[0]

        return self.pc_agent.identity if self.pc_agent else None

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

        # 1. Avtorizatsiya tekshiruvi (Telegram ID allowlist)
        if not self.gateway.is_authorized(user_str):
            self._audit.log(RemoteEventType.REMOTE_REQUEST_DENIED, user_id=user_str, reason="Unauthorized")
            await self.gateway.transport.send_message(
                chat_id,
                "⛔ **Ruxsat berilmadi!**\nSizda ushbu kompyuterni masofadan boshqarish huquqi yo'q."
            )
            return {"success": False, "error": "UNAUTHORIZED", "user_id": user_str}

        self._audit.log(RemoteEventType.REMOTE_REQUEST_AUTHORIZED, user_id=user_str)

        # 2. Qurilmani aniqlash
        device = self.resolve_target_device(user_str)
        dev_id = device.device_id if device else (self.pc_agent.identity.device_id if self.pc_agent else "pc")
        mac_addr = getattr(device, "mac_address", "") or "AA:BB:CC:DD:EE:FF"

        # 3. Kutilayotgan Autentifikatsiya (Authentication Challenge) ni qayta ishlash
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

        # 4. Buyruqni tahlil qilish (Uzbek NLP + slash commands)
        parsed = self.gateway.parse_command(clean_text)
        action = parsed["action"]
        params = parsed.get("params", {})

        # 5. Sessiyani boshqarish buyruqlari (/logout, /lock, /session)
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

        # 6. Standart buyruqlar
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

        elif action in ("restart", "shutdown"):
            # Yuqori xavfli buyruq: Confirmation talab etiladi
            envelope = self.envelope_manager.create_envelope(
                device_id=dev_id,
                action=action,
                params=params,
                user_id=user_str,
                confirmation_required=True
            )
            self.gateway.store_pending_confirmation(
                request_id=envelope.request_id,
                envelope=envelope,
                ttl=60.0,
                chat_id=chat_id,
                prompt=f"Kompyuterni {action} qilish"
            )
            action_desc = "qayta ishga tushiradi" if action == "restart" else "o'chiradi"
            prompt_text = (
                f"⚠️ **DIQQAT! Yuqori xavfli amal:**\n\n"
                f"Ushbu amal kompyuterni `{action_desc}`.\n"
                f"Davom ettirishni tasdiqlaysizmi?"
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

        elif action == "cancel":
            await self.gateway.transport.send_message(chat_id, "❌ **Amal bekor qilindi.**")
            return {"success": True, "action": "cancel"}

        else:
            # Sessiya ruxsati tekshiruvi (ixtiyoriy asboblar faol sessiya talab qiladi)
            if self.require_session_auth:
                active_sess = self.session_manager.get_active_session(user_str, dev_id)
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

            # Standart asboblar (system_info, chat, va boshqalar)
            envelope = self.envelope_manager.create_envelope(
                device_id=dev_id,
                action=action,
                params=params,
                user_id=user_str
            )
            exec_res = await self.execute_command(envelope)
            if exec_res.get("success"):
                await self.gateway.transport.send_message(
                    chat_id,
                    f"✅ **Buyruq bajarildi:** `{action}`\n\nNatija: `{exec_res.get('result')}`"
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

        if not self.gateway.is_authorized(user_str):
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
            envelope = self.envelope_manager.create_envelope(
                device_id=dev_id,
                action="system_info",
                user_id=user_str
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
        CHECK_DEVICE -> WAKE_DEVICE -> WAIT_HEARTBEAT -> VERIFY_ONLINE -> AUTH_CHALLENGE -> GET_STATUS
        """
        user_str = str(user_id) if user_id is not None else ""
        self._audit.log(RemoteEventType.WOL_REQUESTED, device_id=device_id, user_id=user_str)

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
            # Timeout sodir bo'ldi
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
