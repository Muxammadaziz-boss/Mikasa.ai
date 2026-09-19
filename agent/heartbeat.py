# ========== agent/heartbeat.py ==========
# Phase 45 — Windows PC Agent Periodic Heartbeat & State FSM
# Periodic status reporting, system telemetry, and backend keepalive

import time
import asyncio
import logging
from enum import Enum
from typing import Dict, Any, Optional, Tuple

from core.v8.events import RemoteEventType
from agent.audit import AgentAuditLogger
from agent.transport import SecureTransport

logger = logging.getLogger("mikasa.agent.heartbeat")


class AgentState(str, Enum):
    INITIALIZING = "initializing"
    CONNECTING = "connecting"
    ONLINE = "online"
    DEGRADED = "degraded"
    REVOKED = "revoked"
    STOPPED = "stopped"


class AgentHeartbeat:
    """
    Agentning backend bilan doimiy aloqasini ta'minlovchi yurak urishi (heartbeat) tizimi.
    - POST /api/devices/{device_id}/heartbeat ga davriy so'rovlar yuboradi.
    - Qurilma revoke qilinganini (403 DEVICE_REVOKED) aniqlaydi va agentni to'xtatadi.
    - Tizim telemetriyasini (CPU, RAM, Uptime) yig'adi.
    """

    def __init__(
        self,
        transport: SecureTransport,
        device_id: str,
        interval_seconds: float = 15.0,
        agent_version: str = "8.0.0"
    ):
        self.transport = transport
        self.device_id = device_id
        self.interval_seconds = interval_seconds
        self.agent_version = agent_version
        self._audit = AgentAuditLogger.get_instance()

        self.state: AgentState = AgentState.INITIALIZING
        self.started_at: float = time.time()
        self.last_successful_heartbeat: float = 0.0
        self.consecutive_failures: int = 0

        self._task: Optional[asyncio.Task] = None
        self._running: bool = False

    def get_system_metrics(self) -> Dict[str, Any]:
        """Tizim telemetriyasini xavfsiz yig'ish"""
        metrics: Dict[str, Any] = {
            "uptime_seconds": round(time.time() - self.started_at, 2)
        }
        try:
            import psutil
            metrics["cpu_percent"] = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            metrics["ram_percent"] = mem.percent
            metrics["ram_used_mb"] = round(mem.used / (1024 * 1024), 1)
        except Exception as e:
            metrics["telemetry_error"] = str(e)
        return metrics

    async def send_heartbeat(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Yagona heartbeat yuborish.
        Qaytaradi: (muvaffaqiyat, holat_matni, javob_ma'lumotlari)
        """
        metrics = self.get_system_metrics()
        payload = {
            "device_id": self.device_id,
            "timestamp": time.time(),
            "agent_version": self.agent_version,
            "state": self.state.value,
            "metrics": metrics
        }

        endpoint = f"/api/devices/{self.device_id}/heartbeat"
        status, data = await self.transport.post(endpoint, payload)

        if status == 200 and data.get("ok"):
            self.consecutive_failures = 0
            self.last_successful_heartbeat = time.time()
            if self.state != AgentState.ONLINE:
                self.state = AgentState.ONLINE
            self._audit.log_event(
                event_type=RemoteEventType.HEARTBEAT_SENT,
                device_id=self.device_id,
                details={
                    "status": "success",
                    "metrics": metrics
                }
            )
            return True, "ONLINE", data

        # Agar backend 403 (DEVICE_REVOKED) qaytarsa
        err_msg = data.get("error", f"HTTP {status}")
        if status == 403 or "REVOKED" in err_msg.upper():
            self.state = AgentState.REVOKED
            logger.critical(f"[AgentHeartbeat] Qurilma ruxsati bekor qilingan (REVOKED): {err_msg}")
            self._audit.log_event(
                event_type=RemoteEventType.CREDENTIAL_REVOKED,
                device_id=self.device_id,
                details={"reason": err_msg}
            )
            return False, "DEVICE_REVOKED", data

        # Tarmoq yoki boshqa xatolik
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            self.state = AgentState.DEGRADED
        self._audit.log_event(
            event_type=RemoteEventType.HEARTBEAT_FAILED,
            device_id=self.device_id,
            details={
                "consecutive_failures": self.consecutive_failures,
                "error": err_msg
            }
        )
        logger.warning(f"[AgentHeartbeat] Heartbeat xatosi: {err_msg} (ketma-ket: {self.consecutive_failures})")
        return False, err_msg, data

    async def _heartbeat_loop(self):
        """Asinxron heartbeat doimiy sikli"""
        logger.info(f"[AgentHeartbeat] Heartbeat sikli boshlandi (interval={self.interval_seconds}s)")
        while self._running:
            try:
                ok, status_str, _ = await self.send_heartbeat()
                if status_str == "DEVICE_REVOKED":
                    logger.critical("[AgentHeartbeat] Qurilma bekor qilingani uchun sikl to'xtatildi")
                    self._running = False
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[AgentHeartbeat] Kutilmagan istisno: {e}")

            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

    def start(self) -> asyncio.Task:
        """Heartbeat fon vazifasini ishga tushirish"""
        if self._running and self._task and not self._task.done():
            return self._task
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        return self._task

    async def stop(self):
        """Heartbeat fon vazifasini to'xtatish"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.state = AgentState.STOPPED
        logger.info("[AgentHeartbeat] Heartbeat sikli to'xtatildi")
