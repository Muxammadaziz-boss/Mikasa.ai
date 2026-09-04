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

# ========== Ovozli javob berish ==========
def ovoz_chiqar(text, ovoz_turi="erkak"):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if ovoz_turi == "ayol" and len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    else:
        engine.setProperty('voice', voices[0].id)
    engine.say(text)
    engine.runAndWait()

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
    if os.path.exists("commands.json"):
        with open("commands.json", "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print("commands.json fayli topilmadi!")
        return {}

buyruqlar_json = buyruqlar_json_ol()

# ========== Ovozni aniqlash ==========
def tingla():
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language="uz-UZ")
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"Google API xatosi: {e}")
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
        model = genai.GenerativeModel('gemini-flash-latest')

        ruxsat_etilgan = [
            "open_youtube", "youtube_first_video", "music_search", "greeting", "time", "date", "weather",
            "reminder", "reminders", "shutdown", "restart", "lock", "desktop", "taskmgr", "memory",
            "screenshot", "new_file", "caps_lock", "enter", "backspace", "tab", "switch_window",
            "volume_up", "volume_down", "volume_mute", "volume_unmute", "search", "open_discord",
            "open_telegram", "open_code", "open_chrome", "open_brave", "select_next_item", "unknown"
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
        })
        javob = response.text.strip().lower()
        javob = ''.join(ch for ch in javob if ch.isalnum() or ch == '_')
        return javob if javob in ruxsat_etilgan else "unknown"
    except Exception as e:
        print(f"AI xatolik: {e}")
        return "unknown"

# ========== Buyruqni bajarish ==========
def buyruqni_tushun(matn, foydalanuvchi_ismi, ovoz_turi):
    buyruqni_saqla(matn)
    intent = buyruqni_aniqla(matn)
    if intent == "unknown":
        intent = ai_orqali_tushun(matn)

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

    elif intent == "open_discord":
        subprocess.run(["start", "https://discord.com"], shell=True)
        ovoz_chiqar("Discord ochilyapti", ovoz_turi)
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
        try:
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if not api_key:
                ovoz_chiqar("Ob-havo kaliti yo'q", ovoz_turi)
                return
            city = "Tashkent"
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=uz"
            data = requests.get(url).json()
            temp = data["main"]["temp"]
            ovoz_chiqar(f"Hozir {city}da {temp} gradus", ovoz_turi)
        except Exception as e:
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
        ovoz_chiqar("Kompyuter o'chirilmoqda", ovoz_turi)
        subprocess.run(["shutdown", "/s", "/t", "1"], shell=True)
    elif intent == "restart":
        ovoz_chiqar("Kompyuter yangilanmoqda", ovoz_turi)
        subprocess.run(["shutdown", "/r", "/t", "1"], shell=True)
    elif intent == "lock":
        ovoz_chiqar("Qulflanyapti", ovoz_turi)
        os.system("rundll32.exe user32.dll,LockWorkStation")
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

    else:
        ovoz_chiqar(f"{foydalanuvchi_ismi}, buyruq tushunilmadi", ovoz_turi)

# ========== Orqa fon ==========
def fon_xizmat(foydalanuvchi_ismi, ovoz_turi):
    ovoz_chiqar(f"Salom, {foydalanuvchi_ismi}! Men — Yordamchingiz. Nima buyurasiz?", ovoz_turi)
    while True:
        buyruq = tingla()
        if buyruq:
            buyruqni_tushun(buyruq, foydalanuvchi_ismi, ovoz_turi)

# ========== Chiroyli GUI ==========
def gui_ishga_tushir():
    foydalanuvchi_ismi = foydalanuvchi_ismi_ol()
    ovoz_turi = ovoz_turi_ol()

    root = tk.Tk()
    root.title("🎙️ Ovozli Yordamchi")
    root.geometry("600x500")
    root.configure(bg="#2c2f33")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 10), padding=6)
    style.map("TButton",
              foreground=[('pressed', 'white'), ('active', 'white')],
              background=[('pressed', '!disabled', '#5c6bc0'), ('active', '#3949ab')],
              )

    title_label = tk.Label(
        root, text="Ovozli Yordamchi", font=("Segoe UI", 18, "bold"),
        fg="#e0e0e0", bg="#2c2f33"
    )
    title_label.pack(pady=15)

    text_area = scrolledtext.ScrolledText(
        root, width=70, height=18, font=("Consolas", 10),
        bg="#1e1e1e", fg="#00ff00", insertbackground="white", relief="flat"
    )
    text_area.pack(padx=20, pady=10)

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

    button_frame = tk.Frame(root, bg="#2c2f33")
    button_frame.pack(pady=15)

    btn_start = ttk.Button(button_frame, text="▶️ Boshlash", command=tinglashni_boshla)
    btn_start.grid(row=0, column=0, padx=10)

    btn_history = ttk.Button(button_frame, text="📜 Tarix", command=tarix_ko_rsat)
    btn_history.grid(row=0, column=1, padx=10)

    btn_reminders = ttk.Button(button_frame, text="📌 Eslatmalar", command=eslatmalar_ko_rsat)
    btn_reminders.grid(row=0, column=2, padx=10)

    root.mainloop()

# ========== Asosiy qism ==========
if __name__ == "__main__":
    gui_ishga_tushir()  