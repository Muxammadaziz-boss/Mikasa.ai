# ========== agent/executor.py ==========
# Phase 46 — Remote Command Executor Pipeline
# Validates, authorizes, and safely executes remote commands on the Windows agent

import asyncio
import time
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from agent.tools import AgentToolRegistry
from agent.audit import AgentAuditLogger
from core.v8.events import RemoteEventType, sanitize_event_data

logger = logging.getLogger('agent.executor')

# Holatlar ro'yxati (Status enum)
class CommandStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class CommandResult:
    command_id: str
    status: CommandStatus
    tool_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class RemoteCommandExecutor:
    """Xavfsiz buyruq bajaruvchi (Secure command executor)."""
    
    def __init__(self, tool_registry=None, audit_logger=None, max_result_size=65536):
        self._tool_registry = tool_registry or AgentToolRegistry.get_default_instance()
        self._audit = audit_logger  # AgentAuditLogger instance  
        self._max_result_size = max_result_size  # 64KB
        self._idempotency_cache: Dict[str, CommandResult] = {}  # command_id -> result
        self._seen_nonces: Dict[str, float] = {}  # nonce -> expires_at
        self._dangerous_lock = asyncio.Lock()  # Lock for dangerous operations
        self._execution_count: int = 0
        self._max_cache_size: int = 200

    async def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Asosiy buyruq bajarish jarayoni."""
        self._purge_expired_nonces()
        
        start_time = time.time()
        command_id = command.get("command_id", "")
        tool_id = command.get("tool_id", "")
        params = command.get("params", {})
        nonce = command.get("nonce", "")
        expires_at = command.get("expires_at", 0.0)
        confirmation_status = command.get("confirmation_status", "pending")
        timeout = command.get("timeout", 30.0)

        # 2. Idempotency check
        if command_id in self._idempotency_cache:
            cached = self._idempotency_cache[command_id]
            return self._build_result_dict(cached)

        # 3. Expiry check
        if expires_at and time.time() > expires_at:
            res = CommandResult(command_id, CommandStatus.REJECTED, tool_id, error="COMMAND_EXPIRED")
            return self._finalize(res, start_time)

        # 4. Nonce replay check
        if nonce in self._seen_nonces:
            res = CommandResult(command_id, CommandStatus.REJECTED, tool_id, error="REPLAY_BLOCKED")
            return self._finalize(res, start_time)

        # 5. Record nonce
        if nonce:
            self._seen_nonces[nonce] = expires_at

        # 6. Tool lookup
        if not self._tool_registry:
            res = CommandResult(command_id, CommandStatus.FAILED, tool_id, error="NO_TOOL_REGISTRY")
            return self._finalize(res, start_time)
            
        tool = None
        if hasattr(self._tool_registry, "get"):
            tool = self._tool_registry.get(tool_id)
        elif hasattr(self._tool_registry, "get_tool"):
            tool = self._tool_registry.get_tool(tool_id)

        if not tool:
            res = CommandResult(command_id, CommandStatus.REJECTED, tool_id, error="INVALID_TOOL")
            return self._finalize(res, start_time)

        # 7. Confirmation check
        requires_confirmation = getattr(tool, "requires_confirmation", False)
        if requires_confirmation and confirmation_status != 'confirmed':
            res = CommandResult(command_id, CommandStatus.REJECTED, tool_id, error="CONFIRMATION_REQUIRED")
            return self._finalize(res, start_time)

        # 8. Execute
        self._execution_count += 1
        try:
            exec_result = await self._execute_with_timeout(tool, params, timeout)
            res = CommandResult(command_id, CommandStatus.SUCCEEDED, tool_id, result=exec_result)
        except asyncio.TimeoutError:
            res = CommandResult(command_id, CommandStatus.FAILED, tool_id, error="TIMEOUT")
        except Exception as e:
            res = CommandResult(command_id, CommandStatus.FAILED, tool_id, error=str(e))

        # 9, 10, 11, 12. Finalize
        return self._finalize(res, start_time)

    def _finalize(self, res: CommandResult, start_time: float) -> Dict[str, Any]:
        """Tugatish ishlari (cache, audit, sanitize)."""
        res.duration_ms = (time.time() - start_time) * 1000
        
        if res.result:
            res.result = self._sanitize_result(res.result)
            
        self._idempotency_cache[res.command_id] = res
        
        if self._audit:
            self._audit.log(
                RemoteEventType.COMMAND_EXECUTED if res.status == CommandStatus.SUCCEEDED else RemoteEventType.COMMAND_FAILED,
                event_data={
                    "command_id": res.command_id,
                    "tool_id": res.tool_id,
                    "status": res.status.value,
                    "error": res.error,
                    "duration_ms": res.duration_ms
                }
            )
            
        return self._build_result_dict(res)
        
    def _build_result_dict(self, res: CommandResult) -> Dict[str, Any]:
        return {
            "command_id": res.command_id,
            "status": res.status.value,
            "tool_id": res.tool_id,
            "result": res.result,
            "error": res.error,
            "duration_ms": res.duration_ms,
            "timestamp": res.timestamp
        }

    async def _execute_with_timeout(self, tool: Any, params: Dict, timeout: float) -> Dict[str, Any]:
        """Buyruqni vaqt cheklovi bilan bajarish."""
        is_dangerous = getattr(tool, "risk_level", "LOW") in ("HIGH", "CRITICAL") or getattr(tool, "requires_confirmation", False)
        
        def _sync_call():
            if hasattr(tool, "handler") and callable(tool.handler):
                return tool.handler(params)
            elif hasattr(tool, "executor") and callable(tool.executor):
                return tool.executor(params)
            elif hasattr(tool, "execute") and callable(tool.execute):
                try:
                    return tool.execute(**params)
                except TypeError:
                    return tool.execute(params)
            elif callable(tool):
                return tool(params)
            return {"error": "TOOL_NOT_CALLABLE"}

        async def _run():
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, _sync_call)

        if is_dangerous:
            async with self._dangerous_lock:
                return await asyncio.wait_for(_run(), timeout=timeout)
        else:
            return await asyncio.wait_for(_run(), timeout=timeout)

    def _sanitize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Natijani tozalash va qisqartirish."""
        # Redact secrets via shared utility
        sanitized = sanitize_event_data(result)
        
        # Check size
        try:
            dumped = json.dumps(sanitized)
            if len(dumped.encode('utf-8')) > self._max_result_size:
                return {"_truncated": True, "message": "Result exceeded maximum size limit."}
            return sanitized
        except Exception as e:
            logger.warning(f"Error checking result size: {e}")
            return {"_error": "Unserializable result"}

    def _purge_expired_nonces(self):
        """Eski noncelarni tozalash (Garbage collection)."""
        now = time.time()
        self._seen_nonces = {k: v for k, v in self._seen_nonces.items() if v >= now}
        
        # Enforce max cache size on idempotency cache
        if len(self._idempotency_cache) > self._max_cache_size:
            # Sort by timestamp, keep newest
            sorted_items = sorted(self._idempotency_cache.items(), key=lambda x: x[1].timestamp)
            to_keep = sorted_items[-self._max_cache_size:]
            self._idempotency_cache = dict(to_keep)

    def get_stats(self) -> Dict[str, Any]:
        """Statistikani olish."""
        return {
            "execution_count": self._execution_count,
            "cache_size": len(self._idempotency_cache),
            "nonce_count": len(self._seen_nonces)
        }


class CommandPoller:
    """Backenddan buyruqlarni tekshiruvchi (Polling service)."""
    
    def __init__(self, transport, device_id, executor, poll_interval=5.0, audit_logger=None):
        self._transport = transport
        self._device_id = device_id
        self._executor = executor
        self._poll_interval = poll_interval
        self._running = False
        self._audit = audit_logger
        self._poll_task: Optional[asyncio.Task] = None

    async def start(self):
        """Pollingni boshlash."""
        if self._running:
            return
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Command poller started.")

    async def stop(self):
        """Pollingni to'xtatish."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        logger.info("Command poller stopped.")

    async def _poll_loop(self):
        """Asosiy sikl."""
        while self._running:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")
            
            await asyncio.sleep(self._poll_interval)

    async def _poll_once(self):
        """Bir martalik so'rov (Poll iteration)."""
        endpoint = f"/api/devices/{self._device_id}/commands/pending"
        try:
            status, data = await self._transport.get(endpoint)
            
            if status == 200 and data and isinstance(data, list):
                for command in data:
                    await self._process_command(command)
            elif status in (401, 403):
                logger.warning("Auth error while polling commands.")
        except Exception as e:
            logger.error(f"Transport error during poll: {e}")

    async def _process_command(self, command: Dict):
        """Bitta buyruqni qayta ishlash va natijani yuborish."""
        command_id = command.get("command_id", "unknown")
        
        try:
            result = await self._executor.execute(command)
            
            endpoint = f"/api/devices/{self._device_id}/commands/{command_id}/result"
            post_status, post_response = await self._transport.post(endpoint, data=result)
            
            if self._audit:
                self._audit.log(
                    RemoteEventType.COMMAND_RESULT_SENT,
                    event_data={
                        "command_id": command_id,
                        "post_status": post_status
                    }
                )
        except Exception as e:
            logger.error(f"Error processing command {command_id}: {e}")
