# ========== command_dispatcher.py ==========
# Mikasa AI v6.0.0 — Mahalliy va AI Buyruqlarni Taqsimlash Xizmati (Command Dispatcher)
# Tezkor mahalliy buyruqlar va murakkab AI topshiriqlarini boshqarish

import os
import re
import logging
import datetime
import webbrowser
from typing import Tuple, Optional, Dict, Any, Callable
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

try:
    from core.smart_algorithms import aqlli_buyruq_aniqla, xavfli_buyruqmi
    SMART_ALGO_AVAILABLE = True
except ImportError:
    SMART_ALGO_AVAILABLE = False


def get_system_specs_summary() -> str:
    """Kompyuterning asosiy apparat va tizim parametrlarini olish"""
    try:
        import platform
        import psutil

        os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        node_name = platform.node()
        cpu_name = platform.processor() or "Standart protsessor"
        cores_p = psutil.cpu_count(logical=False) or 1
        cores_l = psutil.cpu_count(logical=True) or 1
        cpu_usage = psutil.cpu_percent(interval=0.1)

        mem = psutil.virtual_memory()
        total_ram = round(mem.total / (1024**3), 1)
        used_ram = round(mem.used / (1024**3), 1)
        free_ram = round(mem.available / (1024**3), 1)

        disks = []
        for part in psutil.disk_partitions(all=False):
            if "cdrom" in part.opts or part.fstype == "":
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                free_gb = round(usage.free / (1024**3), 1)
                total_gb = round(usage.total / (1024**3), 1)
                drive = part.mountpoint.rstrip("\\")
                disks.append(f"{drive} ({free_gb} GB bo'sh / {total_gb} GB)")
            except Exception:
                pass
        disks_str = ", ".join(disks) if disks else "Aniqlanmadi"

        lines = [
            "🖥️ Kompyuteringiz parametrlari:",
            f"• Operatsion tizim: {os_info}",
            f"• Kompyuter nomi: {node_name}",
            f"• Protsessor (CPU): {cpu_name} ({cores_p} fiz / {cores_l} mantiqiy yadro, {cpu_usage}% band)",
            f"• Tezkor xotira (RAM): {total_ram} GB (Ishlatilmoqda: {used_ram} GB, Bo'sh: {free_ram} GB, {mem.percent}%)",
            f"• Disk xotirasi: {disks_str}"
        ]

        bat = psutil.sensors_battery()
        if bat:
            plug = "tarmoqqa ulangan" if bat.power_plugged else "batareyada"
            lines.append(f"• Batareya quvvati: {bat.percent}% ({plug})")

        return "\n".join(lines)
    except Exception as e:
        return f"Tizim parametrlarini aniqlashda xatolik: {e}"


class CommandDispatcher:
    """
    Buyruqlarni tezkor mahalliy bajarish va AI agentiga yo'naltirish xizmati.
    """

    def __init__(self, tts_speak_func: Optional[Callable[[str], None]] = None):
        self.speak_func = tts_speak_func
        self._custom_handlers: Dict[str, Callable] = {}

    def register_handler(self, intent: str, handler: Callable):
        """Maxsus buyruq handlerini ro'yxatdan o'tkazish"""
        self._custom_handlers[intent] = handler

    def dispatch_local(self, text: str) -> Tuple[bool, str]:
        """
        Matn mahalliy tizim buyrug'i ekanligini tekshirish va bajarish.
        Agar mahalliy buyruq bo'lsa: (True, "natija xabari")
        Agar AI tahlil talab qilsa: (False, "")
        """
        clean_text = text.lower().strip()
        if not clean_text:
            return True, "Buyruq kiritilmadi."

        # 1. Vaqt va sana
        if clean_text in ["vaqt", "soat", "vaqt necha", "soat necha", "vaqtni ayt"]:
            now = datetime.datetime.now()
            javob = f"Hozirgi vaqt: {now.strftime('%H:%M')}"
            return True, javob

        if clean_text in ["sana", "bugungi sana", "bugun qaysi kun", "qaysi sana"]:
            now = datetime.datetime.now()
            oylar = [
                "yanvar", "fevral", "mart", "aprel", "may", "iyun",
                "iyul", "avgust", "sentyabr", "oktyabr", "noyabr", "dekabr"
            ]
            javob = f"Bugun {now.day}-{oylar[now.month-1]}, {now.year}-yil."
            return True, javob

        # 2. YouTube va Musiqa
        # Agar musiqa/qo'shiq ijrosi so'ralgan bo'lsa, asosiy musiqa pipelineiga o'tkazish
        if any(w in clean_text for w in ["qo'shiq", "qoshiq", "musiqa", "trek", "ashula", "qo'y", "qoy", "ijro", "eshit"]):
            return False, ""

        if re.search(r"^(youtube|yutub|yutubni och|youtubeni och)$", clean_text):
            webbrowser.open("https://www.youtube.com")
            return True, "YouTube ochilmoqda."

        yt_search = re.match(r"(?:youtube|yutub)(?:da|dan)?\s+(?:qidir|och|top)\s+(.+)", clean_text)
        if yt_search:
            query = yt_search.group(1).strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
            return True, f"YouTube'dan '{query}' qidirilmoqda."

        # 3. Google qidiruv
        google_search = re.match(r"(?:google|gugl)(?:da|dan)?\s+(?:qidir|top)\s+(.+)", clean_text)
        if google_search:
            query = google_search.group(1).strip()
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
            return True, f"Google'dan '{query}' qidirilmoqda."

        # 4. Telegram
        if re.search(r"\b(telegram|tg|telegramni och)\b", clean_text):
            try:
                os.system("start telegram:")
                return True, "Telegram ochilmoqda."
            except Exception:
                pass

        # 5. Ovoz darajasi (Volume)
        volume_match = re.search(r"ovoz(?:ni)?\s*(\d+)(?:\s*(?:foiz|qil|ga\s*qo['']y))?", clean_text)
        if volume_match:
            try:
                vol_level = int(volume_match.group(1))
                vol_level = max(0, min(100, vol_level))
                # Windows audio api orqali sozlash
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL

                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(vol_level / 100.0, None)
                return True, f"Ovoz balandligi {vol_level}% ga sozlandi."
            except Exception as e:
                logger.error(f"Ovozni sozlashda xatolik: {e}")

        # 6. Kompyuter va Tizim Parametrlari (PC Specs / System Info)
        pc_specs_keywords = [
            "kompyuterim parametrlarini aytib ber",
            "pc parametrlarini aytib ber",
            "kompyuterim parametrlarini ayt",
            "kompyuter parametrlarini ayt",
            "pc parametrlarini ayt",
            "kompyuterim parametrlari",
            "kompyuter parametrlari",
            "pc parametrlari",
            "tizim parametrlari",
            "tizim ma'lumotlari",
            "tizim malumotlari",
            "kompyuter xususiyatlari",
            "kompyuterim xususiyatlari",
            "pc xususiyatlari",
            "kompyuter haqida ma'lumot",
            "kompyuterim haqida",
        ]
        if clean_text in pc_specs_keywords or (
            any(w in clean_text for w in ["kompyuter", "pc", "tizim", "sistema"]) and
            any(p in clean_text for p in ["parametr", "xususiyat", "ma'lumot", "malumot", "xarakteristika", "info", "spesifikatsiya"])
        ) or clean_text in ["ram qancha", "operativka qancha", "protsessor qanday", "diskda qancha joy bor"]:
            return True, get_system_specs_summary()

        # 7. Maxsus ro'yxatdan o'tgan handlerlar
        for intent, handler in self._custom_handlers.items():
            try:
                handled, result = handler(clean_text)
                if handled:
                    return True, result
            except Exception as e:
                logger.error(f"Custom handler '{intent}' xatolik: {e}")

        # Mahalliy aniqlanmadi — AI agentga uzatiladi
        return False, ""
