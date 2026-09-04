# ========== main.py ===============================
# ========== Ogohlantirishlarni yashirish ==========
import os
import logging
from config import get_config, get_logger

# Logging sozlash
logger = get_logger(__name__)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('absl').setLevel(logging.ERROR)
logging.getLogger('google.auth').setLevel(logging.ERROR)
logging.getLogger('google.auth.transport.requests').setLevel(logging.ERROR)

# ========== Asosiy importlar ==========
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    SPEECH_AVAILABLE = True
except ImportError:
    sd = None
    sf = None
    np = None
    SPEECH_AVAILABLE = False
    print("WARNING: sounddevice/soundfile modullari topilmadi. Ovozli mikrofon ishlamaydi.")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_RECOGNITION_AVAILABLE = False
    print("WARNING: speech_recognition moduli topilmadi. Ovozli mikrofon ishlamaydi.")

_pyaudio_checked = False
_pyaudio_missing_warned = False

try:
    import edge_tts
    import asyncio
    TTS_AVAILABLE = True
except ImportError:
    edge_tts = None
    asyncio = None
    TTS_AVAILABLE = False
    print("WARNING: edge-tts moduli topilmadi. Ovozli javob ishlamaydi.")

import threading
import time
import subprocess
import requests
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import datetime
import pyautogui
import psutil
import keyboard
from dotenv import load_dotenv
# import google.generativeai as genai  # AI integratsiya uchun kerak emas
import re
import tempfile
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

load_dotenv()

# ========== Versiya ==========
VERSION = "2.2.5"

# ========== NirCmd yo'li ==========
NIRCMD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nircmd.exe")

# ========== Global o'zgaruvchilar va thread-safety ==========
from threading import Lock

class GlobalState:
    """Thread-safe global holat klassi"""
    def __init__(self):
        self._lock = Lock()
        self._buyruq_bajarilmoqda = False
        self._so_ngi_natija = ""
        self._ovoz_turi_global = "erkak"
        self._gui_callback = None
        self._youtube_ochiq = False
        self._tinglash_faol = False
        self._tts_engine = None
        self._tts_failed = False
    
    @property
    def buyruq_bajarilmoqda_lock(self):
        return self._lock
    
    @property
    def buyruq_bajarilmoqda(self):
        with self._lock:
            return self._buyruq_bajarilmoqda
    
    @buyruq_bajarilmoqda.setter
    def buyruq_bajarilmoqda(self, value):
        with self._lock:
            self._buyruq_bajarilmoqda = value
    
    @property
    def so_ngi_natija(self):
        with self._lock:
            return self._so_ngi_natija
    
    @so_ngi_natija.setter
    def so_ngi_natija(self, value):
        with self._lock:
            self._so_ngi_natija = value
    
    @property
    def ovoz_turi_global(self):
        with self._lock:
            return self._ovoz_turi_global
    
    @ovoz_turi_global.setter
    def ovoz_turi_global(self, value):
        with self._lock:
            self._ovoz_turi_global = value
    
    @property
    def gui_callback(self):
        with self._lock:
            return self._gui_callback
    
    @gui_callback.setter
    def gui_callback(self, value):
        with self._lock:
            self._gui_callback = value
    
    @property
    def youtube_ochiq(self):
        with self._lock:
            return self._youtube_ochiq
    
    @youtube_ochiq.setter
    def youtube_ochiq(self, value):
        with self._lock:
            self._youtube_ochiq = value
    
    @property
    def tinglash_faol(self):
        with self._lock:
            return self._tinglash_faol
    
    @tinglash_faol.setter
    def tinglash_faol(self, value):
        with self._lock:
            self._tinglash_faol = value
    
    @property
    def tts_engine(self):
        with self._lock:
            return self._tts_engine
    
    @tts_engine.setter
    def tts_engine(self, value):
        with self._lock:
            self._tts_engine = value
    
    @property
    def tts_failed(self):
        with self._lock:
            return self._tts_failed
    
    @tts_failed.setter
    def tts_failed(self, value):
        with self._lock:
            self._tts_failed = value

# Global holat obyekti
global_state = GlobalState()

# ========== GUI bilan integratsiya ==========
def gui_bilan_integratsiya(callback_func):
    global_state.gui_callback = callback_func

def gui_ga_xabar_yuborish(xabar, ovoz=False):
    """GUI ga xabar yuborish. ovoz=True bo'lsa ovozli aytadi"""
    callback = global_state.gui_callback
    if callback:
        try:
            callback(xabar)
        except Exception as e:
            print(f"GUI callback xatolik: {e}")
            print(xabar)
    else:
        print(xabar)
    
    # Agar ovoz kerak bo'lsa
    if ovoz:
        ovoz_xabar = xabar
        # Emoji va vaqt belgisini olib tashlash
        ovoz_xabar = re.sub(r'\[.*?\]', '', ovoz_xabar)  # [12:30:45]
        ovoz_xabar = re.sub(r'[🎤🗣️📝🎯✅❌⚠️💡📊🎵▶️⏸️🔊🔉🔇📌🤖]', '', ovoz_xabar)  # Emojlar
        ovoz_xabar = ovoz_xabar.strip()
        if ovoz_xabar:
            ovoz_chiqar_tez(ovoz_xabar)

# ========== edge-tts engine ==========
_tts_engine = None
_tts_lock = threading.Lock()
_tts_failed = False

def get_tts_engine():
    global _tts_engine
    global _tts_failed
    if not TTS_AVAILABLE or _tts_failed:
        return None
    return True  # edge-tts is always available if imported

# ========== Ovozli javob berish ==========
def ovoz_chiqar_tez(text):
    """Tez ovozli javob (bloklanmaydi)"""
    def _ijro_et():
        try:
            if not TTS_AVAILABLE:
                print(f"TTS (Ovoz): {text}")
                return
            
            async def speak():
                try:
                    voice = "uz-UZ-MadinaNeural" if global_state.ovoz_turi_global == "ayol" else "uz-UZ-SardorNeural"
                    communicate = edge_tts.Communicate(text, voice)
                    await communicate.save(os.path.join(tempfile.gettempdir(), "tts_output.mp3"))
                    
                    # Play the audio file
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(os.path.join(tempfile.gettempdir(), "tts_output.mp3"))
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"TTS xatolik: {e}")
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(speak())
            loop.close()
            
        except Exception as e:
            print(f"Ovoz xatolik: {e}")
    
    threading.Thread(target=_ijro_et, daemon=True).start()

# ========== Foydalanuvchi ma'lumotlarini olish ==========
def foydalanuvchi_ismi_ol():
    if os.path.exists("foydalanuvchi_ismi.txt"):
        with open("foydalanuvchi_ismi.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        root = tk.Tk()
        root.withdraw()
        ism = simpledialog.askstring("Ism", "Iltimos, ismingizni kiriting:")
        root.destroy()
        if ism:
            with open("foydalanuvchi_ismi.txt", "w", encoding="utf-8") as f:
                f.write(ism)
            return ism
        return "Foydalanuvchi"

def ovoz_turi_ol():
    if os.path.exists("ovoz_turi.txt"):
        with open("ovoz_turi.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        root = tk.Tk()
        root.withdraw()
        voice = simpledialog.askstring("Ovoz", "Ovoz turini tanlang (erkak/ayol):")
        root.destroy()
        if voice and voice.lower() in ["erkak", "ayol"]:
            with open("ovoz_turi.txt", "w", encoding="utf-8") as f:
                f.write(voice.lower())
            return voice.lower()
        with open("ovoz_turi.txt", "w", encoding="utf-8") as f:
            f.write("erkak")
        return "erkak"

# ========== Buyruqlarni yuklash ==========
def buyruqlar_json_ol():
    default_commands = {
        "yutub": "open_youtube",
        "youtube": "open_youtube",
        "birinchi video": "youtube_first_video",
        "musiqa": "music_search",
        "qo'shiq": "music_search",
        "telegram": "open_telegram",
        "vs code": "open_code",
        "chrome": "open_chrome",
        "brave": "open_brave",
        "discord": "open_discord",
        "vaqt": "time",
        "sana": "date",
        "eslatma": "reminder",
        "eslatmalar": "reminders",
        "video qo'y": "play_video",
        "to'xtat": "pause_video",
        "pauza": "pause_video",
        "ai": "chat_mode",
        "suhbat qil": "chat_mode"
    }

    if os.path.exists("commands.json"):
        try:
            with open("commands.json", "r", encoding="utf-8") as f:
                existing = json.load(f)
                for k, v in default_commands.items():
                    if k not in existing:
                        existing[k] = v
                return existing
        except:
            return default_commands
    else:
        with open("commands.json", "w", encoding="utf-8") as f:
            json.dump(default_commands, f, ensure_ascii=False, indent=2)
        return default_commands

buyruqlar_json = buyruqlar_json_ol()

# ========== Ovozni aniqlash ==========
def tingla():
    if not global_state.tinglash_faol:
        return None
    
    if not SPEECH_AVAILABLE or not SPEECH_RECOGNITION_AVAILABLE:
        time.sleep(1)
        return None
        
    try:
        # Use sounddevice directly for recording
        gui_ga_xabar_yuborish("🎤 Tinglanmoqda...")
        
        # Record audio
        samplerate = 16000
        duration = 5
        audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        
        # Convert to speech_recognition format
        audio_data = (audio_data * 32767).astype('int16')
        
        # Use speech_recognition for Google API
        r = sr.Recognizer()
        audio = sr.AudioData(audio_data.tobytes(), samplerate, 2)
        
        try:
            text = r.recognize_google(audio, language="uz-UZ")
            gui_ga_xabar_yuborish(f"🗣️ Siz: {text}")
            return text.lower()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            gui_ga_xabar_yuborish(f"❌ Google API xatosi: {e}", ovoz=True)
            return None
    except Exception as e:
        print(f"DEBUG: Microphone Error: {e}")
        gui_ga_xabar_yuborish(f"❌ Mikrofon xatosi: {e}", ovoz=True)
        return None

# ========== Windows Audio API orqali ovoz boshqaruvi ==========
def get_audio_session():
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        return volume
    except Exception as e:
        print(f"Audio session error: {e}")
        return None

def ovoz_sozlash(level):
    volume = get_audio_session()
    if not volume:
        gui_ga_xabar_yuborish("❌ Ovoz boshqarib bo'lmadi", ovoz=True)
        return False
    
    try:
        level = max(0.0, min(1.0, level / 100.0))
        volume.SetMasterVolumeLevelScalar(level, None)
        gui_ga_xabar_yuborish(f"🔊 Ovoz {int(level * 100)}% ga o'rnatildi")
        ovoz_chiqar_tez(f"Ovoz {int(level * 100)} foizga o'rnatildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Ovoz o'rnatilmadi: {e}", ovoz=True)
        return False

def ovoz_oshir(miqdor=5):
    volume = get_audio_session()
    if not volume:
        gui_ga_xabar_yuborish("❌ Ovoz boshqarib bo'lmadi", ovoz=True)
        return False
    
    try:
        current_level = volume.GetMasterVolumeLevelScalar()
        new_level = min(1.0, current_level + (miqdor / 100.0))
        volume.SetMasterVolumeLevelScalar(new_level, None)
        change = int((new_level - current_level) * 100)
        gui_ga_xabar_yuborish(f"🔊 Ovoz {change}% oshirildi")
        ovoz_chiqar_tez(f"Ovoz {change} foizga oshirildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Ovoz oshirilmadi: {e}", ovoz=True)
        return False

def ovoz_pasaytir(miqdor=5):
    volume = get_audio_session()
    if not volume:
        gui_ga_xabar_yuborish("❌ Ovoz boshqarib bo'lmadi", ovoz=True)
        return False
    
    try:
        current_level = volume.GetMasterVolumeLevelScalar()
        new_level = max(0.0, current_level - (miqdor / 100.0))
        volume.SetMasterVolumeLevelScalar(new_level, None)
        change = int((current_level - new_level) * 100)
        gui_ga_xabar_yuborish(f"🔉 Ovoz {change}% pasaytirildi")
        ovoz_chiqar_tez(f"Ovoz {change} foizga pasaytirildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Ovoz pasaytirilmadi: {e}", ovoz=True)
        return False

def ovoz_ochir():
    volume = get_audio_session()
    if not volume:
        gui_ga_xabar_yuborish("❌ Ovoz boshqarib bo'lmadi", ovoz=True)
        return False
    
    try:
        volume.SetMute(1, None)
        gui_ga_xabar_yuborish("🔇 Ovoz o'chirildi")
        ovoz_chiqar_tez("Ovoz o'chirildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Ovoz o'chirilmadi: {e}", ovoz=True)
        return False

def ovoz_och():
    volume = get_audio_session()
    if not volume:
        gui_ga_xabar_yuborish("❌ Ovoz boshqarib bo'lmadi", ovoz=True)
        return False
    
    try:
        volume.SetMute(0, None)
        gui_ga_xabar_yuborish("🔊 Ovoz ochildi")
        ovoz_chiqar_tez("Ovoz ochildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Ovoz ochilmadi: {e}", ovoz=True)
        return False

# ========== YouTube video boshqaruvi ==========
def youtube_video_play():
    try:
        pyautogui.press('k')
        gui_ga_xabar_yuborish("▶️ Video qo'yilmoqda")
        ovoz_chiqar_tez("Video qo'yildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish("❌ Video qo'yilmadi", ovoz=True)
        return False

def youtube_video_pause():
    try:
        pyautogui.press('k')
        gui_ga_xabar_yuborish("⏸️ Video to'xtatildi")
        ovoz_chiqar_tez("Video to'xtatildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish("❌ Video to'xtatilmadi", ovoz=True)
        return False

def youtube_video_boshla_koordinata(video_raqam=1):
    try:
        if not global_state.youtube_ochiq:
            gui_ga_xabar_yuborish("⚠️ Avval YouTube ochilishi kerak", ovoz=True)
            return False
        
        time.sleep(1.5)
        
        screen_width, screen_height = pyautogui.size()
        
        positions = {
            1: (screen_width // 4, screen_height // 3),
            2: (screen_width // 2, screen_height // 3),
            3: (3 * screen_width // 4, screen_height // 3),
            4: (screen_width // 4, screen_height // 2),
            5: (screen_width // 2, screen_height // 2),
            6: (3 * screen_width // 4, screen_height // 2),
        }
        
        x, y = positions.get(video_raqam, positions[1])
        
        pyautogui.click(x, y)
        gui_ga_xabar_yuborish(f"✅ {video_raqam}-video ochilmoqda")
        ovoz_chiqar_tez(f"{video_raqam} chi video ochildi")
        return True
        
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Video ochilmadi", ovoz=True)
        return False

# ========== Musiqa platformalari ==========
def musiqa_platform_tanlash():
    ovoz_chiqar_tez("Qaysi platformadan musiqa qidiraylik? YouTube, Yandex Music yoki Spotify?")
    
    for _ in range(2):
        javob = tingla()
        
        if not javob:
            continue
        
        if "yandex" in javob or "яндекс" in javob:
            return "yandex"
        elif "spotify" in javob:
            return "spotify"
        elif "youtube" in javob or "yutub" in javob:
            return "youtube"
    
    return "youtube"

def musiqa_qidir(query, platform="youtube"):
    try:
        if platform == "youtube":
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+music"
            gui_ga_xabar_yuborish(f"🎵 YouTube'da qidirilmoqda")
        elif platform == "yandex":
            url = f"https://music.yandex.ru/search?text={query.replace(' ', '%20')}"
            gui_ga_xabar_yuborish(f"🎵 Yandex Music'da qidirilmoqda")
        elif platform == "spotify":
            url = f"https://open.spotify.com/search/{query.replace(' ', '%20')}"
            gui_ga_xabar_yuborish(f"🎵 Spotify'da qidirilmoqda")
        else:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+music"
        
        subprocess.Popen(["start", url], shell=True)
        ovoz_chiqar_tez(f"{query} qidirildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Musiqa qidirilmadi", ovoz=True)
        return False

# ========== Qoidalarga asoslangan aniqlash ==========
def buyruqni_aniqla(matn):
    matn_lower = matn.lower().strip()
    
    # Ovoz boshqaruvi
    if "ovoz" in matn_lower:
        match = re.search(r'ovoz(?:ni)?\s+(\d+)(?:\s+qil)?', matn_lower)
        if match:
            level = int(match.group(1))
            return ("volume_set", level)
        
        match = re.search(r'ovoz(?:ni)?\s+(?:oshir|ko\'tar)(?:\s+(\d+))?', matn_lower)
        if match:
            amount = int(match.group(1)) if match.group(1) else 5
            return ("volume_up", amount)
        
        match = re.search(r'ovoz(?:ni)?\s+pasaytir(?:\s+(\d+))?', matn_lower)
        if match:
            amount = int(match.group(1)) if match.group(1) else 5
            return ("volume_down", amount)
        
        if "o'chir" in matn_lower:
            return "volume_mute"
        if "och" in matn_lower:
            return "volume_unmute"
    
    # Video raqami
    match = re.search(r'(\d+)\s*(?:-)?video', matn_lower)
    if match:
        num = int(match.group(1))
        return ("video_number", num)
    
    # Oddiy buyruqlar
    sorted_commands = sorted(buyruqlar_json.items(), key=lambda x: len(x[0]), reverse=True)
    
    for soz, buyruq in sorted_commands:
        if soz in matn_lower:
            return buyruq
    
    return "unknown"

# ========== OpenRouter AI ==========
def openrouter_ai_suhbat(matn):
    """AI integratsiya vaqtincha o'chirilgan"""
    gui_ga_xabar_yuborish("❌ AI integratsiya vaqtincha o'chirilgan", ovoz=True)
    return

# ========== Tarix saqlash ==========
def buyruqni_saqla(matn):
    try:
        with open("buyruqlar_tarixi.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {matn}\n")
    except:
        pass

# ========== Eslatmalar ==========
def eslatma_qoshish(eslatma_matni):
    try:
        sana = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open("eslatmalar.txt", "a", encoding="utf-8") as f:
            f.write(f"[{sana}] {eslatma_matni}\n")
        gui_ga_xabar_yuborish(f"✅ Eslatma saqlandi")
        ovoz_chiqar_tez("Eslatma saqlandi")
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Eslatma saqlanmadi", ovoz=True)

def eslatma_o_chirish(raqam=None):
    """Eslatmani o'chirish. raqam=None bo'lsa oxirgi eslatmani o'chiradi."""
    try:
        if not os.path.exists("eslatmalar.txt"):
            gui_ga_xabar_yuborish("📌 Eslatmalar yo'q", ovoz=True)
            return
        
        with open("eslatmalar.txt", "r", encoding="utf-8") as f:
            eslatmalar = f.readlines()
        
        if not eslatmalar:
            gui_ga_xabar_yuborish("📌 Eslatmalar yo'q", ovoz=True)
            return
        
        if raqam is not None and 1 <= raqam <= len(eslatmalar):
            o_chirilgan = eslatmalar.pop(raqam - 1).strip()
        else:
            o_chirilgan = eslatmalar.pop().strip()
        
        with open("eslatmalar.txt", "w", encoding="utf-8") as f:
            f.writelines(eslatmalar)
        
        gui_ga_xabar_yuborish(f"✅ Eslatma o'chirildi: {o_chirilgan}")
        ovoz_chiqar_tez("Eslatma o'chirildi")
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Eslatma o'chirilmadi: {e}", ovoz=True)

def eslatmalarni_o_qish():
    try:
        if not os.path.exists("eslatmalar.txt"):
            gui_ga_xabar_yuborish("📌 Eslatmalar yo'q", ovoz=True)
            return
        
        with open("eslatmalar.txt", "r", encoding="utf-8") as f:
            eslatmalar = f.readlines()
        
        if not eslatmalar:
            gui_ga_xabar_yuborish("📌 Eslatmalar yo'q", ovoz=True)
            return
        
        gui_ga_xabar_yuborish(f"📌 {len(eslatmalar)} ta eslatma bor")
        ovoz_chiqar_tez(f"Sizda {len(eslatmalar)} ta eslatma bor")
        
        for idx, eslatma in enumerate(eslatmalar[-5:], 1):
            if eslatma.strip():
                gui_ga_xabar_yuborish(f"{idx}. {eslatma.strip()}")
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Eslatmalar o'qilmadi", ovoz=True)

# ========== Buyruqni bajarish ==========
def buyruqni_tushun(matn, foydalanuvchi_ismi, ovoz_turi):
    with global_state.buyruq_bajarilmoqda_lock:
        global_state.ovoz_turi_global = ovoz_turi
        buyruqni_saqla(matn)
        
        intent = buyruqni_aniqla(matn)
        
        # Tuple (buyruq, qiymat)
        if isinstance(intent, tuple):
            buyruq, qiymat = intent
            
            if buyruq == "volume_set":
                ovoz_sozlash(qiymat)
            elif buyruq == "volume_up":
                ovoz_oshir(qiymat)
            elif buyruq == "volume_down":
                ovoz_pasaytir(qiymat)
            elif buyruq == "video_number":
                youtube_video_boshla_koordinata(qiymat)
            return
        
        gui_ga_xabar_yuborish(f"🎯 Buyruq: {intent}")
        
        # Buyruqlarni bajarish
        if intent == "open_youtube":
            subprocess.Popen(["start", "https://www.youtube.com"], shell=True)
            global_state.youtube_ochiq = True
            gui_ga_xabar_yuborish("✅ YouTube ochildi")
            ovoz_chiqar_tez("YouTube ochildi")

        elif intent == "youtube_first_video":
            subprocess.Popen(["start", "https://www.youtube.com"], shell=True)
            global_state.youtube_ochiq = True
            time.sleep(3)
            youtube_video_boshla_koordinata(1)

        elif intent == "music_search":
            platform = musiqa_platform_tanlash()
            ovoz_chiqar_tez("Qaysi musiqani qidiraylik?")
            query = tingla()
            if query:
                musiqa_qidir(query, platform)
            else:
                musiqa_qidir("lofi music", platform)

        elif intent in ["volume_mute", "volume_mute_nircmd"]:
            ovoz_ochir()
        
        elif intent in ["volume_unmute", "volume_unmute_nircmd"]:
            ovoz_och()
        
        elif intent == "play_video":
            youtube_video_play()
        
        elif intent == "pause_video":
            youtube_video_pause()

        elif intent == "time":
            current_time = time.strftime('%H:%M')
            gui_ga_xabar_yuborish(f"⏰ Hozir soat {current_time}")
            ovoz_chiqar_tez(f"Hozir soat {current_time}")
        
        elif intent == "date":
            current_date = time.strftime('%d %B %Y')
            gui_ga_xabar_yuborish(f"📅 Bugun {current_date}")
            ovoz_chiqar_tez(f"Bugun {current_date}")

        elif intent == "reminder":
            ovoz_chiqar_tez("Nima eslataylik?")
            reminder = tingla()
            if reminder:
                eslatma_qoshish(reminder)

        elif intent == "reminders":
            eslatmalarni_o_qish()

        elif intent == "delete_reminder":
            eslatma_o_chirish()

        elif intent == "open_code":
            try:
                subprocess.Popen(["code"], shell=True)
                gui_ga_xabar_yuborish("✅ VS Code ochildi")
                ovoz_chiqar_tez("VS Code ochildi")
            except:
                gui_ga_xabar_yuborish("❌ VS Code ochilmadi", ovoz=True)

        elif intent == "chat_mode":
            ovoz_chiqar_tez("AI rejimi. Nima so'rashingiz mumkin?")
            savol = tingla()
            if savol:
                openrouter_ai_suhbat(savol)

        elif intent == "open_telegram":
            try:
                subprocess.Popen(["start", "telegram:"], shell=True)
                gui_ga_xabar_yuborish("✅ Telegram ochildi")
                ovoz_chiqar_tez("Telegram ochildi")
            except:
                gui_ga_xabar_yuborish("❌ Telegram ochilmadi", ovoz=True)

        elif intent == "open_discord":
            try:
                subprocess.Popen(["start", "discord:"], shell=True)
                gui_ga_xabar_yuborish("✅ Discord ochildi")
                ovoz_chiqar_tez("Discord ochildi")
            except:
                gui_ga_xabar_yuborish("❌ Discord ochilmadi", ovoz=True)

        elif intent == "open_chrome":
            try:
                subprocess.Popen(["start", "chrome"], shell=True)
                gui_ga_xabar_yuborish("✅ Chrome ochildi")
                ovoz_chiqar_tez("Chrome ochildi")
            except:
                gui_ga_xabar_yuborish("❌ Chrome ochilmadi", ovoz=True)

        elif intent == "open_brave":
            try:
                subprocess.Popen(["start", "brave"], shell=True)
                gui_ga_xabar_yuborish("✅ Brave ochildi")
                ovoz_chiqar_tez("Brave ochildi")
            except:
                gui_ga_xabar_yuborish("❌ Brave ochilmadi", ovoz=True)

        elif intent == "weather":
            gui_ga_xabar_yuborish("🌤️ Ob-havo ma'lumoti tayyorlanmoqda...")
            ovoz_chiqar_tez("Hozircha ob-havo ma'lumoti ulanmagan")

        elif intent == "search":
            ovoz_chiqar_tez("Niman qidiraylik?")
            query = tingla()
            if query:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                subprocess.Popen(["start", url], shell=True)
                gui_ga_xabar_yuborish(f"🔍 '{query}' qidirilmoqda")
                ovoz_chiqar_tez(f"{query} qidirilmoqda")

        elif intent == "shutdown":
            gui_ga_xabar_yuborish("⚠️ Kompyuter o'chirilmoqda...")
            ovoz_chiqar_tez("Kompyuter o'chirilmoqda")
            # subprocess.run(["shutdown", "/s", "/t", "60"]) # Xavfsizlik uchun izohda

        elif intent == "restart":
            gui_ga_xabar_yuborish("🔄 Kompyuter qayta yuklanmoqda...")
            ovoz_chiqar_tez("Kompyuter qayta yuklanmoqda")
            # subprocess.run(["shutdown", "/r", "/t", "60"])

        elif intent == "lock":
            gui_ga_xabar_yuborish("🔒 Ekran qulflanmoqda...")
            ovoz_chiqar_tez("Ekran qulflanmoqda")
            os.system("rundll32.exe user32.dll,LockWorkStation")

        else:
            gui_ga_xabar_yuborish(f"❓ Buyruq tushunilmadi: {matn}", ovoz=True)

# ========== Orqa fon ==========
def fon_xizmat(foydalanuvchi_ismi, ovoz_turi, gui_callback_func=None):
    global_state.tinglash_faol = True
    global_state.ovoz_turi_global = ovoz_turi
    
    gui_bilan_integratsiya(gui_callback_func)
    gui_ga_xabar_yuborish(f"👋 Salom, {foydalanuvchi_ismi}!", ovoz=True)
    gui_ga_xabar_yuborish("🎙️ Tinglash boshlandi...")
    
    while global_state.tinglash_faol:
        try:
            buyruq = tingla()
            if buyruq and global_state.tinglash_faol:
                gui_ga_xabar_yuborish(f"📝 Buyruq: {buyruq}")
                buyruqni_tushun(buyruq, foydalanuvchi_ismi, ovoz_turi)
                time.sleep(0.5)
        except KeyboardInterrupt:
            break
        except Exception as e:
            gui_ga_xabar_yuborish(f"❌ Xatolik: {e}", ovoz=True)
            time.sleep(1)
    
    gui_ga_xabar_yuborish("🛑 Tinglash to'xtatildi", ovoz=True)

def fon_xizmat_toxtat():
    global_state.tinglash_faol = False

# ========== GUI ==========
def gui_ishga_tushir():
    foydalanuvchi_ismi = foydalanuvchi_ismi_ol()
    ovoz_turi = ovoz_turi_ol()
    
    # Windows Audio API tekshiruvi - endi pycaw ishlatiladi
    print("✅ Windows Audio API orqali ovoz boshqaruvi tayyor")
    
    try:
        import gui
        gui.gui_ishga_tushir(foydalanuvchi_ismi, ovoz_turi, fon_xizmat, gui_bilan_integratsiya)
    except ImportError as e:
        messagebox.showerror("Xatolik", f"gui.py fayli topilmadi!\n{e}")
    except Exception as e:
        messagebox.showerror("Xatolik", f"Dastur ishga tushmadi:\n{e}")

def main():
    gui_ishga_tushir()

if __name__ == "__main__":
    main()