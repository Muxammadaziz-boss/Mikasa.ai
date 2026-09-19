# ========== agent/recovery.py ==========
# Phase 45 — Windows PC Agent Crash Recovery Manager
# Transparent crash detection, dirty state recovery, and stale cleanup

import os
import json
import time
import logging
from typing import Dict, Any

from core.v8.events import RemoteEventType
from agent.audit import AgentAuditLogger

logger = logging.getLogger("mikasa.agent.recovery")


class CrashRecoveryManager:
    """
    Agent kutilmaganda to'xtab qolganda yoki tizim qayta yuklanganda
    holatni shaffof aniqlash va xavfsiz tiklash boshqaruvchisi.
    - Yashirin persistence yoki UAC bypass aslo qo'llanilmaydi.
    - Faqat mahalliy vaultda holat bayrog'i (state flag) yoziladi.
    """

    def __init__(self, vault_dir: str):
        self.vault_dir = vault_dir
        os.makedirs(self.vault_dir, exist_ok=True)
        self.state_file = os.path.join(self.vault_dir, "agent_runtime_state.json")
        self._audit = AgentAuditLogger.get_instance()

    def on_startup(self, device_id: str) -> bool:
        """
        Agent ishga tushganda oldingi sessiya holatini tekshirish.
        Agar oldingi sessiya 'clean_exit: false' bo'lsa, demak avariya yuz bergan.
        Qaytaradi: True agar crash recovery bo'lsa, False agar toza boshlanish bo'lsa.
        """
        is_recovered = False
        prev_data: Dict[str, Any] = {}

        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    prev_data = json.load(f)
                if prev_data.get("is_running") and not prev_data.get("clean_exit"):
                    is_recovered = True
                    logger.warning(f"[CrashRecovery] Kutilmagan to'xtash aniqlandi! PID={prev_data.get('pid')}")
                    self._audit.log_event(
                        event_type=RemoteEventType.CRASH_RECOVERY,
                        device_id=device_id,
                        details={
                            "previous_pid": prev_data.get("pid"),
                            "previous_started_at": prev_data.get("started_at"),
                            "recovered_at": time.time()
                        }
                    )
            except Exception as e:
                logger.warning(f"[CrashRecovery] Holat faylini tekshirishda xato: {e}")

        # Yangi ish holatini yozish
        self._write_state(device_id=device_id, is_running=True, clean_exit=False)
        return is_recovered

    def on_clean_shutdown(self, device_id: str):
        """Toza to'xtash vaqtida bayroqni yopish"""
        self._write_state(device_id=device_id, is_running=False, clean_exit=True)
        logger.info("[CrashRecovery] Agent toza to'xtatildi (clean_exit=True)")

    def _write_state(self, device_id: str, is_running: bool, clean_exit: bool):
        data = {
            "device_id": device_id,
            "pid": os.getpid(),
            "timestamp": time.time(),
            "is_running": is_running,
            "clean_exit": clean_exit,
            "started_at": time.time() if is_running else 0.0
        }
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[CrashRecovery] Holatni saqlashda xato: {e}")
