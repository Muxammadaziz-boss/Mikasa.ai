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

        # 6. Maxsus ro'yxatdan o'tgan handlerlar
        for intent, handler in self._custom_handlers.items():
            try:
                handled, result = handler(clean_text)
                if handled:
                    return True, result
            except Exception as e:
                logger.error(f"Custom handler '{intent}' xatolik: {e}")

        # Mahalliy aniqlanmadi — AI agentga uzatiladi
        return False, ""
