# ========== core/v8/pc_agent.py ==========
# Phase 35/36 — Mikasa PC Agent Service
# Gateway Connection, Heartbeat, Device Registry Pairing, Reconnect & Safe Tool Execution

import time
import logging
from typing import Dict, Any, Optional

from core.v8.device import DeviceIdentity, DeviceIdentityManager, DeviceRegistry
from core.v8.heartbeat import DeviceState, HeartbeatPayload, HeartbeatManager
from core.v8.envelope import RemoteCommandEnvelope, EnvelopeManager
from core.v8.events import RemoteEventType, RemoteAuditLogger
from core.intelligence.permission import PermissionEngine
from core.agent_tools import get_registry

logger = logging.getLogger("core.v8.pc_agent")


class MikasaPCAgent:
    """
    Foydalanuvchi kompyuterida ishlovchi agent.
    Gatewayga ulanish, pairing tekshiruvi, davriy heartbeat jo'natish
    va tasdiqlangan buyruqlarni xavfsiz (eval/exec'siz) bajarish.
    """

    def __init__(
        self,
        identity: Optional[DeviceIdentity] = None,
        heartbeat_manager: Optional[HeartbeatManager] = None,
        envelope_manager: Optional[EnvelopeManager] = None,
        permission_engine: Optional[PermissionEngine] = None,
        device_registry: Optional[DeviceRegistry] = None,
        heartbeat_interval: float = 10.0,
        max_backoff: float = 30.0
    ):
        self.identity = identity or DeviceIdentityManager.create_local_identity()
        self.heartbeat_manager = heartbeat_manager or HeartbeatManager()
        self.envelope_manager = envelope_manager or EnvelopeManager()
        self.permission_engine = permission_engine or PermissionEngine()
        self.device_registry = device_registry or DeviceRegistry.get_default_instance()
        self.heartbeat_interval = heartbeat_interval
        self.max_backoff = max_backoff

        self.is_running = False
        self._registered = False
        self._backoff = 1.0
        self.agent_state = "INITIALIZING"
        self._audit = RemoteAuditLogger.get_instance()

    async def register(self) -> bool:
        """Qurilmani ro'yxatdan o'tkazish va state'ni ONLINE qilish"""
        self.agent_state = "REGISTERING"
        self.heartbeat_manager.register_device(
            self.identity.device_id,
            initial_state=DeviceState.CONNECTING,
            info=self.identity.to_dict()
        )

        # DeviceRegistry mavjud bo'lsa ro'yxatga olish
        if self.device_registry and not self.device_registry.get_device(self.identity.device_id):
            self.device_registry.register_device(self.identity)

        self._registered = True
        self.heartbeat_manager.set_device_state(self.identity.device_id, DeviceState.ONLINE)
        self.agent_state = "ONLINE"
        self.is_running = True

        self._audit.log(
            RemoteEventType.DEVICE_REGISTERED,
            device_id=self.identity.device_id,
            hostname=self.identity.hostname,
            agent_version=self.identity.agent_version
        )
        self._audit.log(
            RemoteEventType.AGENT_CONNECTED,
            device_id=self.identity.device_id
        )
        logger.info(f"[PCAgent] Qurilma muvaffaqiyatli ro'yxatdan o'tdi: {self.identity.device_id}")
        return True

    def pair_with_gateway(self, pairing_token: str, user_id: str) -> bool:
        """Token orqali gatewayga qurilmani bog'lash (pairing)"""
        self.agent_state = "AUTHENTICATING"
        if not self.device_registry:
            return False

        ok, msg = self.device_registry.pair_device(
            device_id=self.identity.device_id,
            pairing_token=pairing_token,
            user_id=user_id,
            fingerprint=self.identity.fingerprint
        )
        if ok:
            self.agent_state = "ONLINE"
            logger.info(f"[PCAgent] Qurilma foydalanuvchi {user_id} ga bog'landi (paired)")
            return True
        else:
            self.agent_state = "ERROR"
            self._audit.log(
                RemoteEventType.DEVICE_AUTH_FAILED,
                device_id=self.identity.device_id,
                user_id=user_id,
                reason=msg
            )
            logger.warning(f"[PCAgent] Bog'lash (pairing) rad etildi: {msg}")
            return False

    async def send_heartbeat(self, metrics: Optional[Dict[str, Any]] = None) -> bool:
        """Heartbeat yuborish"""
        if not self._registered:
            await self.register()

        payload = HeartbeatPayload(
            device_id=self.identity.device_id,
            timestamp=time.time(),
            agent_version=self.identity.agent_version,
            state=DeviceState.ONLINE,
            metrics=metrics or {"uptime": time.time()}
        )
        res = self.heartbeat_manager.record_heartbeat(payload)
        if res:
            self._audit.log(
                RemoteEventType.DEVICE_ONLINE,
                device_id=self.identity.device_id
            )
        return res

    async def handle_remote_command(self, envelope: RemoteCommandEnvelope) -> Dict[str, Any]:
        """
        Masofaviy buyruqni tekshirib, xavfsiz bajarish (hech qanday eval/exec EMAS).
        Idempotentlik, permission va audit to'liq ta'minlangan.
        """
        req_id = envelope.request_id

        # 0. Idempotentlik tekshiruvi: Agar bu buyruq avval bajarilgan bo'lsa, keshdagi natijani qaytarish
        if self.envelope_manager.is_executed(req_id):
            logger.info(f"[PCAgent] Idempotent buyruq: avval bajarilgan natija qaytarilmoqda ({req_id})")
            return self.envelope_manager.get_cached_result(req_id)

        # 1. Envelope validatsiyasi (Auth, Expiration, Replay)
        is_valid, reason = self.envelope_manager.validate_envelope(envelope)
        if not is_valid:
            logger.warning(f"[PCAgent] Buyruq rad etildi: {reason}")
            res = {
                "success": False,
                "request_id": req_id,
                "error": reason
            }
            return res

        action = envelope.action.lower().strip()
        params = envelope.params

        self._audit.log(
            RemoteEventType.COMMAND_STARTED,
            request_id=req_id,
            device_id=self.identity.device_id,
            action=action
        )
        logger.info(f"[PCAgent] Bajarilmoqda: action='{action}', request_id={req_id}")

        # 2. Xavf darajasini baholash (PermissionEngine)
        risk_level, requires_confirmation, confirmation_prompt = self.permission_engine.evaluate(action, params)
        if requires_confirmation and not envelope.confirmation_required:
            res = {
                "success": False,
                "request_id": req_id,
                "error": f"PERMISSION_DENIED: {confirmation_prompt or 'Ushbu amal uchun tasdiqlash talab etiladi'}",
                "confirmation_required": True,
                "prompt": confirmation_prompt
            }
            return res

        result_payload: Dict[str, Any] = {}
        success = False

        # 3. Ichki xavfsiz tizim buyruqlari
        if action in ("status", "ping"):
            success = True
            result_payload = {
                "device_id": self.identity.device_id,
                "state": DeviceState.ONLINE.value,
                "hostname": self.identity.hostname,
                "os": f"{self.identity.os_name} {self.identity.os_release}",
                "agent_version": self.identity.agent_version
            }

        elif action in ("shutdown", "restart", "system_shutdown"):
            success = True
            result_payload = {"action": action, "status": "executed"}

        elif action == "system_info":
            reg = get_registry()
            tool = reg.get("system_info")
            if tool:
                res = tool.call(**params)
                res_dict = res.to_dict() if hasattr(res, "to_dict") else res
                success = True
                result_payload = res_dict.get("data", res_dict) if isinstance(res_dict, dict) else res_dict
            else:
                success = True
                result_payload = {
                    "hostname": self.identity.hostname,
                    "os": f"{self.identity.os_name} {self.identity.os_release}",
                    "agent_version": self.identity.agent_version
                }

        else:
            # 4. Mikasa Tool System 2.0 orqali chaqirish
            reg = get_registry()
            tool = reg.get(action)
            if tool:
                try:
                    res = tool.call(**params)
                    res_dict = res.to_dict() if hasattr(res, "to_dict") else (
                        res if isinstance(res, dict) else {"raw": str(res)}
                    )
                    success = getattr(res, "success", True)
                    result_payload = res_dict.get("data", res_dict) if isinstance(res_dict, dict) else res_dict
                except Exception as ex:
                    success = False
                    result_payload = {"error": str(ex)}
            else:
                success = False
                final_res = {
                    "success": False,
                    "request_id": req_id,
                    "error": f"UNKNOWN_ACTION: Noma'lum buyruq '{action}'"
                }
                self._audit.log(
                    RemoteEventType.COMMAND_FAILED,
                    request_id=req_id,
                    device_id=self.identity.device_id,
                    reason=f"Unknown action {action}"
                )
                return final_res

        final_res = {
            "success": success,
            "request_id": req_id,
            "result": result_payload
        }

        # Idempotentlik keshiga natijani yozish
        self.envelope_manager.record_execution_result(req_id, final_res)

        if success:
            self._audit.log(
                RemoteEventType.COMMAND_COMPLETED,
                request_id=req_id,
                device_id=self.identity.device_id,
                action=action
            )
        else:
            self._audit.log(
                RemoteEventType.COMMAND_FAILED,
                request_id=req_id,
                device_id=self.identity.device_id,
                action=action
            )

        return final_res

    async def run_step(self) -> bool:
        """Bitta davriy sikl (reconnect backoff bilan)"""
        try:
            res = await self.send_heartbeat()
            self._backoff = 1.0
            self.agent_state = "ONLINE"
            return res
        except Exception as e:
            self.agent_state = "ERROR"
            logger.warning(f"[PCAgent] Heartbeat yuborishda xato: {e}. Qayta ulanish: {self._backoff:.1f}s")
            self._backoff = min(self._backoff * 2.0, self.max_backoff)
            return False

    async def disconnect(self):
        """Agentni tarmoqdan uzish (simulyatsiya yoki shutdown)"""
        self.is_running = False
        self.agent_state = "OFFLINE"
        self.heartbeat_manager.set_device_state(self.identity.device_id, DeviceState.OFFLINE)
        self._audit.log(
            RemoteEventType.AGENT_DISCONNECTED,
            device_id=self.identity.device_id
        )
        self._audit.log(
            RemoteEventType.DEVICE_OFFLINE,
            device_id=self.identity.device_id
        )
        logger.info(f"[PCAgent] Qurilma tarmoqdan uzildi: {self.identity.device_id}")

    async def reconnect(self) -> bool:
        """Qayta ulanish"""
        logger.info(f"[PCAgent] Qayta ulanmoqda: {self.identity.device_id}")
        self.heartbeat_manager.set_device_state(self.identity.device_id, DeviceState.CONNECTING)
        self.agent_state = "CONNECTING"
        res = await self.send_heartbeat()
        if res:
            self._backoff = 1.0
            self.is_running = True
            self.agent_state = "ONLINE"
            self._audit.log(
                RemoteEventType.AGENT_CONNECTED,
                device_id=self.identity.device_id
            )
            return True
        return False

    def shutdown(self):
        self.is_running = False
        self.agent_state = "OFFLINE"
        self.heartbeat_manager.set_device_state(self.identity.device_id, DeviceState.OFFLINE)
        logger.info("[PCAgent] Agent to'xtatildi")
