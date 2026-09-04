# ========== system_agent.py ==========
# Multi-Agent: SystemAgent (DevOps / Tizim monitoring va optimallashtirish agenti)
# Kompyuter holati, resurslar, xotira tozalash va jarayonlarni boshqarish

import os
import shutil
import tempfile
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class SystemAgent(BaseAgent):
    """
    SystemAgent — kompyuter tizimi va resurslarini boshqarish bo'yicha mutaxassis agent.
    CPU, RAM, Disk, fon jarayonlari va tizimni tozalashni amalga oshiradi.
    """

    def __init__(self, ai_call_func):
        super().__init__(
            name="SystemAgent",
            specialty="Tizim monitoringi va optimallashtirish",
            ai_call_func=ai_call_func,
        )

        self._system_keywords = {
            "tizim", "sistema", "ram", "xotira", "protsessor", "cpu", "disk",
            "joy", "tozala", "temp", "monitoring", "jarayon", "process",
            "tezlashtir", "nagruzka", "qotyapti", "resurs"
        }

    def _build_system_prompt(self) -> str:
        return """Sen SystemAgent — Mikasa AI tizimining kompyuter resurslari va operatsion tizim boshqaruvchisisan.

Vazifalaring:
1. Kompyuterning joriy holatini (RAM, CPU, Disk) tahlil qilish
2. Qotib qolgan yoki xotirani ko'p yeyayotgan jarayonlarni aniqlash
3. Vaqtinchalik fayllarni (temp/cache) tozalash bo'yicha tavsiya va amallar berish
4. Foydalanuvchiga (Muxammadaziz uchun) qisqa, aniq va texnik jihatdan to'g'ri hisobot berish.

Muloqot tili: O'zbekcha.
"""

    def can_handle(self, task: str) -> bool:
        """Ushbu vazifa tizim monitoringi yoki boshqaruviga oidmi?"""
        task_lower = task.lower()
        return any(kw in task_lower for kw in self._system_keywords)

    def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Tizim vazifasini bajarish"""
        logger.info(f"SystemAgent vazifani boshladi: {task}")
        task_lower = task.lower()

        # 1. Tizim holati ma'lumotlarini yig'ish
        sys_stats = self.get_system_health()

        # 2. Agar tozalash so'ralgan bo'lsa
        clean_result = None
        if "tozala" in task_lower or "temp" in task_lower or "kesh" in task_lower:
            clean_result = self.clean_temp_files()

        # 3. AI orqali foydalanuvchiga xulosa tayyorlash
        prompt = f"""Foydalanuvchi vazifasi: {task}
Joriy tizim ko'rsatkichlari:
- CPU: {sys_stats.get('cpu_percent')}%
- RAM: {sys_stats.get('ram_percent')}% ({sys_stats.get('ram_used_gb')}GB / {sys_stats.get('ram_total_gb')}GB)
- Disk: {sys_stats.get('disk_percent')}% bo'sh: {sys_stats.get('disk_free_gb')}GB
- Eng ko'p RAM yeyayotgan dasturlar: {', '.join([p['name'] for p in sys_stats.get('top_processes', [])[:3]])}
{f"- Tozalash natijasi: {clean_result.get('message')}" if clean_result else ""}

Foydalanuvchiga muloyim, qisqa va aniq o'zbek tilida javob tayyorla."""

        ai_response = self.ai_call_func(prompt, self._system_prompt)

        return {
            "status": "success",
            "agent": self.name,
            "response": ai_response,
            "system_health": sys_stats,
            "cleaning": clean_result,
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Batafsil tizim ko'rsatkichlari"""
        if not PSUTIL_AVAILABLE:
            return {
                "cpu_percent": 0.0,
                "ram_percent": 0.0,
                "disk_percent": 0.0,
                "top_processes": [],
            }
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")

            # Eng ko'p RAM sarflayotgan jarayonlar
            top_procs = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    info = proc.info
                    if info['memory_percent'] and info['memory_percent'] > 1.0:
                        top_procs.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            top_procs.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)

            return {
                "cpu_percent": cpu,
                "ram_percent": ram.percent,
                "ram_used_gb": round(ram.used / (1024**3), 2),
                "ram_total_gb": round(ram.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "top_processes": top_procs[:5],
            }
        except Exception as e:
            logger.error(f"Tizim ma'lumotlarini olishda xatolik: {e}")
            return {}

    def clean_temp_files(self) -> Dict[str, Any]:
        """Xavfsiz vaqtinchalik fayllarni tozalash"""
        temp_dir = tempfile.gettempdir()
        deleted_count = 0
        freed_bytes = 0

        try:
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        size = os.path.getsize(item_path)
                        os.unlink(item_path)
                        deleted_count += 1
                        freed_bytes += size
                except Exception:
                    continue  # Band fayllarni o'tkazib yuboramiz

            freed_mb = round(freed_bytes / (1024 * 1024), 2)
            return {
                "success": True,
                "deleted_files": deleted_count,
                "freed_mb": freed_mb,
                "message": f"Vaqtinchalik papkadan {deleted_count} ta fayl tozalandi ({freed_mb} MB bo'shatildi).",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "message": "Tozalashda qisman xatolik bo'ldi."}
