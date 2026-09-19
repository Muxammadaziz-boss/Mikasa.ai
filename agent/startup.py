# ========== agent/startup.py ==========
# Phase 45 — Windows Startup & Service Integration
# Transparent, user-controlled autostart without UAC bypass or stealth techniques

import sys
import logging
from typing import Dict, Any

logger = logging.getLogger("mikasa.agent.startup")

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "MikasaWindowsAgent"


class WindowsStartupManager:
    """
    Windows tizimida agentning avtomatik ishga tushishini boshqarish.
    Xavfsizlik qoidalari:
    - Yashirin persistence mexanizmlari taqiqlangan.
    - UAC bypass texnikalari mutlaqo ishlatilmaydi.
    - Faqat foydalanuvchining o'zi (HKCU) doirasida shaffof ro'yxatdan o'tkaziladi.
    - O'chirish (uninstall/disable) to'liq qo'llab-quvvatlanadi.
    """

    @staticmethod
    def is_windows() -> bool:
        return sys.platform.startswith("win")

    @classmethod
    def is_startup_enabled(cls) -> bool:
        """HKCU Run kalitida MikasaAgent mavjudligini tekshirish"""
        if not cls.is_windows():
            return False
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY_PATH,
                0,
                winreg.KEY_READ
            ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.warning(f"[WindowsStartup] Kalitni o'qishda xatolik: {e}")
            return False

    @classmethod
    def enable_startup(cls, executable_path: str, args: str = "--background") -> bool:
        """
        HKCU Run kalitiga agentni yozish (Administrator huquqi yoki UAC bypass talab qilinmaydi).
        """
        if not cls.is_windows():
            logger.info("[WindowsStartup] Windows bo'lmagan tizimda autostart o'tkazib yuborildi")
            return False
        try:
            import winreg
            cmd = f'"{executable_path}" {args}'.strip()
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            logger.info(f"[WindowsStartup] Agent avtomatik ishga tushishga qo'shildi: {cmd}")
            return True
        except Exception as e:
            logger.error(f"[WindowsStartup] Autostartni yoqishda xatolik: {e}")
            return False

    @classmethod
    def disable_startup(cls) -> bool:
        """HKCU Run kalitidan MikasaAgentni toza o'chirish"""
        if not cls.is_windows():
            return False
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, APP_NAME)
            logger.info("[WindowsStartup] Agent avtomatik ishga tushishdan olib tashlandi")
            return True
        except FileNotFoundError:
            return True
        except Exception as e:
            logger.error(f"[WindowsStartup] Autostartni o'chirishda xatolik: {e}")
            return False

    @classmethod
    def get_service_guidance(cls) -> Dict[str, Any]:
        """
        Tizim ma'murlari uchun Windows Service yoki Task Scheduler qo'llanmasi.
        """
        return {
            "service_name": "MikasaAgentService",
            "task_scheduler_cmd": (
                'schtasks /create /tn "MikasaAgent" /tr "C:\\Path\\To\\MikasaAgent.exe --service" '
                '/sc onlogon /rl limited'
            ),
            "nssm_cmd": (
                'nssm install MikasaAgent "C:\\Path\\To\\MikasaAgent.exe" && '
                'nssm set MikasaAgent AppParameters "--service"'
            ),
            "uac_bypass": False,
            "stealth": False
        }
