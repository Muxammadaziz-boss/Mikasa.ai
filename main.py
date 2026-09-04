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

load_dotenv()

# ========== Versiya ==========
VERSION = "1.3.0"
GITHUB_REPO = "https://api.github.com/repos/Muxammadaziz_boss/ovozli-yordamchi/releases/latest"

# ========== Global o'zgaruvchilar ==========
buyruq_bajarilmoqda = False
so_ngi_natija = ""
oyin_rejimi = False
ovoz_turi_global = "erkak"

# ========== pyttsx3 engine (global, xatolikni oldini oladi) ==========
_tts_engine = None

def get_tts_engine():
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty('rate', 200)
    return _tts_engine

# ========== Parolni olish ==========
def parolni_olish():
    return os.getenv("ADMIN_PAROL", "1234")

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
        "yutub och": "open_youtube",
        "birinchi video": "youtube_first_video",
        "musiqa": "music_search",
        "muzika": "music_search",
        "qo'shiq": "music_search",
        "telegram": "open_telegram",
        "vs code": "open_code",
        "visual studio code": "open_code",
        "chrome": "open_chrome",
        "brave": "open_brave",
        "discord": "open_discord",
        "tanla": "select_next_item",
        "enter": "enter",
        "havo": "weather",
        "ob-havo": "weather",
        "qidir": "search",
        "vaqt": "time",
        "soat": "time",
        "sana": "date",
        "bugun": "date",
        "eslatma": "reminder",
        "eslatmalar": "reminders",
        "o'chir": "shutdown",
        "yangila": "restart",
        "qulufla": "lock",
        "ish stoli": "desktop",
        "task menejr": "taskmgr",
        "xotira": "memory",
        "ekran rasmi": "screenshot",
        "yangi fayl": "new_file",
        "katta harf": "caps_lock",
        "backspace": "backspace",
        "tab": "tab",
        "oynani o'tkaz": "switch_window",
        "ovozni ko'tar": "volume_up",
        "ovozni pasaytir": "volume_down",
        "ovozni o'chir": "volume_mute",
        "ovozni yoq": "volume_unmute",
        "o'yin rejimini yoq": "game_mode_on",
        "o'yin rejimini o'chir": "game_mode_off",
        "youtube qidir": "youtube_search",
        "video qidir": "youtube_search",
        "yutubda qidir": "youtube_search",
        "discord xabar yubor": "discord_xabar",
        "do'stga xabar": "discord_xabar",
        "ai": "chat_mode",
        "suhbat qil": "chat_mode",
        "so'rayman": "chat_mode"
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
            print("...")
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            try:
                text = r.recognize_google(audio, language="uz-UZ")
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"Google API xatosi: {e}")
                return None
            except sr.WaitTimeoutError:
                return None
    except Exception as e:
        print("Mikrofon ishlamayapti, so'z kiriting")
        return input("So'zni kiriting: ")

# ========== Qoidalarga asoslangan aniqlash ==========
def buyruqni_aniqla(matn):
    matn_lower = matn.lower()
    for soz, buyruq in buyruqlar_json.items():
        if soz in matn_lower:
            return buyruq
    return "unknown"

# ========== Ovoz boshqaruvi ==========
def ovozni_soza(action):
    if os.name != 'nt':
        return
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        if action == "up":
            volume.VolumeStepUp(None)
        elif action == "down":
            volume.VolumeStepDown(None)
        elif action == "mute":
            volume.SetMute(1, None)
        elif action == "unmute":
            volume.SetMute(0, None)
    except Exception as e:
        print(f"Ovoz sozlamasida xatolik: {e}")

def ovoz_oshir(): ovozni_soza("up")
def ovoz_pasaytir(): ovozni_soza("down")
def ovoz_ochir(): ovozni_soza("mute")
def ovoz_och(): ovozni_soza("unmute")

# ========== O'yin rejimi ==========
def oyin_rejimini_oshir():
    global oyin_rejimi
    if os.name == 'nt':
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            from ctypes import cast, POINTER
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterScalarVolume(0.3, None)
        except:
            pass
    oyin_rejimi = True
    ovoz_chiqar("O'yin rejimi yoqildi", ovoz_turi_global)

def oyin_rejimini_yop():
    global oyin_rejimi
    if os.name == 'nt':
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            from ctypes import cast, POINTER
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterScalarVolume(1.0, None)
        except:
            pass
    oyin_rejimi = False
    ovoz_chiqar("O'yin rejimi o'chirildi", ovoz_turi_global)

# ========== AI bilan suhbat ==========
def ai_bilan_suhbat(matn, ovoz_turi):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        ovoz_chiqar("AI kaliti .env faylida yo'q", ovoz_turi)
        return
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            f"Foydalanuvchi: {matn}",
            safety_settings={
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=150,
                temperature=0.7
            )
        )
        javob = response.text.strip()
        ovoz_chiqar(javob, ovoz_turi)
    except Exception as e:
        print(f"AI xatolik: {e}")
        ovoz_chiqar("AI javob berishda xatolik yuz berdi", ovoz_turi)

# ========== YouTube qidiruv ==========
def youtube_qidir(query, ovoz_turi):
    if query:
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        subprocess.run(["start", url], shell=True)
        ovoz_chiqar(f"YouTube’da {query} bo‘yicha natijalar ochildi", ovoz_turi)
    else:
        ovoz_chiqar("Qidirish so'zi aniqlanmadi", ovoz_turi)

# ========== Tarix saqlash ==========
def buyruqni_saqla(matn):
    with open("buyruqlar_tarixi.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()}: {matn}\n")

# ========== Google AI orqali tushunish ==========
def ai_orqali_tushun(matn):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY .env faylida yo'q")
        return "unknown"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        ruxsat_etilgan = [
            "open_youtube", "youtube_first_video", "music_search", "greeting", "time", "date", "weather",
            "reminder", "reminders", "shutdown", "restart", "lock", "desktop", "taskmgr", "memory",
            "screenshot", "new_file", "caps_lock", "enter", "backspace", "tab", "switch_window",
            "volume_up", "volume_down", "volume_mute", "volume_unmute", "search", "open_discord",
            "open_telegram", "open_code", "open_chrome", "open_brave", "select_next_item", "unknown",
            "game_mode_on", "game_mode_off", "youtube_search", "discord_xabar", "chat_mode"
        ]

        prompt = f"""Siz faqat quyidagi buyruqlardan birini qaytarishingiz kerak:
{', '.join(ruxsat_etilgan)}
Foydalanuvchi so'zi: "{matn}"
Javob:"""
        
        response = model.generate_content(prompt, safety_settings={
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        }, generation_config=genai.types.GenerationConfig(
            max_output_tokens=10,
            temperature=0.1
        ))
        
        javob = response.text.strip().lower()
        javob = ''.join(ch for ch in javob if ch.isalnum() or ch == '_')
        return javob if javob in ruxsat_etilgan else "unknown"
    except Exception as e:
        print(f"AI xatolik: {e}")
        return "unknown"

# ========== Buyruqni bajarish ==========
def buyruqni_tushun(matn, foydalanuvchi_ismi, ovoz_turi):
    global buyruq_bajarilmoqda, ovoz_turi_global
    ovoz_turi_global = ovoz_turi
    buyruq_bajarilmoqda = True
    buyruqni_saqla(matn)
    
    intent = buyruqni_aniqla(matn)
    if intent == "unknown":
        intent = ai_orqali_tushun(matn)

    ovoz_chiqar(f"Buyruq aniqlandi: {intent.replace('_', ' ')}", ovoz_turi)
    
    if intent == "greeting":
        ovoz_chiqar(f"Salom, {foydalanuvchi_ismi}! Sizga qanday yordam bera olaman?", ovoz_turi)

    elif intent == "open_youtube":
        subprocess.run(["start", "https://www.youtube.com"], shell=True)
        ovoz_chiqar(f"{foydalanuvchi_ismi}, YouTube ochilyapti", ovoz_turi)

    elif intent == "youtube_first_video":
        subprocess.run(["start", "https://www.youtube.com"], shell=True)
        time.sleep(3)
        pyautogui.press('tab')
        pyautogui.press('tab')
        pyautogui.press('enter')
        ovoz_chiqar(f"{foydalanuvchi_ismi}, birinchi video ochilyapti", ovoz_turi)

    elif intent == "music_search":
        ovoz_chiqar("Qaysi musiqani qidiraylik?", ovoz_turi)
        query = tingla()
        if query:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+music"
            subprocess.run(["start", url], shell=True)
            ovoz_chiqar(f"{query} bo'yicha musiqa topildi", ovoz_turi)
        else:
            subprocess.run(["start", "https://www.youtube.com/results?search_query=lofi+music"], shell=True)
            ovoz_chiqar("Lofi musiqa qidirildi", ovoz_turi)

    elif intent == "youtube_search":
        ovoz_chiqar("Nima qidiraylik YouTube’da?", ovoz_turi)
        query = tingla()
        youtube_qidir(query, ovoz_turi)

    elif intent == "open_discord":
        subprocess.run(["start", "discord"], shell=True)
        ovoz_chiqar("Discord ochilyapti", ovoz_turi)

    elif intent == "discord_xabar":
        ovoz_chiqar("Discord ochilmoqda. Do'stingizga xabar yozishingiz mumkin.", ovoz_turi)
        subprocess.run(["start", "discord"], shell=True)

    elif intent == "open_telegram":
        subprocess.run(["start", "telegram"], shell=True)
        ovoz_chiqar("Telegram ochilyapti", ovoz_turi)

    elif intent == "open_code":
        subprocess.run(["start", "code"], shell=True)
        ovoz_chiqar("VS Code ochilyapti", ovoz_turi)

    elif intent == "open_chrome":
        subprocess.run(["start", "chrome"], shell=True)
        ovoz_chiqar("Chrome ochilyapti", ovoz_turi)

    elif intent == "open_brave":
        subprocess.run(["start", "brave"], shell=True)
        ovoz_chiqar("Brave ochilyapti", ovoz_turi)

    elif intent == "select_next_item":
        pyautogui.press('tab')
        ovoz_chiqar("Tanlandi", ovoz_turi)

    elif intent == "weather":
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            ovoz_chiqar("Ob-havo kaliti yo'q", ovoz_turi)
            return
        city = "Tashkent"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=uz"
        try:
            data = requests.get(url).json()
            temp = data["main"]["temp"]
            ovoz_chiqar(f"Hozir {city}da {temp} gradus", ovoz_turi)
        except:
            ovoz_chiqar("Ob-havo ma'lumoti olinmadi", ovoz_turi)

    elif intent == "search":
        ovoz_chiqar("Nima qidiraylik?", ovoz_turi)
        query = tingla()
        if query:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            subprocess.run(["start", url], shell=True)
            ovoz_chiqar("Natija topildi", ovoz_turi)

    elif intent == "time":
        ovoz_chiqar(f"Hozir soat {time.strftime('%H:%M')}", ovoz_turi)
    elif intent == "date":
        ovoz_chiqar(f"Bugun {time.strftime('%Y-%m-%d')}", ovoz_turi)

    elif intent == "reminder":
        ovoz_chiqar("Nima eslataylik?", ovoz_turi)
        reminder = tingla()
        if reminder:
            with open("eslatmalar.txt", "a", encoding="utf-8") as f:
                f.write(reminder + "\n")
            ovoz_chiqar(f"Eslatma saqlandi: {reminder}", ovoz_turi)

    elif intent == "reminders":
        try:
            with open("eslatmalar.txt", "r", encoding="utf-8") as f:
                reminders = f.read()
            if reminders.strip():
                ovoz_chiqar("Sizning eslatmalaringiz:", ovoz_turi)
                ovoz_chiqar(reminders, ovoz_turi)
            else:
                ovoz_chiqar("Eslatmalar yo'q", ovoz_turi)
        except FileNotFoundError:
            ovoz_chiqar("Eslatmalar fayli yo'q", ovoz_turi)

    elif intent == "shutdown":
        if parolni_tekshir():
            ovoz_chiqar("Kompyuter o'chirilmoqda", ovoz_turi)
            subprocess.run(["shutdown", "/s", "/t", "1"], shell=True)
        else:
            ovoz_chiqar("Buyruq bekor qilindi", ovoz_turi)

    elif intent == "restart":
        if parolni_tekshir():
            ovoz_chiqar("Kompyuter yangilanmoqda", ovoz_turi)
            subprocess.run(["shutdown", "/r", "/t", "1"], shell=True)
        else:
            ovoz_chiqar("Buyruq bekor qilindi", ovoz_turi)

    elif intent == "lock":
        if parolni_tekshir():
            ovoz_chiqar("Qulflanyapti", ovoz_turi)
            os.system("rundll32.exe user32.dll,LockWorkStation")
        else:
            ovoz_chiqar("Buyruq bekor qilindi", ovoz_turi)

    elif intent == "desktop":
        pyautogui.hotkey('win', 'd')
        ovoz_chiqar("Ish stoli", ovoz_turi)

    elif intent == "taskmgr":
        os.system("taskmgr")
        ovoz_chiqar("Vazifalar menejeri", ovoz_turi)

    elif intent == "memory":
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        ovoz_chiqar(f"CPU: {cpu}%, RAM: {ram}%", ovoz_turi)

    elif intent == "screenshot":
        path = f"screenshot_{int(time.time())}.png"
        pyautogui.screenshot(path)
        ovoz_chiqar("Rasm saqlandi", ovoz_turi)

    elif intent == "new_file":
        pyautogui.hotkey('ctrl', 'n')
        ovoz_chiqar("Yangi fayl", ovoz_turi)

    elif intent == "caps_lock":
        keyboard.press_and_release('caps lock')

    elif intent == "enter":
        pyautogui.press('enter')
        ovoz_chiqar("Enter bosildi", ovoz_turi)

    elif intent == "backspace":
        pyautogui.press('backspace')

    elif intent == "tab":
        pyautogui.press('tab')

    elif intent == "switch_window":
        pyautogui.hotkey('alt', 'tab')
        ovoz_chiqar("Oyna almashtirildi", ovoz_turi)

    elif intent == "volume_up":
        ovoz_oshir()
        ovoz_chiqar("Ovoz oshirildi", ovoz_turi)

    elif intent == "volume_down":
        ovoz_pasaytir()
        ovoz_chiqar("Ovoz pasaytirildi", ovoz_turi)

    elif intent == "volume_mute":
        ovoz_ochir()
        ovoz_chiqar("Ovoz o'chirildi", ovoz_turi)

    elif intent == "volume_unmute":
        ovoz_och()
        ovoz_chiqar("Ovoz ochildi", ovoz_turi)

    elif intent == "game_mode_on":
        oyin_rejimini_oshir()

    elif intent == "game_mode_off":
        oyin_rejimini_yop()

    elif intent == "chat_mode":
        ovoz_chiqar("AI rejimiga o'tildi. Nima so'rashingiz mumkin?", ovoz_turi)
        savol = tingla()
        if savol:
            ai_bilan_suhbat(savol, ovoz_turi)

    else:
        ovoz_chiqar(f"{foydalanuvchi_ismi}, buyruq tushunilmadi", ovoz_turi)
    
    buyruq_bajarilmoqda = False
    ovoz_chiqar("Buyruq bajarildi", ovoz_turi)

# ========== Orqa fon ==========
def fon_xizmat(foydalanuvchi_ismi, ovoz_turi):
    ovoz_chiqar(f"Salom, {foydalanuvchi_ismi}! Men — Yordamchingiz. Nima buyurasiz?", ovoz_turi)
    while True:
        try:
            buyruq = tingla()
            if buyruq:
                ovoz_chiqar("Buyruq qabul qilindi", ovoz_turi, kechikish=0.5)
                buyruqni_tushun(buyruq, foydalanuvchi_ismi, ovoz_turi)
        except KeyboardInterrupt:
            print("Dastur to'xtatildi")
            break
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            time.sleep(1)

# ========== Haqida va yangilanish ==========
def haqida_oynasi():
    about_win = tk.Toplevel()
    about_win.title("ℹ️ Haqida")
    about_win.geometry("400x250")
    about_win.configure(bg="#2c2f33")
    tk.Label(about_win, text="🎙️ Ovozli Yordamchi", font=("Segoe UI", 16, "bold"),
             fg="#e0e0e0", bg="#2c2f33").pack(pady=10)
    tk.Label(about_win, text=f"Versiya: v{VERSION}", font=("Segoe UI", 11),
             fg="#bbbbbb", bg="#2c2f33").pack()
    tk.Label(about_win, text="Muallif: Muxammadaziz", font=("Segoe UI", 10),
             fg="#999999", bg="#2c2f33").pack(pady=5)
    tk.Label(about_win, text="Bu dastur — ovoz orqali boshqariladigan\nyordamchi vositasi.\nYouTube, Discord, AI, tizim boshqaruvi va boshqalar.",
             font=("Segoe UI", 10), fg="#cccccc", bg="#2c2f33", justify="center").pack(pady=10)
    ttk.Button(about_win, text="GitHub", command=lambda: subprocess.run(["start", "https://github.com/Muxammadaziz-boss/Yordamchi"], shell=True)).pack(pady=5)

def yangilanishni_tekshir():
    try:
        response = requests.get(GITHUB_REPO, timeout=5)
        if response.status_code == 200:
            latest = response.json()
            latest_version = latest["tag_name"].lstrip("v")
            current = VERSION
            if latest_version != current:
                ovoz_chiqar(f"Yangi versiya mavjud: {latest_version}. Yangilash tavsiya etiladi.", ovoz_turi_global)
                messagebox.showinfo("Yangilanish", f"Yangi versiya: v{latest_version}\n\n{latest['html_url']}")
            else:
                ovoz_chiqar("Sizning dasturingiz eng so'nggi versiyada", ovoz_turi_global)
        else:
            print("Yangilanish tekshiruvi: server javob bermadi")
    except Exception as e:
        print(f"Yangilanish tekshiruvida xatolik: {e}")

# ========== Chiroyli GUI ==========
def gui_ishga_tushir():
    foydalanuvchi_ismi = foydalanuvchi_ismi_ol()
    ovoz_turi = ovoz_turi_ol()

    root = tk.Tk()
    root.title("🎙️ Ovozli Yordamchi")
    root.geometry("700x600")
    root.configure(bg="#2c2f33")
    root.resizable(True, True)

    try:
        root.iconbitmap('icon.ico')
    except:
        pass

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 10), padding=6)
    style.map("TButton",
              foreground=[('pressed', 'white'), ('active', 'white')],
              background=[('pressed', '!disabled', '#5c6bc0'), ('active', '#3949ab')],
              )

    title_label = tk.Label(
        root, text="🎙️ Ovozli Yordamchi", font=("Segoe UI", 20, "bold"),
        fg="#e0e0e0", bg="#2c2f33"
    )
    title_label.pack(pady=15)

    description = tk.Label(
        root, text=f"Salom {foydalanuvchi_ismi}! Gapirish tugmasini bosing va buyruq bering.",
        font=("Segoe UI", 12), fg="#bbbbbb", bg="#2c2f33"
    )
    description.pack(pady=5)

    text_area = scrolledtext.ScrolledText(
        root, width=80, height=20, font=("Consolas", 10),
        bg="#1e1e1e", fg="#00ff00", insertbackground="white", relief="flat"
    )
    text_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

    def tinglashni_boshla():
        threading.Thread(target=fon_xizmat, args=(foydalanuvchi_ismi, ovoz_turi), daemon=True).start()
        ovoz_chiqar("Yordamchi ishga tushdi!", ovoz_turi)

    def tarix_ko_rsat():
        try:
            with open("buyruqlar_tarixi.txt", "r", encoding="utf-8") as f:
                history = f.read()
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, history if history else "Tarix bo'sh.")
        except FileNotFoundError:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, "Tarix fayli topilmadi.")

    def eslatmalar_ko_rsat():
        try:
            with open("eslatmalar.txt", "r", encoding="utf-8") as f:
                reminders = f.read()
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, reminders if reminders else "Eslatmalar yo'q.")
        except FileNotFoundError:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, "Eslatmalar fayli yo'q.")

    def sozlamalar():
        settings_win = tk.Toplevel(root)
        settings_win.title("Sozlamalar")
        settings_win.geometry("400x420")
        settings_win.configure(bg="#2c2f33")
        
        tk.Label(settings_win, text="Sozlamalar", font=("Segoe UI", 16, "bold"), 
                fg="#e0e0e0", bg="#2c2f33").pack(pady=10)
        
        def ismni_ozgartir():
            new_name = simpledialog.askstring("Ism", "Yangi ismingizni kiriting:")
            if new_name:
                with open("foydalanuvchi_ismi.txt", "w", encoding="utf-8") as f:
                    f.write(new_name)
                messagebox.showinfo("Bajarildi", f"Ism {new_name} ga o'zgartirildi!")
                settings_win.destroy()
                root.destroy()
                gui_ishga_tushir()
        
        def ovozni_ozgartir():
            current_voice = ovoz_turi_ol()
            new_voice = "ayol" if current_voice == "erkak" else "erkak"
            with open("ovoz_turi.txt", "w", encoding="utf-8") as f:
                f.write(new_voice)
            messagebox.showinfo("Bajarildi", f"Ovoz {new_voice} ga o'zgartirildi!")
            settings_win.destroy()
            root.destroy()
            gui_ishga_tushir()
        
        def parolni_ozgartir():
            new_pass = simpledialog.askstring("Parol", "Yangi parolni kiriting:", show='*')
            if new_pass:
                from dotenv import set_key
                set_key(".env", "ADMIN_PAROL", new_pass)
                messagebox.showinfo("Bajarildi", "Parol yangilandi!")
        
        tk.Button(settings_win, text="Ismni o'zgartirish", command=ismni_ozgartir,
                 bg="#3949ab", fg="white", font=("Segoe UI", 10)).pack(pady=8)
        tk.Button(settings_win, text="Ovoz turini o'zgartirish", command=ovozni_ozgartir,
                 bg="#3949ab", fg="white", font=("Segoe UI", 10)).pack(pady=8)
        tk.Button(settings_win, text="Parolni o'zgartirish", command=parolni_ozgartir,
                 bg="#3949ab", fg="white", font=("Segoe UI", 10)).pack(pady=8)
        tk.Button(settings_win, text="ℹ️ Haqida", command=haqida_oynasi,
                 bg="#3949ab", fg="white", font=("Segoe UI", 10)).pack(pady=8)
        tk.Button(settings_win, text="🔄 Yangilanishni tekshir", 
                 command=lambda: threading.Thread(target=yangilanishni_tekshir, daemon=True).start(),
                 bg="#4caf50", fg="white", font=("Segoe UI", 10)).pack(pady=8)
        
        def fayllarni_tozala():
            for file in ["buyruqlar_tarixi.txt", "eslatmalar.txt"]:
                if os.path.exists(file):
                    open(file, 'w').close()
            messagebox.showinfo("Bajarildi", "Tarix va eslatmalar tozalandi!")

        tk.Button(settings_win, text="Tarix va eslatmalarni tozalash", command=fayllarni_tozala,
                 bg="#e53935", fg="white", font=("Segoe UI", 10)).pack(pady=10)

    button_frame = tk.Frame(root, bg="#2c2f33")
    button_frame.pack(pady=15)

    ttk.Button(button_frame, text="▶️ Boshlash", command=tinglashni_boshla).grid(row=0, column=0, padx=10)
    ttk.Button(button_frame, text="📜 Tarix", command=tarix_ko_rsat).grid(row=0, column=1, padx=10)
    ttk.Button(button_frame, text="📌 Eslatmalar", command=eslatmalar_ko_rsat).grid(row=0, column=2, padx=10)
    ttk.Button(button_frame, text="⚙️ Sozlamalar", command=sozlamalar).grid(row=0, column=3, padx=10)

    status_label = tk.Label(root, text="Tayyor", font=("Segoe UI", 9), 
                           fg="#bbbbbb", bg="#2c2f33")
    status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    root.mainloop()

# ========== Asosiy qism ==========
if __name__ == "__main__":
    gui_ishga_tushir()