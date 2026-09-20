# ========== core/v8/command_queue.py ==========
# Phase 46 — Server-Side Remote Command Queue & Confirmation Manager

import time
import uuid
import secrets
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from core.v8.events import RemoteEventType, RemoteAuditLogger

logger = logging.getLogger(__name__)

# ==========================================
# 1. CommandState Enum
# ==========================================
class CommandState(str, Enum):
    PENDING = 'pending'
    AWAITING_CONFIRMATION = 'awaiting_confirmation'
    CONFIRMED = 'confirmed'
    DISPATCHED = 'dispatched'
    EXECUTING = 'executing'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'

# ==========================================
# 2. ConfirmationToken
# ==========================================
@dataclass
class ConfirmationToken:
    command_id: str = ''
    user_id: str = ''
    device_id: str = ''
    action: str = ''
    token: str = field(default_factory=lambda: secrets.token_hex(16))
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    is_used: bool = False

    def is_valid(self, now: Optional[float] = None) -> bool:
        if now is None:
            now = time.time()
        return not self.is_used and now < self.expires_at

    def use(self) -> None:
        self.is_used = True

# ==========================================
# 3. QueuedCommand
# ==========================================
@dataclass
class QueuedCommand:
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str = ''
    user_id: str = ''
    tool_id: str = ''
    params: Dict[str, Any] = field(default_factory=dict)
    origin: str = 'web'  # 'web', 'telegram', 'api'
    state: CommandState = CommandState.PENDING
    requires_confirmation: bool = False
    confirmation_token: Optional[str] = None
    nonce: str = field(default_factory=lambda: secrets.token_hex(8))
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    dispatched_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    risk_level: str = 'low'
    telegram_user_id: Optional[str] = None

    def is_expired(self, now: Optional[float] = None) -> bool:
        if now is None:
            now = time.time()
        return now > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "tool_id": self.tool_id,
            "params": self.params,
            "origin": self.origin,
            "state": self.state.value,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_token": self.confirmation_token,
            "nonce": self.nonce,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "dispatched_at": self.dispatched_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "risk_level": self.risk_level,
            "telegram_user_id": self.telegram_user_id
        }

    def to_dispatch_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "tool_id": self.tool_id,
            "params": self.params,
            "nonce": self.nonce,
            "expires_at": self.expires_at,
            "confirmation_status": "confirmed" if self.requires_confirmation else "none"
        }

# ==========================================
# 4. CommandQueueManager
# ==========================================
class CommandQueueManager:
    _default_instance = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_default_instance(cls):
        with cls._instance_lock:
            if cls._default_instance is None:
                cls._default_instance = cls()
            return cls._default_instance

    def __init__(self, max_history=100, command_ttl=300.0, confirmation_ttl=60.0):
        self._queues: Dict[str, List[QueuedCommand]] = {}  # device_id -> [commands]
        self._commands: Dict[str, QueuedCommand] = {}  # command_id -> command
        self._confirmations: Dict[str, ConfirmationToken] = {}  # token -> ConfirmationToken
        self._history: Dict[str, List[QueuedCommand]] = {}  # device_id -> completed commands
        self._command_ttl = command_ttl
        self._confirmation_ttl = confirmation_ttl
        self._max_history = max_history
        self._dangerous_locks: Dict[str, str] = {}  # device_id -> command_id
        self._audit = RemoteAuditLogger()
        self._lock = threading.RLock()

    # ------------------------------------------
    # Buyruqlarni qo'shish (Submit)
    # ------------------------------------------
    def submit_command(self, device_id: str, user_id: str, tool_id: str, params: Dict[str, Any], 
                       origin: str = 'web', requires_confirmation: bool = False, 
                       risk_level: str = 'low', telegram_user_id: Optional[str] = None) -> Tuple[QueuedCommand, Optional[ConfirmationToken]]:
        with self._lock:
            self._purge_expired(device_id)
            
            # Xavfli amallar uchun qulf (Dangerous lock check)
            if risk_level == 'high':
                if device_id in self._dangerous_locks:
                    existing_cmd = self._dangerous_locks[device_id]
                    if existing_cmd in self._commands and not self._commands[existing_cmd].is_expired():
                        raise RuntimeError(f"Another high risk command ({existing_cmd}) is already pending/executing for this device.")
                    else:
                        del self._dangerous_locks[device_id]

            # Idempotency check
            queue = self._queues.setdefault(device_id, [])
            for cmd in queue:
                if (cmd.user_id == user_id and cmd.tool_id == tool_id and 
                    cmd.params == params and cmd.state in (CommandState.PENDING, CommandState.AWAITING_CONFIRMATION)):
                    if cmd.state == CommandState.AWAITING_CONFIRMATION and cmd.confirmation_token:
                        token_obj = self._confirmations.get(cmd.confirmation_token)
                        if token_obj and token_obj.is_valid():
                            return cmd, token_obj
                    return cmd, None

            now = time.time()
            cmd = QueuedCommand(
                device_id=device_id,
                user_id=user_id,
                tool_id=tool_id,
                params=params,
                origin=origin,
                requires_confirmation=requires_confirmation,
                risk_level=risk_level,
                telegram_user_id=telegram_user_id,
                created_at=now,
                expires_at=now + self._command_ttl
            )
            
            self._commands[cmd.command_id] = cmd

            if risk_level == 'high':
                self._dangerous_locks[device_id] = cmd.command_id

            if requires_confirmation:
                cmd.state = CommandState.AWAITING_CONFIRMATION
                token_obj = ConfirmationToken(
                    command_id=cmd.command_id,
                    user_id=user_id,
                    device_id=device_id,
                    action=tool_id,
                    created_at=now,
                    expires_at=now + self._confirmation_ttl
                )
                self._confirmations[token_obj.token] = token_obj
                cmd.confirmation_token = token_obj.token
                
                self._audit.log(
                    RemoteEventType.REMOTE_COMMAND_SUBMITTED,
                    device_id=device_id,
                    user_id=user_id,
                    command_id=cmd.command_id, tool_id=tool_id, status="awaiting_confirmation"
                )
                return cmd, token_obj
            else:
                cmd.state = CommandState.PENDING
                queue.append(cmd)
                
                self._audit.log(
                    RemoteEventType.REMOTE_COMMAND_SUBMITTED,
                    device_id=device_id,
                    user_id=user_id,
                    command_id=cmd.command_id, tool_id=tool_id, status="pending"
                )
                return cmd, None

    # ------------------------------------------
    # Buyruqni tasdiqlash (Confirm)
    # ------------------------------------------
    def confirm_command(self, command_id: str, token_str: str, user_id: str) -> Tuple[bool, str]:
        with self._lock:
            self._purge_expired_confirmations()
            
            token_obj = self._confirmations.get(token_str)
            if not token_obj:
                return False, "Token not found or expired."
            
            if not token_obj.is_valid():
                return False, "Token expired or already used."
                
            if token_obj.command_id != command_id:
                return False, "Token does not match command ID."
                
            if token_obj.user_id != user_id:
                return False, "Token does not match user ID."
                
            cmd = self._commands.get(command_id)
            if not cmd:
                return False, "Command not found."
                
            if cmd.state != CommandState.AWAITING_CONFIRMATION:
                return False, f"Command cannot be confirmed (state: {cmd.state.value})."
                
            token_obj.use()
            cmd.state = CommandState.CONFIRMED
            
            queue = self._queues.setdefault(cmd.device_id, [])
            queue.append(cmd)
            
            self._audit.log(
                RemoteEventType.REMOTE_COMMAND_CONFIRMED,
                device_id=cmd.device_id,
                user_id=user_id,
                command_id=command_id
            )
            
            return True, "Command confirmed successfully."

    # ------------------------------------------
    # Buyruqni bekor qilish (Cancel)
    # ------------------------------------------
    def cancel_command(self, command_id: str, user_id: str) -> Tuple[bool, str]:
        with self._lock:
            cmd = self._commands.get(command_id)
            if not cmd:
                return False, "Command not found."
                
            if cmd.user_id != user_id:
                return False, "Unauthorized to cancel this command."
                
            if cmd.state in (CommandState.EXECUTING, CommandState.SUCCEEDED, CommandState.FAILED, CommandState.EXPIRED, CommandState.CANCELLED, CommandState.REJECTED):
                return False, f"Cannot cancel command in state {cmd.state.value}."
                
            cmd.state = CommandState.CANCELLED
            
            if cmd.device_id in self._queues and cmd in self._queues[cmd.device_id]:
                self._queues[cmd.device_id].remove(cmd)
                
            self._move_to_history(cmd)
            
            # Clear dangerous lock
            if self._dangerous_locks.get(cmd.device_id) == command_id:
                del self._dangerous_locks[cmd.device_id]
                
            return True, "Command cancelled."

    # ------------------------------------------
    # Kutayotgan buyruqlarni olish (Get pending)
    # ------------------------------------------
    def get_pending_commands(self, device_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            self._purge_expired(device_id)
            
            queue = self._queues.get(device_id, [])
            pending_cmds = [cmd for cmd in queue if cmd.state in (CommandState.PENDING, CommandState.CONFIRMED)]
            
            result = []
            now = time.time()
            for cmd in pending_cmds:
                cmd.state = CommandState.DISPATCHED
                cmd.dispatched_at = now
                result.append(cmd.to_dispatch_dict())
                # Dispatched means it is sent to device
                queue.remove(cmd) 
            
            return result

    # ------------------------------------------
    # Natijani saqlash (Record result)
    # ------------------------------------------
    def record_result(self, command_id: str, result: Dict[str, Any]) -> bool:
        with self._lock:
            cmd = self._commands.get(command_id)
            if not cmd:
                return False
                
            success = result.get('success', False)
            if success:
                cmd.state = CommandState.SUCCEEDED
            else:
                cmd.state = CommandState.FAILED
                cmd.error = result.get('error', 'Unknown error')
                
            cmd.result = result
            cmd.completed_at = time.time()
            
            # Clear dangerous lock
            if self._dangerous_locks.get(cmd.device_id) == command_id:
                del self._dangerous_locks[cmd.device_id]
                
            # If it somehow was in queue, remove it
            if cmd.device_id in self._queues and cmd in self._queues[cmd.device_id]:
                self._queues[cmd.device_id].remove(cmd)
                
            self._move_to_history(cmd)
            
            return True

    # ------------------------------------------
    # Buyruqni olish (Get)
    # ------------------------------------------
    def get_command(self, command_id: str) -> Optional[QueuedCommand]:
        with self._lock:
            return self._commands.get(command_id)

    # ------------------------------------------
    # Qurilma tarixini olish (History)
    # ------------------------------------------
    def get_device_history(self, device_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            hist = self._history.get(device_id, [])
            return [cmd.to_dict() for cmd in hist[-limit:]]

    # ------------------------------------------
    # Yordamchi metodlar (Private)
    # ------------------------------------------
    def _move_to_history(self, cmd: QueuedCommand):
        device_hist = self._history.setdefault(cmd.device_id, [])
        device_hist.append(cmd)
        if len(device_hist) > self._max_history:
            self._history[cmd.device_id] = device_hist[-self._max_history:]

    def _purge_expired(self, device_id: Optional[str] = None):
        now = time.time()
        
        device_ids = [device_id] if device_id else list(self._queues.keys())
        
        for did in device_ids:
            if did not in self._queues:
                continue
                
            queue = self._queues[did]
            expired_cmds = [cmd for cmd in queue if cmd.is_expired(now)]
            
            for cmd in expired_cmds:
                cmd.state = CommandState.EXPIRED
                queue.remove(cmd)
                
                # Clear dangerous lock if expired
                if self._dangerous_locks.get(cmd.device_id) == cmd.command_id:
                    del self._dangerous_locks[cmd.device_id]
                    
                self._move_to_history(cmd)

    def _purge_expired_confirmations(self):
        now = time.time()
        expired = [token for token, obj in self._confirmations.items() if not obj.is_valid(now)]
        for token in expired:
            del self._confirmations[token]

    # ------------------------------------------
    # Phase 47: Qurilma uchun pending buyruqlarni bekor qilish
    # ------------------------------------------
    def cancel_pending_for_device(self, device_id: str, reason: str = "emergency_revoke") -> int:
        """
        Berilgan qurilma uchun barcha pending/awaiting buyruqlarni bekor qilish.
        Emergency revoke paytida ishlatiladi.
        Returns: bekor qilingan buyruqlar soni
        """
        cancelled_count = 0
        with self._lock:
            queue = self._queues.get(device_id, [])
            to_cancel = [
                cmd for cmd in queue
                if cmd.state in (CommandState.PENDING, CommandState.CONFIRMED, CommandState.AWAITING_CONFIRMATION)
            ]

            for cmd in to_cancel:
                cmd.state = CommandState.CANCELLED
                cmd.error = f"Cancelled: {reason}"
                cmd.completed_at = time.time()
                if cmd in queue:
                    queue.remove(cmd)
                self._move_to_history(cmd)
                cancelled_count += 1

            # Clear dangerous locks for this device
            if device_id in self._dangerous_locks:
                del self._dangerous_locks[device_id]

        return cancelled_count

    def invalidate_confirmations_for_device(self, device_id: str) -> int:
        """
        Berilgan qurilma uchun barcha confirmation tokenlarni bekor qilish.
        Returns: bekor qilingan tokenlar soni
        """
        invalidated = 0
        with self._lock:
            to_remove = []
            for token, conf_obj in self._confirmations.items():
                # Confirmation object da device_id bo'lishi kerak
                cmd_id = getattr(conf_obj, "command_id", None)
                if cmd_id:
                    cmd = self._commands.get(cmd_id)
                    if cmd and cmd.device_id == device_id:
                        to_remove.append(token)
            for token in to_remove:
                del self._confirmations[token]
                invalidated += 1

        return invalidated
