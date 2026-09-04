# ========== proactive_watcher.py ==========
# Proaktiv Kuzatuvchi Tizimi
# Daemon thread — jarayonlarni kuzatadi va tashabbus ko'rsatadi

import os
import time
import logging
import threading
from typing import Optional, Callable, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ProactiveWatcher:
    """Proaktiv kuzatuvchi — foydalanuvchiga o'zi yordam taklif qiladi"""

    def __init__(self, check_interval: int = 180, min_silent_time: int = 300):
        self.check_interval = check_interval
        self.min_silent_time = min_silent_time
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._callbacks: List[Callable] = []
        self._last_activity = time.time()
        self._last_suggestion = time.time()
        self._known_processes: Dict[str, float] = {}
        self._suggestion_cooldown = 600
        self._enabled = False
        self._activity_lock = threading.Lock()

    def start(self):
        """Kuzatuvchini ishga tushirish"""
        if self._running:
            logger.warning("Watcher allaqachon ishlamoqda")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._watch_loop, daemon=True, name="ProactiveWatcher"
        )
        self._thread.start()
        self._enabled = True
        logger.info(f"ProactiveWatcher started (interval: {self.check_interval}s)")

    def stop(self):
        """Kuzatuvchini to'xtatish"""
        self._running = False
        self._enabled = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("ProactiveWatcher stopped")

    def on_suggestion(self, callback: Callable[[str], None]):
        """Taklif kelganda callback"""
        self._callbacks.append(callback)

    def record_activity(self):
        """Foydalanuvchi faolligini qayd etish"""
        with self._activity_lock:
            self._last_activity = time.time()

    def _watch_loop(self):
        """Asosiy kuzatuv loop"""
        import psutil

        while self._running:
            try:
                time.sleep(self.check_interval)

                if not self._enabled:
                    continue

                current_time = time.time()

                with self._activity_lock:
                    silent = current_time - self._last_activity < self.min_silent_time
                if silent:
                    continue

                suggestions = self._check_system(psutil)

                if suggestions and (
                    current_time - self._last_suggestion > self._suggestion_cooldown
                ):
                    for callback in self._callbacks:
                        try:
                            callback(suggestions)
                        except Exception as e:
                            logger.error(f"Callback xatolik: {e}")
                    self._last_suggestion = current_time

            except Exception as e:
                logger.error(f"Watch loop xatolik: {e}")

    def _check_system(self, psutil) -> Optional[str]:
        """Sistema tekshiruvi va taklif generatsiya"""
        try:
            suggestions = []

            processes = []
            for p in psutil.process_iter(["name", "status"]):
                try:
                    processes.append(p.info["name"].lower())
                except:
                    pass

            new_procs = [p for p in processes if p not in self._known_processes]
            for p in new_procs:
                self._known_processes[p] = time.time()

            self._known_processes = {
                k: v for k, v in self._known_processes.items() if time.time() - v < 3600
            }

            if any(
                "code" in p or "cursor" in p or "pycharm" in p or "vscode" in p
                for p in processes
            ):
                suggestions.append(self._check_coding_environment())

            if any("chrome" in p or "firefox" in p or "edge" in p for p in processes):
                suggestions.append(self._check_browser_activity())

            suggestions = [s for s in suggestions if s]
            return suggestions[0] if suggestions else None

        except Exception as e:
            logger.error(f"System check xatolik: {e}")
            return None

    def _check_coding_environment(self) -> Optional[str]:
        """Kodlash muhitini tekshirish"""
        import psutil

        try:
            for p in psutil.process_iter(["name", "cpu_percent"]):
                name = (p.info["name"] or "").lower()
                if any(ide in name for ide in ["code", "cursor", "pycharm", "devenv"]):
                    try:
                        cpu = p.cpu_percent(interval=0.5)
                        if cpu > 80:
                            return "Kod muharririda CPU yuqori. Xato bo'lishi mumkin, yordam kerakmi?"
                    except:
                        pass
            return None
        except:
            return None

    def _check_browser_activity(self) -> Optional[str]:
        """Brauzer faolligini tekshirish"""
        return None

    def is_running(self) -> bool:
        return self._running and self._enabled

    def get_status(self) -> Dict:
        """Holat ma'lumot"""
        return {
            "running": self.is_running(),
            "check_interval": self.check_interval,
            "last_activity": datetime.fromtimestamp(self._last_activity).isoformat(),
            "last_suggestion": datetime.fromtimestamp(
                self._last_suggestion
            ).isoformat(),
            "known_processes": len(self._known_processes),
        }


_proactive_watcher: Optional[ProactiveWatcher] = None


def get_proactive_watcher() -> ProactiveWatcher:
    """Global watcher instance"""
    global _proactive_watcher
    if _proactive_watcher is None:
        _proactive_watcher = ProactiveWatcher()
    return _proactive_watcher


def start_proactive_watcher(on_suggestion: Callable[[str], None] = None):
    """Kuzatuvchini ishga tushirish (qulay funksiya)"""
    watcher = get_proactive_watcher()
    if on_suggestion:
        watcher.on_suggestion(on_suggestion)
    watcher.start()
    return watcher


def stop_proactive_watcher():
    """Kuzatuvchini to'xtatish"""
    global _proactive_watcher
    if _proactive_watcher:
        _proactive_watcher.stop()
        _proactive_watcher = None
