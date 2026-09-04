# 📝 O'zgarishlar Jurnali

---

## 🚀 v3.0.0 — "Aqlli Yordamchi" (2026-03-05)

### ⭐ Asosiy yangiliklar

#### 🤖 AI Agent tizimi

- **AI Engine** (`ai_engine.py`): Google Gemini va OpenRouter integratsiya
- **ReAct Agent** (`core/agent_planner.py`): Fikrlash → Harakat → Kuzatish sikli
- **14 ta Tool**: calculator, weather, web_search, translator, currency, scheduler, rag_reader, reminder, knowledge, datetime, app_control, system_info, screen_analyze, note
- **Agent Memory** (`core/agent_memory.py`): Qisqa, o'rta va uzoq muddatli xotira
- **Agent Scheduler** (`core/agent_scheduler.py`): Vaqtli vazifalar va eslatmalar
- **Plugin tizimi** (`core/agent_plugins.py`): JSON va Python plugin yuklash
- **Proactive Agent**: Salomlash va kontekstga asoslangan takliflar

#### 🧠 Aqlli algoritmlar (`core/smart_algorithms.py`)

- **Levenshtein Distance**: Noto'g'ri yozilgan buyruqlarni aniqlash
- **TF-IDF Matcher**: Matnli buyruqlarni tahlil qilish
- **Markov Chain**: Keyingi buyruqni bashorat qilish
- **LRU Cache**: Natijalarni keshlash
- **Rate Limiter**: API chaqiruvlarni cheklash
- **Priority Queue**: Buyruqlarni ustuvorlik bo'yicha bajarish

#### 🗂️ Loyiha strukturasi

- **`core/`**: 7 ta modul (agent_tools, agent_planner, agent_memory, agent_scheduler, agent_plugins, smart_algorithms, tts_manager)
- **`tests/`**: 5 ta test fayl, **108 ta unit test**
- **`data/`**: Ma'lumot fayllar (commands.json, config.json, foydalanuvchi_ismi.txt, ovoz_turi.txt)
- **`plugins/`**: Kengaytmalar uchun papka

#### 🧪 Testlash

- **108 ta unit test** — barcha modullar uchun
- **test_agent.py**: Tool, Registry, ReAct Agent, Memory testlari
- **test_agent_v2.py**: Scheduler, RAG Reader, yangi toollar testlari
- **test_agent_v3.py**: Async, Retry, Plugin, Proactive agent testlari
- **test_smart_algorithms.py**: Barcha algoritmlar uchun testlar
- **test_main.py**: Asosiy funksiyalar, config, audio testlari

---

## 🔧 v2.2.5 — "Zamonaviy Platforma" (2026-02)

### 🔊 Audio tizimi

- **PyAudio → sounddevice**: Zamonaviy mikrofon kutubxonasi
- **pyttsx3 → edge-tts**: Tabiiy ovoz sintezi (Microsoft Edge TTS)
- **NirCmd → Windows Audio API (pycaw)**: Tashqi dastur kerak emas
- **pygame**: TTS audio pleyeri

### 🖥️ GUI modernizatsiyasi

- **Tkinter → CustomTkinter**: Zamonaviy qorong'u dizayn
- **Animatsiyalar**: Yumshoq o'tishlar va effektlar
- **Responsive**: Ekran o'lchamiga moslashuvchan
- **Real-time**: Soat va status indikatori

### 🔧 Konfiguratsiya tizimi

- **config.py**: Barcha sozlamalar birlashtirilgan
- **JSON format**: O'qish va tahrirlash oson
- **Logging**: Avtomatik log fayllari aylanishi
- **Thread-safety**: `GlobalState` klassi

### 🛡️ Xavfsizlik

- **Input validation**: Kiruvchi ma'lumotlarni tekshirish
- **Safe eval**: `_calculator` da xavfsiz hisoblash
- **shell=False**: `subprocess` xavfsizligi
- **Error handling**: Barcha xatolarni to'g'ri qaytarish

---

## 📊 Versiyalar solishtiruvi

| Xususiyat       | v2.2.5 | v3.0.0                         |
| --------------- | ------ | ------------------------------ |
| Fayl soni       | ~5     | **20+**                        |
| AI integratsiya | ❌     | ✅ Gemini + OpenRouter         |
| Agent tizimi    | ❌     | ✅ ReAct Agent                 |
| Tool soni       | 0      | **14 ta**                      |
| Xotira tizimi   | ❌     | ✅ 3 darajali                  |
| Plugin tizimi   | ❌     | ✅ JSON + Python               |
| Algoritmlar     | regex  | ✅ Levenshtein, TF-IDF, Markov |
| Test soni       | ~10    | **108 ta**                     |
| Papka struktura | tekis  | ✅ core/, tests/, data/        |

---

## 🎊 Muvaffaqiyat

**v3.0.0** — O'zbek tilida ishlaydigan **aqlli, AI-quvvatli, zamonaviy** ovozli yordamchi!

**🎯 Asosiy yutuqlar:**

- ✅ AI agent tizimi to'liq ishlaydi
- ✅ 14 ta tool mavjud
- ✅ 108 ta test muvaffaqiyatli o'tdi
- ✅ Loyiha toza va tartibli
- ✅ Plugin tizimi kengaytirish uchun tayyor
