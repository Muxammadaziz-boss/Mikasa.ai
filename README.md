# 🎙️ MIKASA AI v5.0.0 - Ultimate Level 5 Assistant

Zamonaviy ovozli yordamchi - O'zbek tilida so'zlash va buyruqlarni bajarish imkoniyati.

## ✨ Xususiyatlar

### 🎵 Audio va Ovoz

- **Mikrofon**: `sounddevice` orqali yuqori sifatli yozib olish
- **TTS**: `edge-tts` orqali tabiiy ovoz sintezi (erkak/ayol)
- **Ovoz boshqaruvi**: Windows Audio API orqali to'g'ri boshqarish

### 🖥️ Zamonaviy GUI

- **CustomTkinter**: Zamonaviy qorong'u dizayn
- **Animatsiyalar**: Yumshoq o'tishlar va effektlar
- **Real-time**: Soat va status indikatori

### 🔧 Konfiguratsiya

- **config.py**: Barcha sozlamalar birlashtirilgan
- **Logging**: Avtomatik log fayllari
- **Thread-safety**: Xavfsiz ko'p thread ishlashi

## 🚀 O'rnatish

### 1. Talablar

- **Python**: 3.11 yoki undan yuqori
- **Windows**: 10/11 (Audio API uchun)
- **Internet**: Google Speech API uchun

### 2. Virtual muhit

```bash
# Python 3.11 venv yaratish
py -3.11 -m venv .venv

# Faollashtirish
.venv\\Scripts\\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

### 3. Ishga tushirish

```bash
python main.py
```

## 📋 Kutubxonalar

### Asosiy

- `sounddevice` - Mikrofon yozib olish
- `edge-tts` - Ovoz sintezi
- `pycaw` - Windows ovoz boshqaruvi
- `customtkinter` - Zamonaviy GUI

### Qo'shimcha

- `speech_recognition` - Google API
- `pygame` - TTS audio pleyeri
- `requests` - API so'rovlari
- `pyautogui` - Avtomatizatsiya

## 🎮 Buyruqlar

### 🎵 Media

- `"youtube"` / `"yutub"` - YouTube ochish
- `"musiqa"` / `"qo'shiq"` - Musiqa qidirish
- `"video qo'y"` / `"to'xtat"` - Video boshqaruvi

### 🔊 Ovoz

- `"ovozni 50 qil"` - Ovoz darajasi
- `"ovozni oshir"` - Ovozni ko'tarish
- `"ovozni pasaytir"` - Ovozni pasaytirish
- `"o'chir"` / `"och"` - Ovoz o'chirish/ochish

### 📊 Ma'lumot

- `"vaqt"` / `"soat"` - Joriy vaqt
- `"sana"` - Bugungi sana

### 📌 Eslatmalar

- `"eslatma"` - Yangi eslatma
- `"eslatmalar"` - Barcha eslatmalar

### 🤖 AI

- `"ai"` / `"suhbat qil"` - AI bilan suhbat

### 🔧 Sistema

- `"kompyuterni o'chir"` - Kompyuterni o'chirish
- `"ekranni yop"` - Ekranni qulflash

## 🛠️ Sozlamalar

### Konfiguratsiya fayli (`config.json`)

```json
{
  "app": {
    "version": "2.2.5",
    "debug": false
  },
  "audio": {
    "sample_rate": 16000,
    "tts_voice_male": "uz-UZ-SardarNeural",
    "tts_voice_female": "uz-UZ-MadinaNeural"
  },
  "gui": {
    "theme": "dark",
    "window_size": "1100x800"
  }
}
```

### .env fayli

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-3.5-turbo
```

## 🧪 Testlash

```bash
# Barcha testlarni ishga tushirish
python test_main.py

# Ma'lum bir test
python -m unittest test_main.TestMainFunctions.test_tingla_success
```

## 📁 Fayl tuzilishi

```
Yordamchi v2.2.5/
├── main.py              # Asosiy dastur
├── gui.py               # GUI interfeysi
├── config.py            # Konfiguratsiya
├── test_main.py         # Unit testlar
├── requirements.txt     # Kutubxonalar
├── commands.json       # Buyruqlar lug'ati
├── logs/               # Log fayllari
├── foydalanuvchi_ismi.txt
├── ovoz_turi.txt
├── buyruqlar_tarixi.txt
└── eslatmalar.txt
```

## 🔍 Muammolarni hal qilish

### Umumiy xatolar

1. **Mikrofon ishlamaydi**:
   - Windows Settings → Privacy → Microphone
   - Ruxsat bering

2. **Ovoz chiqmaydi**:
   - Internet ulanishini tekshiring
   - Windows Audio xizmati ishlayotganini tekshiring

3. **Dastur ishga tushmaydi**:
   - Python 3.11 venv da ishlatilganini tekshiring
   - `pip install -r requirements.txt` qayta bajaring

### Log fayllari

- `logs/yordamchi.log` - Asosiy log
- `logs/yordamchi.log.1` - Avvalgi loglar

## 🔄 Versiyalar tarixi

### v2.2.5 (Joriy)

- ✅ CustomTkinter GUI
- ✅ edge-tts ovoz sintezi
- ✅ sounddevice mikrofon
- ✅ Windows Audio API
- ✅ Konfiguratsiya tizimi
- ✅ Thread-safety
- ✅ Unit testlar

### v1.0.0 (Eski)

- ❌ Tkinter GUI
- ❌ pyttsx3 TTS
- ❌ PyAudio mikrofon
- ❌ NirCmd ovoz boshqaruvi

## 🤝 Hissa qo'shish

1. Repozitoriyani forking qiling
2. Yangi branch yaratish: `git checkout -b feature/yangilik`
3. O'zgarishlarni qilish
4. Testlarni ishga tushirish: `python test_main.py`
5. Commit qilish: `git commit -m "Yangilik qo'shildi"`
6. Push qilish: `git push origin feature/yangilik`
7. Pull request yaratish

## 📄 Litsenziya

Bu loyiha MIT litsenziyasi ostida tarqatilgan.

## 👥 Muallif

Ovozli Yordamchi Pro - O'zbekiston uchun yaratilgan zamonaviy ovozli assistent.

---

**🎯 Maqsad**: O'zbek tilida sifatli ovozli yordamchi yaratish
