# ========== agent_scheduler.py ==========
# Vaqtli vazifalar tizimi — eslatmalar, buyruqlar, cron
# Background thread da ishlaydi

import os
import json
import time
import logging
import datetime
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Loyiha ildizi


class ScheduledTask:
    """Bitta rejalashtirilgan vazifa"""

    def __init__(
        self,
        task_id: str,
        run_at: datetime.datetime,
        task_type: str,
        data: dict,
        repeat_seconds: int = 0,
    ):
        self.task_id = task_id
        self.run_at = run_at
        self.task_type = task_type  # "reminder", "command", "tool_call"
        self.data = data  # {"text": "..."} yoki {"tool": "...", "params": {...}}
        self.repeat_seconds = repeat_seconds  # 0 = bir marta, >0 = takrorlanuvchi
        self.completed = False
        self.created_at = datetime.datetime.now()

    def is_due(self) -> bool:
        """Vaqti keldimi?"""
        return not self.completed and datetime.datetime.now() >= self.run_at

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "run_at": self.run_at.isoformat(),
            "task_type": self.task_type,
            "data": self.data,
            "repeat_seconds": self.repeat_seconds,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ScheduledTask":
        task = cls(
            task_id=d["task_id"],
            run_at=datetime.datetime.fromisoformat(d["run_at"]),
            task_type=d["task_type"],
            data=d["data"],
            repeat_seconds=d.get("repeat_seconds", 0),
        )
        task.completed = d.get("completed", False)
        task.created_at = datetime.datetime.fromisoformat(
            d.get("created_at", datetime.datetime.now().isoformat())
        )
        return task


class AgentScheduler:
    """Vaqtli vazifalar boshqaruvchisi.

    Background thread da har 5 soniyada tekshiradi.
    Vazifa vaqti kelganda callback chaqiradi.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._tasks = {}  # {task_id: ScheduledTask}
        self._file = os.path.join(BASE_DIR, "data", "scheduled_tasks.json")
        self._running = False
        self._thread = None
        self._callback = None  # Vazifa bajarilganda chaqiriladigan funksiya
        self._counter = 0
        self._load()

    def set_callback(self, callback: Callable):
        """Vazifa bajarilganda chaqiriladigan funksiya.

        Callback signature: callback(task: ScheduledTask)
        """
        self._callback = callback

    def start(self):
        """Background thread ni ishga tushirish"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="Scheduler"
        )
        self._thread.start()
        logger.info(f"Scheduler ishga tushdi: {len(self._tasks)} ta vazifa")

    def stop(self):
        """To'xtatish"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        self._save()
        logger.info("Scheduler to'xtatildi")

    def add(
        self,
        task_type: str,
        data: dict,
        run_at: datetime.datetime = None,
        delay_seconds: int = 0,
        repeat_seconds: int = 0,
    ) -> str:
        """Yangi vazifa qo'shish.

        Args:
            task_type: "reminder", "command", "tool_call"
            data: {"text": "suv ich"} yoki {"tool": "weather", "params": {"city": "Toshkent"}}
            run_at: Aniq vaqt (datetime)
            delay_seconds: X soniyadan keyin
            repeat_seconds: Har X soniyada takrorlash (0 = bir marta)

        Returns:
            task_id
        """
        with self._lock:
            self._counter += 1
            task_id = f"task_{self._counter}_{time.time_ns()}"  # time_ns = takrorlanmas

            if run_at is None:
                run_at = datetime.datetime.now() + datetime.timedelta(
                    seconds=delay_seconds
                )

            task = ScheduledTask(task_id, run_at, task_type, data, repeat_seconds)
            self._tasks[task_id] = task
            self._save()

            vaqt_str = run_at.strftime("%H:%M:%S")
            logger.info(f"Vazifa qo'shildi: {task_id} ({task_type}) → {vaqt_str}")
            return task_id

    def remove(self, task_id: str) -> bool:
        """Vazifani o'chirish"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                self._save()
                return True
            return False

    def list_tasks(self, include_completed: bool = False) -> list:
        """Barcha vazifalar ro'yxati"""
        with self._lock:
            tasks = []
            for task in self._tasks.values():
                if include_completed or not task.completed:
                    tasks.append(
                        {
                            "id": task.task_id,
                            "type": task.task_type,
                            "run_at": task.run_at.strftime("%Y-%m-%d %H:%M:%S"),
                            "data": task.data,
                            "completed": task.completed,
                            "repeat": task.repeat_seconds > 0,
                        }
                    )
            return tasks

    def clear_completed(self):
        """Bajarilgan vazifalarni tozalash"""
        with self._lock:
            self._tasks = {k: v for k, v in self._tasks.items() if not v.completed}
            self._save()

    @property
    def active_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._tasks.values() if not t.completed)

    def _loop(self):
        """Background loop — har 5 soniyada tekshirish"""
        while self._running:
            try:
                self._check_tasks()
            except Exception as e:
                logger.error(f"Scheduler loop xatolik: {e}")
            time.sleep(5)  # 5 soniyada bir tekshirish

    def _check_tasks(self):
        """Vaqti kelgan vazifalarni bajarish"""
        with self._lock:
            for task in list(self._tasks.values()):
                if task.is_due():
                    self._execute_task(task)

    def _execute_task(self, task: ScheduledTask):
        """Vazifani bajarish"""
        logger.info(f"Vazifa bajarilmoqda: {task.task_id} ({task.task_type})")

        try:
            if self._callback:
                self._callback(task)

            if task.repeat_seconds > 0:
                # Takrorlanuvchi — keyingi vaqtni belgilash
                task.run_at = datetime.datetime.now() + datetime.timedelta(
                    seconds=task.repeat_seconds
                )
                task.completed = False
            else:
                task.completed = True

            self._save()
        except Exception as e:
            logger.error(f"Vazifa bajarish xatolik: {task.task_id}: {e}")
            task.completed = True

    def _load(self):
        """Fayldan yuklash"""
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for d in data.get("tasks", []):
                    task = ScheduledTask.from_dict(d)
                    if not task.completed:
                        self._tasks[task.task_id] = task
                self._counter = data.get("counter", 0)
                logger.debug(f"Scheduler: {len(self._tasks)} ta vazifa yuklandi")
            except Exception as e:
                logger.warning(f"Scheduler yuklash xatolik: {e}")

    def _save(self):
        """Faylga saqlash"""
        try:
            data = {
                "counter": self._counter,
                "tasks": [t.to_dict() for t in self._tasks.values()],
            }
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Scheduler saqlash xatolik: {e}")


# ========== Vaqt parsing yordamchilari ==========


def parse_time_expression(text: str) -> Optional[dict]:
    """Matndan vaqtni ajratish.

    Misollari:
    - "5 daqiqadan keyin" → {"delay_seconds": 300}
    - "soat 14:00 da" → {"run_at": today 14:00}
    - "30 soniyadan keyin" → {"delay_seconds": 30}
    - "1 soatdan keyin" → {"delay_seconds": 3600}
    - "har 10 daqiqada" → {"repeat_seconds": 600}

    Returns:
        {"delay_seconds": int} yoki {"run_at": datetime} yoki {"repeat_seconds": int} yoki None
    """
    import re

    text = text.lower().strip()

    # "X daqiqadan keyin" / "X minut"
    m = re.search(r"(\d+)\s*(?:daqiqa|minut|min)", text)
    if m:
        minutes = int(m.group(1))
        if "har" in text:
            return {"repeat_seconds": minutes * 60}
        return {"delay_seconds": minutes * 60}

    # "X soniyadan keyin" / "X sekund"
    m = re.search(r"(\d+)\s*(?:soniya|sekund|sek)", text)
    if m:
        seconds = int(m.group(1))
        if "har" in text:
            return {"repeat_seconds": seconds}
        return {"delay_seconds": seconds}

    # "X soatdan keyin"
    m = re.search(r"(\d+)\s*(?:soat|hour)", text)
    if m:
        hours = int(m.group(1))
        if "har" in text:
            return {"repeat_seconds": hours * 3600}
        return {"delay_seconds": hours * 3600}

    # "soat HH:MM da"
    m = re.search(r"(?:soat\s*)?(\d{1,2})[:\.](\d{2})", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        now = datetime.datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)  # Ertaga
        return {"run_at": target}

    return None


# Global singleton
_scheduler = None


def get_scheduler() -> AgentScheduler:
    """Global scheduler olish"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AgentScheduler()
    return _scheduler
