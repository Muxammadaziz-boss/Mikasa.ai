# ========== base_agent.py ==========
# Multi-Agent Architecture — Base Agent Class
# Barcha agentlar uchun umumiy asos

import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Barcha agentlar uchun asosiy klass.
    Har bir sub-agent o'z sohasi bo'yicha mutaxassis.
    """

    def __init__(self, name: str, specialty: str, ai_call_func: Callable):
        self.name = name
        self.specialty = specialty
        self.ai_call_func = ai_call_func
        self._lock = threading.Lock()
        self._busy = False
        self._last_task = None
        self._task_history: List[Dict] = []
        self._system_prompt = self._build_system_prompt()

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Har bir agent o'z system promptini yaratadi"""
        pass

    @abstractmethod
    def can_handle(self, task: str) -> bool:
        """Bu agent bu vazifani bajaradimi?"""
        pass

    @abstractmethod
    def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Vazifani bajarish — har bir agent o'zicha implement qiladi"""
        pass

    def run(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Thread-safe vazifa bajarish"""
        with self._lock:
            if self._busy:
                return {"status": "busy", "error": f"{self.name} allaqachon band"}
            self._busy = True
            self._last_task = task

        try:
            start_time = datetime.now()
            result = self.execute(task, context)
            duration = (datetime.now() - start_time).total_seconds()

            task_record = {
                "task": task,
                "agent": self.name,
                "status": "success",
                "duration": duration,
                "timestamp": start_time.isoformat(),
            }
            self._task_history.append(task_record)
            self._task_history = self._task_history[-50:]

            return result

        except Exception as e:
            logger.error(f"{self.name} execute xatolik: {e}")
            return {"status": "error", "error": str(e), "agent": self.name}
        finally:
            self._busy = False

    def is_busy(self) -> bool:
        return self._busy

    def get_stats(self) -> Dict:
        """Agent statistikasi"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "busy": self._busy,
            "tasks_completed": len(self._task_history),
            "last_task": self._last_task,
        }
