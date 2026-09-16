# 🔷 MIKASA AI v6.0.0 — Level 6 Autonomous Desktop Assistant

> **O'zbek tilidagi birinchi professional avtonom AI desktop yordamchisi**  
> Yuqori unumdorlikka ega VAD ovoz tizimi, ko'p agentli arxitektura (Multi-Agent), Raycast uslubidagi Command Center va Apple Dark Minimal zamonaviy interfeysi.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blue)](https://github.com/TomSchimansky/CustomTkinter)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows)](https://microsoft.com/windows)
[![Release](https://img.shields.io/badge/Release-v6.0.0--final-success)](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v6.0.0-final)
[![Tests](https://img.shields.io/badge/Tests-48%2F48%20Passed-brightgreen)](tests/)

---

## 🌟 6-Versiyadagi Asosiy Yangiliklar

### 1. ⚡ Dinamik VAD (Voice Activity Detection) Ovoz Xizmati
* Avvalgi qat'iy kechikishlar o'rniga dinamik ovoz faolligini aniqlash (`core/audio_service.py`).
* Foydalanuvchi gapirib bo'lgach (1.2 soniya sukunatdan so'ng) yozish darhol to'xtatiladi va tezkor ishlanadi.
* Javob qaytarish tezligi 2 barobardan ziyod oshirildi.

### 2. 🔀 Tezkor Mahalliy Buyruqlar Taqsimlagichi (`CommandDispatcher`)
* Tizim buyruqlari (ovozni boshqarish, vaqt/sana, YouTube/Google qidiruvlari, dasturlarni ochish) AI modeliga so'rov yubormasdan lahzada bajariladi.
* AI tokenlarini tejaydi va mahalliy buyruqlarni 0 kechikish bilan bajaradi.

### 3. 🛠️ Ko'p Agentli Arxitektura (Multi-Agent System)
* **ManagerAgent**: Barcha kiruvchi vazifalarni tahlil qilib, kerakli agentlarga yo'naltiruvchi orkestrator.
* **SystemAgent (DevOps)**: Kompyuterning texnik holatini (CPU, RAM, Disk), eng ko'p resurs sarflayotgan ilovalarni tahlil qilish va xavfsiz kesh tozalash.
* **ResearchAgent & CoderAgent**: Dasturlash va axborot qidirish vazifalarini alohida ixtisoslashgan holda yechish.

### 4. 🎛️ Raycast Uslubidagi Tezkor "Command Center"
* 128+ dan ortiq tizim va aqlli buyruqlar katalogi.
* Raycast darajasidagi filtrlash, klaviatura boshqaruvi va bir bosishda bajarish.
* Tezkor qidiruv, qulay toifalar va status ko'rsatkichlari.

### 5. 🖥️ Apple Dark Minimal Custom Window Chrome
* Maxsus silliq oyna sarlavhasi (Clean Titlebar) va oynani xavfsiz surish mexanizmi (GIL va thread-safe).
* Windows DWM resizing bilan mukammal uyg'unlashgan va yuqori hoshiyadagi keraksiz chiziqlardan tozalangan.
* Toza, ortiqcha elementlarsiz sarlavha paneli.

### 6. 👤 Foydalanuvchi Hisob Maydoni (Account Area)
* Sidebar pastki qismida ixcham va qulay hisob bloki: `[MA] Muxammadaziz / Hisob ›`.
* Sozlamalar va hisob boshqaruvi uchun sichqonchaning o'ng tugmasi kontekst menyusi.
* Chat muloqotida foydalanuvchi hamda Mikasa AI ning professional vektor avatarlari.

### 7. 🔔 Proaktiv Bildirishnomalar (Smooth Toast UI)
* Foydalanuvchi boshqa dasturlarda ishlayotgan paytda ham muhim taklif va hodisalar haqida ekranning pastki o'ng burchagida paydo bo'luvchi silliq xabarnomalar.

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Talablar
* **Python**: 3.11 (tavsiya etiladi)
* **OS**: Windows 10 / 11
* **Internet**: Ovozni aniqlash va AI modellar uchun

### 2. O'rnatish qadamlari
```bash
# Repozitoriyani klonlash
git clone https://github.com/Muxammadaziz-boss/Mikasa.ai.git
cd Mikasa.ai

# Virtual muhit yaratish va faollashtirish
python -m venv .venv
.venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

### 3. Konfiguratsiya
Loyiha ildizidagi `.env` faylida o'zingizning API kalitingizni ko'rsating:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openai/gpt-3.5-turbo
DEFAULT_MUSIC_PLATFORM=youtube
DEBUG=false
```

### 4. Ishga tushirish
```bash
# Asosiy GUI interfeysini ishga tushirish
python run_gui.py

# Yoki konsol orqali ishga tushirish
python main.py
```

---

## 📁 Loyiha Strukturasi

```
Mikasa.ai/
├── core/                       # Asosiy xizmatlar va aqlli tizimlar
│   ├── audio_service.py        # Modulli Audio va VAD xizmati
│   ├── command_dispatcher.py   # Tezkor buyruqlar taqsimlagichi
│   ├── agent_planner.py        # ReAct agent orkestratsiyasi
│   ├── agent_tools.py          # 29+ ta agent asboblari
│   ├── proactive_watcher.py    # Proaktiv monitoring va tavsiyalar
│   ├── smart_algorithms.py     # Markov zanjiri, Levenshtein tahlili
│   └── agents/                 # Sub-agentlar (SystemAgent, Coder, Research)
├── gui/                        # Zamonaviy CustomTkinter interfeysi
│   ├── app.py                  # Asosiy oyna va Custom Chrome
│   ├── theme.py                # Ranglar, shriftlar va vektor ikonkalar
│   ├── components.py           # NavItem, AccountRow, UserAvatar, Toast UI
│   ├── backend.py              # Asinxron BackendBridge
│   └── pages/                  # Sahifalar (Chat, Commands, Dashboard, ...)
├── tests/                      # Keng qamrovli test to'plamlari
├── data/                       # Ma'lumotlar bazasi va konfiguratsiyalar
├── run_gui.py                  # Tezkor GUI start skripti
├── main.py                     # Asosiy tizim boshqaruvchisi
├── requirements.txt            # Bog'liqliklar ro'yxati
└── README.md                   # Loyiha hujjati
```

---

## 🧪 Avtomatlashtirilgan Testlar

Loyiha to'liq avtomatlashtirilgan testlar bilan ta'minlangan:
```bash
# Barcha asosiy testlarni yurgizish
python -m unittest tests/test_v6_user_account.py tests/test_v6_window_chrome.py tests/test_v6_chat.py tests/test_v6_chat_ux.py tests/test_v6_surfaces.py tests/test_v6_final_qa.py
```
Natija: `48/48 OK` (100% barqaror).

---

## 📄 Litsenziya va Muallif

* **Muallif:** Muxammadaziz ([@Muxammadaziz-boss](https://github.com/Muxammadaziz-boss))
* **Litsenziya:** MIT License
