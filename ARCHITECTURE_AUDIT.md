# MIKASA AI 7.x — TO'LIQ ARXITEKTURA AUDITI VA ISHLAB CHIQARISH TAHLILI
**Hujjat kodi:** `ARCHITECTURE_AUDIT.md`  
**Loyiha:** `Muxammadaziz-boss/Mikasa.ai`  
**Tarmoq:** `dev-v7.0.0`  
**Versiya:** 7.1.0-dev  
**Sana:** 2026-09-12  
**Holat:** Phase 0 — Audit yakunlandi, Kod o'zgarishlaridan oldingi holat

---

## 1. KIRISH VA MAQSAD (EXECUTIVE SUMMARY)

Ushbu audit **Mikasa AI 7.x** loyihasini haqiqiy, professional, xavfsiz va mustaqil Windows ishchi stoli AI yordamchisiga aylantirish (Master Plan: Phases 0–27) oldidan mavjud kod bazasining to'liq tahlilidir.

### 1.1 Asosiy Maqsad
* Brauzer asosidagi vaqtinchalik yechimlar (`Chrome/Edge --app` rejimi) o'rniga haqiqiy mahalliy desktop ilova (**Tauri 2 + WebView2** asosida `Mikasa AI.exe`) yaratish.
* Python AI yadrosi (`core/api_server.py`, `core/command_dispatcher.py`, `core/ai_engine.py`, `core/agent_*.py`) va zamonaviy React/TypeScript interfeysi o'rtasida mustahkam, yuqori tezlikdagi, uzluksiz aloqani ta'minlash.
* Loyihadagi barcha qattiq kodlangan (hardcoded) yo'llarni, yadro jarayonlarini boshqarishdagi yetishmovchiliklarni (orphan process bugs), xavfsizlik zaifliklarini va texnik qarzlarni bartaraf etish.
* Eski v6 CustomTkinter GUI (`gui/` katalogi) bilan v7 zamonaviy Tauri arxitekturasini qat'iy ajratilgan holda saqlash.

---

## 2. FRONTEND ARXITEKTURASI (`mikasa-7/src`)

### 2.1 Texnologiyalar Steki
* **Kutubxonalar:** React 19.1.0, React DOM 19.1.0, TypeScript 6.0.3, Vite 8.0.16.
* **Tauri API:** `@tauri-apps/api` ^2.0, `@tauri-apps/plugin-opener` ^2.0.
* **Uslublar:** Modulli CSS (`App.css`, `index.css`, `components/*.css`).
* **Ikonkalar:** Maxsus vektorli SVG ikonkalar (`components/icons/Icons.tsx`).

### 2.2 Sahifalar va Yo'naltirish (Routing) Holati
* Yo'naltirish mexanizmi `src/App.tsx` ichida oddiy `useState<string>("/")` orqali amalga oshirilgan.
* Barcha 8 ta sahifa (`LandingPage`, `ChatPage`, `VoicePage`, `CommandsPage`, `MemoryPage`, `SchedulerPage`, `PluginsPage`, `AccountPage`) `App.tsx` da **eager loading** (to'g'ridan-to'g'ri sinxron import) orqali yuklangan:
  ```typescript
  // mikasa-7/src/App.tsx:3-10
  import { LandingPage } from "./pages/LandingPage";
  import { ChatPage } from "./pages/ChatPage";
  import { VoicePage } from "./pages/VoicePage";
  import { CommandsPage } from "./pages/CommandsPage";
  import { MemoryPage } from "./pages/MemoryPage";
  import { SchedulerPage } from "./pages/SchedulerPage";
  import { PluginsPage } from "./pages/PluginsPage";
  import { AccountPage } from "./pages/AccountPage";
  ```
  **Muammo:** Eager loading dastlabki yuklanish vaqtini (startup latency) va xotira hajmini oshiradi. `React.lazy()` va `<Suspense>` orqali yuklanishi lozim.

### 2.3 Komponentlar Tahlili
* **`AppShell` (`src/layout/AppShell.tsx`):**
  * Asosiy ramka, navigatsiya paneli (`Sidebar`) va yuqori sarlavha panelini (`TopBar`) o'z ichiga oladi.
  * Oyna boshqaruvi (`WindowControls`) sarlavha paneliga biriktirilgan.
* **`WindowControls` (`src/components/WindowControls.tsx`):**
  * Kichraytirish (`app_minimize`), kattalashtirish (`app_toggle_maximize`), va yopish (`app_close`) funksiyalarini `@tauri-apps/api/core` dagi `invoke` orqali Rust backendiga yuboradi.
  * Brauzer rejimida (`window.__TAURI_INTERNALS__` mavjud bo'lmaganda) console orqali xavfsiz fallback ishlaydi.
* **`MikasaOrb` (`src/components/MikasaOrb.tsx`):**
  * Ovoz va tizim holatini (`idle`, `listening`, `thinking`, `speaking`) vizual aks ettiruvchi interaktiv orb elementi.
* **`Command Palette` (Ctrl+K) Kamchiligi:**
  * Hozirda `App.tsx` dagi `Ctrl+K` hodisasi haqiqiy modal/dialog ochmaydi, balki shunchaki DOM dan `.landing-composer input` elementini qidirib fokus qiladi (`App.tsx:51-57`):
  ```typescript
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    const input = document.querySelector<HTMLInputElement>(".landing-composer input");
    if (input) input.focus();
  }
  ```
  Bu boshqa sahifalarda (Chat, Memory, Scheduler) ishlashda xatolik keltiradi va haqiqiy Command Palette talabiga javob bermaydi.

### 2.4 Aloqa Qatlami (`src/services/backendService.ts`)
* **REST & WebSocket Ko'prigi:**
  * Server manzili: `http://127.0.0.1:18420` va `ws://127.0.0.1:18420/api/ws`.
  * Tizim holati (`checkStatus`), chat xabarlari (`sendChatMessage`), ovozli boshqaruv (`startVoice`, `stopVoice`, `speakText`), buyruqlar, xotira, rejalashtiruvchi va sozlamalar uchun to'liq TypeScript interfeyslari mavjud.
  * WebSocket orqali jonli voqealar eshitiladi: `voice_state`, `ai_response`, `scheduler_alarm`.
  * **Kamchilik:** Reconnection (qayta ulanish) intervallari cheksiz qattiq so'rov yuborishi mumkin; backend hali to'liq yuklanmagan vaqtda foydalanuvchiga aniq yuklanish indikatori ("Backend starting...") ko'rsatilmaydi.

---

## 3. RUST TAURI QOBIG'I (`mikasa-7/src-tauri`)

### 3.1 Konfiguratsiya (`tauri.conf.json`)
* **Oyna Parametrlari:**
  * Standart o'lcham: `1280x800`, minimal o'lcham: `1024x700`.
  * `"decorations": false` — maxsus sarlavha paneli (custom titlebar) bilan ramkasiz zamonaviy dizayn.
  * `"theme": "Dark"`
* **Xavfsizlik (`security`):**
  * `"csp": null` — Content Security Policy yoqilmagan. Mahsulot darajasida xavfsiz CSP belgilanishi zarur.

### 3.2 Rust Koding va Buyruqlar (`src-tauri/src/lib.rs`)
* **Mavjud Buyruqlar:**
  * `greet`, `app_minimize`, `app_toggle_maximize`, `app_close`, `app_is_maximized`.
* **Kritik Arxitektura Kamchiliklari:**
  1. **Qattiq Kodlangan Ishchi Yo'llar (`lib.rs:71-73`, `lib.rs:82`):**
     ```rust
     let base_dir = resolved_base.unwrap_or_else(|| {
         PathBuf::from(r"D:\Ishchi stoli\Mikasa\yordamchi_7.0.0")
     });
     ...
     candidates.push(PathBuf::from(r"D:\Ishchi stoli\Mikasa\.venv\Scripts\python.exe"));
     ```
     Ushbu qatorlar ilovani boshqa kompyuterda yoki boshqa katalogda ishga tushirishni butunlay to'xtatadi.
  2. **Yadro Jarayoni Boshqaruvi va Yetim Jarayonlar (Orphan Processes):**
     * `ensure_backend_running()` funksiyasi `std::thread::spawn` orqali orqa fonda Python jarayonini ishga tushiradi (`lib.rs:87-105`), lekin qaytgan `std::process::Child` obyekti saqlanmaydi va PID qayd etilmaydi.
     * Foydalanuvchi Tauri oynasini yopganida (`app_close` yoki Alt+F4), Python jarayoni Windows xotirasida abadiy qolib ketadi (`python.exe` / `core/api_server.py`).
     * `on_window_event` yoki `RunEvent::Exit` hodisalari orqali bolalar jarayonini to'xtatish mexanizmi mavjud emas.
  3. **Port Tekshiruvi:**
     * `TcpStream::connect_timeout` orqali 18420 porti tekshiriladi, ammo u aynan Mikasa backendmi yoki boshqa dastur ekanligi `/api/status` orqali tasdiqlanmaydi.

### 3.3 Ishga Tushirish va Yig'ish Skriptlari (`mikasa-7/scripts/` & `run_desktop.js`)
1. **`run_desktop.js` (Eski va xato oqim):**
   * Chrome va Microsoft Edge brauzerlarini `--app=http://localhost:1420` parametri bilan ishga tushiradi (`run_desktop.js:65-79`).
   * **Qaror:** Ushbu oqim Phase 1 da to'liq chiqarib tashlanishi va faqat haqiqiy Tauri desktop jarayoni ishlatilishi shart.
2. **`scripts/tauri.js`:**
   * `D:\tools\w64devkit\bin` qattiq kodlangan.
   * Katalog nomida bo'sh joy (`Ishchi stoli`) bo'lgani sababli `cmd /c mklink /J "D:\Mikasa" "D:\Ishchi stoli\Mikasa"` orqali NTFS junction yaratishga urinadi.
   * **Qaror:** Dinamik yo'l aniqlash va xavfsiz argumentlar uzatish orqali to'g'rilanishi lozim.
3. **`scripts/package_release.cjs`:**
   * Tayyor release fayllarini `release/v<version>/` katalogiga yig'adi, SHA-256 hisoblaydi va `run_portable.bat` yaratadi.

---

## 4. PYTHON YADROSI ARXITEKTURASI (`core/`, `main.py`)

### 4.1 API Server (`core/api_server.py`)
* `aiohttp` kutubxonasiga asoslangan to'liq asinxron HTTP REST + WebSocket server.
* Tinglovchi port: `127.0.0.1:18420`.
* **Marshrutlar (19 ta REST + 1 ta WebSocket):**
  * Tizim: `GET /api/status`, `GET /api/ws`.
  * AI & Ovoz: `POST /api/chat`, `POST /api/chat/clear`, `POST /api/voice/start`, `POST /api/voice/stop`, `POST /api/voice/speak`.
  * Buyruqlar: `GET /api/commands`, `POST /api/commands/execute`.
  * Xotira: `GET /api/memory`, `POST /api/memory/knowledge`, `DELETE /api/memory/knowledge`.
  * Rejalashtiruvchi: `GET /api/scheduler`, `POST /api/scheduler/add`, `DELETE /api/scheduler/task`, `POST /api/scheduler/clear-completed`.
  * Plaginlar: `GET /api/plugins`, `POST /api/plugins/execute`.
  * Hisob & Sozlamalar: `GET /api/account`, `POST /api/account`.
* **Kamchilik:** `aiohttp` kutubxonasi loyiha ildizidagi `requirements.txt` faylida ko'rsatilmagan! Yangi muhitda o'rnatishda xatolik yuz beradi.

### 4.2 AI Dvigateli (`core/ai_engine.py`)
* **Modellar:** Google Gemini (`gemini-2.0-flash` / API) va OpenRouter (`google/gemini-2.0-flash-exp:free`, `openai/gpt-3.5-turbo`) integratsiyasi.
* **Mexanizm:**
  * Har bir so'rov oldidan tizim prompti (`SYSTEM_PROMPT`) orqali o'zbek tilida tabiiy javob yoki tizimli JSON buyruq (`{"type": "command", "intent": "..."}`) qaytarish talab etiladi.
  * Suhbat xotirasi (`suhbat_tarixi_gemini`, `suhbat_tarixi_openrouter`) maksimal 10 ta xabar bilan cheklangan.

### 4.3 Buyruqlar Dispatcheri (`core/command_dispatcher.py` & `main.py`)
* **Mahalliy Tezkor Bajarish:**
  * Ovoz darajasi (`volume_set`, `volume_up`, `volume_down`, `volume_mute`).
  * Ilovalarni ishga tushirish (Chrome, VS Code, Telegram, YouTube, Explorer, CMD, Task Manager, Settings).
  * Oynalarni boshqarish (`switch_window`, `close_window`, `minimize_all`, `show_desktop`).
  * Tizim apparat ma'lumotlari (`get_system_specs_summary`, `get_system_specs_detailed` — CPU, RAM, Disk, Uptime, Battery).
* **`main.py` ning Monolitligi:**
  * `main.py` 2730 qatordan iborat bo'lib, o'zida yordamchi funksiyalar, v6 GUI ulanishlari va buyruqlar mantiqini aralashtirib yuborgan.
  * `api_server.py` ba'zi joylarda `main.py` dagi funksiyalarni chaqiradi. Ushbu bog'liqliklar asta-sekin toza xizmatlarga ajratilishi kerak.

### 4.4 Agent Tizimi va Xotira
* `core/agent_memory.py`: Qisqa muddatli suhbatlar va uzoq muddatli bilimlar bazasi (`data/agent_conversations.json`, `data/agent_knowledge.json`).
* `core/agent_scheduler.py`: Vaqtga asoslangan fon eslatmalari va vazifalar (`data/scheduled_tasks.json`).
* `core/agent_tools.py`: 90 KB hajmdagi keng qamrovli tizim va yordamchi vositalar to'plami.
* `core/agents/`: Multi-agent rollari (`base_agent`, `coder_agent`, `manager_agent`, `research_agent`, `system_agent`).

### 4.5 Legacy GUI (`gui/`) Izolyatsiyasi
* `gui/` katalogi (CustomTkinter) v6 kod bazasi bo'lib, unga v7 yangilanishlarida tegilmaydi va aralashtirilmaydi. U faqat v6 zaxira GUI sifatida saqlanadi.

---

## 5. AUDIO, STT VA TTS QUVELLARI TAHLILI

### 5.1 Ovoz Yozish va VAD (`core/audio_service.py`)
* **Texnologiya:** `sounddevice` va `numpy`.
* **Xususiyat:** Statik kutish o'rniga dinamik RMS (Root Mean Square) asosidagi Voice Activity Detection (VAD).
  * Jimlik vaqti (silence timeout): `1.2` soniya.
  * Sezuvchanlik chegarasi: `0.015`.
  * Maksimal yozish davomiyligi: `10.0` soniya.

### 5.2 Nutqni Matnga Aylantirish (STT)
* **Joriy Holat:** `SpeechRecognition` kutubxonasi orqali Google Web Speech API (`recognize_google`, `language="uz-UZ"`).
* **Muammo:** Ushbu API Google ning bepul, norasmiy veb-servisiga tayanadi. Internet uzilsa yoki Google cheklov qo'ysa, nutq tanish butunlay to'xtaydi.
* **Tavsiya:** Kelgusida mahalliy Whisper (faster-whisper) yoki muqobil offline STT quvurini qo'shish.

### 5.3 Ovoz Sintezi (TTS) (`core/tts_manager.py`)
* **1-darajali (Offline / Primary):** `Silero TTS` (`v4_uz` modeli, PyTorch orqali).
  * Internet talab qilmaydi, tez va tabiiy o'zbek tili talaffuzi.
* **2-darajali (Online / Fallback):** `Edge TTS` (`uz-UZ-MadinaNeural`, `uz-UZ-SardorNeural`).
  * Yuqori sifatli Microsoft bulut sintezi, internet kerak.

---

## 6. QATTIQ KODLANGAN YO'LLAR VA PORTATIVLIK TO'SIQLARI

Audit davomida aniqlangan barcha statik va portativlikka zid yo'llar ro'yxati:

| Fayl | Qator(lar) | Qattiq Kodlangan Qiymat | Tavsiya etilgan Yechim |
| :--- | :--- | :--- | :--- |
| `mikasa-7/src-tauri/src/lib.rs` | 72 | `D:\Ishchi stoli\Mikasa\yordamchi_7.0.0` | `current_exe()` dan dinamik nisbiy yo'l |
| `mikasa-7/src-tauri/src/lib.rs` | 82 | `D:\Ishchi stoli\Mikasa\.venv\Scripts\python.exe` | Nisbiy `../../.venv` yoki tizim `python` |
| `mikasa-7/scripts/tauri.js` | 11 | `D:\tools\w64devkit\bin` | Tizim `PATH` yoki `process.env` |
| `mikasa-7/scripts/tauri.js` | 20, 26 | `D:\Mikasa`, `D:\Ishchi stoli\Mikasa` | Bo'sh joyli yo'llarni to'g'ri qo'shtirnoqlash |
| `data/config.json` | 35 | `"C:\Users\MUXAMM~1\AppData\Local\Temp"` | Dinamik `tempfile.gettempdir()` |
| `requirements.txt` | — | `aiohttp` yo'q | `aiohttp>=3.9.0` qo'shish |

---

## 7. XAVFSIZLIK VA TEXNIK QARZLAR (RISK & TECH DEBT)

1. **Jarayonlar Boshqaruvi:**
   * Tauri chiqib ketganda Python `api_server.py` fon xizmati to'xtatilmaydi. Bu xotirada "zombi" jarayonlarni to'playdi va keyingi ishga tushirishda port to'qnashuviga (port 18420 already in use) olib keladi.
2. **CORS va Tarmoq Ochiqligi:**
   * `api_server.py` dagi CORS middleware `Access-Control-Allow-Origin: *` qilib belgilangan.
   * Mahalliy brauzerda ochilgan har qanday zararli sayt `127.0.0.1:18420` portiga so'rov yuborib, foydalanuvchi tizimida buyruqlar bajarishi mumkin.
   * **Yechim:** Frontend va Backend o'rtasida bir martalik sessiya tokeni (Bearer Token / Secret Key) joriy etish.
3. **CSP (Content Security Policy):**
   * `tauri.conf.json` da CSP yo'q (`null`).
4. **Ikonkalar va UI:**
   * Matnli xabarlarda qattiq emojilar aralashgan (`✅`, `▶️`, `🔊`, `🖥️`). Master planga asosan, barcha UI ko'rinishlari zamonaviy vektor ikonkalarga asoslanishi lozim.

---

## 8. XAVFLAR REESTRI (RISK REGISTER)

| # | Xavf Tavsifi | Ehtimollik | Ta'sir | Bartaraf Etish Strategiyasi |
| :- | :--- | :---: | :---: | :--- |
| **R1** | Python backend yopilmasdan xotirada yetim qolishi | Yuqori | Yuqori | Rust `lib.rs` da Child PID saqlash va `RunEvent::Exit` da kill qilish |
| **R2** | Chrome/Edge `--app` rejimidan foydalanish | O'rta | Yuqori | `run_desktop.js` ni desktop oqimidan chiqarish, Tauri ni yagona oqim qilish |
| **R3** | Boshqa foydalanuvchi kompyuterida yo'llar topilmasligi | Yuqori | Kritik | `lib.rs` va `config.json` dagi barcha absolyut yo'llarni nisbiy qilish |
| **R4** | Yangi virtual muhitda `aiohttp` yetishmasligi | Yuqori | O'rta | `requirements.txt` ga barcha yadro bog'liqliklarini kiritish |
| **R5** | Frontend sahifalarining og'ir yuklanishi | O'rta | O'rta | React.lazy va Suspense bilan dinamik yuklash |

---

## 9. BOSQICHMA-BOSQICH AMALGA OSHIRISH REJASI (PHASES 1–27)

Master plandagi barcha bosqichlar qat'iy ketma-ketlikda bajariladi:

* **PHASE 1 — TAURI NATIVE DESKTOP:** Chrome/Edge `--app` rejimidan butunlay voz kechish; Tauri dev va build jarayonini to'liq mahalliy ishchi rejimga o'tkazish.
* **PHASE 2 — RUNTIME BACKEND SUPERVISOR:** Rust da Python jarayonini to'liq nazorat qilish (avtomatik ishga tushirish, `/api/status` orqali tayyorlikni tekshirish, dastur yopilganda jarayonni toza o'ldirish).
* **PHASE 3 — PORTABILITY & PATH REMOVAL:** Loyihadagi barcha qattiq kodlangan yo'llarni dinamik nisbiy yo'llarga almashtirish; `requirements.txt` ni to'ldirish.
* **PHASE 4 — FRONTEND SPLITTING & COMMAND PALETTE:** `React.lazy` joriy etish; haqiqiy global `Command Palette` (Ctrl+K modal) yaratish; barcha 8 ta sahifaning yuklanishini tezlashtirish.
* **PHASE 5 — UI ICON SANITIZATION:** Qolgan matnli emojilarni toza SVG vektor ikonkalar bilan almashtirish.
* **PHASE 6–10 — DESKTOP POLISH & AUDIO/SYSTEM:** Tizim tray boshqaruvi, bildirishnomalar, audio oqimi va xavfsiz IPC.
* **PHASE 11–27 — AGENT CAPABILITIES, PLUGINS & PACKAGING:** To'liq avtonom agent qobiliyatlari, Windows xizmatlari va professional MSI/NSIS reliz tayyorlash.

---

*Hujjat Phase 0 talablariga muvofiq tayyorlandi va loyiha ildiziga muhrlandi.*
