# ========== main.py ===============================
# ========== Ogohlantirishlarni yashirish ==========
import os
import logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('absl').setLevel(logging.ERROR)
logging.getLogger('google.auth').setLevel(logging.ERROR)
logging.getLogger('google.auth.transport.requests').setLevel(logging.ERROR)

# ========== Asosiy importlar ==========
import speech_recognition as sr
import pyttsx3
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
import google.generativeai as genai
import re

load_dotenv()

# ========== Versiya ==========
VERSION = "2.0.0"
GITHUB_REPO = "https://api.github.com/repos/Muxammadaziz_boss/ovozli-yordamchi/releases/latest"

# ========== Global o'zgaruvchilar ==========
buyruq_bajarilmoqda = False
so_ngi_natija = ""
oyin_rejimi = False
ovoz_turi_global = "erkak"
gui_callback = None
youtube_ochiq = False
brauzer_turi = "chrome"  # chrome, brave, firefox

# ========== GUI bilan integratsiya ==========
def gui_bilan_integratsiya(callback_func):
    """GUI dan kelgan callback funksiyasini saqlash"""
    global gui_callback
    gui_callback = callback_func

def gui_ga_xabar_yuborish(xabar):
    """GUI ga xabar yuborish"""
    if gui_callback:
        try:
            gui_callback(xabar)
        except:
            print(xabar)
    else:
        print(xabar)

# ========== pyttsx3 engine ==========
_tts_engine = None

def get_tts_engine():
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty('rate', 200)
    return _tts_engine

# ========== Parolni olish ==========
def parolni_olish():
    return os.getenv("ADMIN_PAROL", "4881")

def parolni_tekshir():
    to_gri_parol = parolni_olish()
    ovoz_chiqar("Parolni ayting", ovoz_turi_global)
    kiritilgan = tingla()
    if kiritilgan and kiritilgan.replace(" ", "") == to_gri_parol:
        return True
    ovoz_chiqar("Noto'g'ri parol", ovoz_turi_global)
    return False

# ========== Ovozli javob berish ==========
def ovoz_chiqar(text, ovoz_turi="erkak", kechikish=0):
    def _ijro_et():
        global so_ngi_natija
        try:
            gui_ga_xabar_yuborish(text)
            
            engine = get_tts_engine()
            voices = engine.getProperty('voices')
            if ovoz_turi == "ayol" and len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
            else:
                engine.setProperty('voice', voices[0].id)
            engine.say(text)
            engine.runAndWait()
            so_ngi_natija = text
        except Exception as e:
            print(f"Ovoz chiqarishda xatolik: {e}")
            gui_ga_xabar_yuborish(f"Xatolik: {e}")
    
    threading.Thread(target=_ijro_et, daemon=True).start()
    if kechikish > 0:
        time.sleep(kechikish)

# ========== Foydalanuvchi ma'lumotlarini olish ==========
def foydalanuvchi_ismi_ol():
    if os.path.exists("foydalanuvchi_ismi.txt"):
        with open("foydalanuvchi_ismi.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        root = tk.Tk()
        root.withdraw()
        ism = simpledialog.askstring("Ism", "Iltimos, ismingizni kiriting:")
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
        "havo": "weather",
        "qidir": "search",
        "vaqt": "time",
        "sana": "date",
        "eslatma": "reminder",
        "eslatmalar": "reminders",
        "eslatmani o'chir": "delete_reminder",
        "o'chir": "shutdown",
        "yangila": "restart",
        "qulufla": "lock",
        "ovozni ko'tar": "volume_up_nircmd",
        "ovozni pasaytir": "volume_down_nircmd",
        "ovozni o'chir": "volume_mute_nircmd",
        "ovozni och": "volume_unmute_nircmd",
        "video qo'y": "play_video",
        "to'xtat": "pause_video",
        "pauza": "pause_video",
        "ai": "chat_mode",
        "suhbat qil": "chat_mode"
    }

    if os.path.exists("commands.json"):
        with open("commands.json", "r", encoding="utf-8") as f:
            existing = json.load(f)
            for k, v in default_commands.items():
                if k not in existing:
                    existing[k] = v
            return existing
    else:
        with open("commands.json", "w", encoding="utf-8") as f:
            json.dump(default_commands, f, ensure_ascii=False, indent=2)
        return default_commands

buyruqlar_json = buyruqlar_json_ol()

# ========== Ovozni aniqlash ==========
def tingla():
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            gui_ga_xabar_yuborish("🎤 Tinglanmoqda...")
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            try:
                text = r.recognize_google(audio, language="uz-UZ")
                gui_ga_xabar_yuborish(f"🗣️ Siz aytdingiz: {text}")
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                gui_ga_xabar_yuborish(f"❌ Google API xatosi: {e}")
                return None
            except sr.WaitTimeoutError:
                return None
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Mikrofon xatosi: {e}")
        return None

# ========== NirCmd orqali ovoz boshqaruvi ==========
def nircmd_ovoz_sozlash(level):
    """NirCmd orqali ovoz sozlash (0-100%)"""
    try:
        # 0-100% ni 0-65535 ga aylantirish
        volume = int((level / 100) * 65535)
        subprocess.run(["nircmd.exe", "setsysvolume", str(volume)], 
                      shell=True, check=False, capture_output=True)
        gui_ga_xabar_yuborish(f"🔊 Ovoz {level}% ga o'rnatildi")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ NirCmd xatolik: {e}")
        return False

def nircmd_ovoz_oshir(miqdor=5):
    """Ovozni belgilangan miqdorda oshirish"""
    try:
        change = int((miqdor / 100) * 65535)
        subprocess.run(["nircmd.exe", "changesysvolume", str(change)], 
                      shell=True, check=False, capture_output=True)
        gui_ga_xabar_yuborish(f"🔊 Ovoz {miqdor}% oshirildi")
        ovoz_chiqar(f"Ovoz {miqdor} foizga oshirildi", ovoz_turi_global)
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ NirCmd xatolik: {e}")
        return False

def nircmd_ovoz_pasaytir(miqdor=5):
    """Ovozni belgilangan miqdorda pasaytirish"""
    try:
        change = int((miqdor / 100) * 65535)
        subprocess.run(["nircmd.exe", "changesysvolume", f"-{change}"], 
                      shell=True, check=False, capture_output=True)
        gui_ga_xabar_yuborish(f"🔉 Ovoz {miqdor}% pasaytirildi")
        ovoz_chiqar(f"Ovoz {miqdor} foizga pasaytirildi", ovoz_turi_global)
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ NirCmd xatolik: {e}")
        return False

def nircmd_ovoz_ochir():
    """Ovozni mute qilish"""
    try:
        subprocess.run(["nircmd.exe", "mutesysvolume", "1"], 
                      shell=True, check=False, capture_output=True)
        gui_ga_xabar_yuborish("🔇 Ovoz o'chirildi (mute)")
        ovoz_chiqar("Ovoz o'chirildi", ovoz_turi_global)
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ NirCmd xatolik: {e}")
        return False

def nircmd_ovoz_och():
    """Ovozni unmute qilish"""
    try:
        subprocess.run(["nircmd.exe", "mutesysvolume", "0"], 
                      shell=True, check=False, capture_output=True)
        gui_ga_xabar_yuborish("🔊 Ovoz ochildi (unmute)")
        ovoz_chiqar("Ovoz ochildi", ovoz_turi_global)
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ NirCmd xatolik: {e}")
        return False

# ========== YouTube video boshqaruvi ==========
def youtube_video_play_pause():
    """YouTube videoni play/pause qilish (K tugmasi)"""
    try:
        pyautogui.press('k')
        gui_ga_xabar_yuborish("▶️ Video play/pause")
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Xatolik: {e}")
        return False

def youtube_video_play():
    """YouTube videoni play qilish"""
    try:
        pyautogui.press('k')
        gui_ga_xabar_yuborish("▶️ Video ijro etilmoqda")
        ovoz_chiqar("Video qo'yildi", ovoz_turi_global)
        return True
    except Exception as e:
        return False

def youtube_video_pause():
    """YouTube videoni pause qilish"""
    try:
        pyautogui.press('k')
        gui_ga_xabar_yuborish("⏸️ Video to'xtatildi")
        ovoz_chiqar("Video to'xtatildi", ovoz_turi_global)
        return True
    except Exception as e:
        return False

def youtube_video_boshla_koordinata(video_raqam=1):
    """YouTube'da video raqami bo'yicha ochish"""
    global youtube_ochiq
    try:
        if not youtube_ochiq:
            gui_ga_xabar_yuborish("❌ Avval YouTube'ni oching")
            ovoz_chiqar("Avval YouTube'ni oching", ovoz_turi_global)
            return False
        
        time.sleep(1)
        
        # Ekran o'lchamiga qarab koordinatalarni sozlash
        screen_width, screen_height = pyautogui.size()
        
        # Video joylashuvini hisoblash (qatorlar bo'yicha)
        if video_raqam == 1:
            x, y = screen_width // 4, screen_height // 4
        elif video_raqam == 2:
            x, y = screen_width // 2, screen_height // 4
        elif video_raqam == 3:
            x, y = 3 * screen_width // 4, screen_height // 4
        elif video_raqam == 4:
            x, y = screen_width // 4, screen_height // 2
        elif video_raqam == 5:
            x, y = screen_width // 2, screen_height // 2
        else:
            x, y = 3 * screen_width // 4, screen_height // 2
        
        pyautogui.click(x, y)
        gui_ga_xabar_yuborish(f"✅ {video_raqam}-video ochilyapti")
        ovoz_chiqar(f"{video_raqam}-video ochilyapti", ovoz_turi_global)
        return True
        
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Xatolik: {e}")
        return False

# ========== Musiqa platformalari ==========
def musiqa_platform_tanlash():
    """Foydalanuvchiga musiqa platformasini tanlash imkonini berish"""
    ovoz_chiqar("Qaysi platformadan musiqa qidiraylik? YouTube, Yandex Music yoki Spotify?", ovoz_turi_global)
    javob = tingla()
    
    if not javob:
        return "youtube"  # default
    
    javob = javob.lower()
    if "yandex" in javob:
        return "yandex"
    elif "spotify" in javob:
        return "spotify"
    else:
        return "youtube"

def musiqa_qidir(query, platform="youtube"):
    """Turli platformalarda musiqa qidirish"""
    try:
        if platform == "youtube":
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+music"
            ovoz_chiqar(f"YouTube'da {query} qidirilmoqda", ovoz_turi_global)
        elif platform == "yandex":
            url = f"https://music.yandex.ru/search?text={query.replace(' ', '%20')}"
            ovoz_chiqar(f"Yandex Music'da {query} qidirilmoqda", ovoz_turi_global)
        elif platform == "spotify":
            url = f"https://open.spotify.com/search/{query.replace(' ', '%20')}"
            ovoz_chiqar(f"Spotify'da {query} qidirilmoqda", ovoz_turi_global)
        else:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+music"
        
        subprocess.run(["start", url], shell=True)
        gui_ga_xabar_yuborish(f"🎵 {platform.upper()}'da musiqa qidirildi")
        time.sleep(1)
        ovoz_chiqar("Musiqa topildi va ochildi", ovoz_turi_global)
        return True
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Xatolik: {e}")
        return False

# ========== Qoidalarga asoslangan aniqlash ==========
def buyruqni_aniqla(matn):
    matn_lower = matn.lower()
    
    # Ovoz boshqaruvi (raqamli)
    if "ovoz" in matn_lower:
        # "ovozni 50 qil" yoki "ovoz 50"
        match = re.search(r'ovoz(?:ni)?\s+(\d+)', matn_lower)
        if match:
            level = int(match.group(1))
            return ("volume_set", level)
        
        # "ovozni oshir 5" yoki "ovozni ko'tar 10"
        match = re.search(r'ovoz(?:ni)?\s+(?:oshir|ko\'tar)\s+(\d+)', matn_lower)
        if match:
            amount = int(match.group(1))
            return ("volume_up", amount)
        
        # "ovozni pasaytir 5"
        match = re.search(r'ovoz(?:ni)?\s+pasaytir\s+(\d+)', matn_lower)
        if match:
            amount = int(match.group(1))
            return ("volume_down", amount)
    
    # Video raqami
    match = re.search(r'(\d+)\s*(?:-)?video', matn_lower)
    if match:
        num = int(match.group(1))
        return ("video_number", num)
    
    # Oddiy buyruqlar
    for soz, buyruq in buyruqlar_json.items():
        if soz in matn_lower:
            return buyruq
    
    return "unknown"

# ========== OpenRouter AI ==========
def openrouter_ai_suhbat(matn, ovoz_turi):
    """OpenRouter API orqali GPT bilan suhbat"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo-instruct")
    
    if not api_key:
        ovoz_chiqar("OpenRouter API kaliti topilmadi", ovoz_turi)
        return
    
    try:
        gui_ga_xabar_yuborish(f"🤖 AI ishlamoqda...")
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Siz yordamchi assistentsiz. Qisqa va aniq javob bering."},
                {"role": "user", "content": matn}
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            javob = data['choices'][0]['message']['content'].strip()
            gui_ga_xabar_yuborish(f"🤖 AI: {javob}")
            ovoz_chiqar(javob, ovoz_turi)
        else:
            ovoz_chiqar("AI javob berishda xatolik", ovoz_turi)
            
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ AI xatolik: {e}")
        ovoz_chiqar("AI bilan suhbatda xatolik", ovoz_turi)

# ========== Tarix saqlash ==========
def buyruqni_saqla(matn):
    with open("buyruqlar_tarixi.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {matn}\n")

# ========== Eslatmalar ==========
def eslatma_qoshish(eslatma_matni, ovoz_turi):
    try:
        sana = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open("eslatmalar.txt", "a", encoding="utf-8") as f:
            f.write(f"[{sana}] {eslatma_matni}\n")
        ovoz_chiqar(f"Eslatma saqlandi", ovoz_turi)
        gui_ga_xabar_yuborish(f"✅ Eslatma saqlandi: {eslatma_matni}")
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Xatolik: {e}")

def eslatmalarni_o_qish(ovoz_turi):
    try:
        if not os.path.exists("eslatmalar.txt"):
            ovoz_chiqar("Eslatmalar yo'q", ovoz_turi)
            return
        
        with open("eslatmalar.txt", "r", encoding="utf-8") as f:
            eslatmalar = f.readlines()
        
        if not eslatmalar:
            ovoz_chiqar("Eslatmalar yo'q", ovoz_turi)
            return
        
        ovoz_chiqar(f"Sizda {len(eslatmalar)} ta eslatma bor", ovoz_turi)
        for idx, eslatma in enumerate(eslatmalar, 1):
            if eslatma.strip():
                gui_ga_xabar_yuborish(f"{idx}. {eslatma.strip()}")
                
    except Exception as e:
        gui_ga_xabar_yuborish(f"❌ Xatolik: {e}")

# ========== Buyruqni bajarish ==========
def buyruqni_tushun(matn, foydalanuvchi_ismi, ovoz_turi):
    global buyruq_bajarilmoqda, ovoz_turi_global, youtube_ochiq
    ovoz_turi_global = ovoz_turi
    buyruq_bajarilmoqda = True
    buyruqni_saqla(matn)
    
    intent = buyruqni_aniqla(matn)
    
    # Tuple (buyruq, qiymat)
    if isinstance(intent, tuple):
        buyruq, qiymat = intent
        
        if buyruq == "volume_set":
            nircmd_ovoz_sozlash(qiymat)
            ovoz_chiqar(f"Ovoz {qiymat} foizga o'rnatildi", ovoz_turi)
        
        elif buyruq == "volume_up":
            nircmd_ovoz_oshir(qiymat)
        
        elif buyruq == "volume_down":
            nircmd_ovoz_pasaytir(qiymat)
        
        elif buyruq == "video_number":
            youtube_video_boshla_koordinata(qiymat)
        
        buyruq_bajarilmoqda = False
        gui_ga_xabar_yuborish("✅ Buyruq bajarildi!")
        ovoz_chiqar("Bajarildi", ovoz_turi)
        return
    
    gui_ga_xabar_yuborish(f"🎯 Buyruq: {intent}")
    
    if intent == "open_youtube":
        subprocess.run(["start", "https://www.youtube.com"], shell=True)
        youtube_ochiq = True
        ovoz_chiqar("YouTube ochilyapti", ovoz_turi)
        gui_ga_xabar_yuborish("✅ YouTube ochildi")

    elif intent == "youtube_first_video":
        subprocess.run(["start", "https://www.youtube.com"], shell=True)
        youtube_ochiq = True
        time.sleep(3)
        youtube_video_boshla_koordinata(1)

    elif intent == "music_search":
        platform = musiqa_platform_tanlash()
        ovoz_chiqar("Qaysi musiqani qidiraylik?", ovoz_turi)
        query = tingla()
        if query:
            musiqa_qidir(query, platform)
        else:
            musiqa_qidir("lofi music", platform)

    elif intent == "volume_up_nircmd":
        nircmd_ovoz_oshir(5)
    
    elif intent == "volume_down_nircmd":
        nircmd_ovoz_pasaytir(5)
    
    elif intent == "volume_mute_nircmd":
        nircmd_ovoz_ochir()
    
    elif intent == "volume_unmute_nircmd":
        nircmd_ovoz_och()
    
    elif intent == "play_video":
        youtube_video_play()
    
    elif intent == "pause_video":
        youtube_video_pause()

    elif intent == "time":
        ovoz_chiqar(f"Hozir soat {time.strftime('%H:%M')}", ovoz_turi)
    
    elif intent == "date":
        ovoz_chiqar(f"Bugun {time.strftime('%Y-%m-%d')}", ovoz_turi)

    elif intent == "reminder":
        ovoz_chiqar("Nima eslataylik?", ovoz_turi)
        reminder = tingla()
        if reminder:
            eslatma_qoshish(reminder, ovoz_turi)

    elif intent == "reminders":
        eslatmalarni_o_qish(ovoz_turi)

    elif intent == "chat_mode":
        ovoz_chiqar("AI rejimi. Nima so'rashingiz mumkin?", ovoz_turi)
        savol = tingla()
        if savol:
            openrouter_ai_suhbat(savol, ovoz_turi)

    else:
        ovoz_chiqar("Buyruq tushunilmadi", ovoz_turi)
    
    buyruq_bajarilmoqda = False
    gui_ga_xabar_yuborish("✅ Buyruq bajarildi!")
    ovoz_chiqar("Bajarildi", ovoz_turi)

# ========== Orqa fon ==========
def fon_xizmat(foydalanuvchi_ismi, ovoz_turi, gui_callback_func=None):
    ovoz_chiqar(f"Salom, {foydalanuvchi_ismi}! Men — Yordamchingiz.", ovoz_turi)
    while True:
        try:
            buyruq = tingla()
            if buyruq:
                gui_ga_xabar_yuborish(f"📝 Buyruq: {buyruq}")
                buyruqni_tushun(buyruq, foydalanuvchi_ismi, ovoz_turi)
        except KeyboardInterrupt:
            break
        except Exception as e:
            gui_ga_xabar_yuborish(f"❌ Xatolik: {e}")
            time.sleep(1)

# ========== GUI ==========
def gui_ishga_tushir():
    foydalanuvchi_ismi = foydalanuvchi_ismi_ol()
    ovoz_turi = ovoz_turi_ol()
    
    try:
        import gui
        gui.gui_ishga_tushir(foydalanuvchi_ismi, ovoz_turi, fon_xizmat)
    except ImportError:
        messagebox.showerror("Xatolik", "gui.py fayli topilmadi!")

if __name__ == "__main__":
    gui_ishga_tushir()