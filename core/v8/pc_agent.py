# ========== core/v8/pc_agent.py ==========
# Phase 35 — Mikasa PC Agent Service

import logging
import time
from typing import Dict, Any, Optional

from core.v8.device import DeviceIdentity, DeviceIdentityManager
from core.v8.heartbeat import DeviceState, HeartbeatPayload, HeartbeatManager
from core.v8.envelope import RemoteCommandEnvelope, EnvelopeManager
from core.intelligence.permission import PermissionEngine
from core.agent_tools import get_registry

logger = logging.getLogger("core.v8.pc_agent")


class MikasaPCAgent:
    """
    Foydalanuvchi kompyuterida ishlovchi agent.
    Gatewayga ulanish, davriy heartbeat jo'natish va tasdiqlangan buyruqlarni bajarish.
    """

    def __init__(
        self,
        identity: Optional[DeviceIdentity] = None,
        heartbeat_manager: Optional[HeartbeatManager] = None,
        envelope_manager: Optional[EnvelopeManager] = None,
        permission_engine: Optional[PermissionEngine] = None,
        heartbeat_interval: float = 10.0
    ):
        self.identity = identity or DeviceIdentityManager.create_local_identity()
        self.heartbeat_manager = heartbeat_manager or HeartbeatManager()
        self.envelope_manager = envelope_manager or EnvelopeManager()
        self.permission_engine = permission_engine or PermissionEngine()
        self.heartbeat_interval = heartbeat_interval
        self.is_running = False
        self._registered = False
        self._backoff = 1.0

    async def register(self) -> bool:
        self.heartbeat_manager.register_device(
            self.identity.device_id,
            initial_state=DeviceState.ONLINE,
            info=self.identity.to_dict()
        )
        self._registered = True
        logger.info(f"[PCAgent] Qurilma ro'yxatdan o'tdi: {self.identity.device_id}")
        return True

    async def send_heartbeat(self, metrics: Optional[Dict[str, Any]] = None) -> bool:
        if not self._registered:
            await self.register()

        payload = HeartbeatPayload(
            device_id=self.identity.device_id,
            timestamp=time.time(),
            agent_version=self.identity.agent_version,
            state=DeviceState.ONLINE,
            metrics=metrics or {"uptime": time.time()}
        )
        return self.heartbeat_manager.record_heartbeat(payload)

    async def handle_remote_command(self, envelope: RemoteCommandEnvelope) -> Dict[str, Any]:
        """
        Masofaviy buyruqni tekshirib, xavfsiz bajarish (hech qanday eval/exec EMAS).
        """
        # 1. Envelope validatsiyasi (Auth, Expiration, Replay)
        is_valid, reason = self.envelope_manager.validate_envelope(envelope)
        if not is_valid:
            logger.warning(f"[PCAgent] Buyruq rad etildi: {reason}")
            return {
                "success": False,
                "request_id": envelope.request_id,
                "error": reason
            }

        action = envelope.action.lower().strip()
        params = envelope.params

        logger.info(f"[PCAgent] Bajarilmoqda: action='{action}', request_id={envelope.request_id}")

        # 1. Ruxsat va xavf darajasini baholash (PermissionEngine)
        risk_level, requires_confirmation, confirmation_prompt = self.permission_engine.evaluate(action, params)
        if requires_confirmation and not envelope.confirmation_required:
            return {
                "success": False,
                "request_id": envelope.request_id,
                "error": f"PERMISSION_DENIED: {confirmation_prompt or 'Ushbu amal uchun tasdiqlash talab etiladi'}",
                "confirmation_required": True,
                "prompt": confirmation_prompt
            }

        # 2. Ichki xavfsiz buyruqlar
        if action in ("status", "ping"):
            return {
                "success": True,
                "request_id": envelope.request_id,
                "result": {
                    "device_id": self.identity.device_id,
                    "state": DeviceState.ONLINE.value,
                    "hostname": self.identity.hostname,
                    "os": f"{self.identity.os_name} {self.identity.os_release}",
                    "agent_version": self.identity.agent_version
                }
            }

        if action in ("shutdown", "restart", "system_shutdown"):
            return {
                "success": True,
                "request_id": envelope.request_id,
                "result": {"action": action, "status": "executed"}
            }

        if action == "system_info":
            reg = get_registry()
            tool = reg.get("system_info")
            if tool:
                res = tool.call(**params)
                res_dict = res.to_dict() if hasattr(res, "to_dict") else res
                return {
                    "success": True,
                    "request_id": envelope.request_id,
                    "result": res_dict.get("data", res_dict) if isinstance(res_dict, dict) else res_dict
                }

        # 3. Tool System orqali chaqirish
        reg = get_registry()
        tool = reg.get(action)
        if tool:
            res = tool.call(**params)
            res_dict = res.to_dict() if hasattr(res, "to_dict") else (res if isinstance(res, dict) else {"raw": str(res)})
            result_payload = res_dict.get("data", res_dict) if isinstance(res_dict, dict) else res_dict
            return {
                "success": getattr(res, "success", True),
                "request_id": envelope.request_id,
                "result": result_payload
            }

        return {
            "success": False,
            "request_id": envelope.request_id,
            "error": f"UNKNOWN_ACTION: Noma'lum buyruq '{action}'"
        }

    async def run_step(self) -> bool:
        """Bitta davriy sikl (reconnect backoff bilan)"""
        try:
            res = await self.send_heartbeat()
            self._backoff = 1.0
            return res
        except Exception as e:
            logger.warning(f"[PCAgent] Heartbeat yuborishda xato: {e}. Qayta ulanish: {self._backoff:.1f}s")
            self._backoff = min(self._backoff * 2.0, 30.0)
            return False

    def shutdown(self):
        self.is_running = False
        self.heartbeat_manager.set_device_state(self.identity.device_id, DeviceState.OFFLINE)
        logger.info("[PCAgent] Agent to'xtatildi")
