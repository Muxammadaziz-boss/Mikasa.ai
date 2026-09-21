# MIKASA AI 8.x — TO'LIQ ARXITEKTURA AUDITI VA ISHLAB CHIQARISH TAHLILI
**Hujjat kodi:** `ARCHITECTURE_AUDIT.md`  
**Loyiha:** `Muxammadaziz-boss/Mikasa.ai`  
**Tarmoq:** `dev-v8.0.0`  
**Versiya:** 8.0.0 (Production Release)  
**Sana:** 2026-09-21  
**Holat:** Phase 48 — Rasmiy Reliz Yakunlandi, 100% Sinovdan O'tgan Production Arxitekturasi

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

## 10. POST-PHASE-27 AUDIT & PRODUCTION RELEASE CANDIDATE (RC) STATUS

**Holat:** `v7.1.0-RC1` (Branch: `dev-v7.0.0`)  
**Yakunlangan sana:** 2026-09-13  
**Baho:** Production-Ready Release Candidate

### 10.1 Hal Qilingan Texnik Qarzlar va Arxitektura Natijalari

1. **Native Desktop Windowing & Supervisor (Phase 1, 2, 26, Hardening Pass):**
   - Brauzer yoki `Chrome/Edge --app` rejimiga bog'liqlik butunlay yo'q qilindi. Ilova native **Tauri 2.0 (x64)** qobig'ida ishlaydi.
   - Frontend assetlari (`dist/`) to'liq `.exe` binar fayli ichiga joylandi (`beforeBuildCommand` orqali to'g'ridan-to'g'ri bog'langan).
   - Rust supervisor (`mikasa-7/src-tauri/src/lib.rs`) o'ziga tegishli backend bolalar jarayonini (`state.backend_child`) kuzatadi, `child.try_wait()` orqali kutilmagan to'xtashlarni darhol aniqlaydi va ilova yopilganda faqat o'zi ochgan jarayon daraxtini xavfsiz tozalaydi (`taskkill /F /T /PID`).
   - Python kashfiyoti kengaytirildi: o'rnatilgan/portativ (`python/python.exe`, `runtime/python.exe`), virtual muhit (`.venv`) va tizim darajasidagi runtime'larni avtomatik aniqlaydi.

2. **Dasturchi Yo'llaridan Tozalash (Portativlik):**
   - Dasturchi kompyuteriga bog'langan statik yo'llar (`D:\tools\w64devkit\bin`, `D:\Ishchi stoli\Mikasa`, `C:\Users\...`) butunlay chiqarib tashlandi.
   - `scripts/tauri.js` dinamik toolchain discovery va bo'sh joyli yo'llarda (spaces in path) xavfsiz ishlash uchun dinamik ishchi katalog boshqaruviga o'tkazildi.

3. **Xavfsizlik va Tarmoq Himoyasi (Phase 20, Hardening Pass):**
   - **CSP:** `tauri.conf.json` da qat'iy Content Security Policy joriy etildi (`default-src 'self' tauri: http://localhost:18420 ...`).
   - **CORS:** `core/api_server.py` faqat ruxsat etilgan mahalliy originlarni (`tauri://localhost`, `http://localhost:*`, `http://127.0.0.1:*`) qabul qiladi; begona saytlar (`evil.com`, va h.k.) 403 Forbidden bilan to'xtatiladi.
   - **Lokal Tarmoq Izolyatsiyasi:** `ALLOWED_REMOTE_IPS` faqat `127.0.0.1` va `::1` ga ruxsat beradi; tashqi LAN so'rovlari bloklanadi.
   - **Path Traversal Himoyasi:** `core/agent_plugins.py` plagin nomlarini `^[a-zA-Z0-9_\-]+$` regexi va `os.path.realpath` tekshiruvi orqali xavfsiz chegaralaydi.

4. **Kodni Tozalash va Maxfiy Ma'lumotlarni Sanitarizatsiya Qilish (Phase 22):**
   - `core/logger.py` dagi `SensitiveDataFilter` barcha API kalitlar (`AIza...`, `sk-...`, `Bearer ...`) va parollarni log fayllariga yozilishidan oldin avtomatik yashiradi (`***MASKED_KEY***`).

5. **Avtomatlashtirilgan Test Sinovlari (Phases 23–25, CI):**
   - **Backend:** 39 ta birlik va integratsiya testlari (`test_e2e_lifecycle.py`, `test_windows_qa.py`, `test_stress.py`, `test_logging.py`, `test_security_api.py`, va h.k.) 100% muvaffaqiyatli o'tdi (3.82s).
   - **Frontend:** 10 ta Node.js testlari (`frontend.test.mjs`, `stress.test.mjs`) to'liq o'tdi (308ms).
   - **Stress:** 1000 ta so'rov tezkor rejimda sinovdan o'tkazildi (1731 req/s, o'rtacha kechikish 0.56ms, xotira o'zgarishi +0.08MB).
   - **CI:** `.github/workflows/ci.yml` GitHub Actions orqali Python 3.11/3.12 va Node 20 uchun avtomatik tekshiruvni ta'minlaydi.

6. **Reliz Paketlari va Portativ Launcher (Phase 26, 27):**
   - Barcha reliz fayllari `release/v7.1.0/` katalogida tayyorlandi:
     - `Mikasa-AI-v7.1.0.exe` (4.78 MB, mustaqil native desktop ilova)
     - `WebView2Loader.dll` (0.15 MB, native bog'liqlik)
     - `Mikasa-AI-v7.1.0.msi` (2.60 MB, Windows MSI o'rnatuvchi)
     - `Mikasa-AI-Setup-v7.1.0.exe` (1.85 MB, NSIS o'rnatuvchi)
     - `run_portable.bat` (bir marta bosish bilan ishga tushiruvchi avtomatik skript)
     - `version_manifest.json` (SHA-256 xesh kodlari va hajm ko'rsatkichlari)

### 10.2 Ishlab Chiqarish Asoslari va Qolgan Taxminlar (Production Assumptions)

1. **Python Runtime:**
   - Foydalanuvchi tizimida Python 3.10+ (yoki ilova yoniga qo'yilgan embedded `python/` jildi) va `requirements.txt` dagi paketlar (`aiohttp`, `psutil`, va h.k.) mavjud bo'lishi talab etiladi.
2. **Windows WebView2 Runtime:**
   - Windows 11 va Windows 10 ning zamonaviy versiyalarida WebView2 sukut bo'yicha mavjud; eski Windows versiyalarida Microsoft WebView2 Evergreen Bootstrapper talab etiladi.
3. **Port 18420:**
   - Ilova `127.0.0.1:18420` portida faoliyat ko'rsatadi. Ushbu port boshqa dasturlar tomonidan band qilinmagan bo'lishi kerak.

*Hujjat Post-Phase-27 yakuniy ishlab chiqarish auditi talablariga muvofiq yangilandi.*

---

## 11. PHASE 28 — INTELLIGENCE CORE ARCHITECTURE

**Holat:** `Phase 28 — Intelligence Core Yakunlandi`  
**Tarmoq:** `dev-v7.0.0`  
**Baho:** Production-Grade Modular Intelligence Layer

### 11.1 Arxitektura Transformatsiyasi

Oldingi monolitik va qattiq bog'langan oqim:
```
USER ──> LLM ──> RAW JSON COMMAND
```

Yangi ko'p bosqichli va xavfsiz **Intelligence Core** oqimi:
```
USER
  │
CONTEXT ENGINE (Selective & Bounded Context Assembly)
  │
AI PROVIDER MANAGER (Gemini 2.5 Flash / OpenRouter Fallback)
  │
INTENT ENGINE (Normalized Intent Categorization)
  │
DECISION ENGINE + PERMISSION ENGINE (Risk Assessment & Action Routing)
  ├── ANSWER (Direct conversation)
  ├── CLARIFICATION (Ambiguity resolution)
  ├── CONFIRMATION (High-risk action safeguard)
  └── COMMAND / TOOL
        │
     TOOL REGISTRY (Safe execution)
        │
     RESULT VERIFICATION (No fake success)
        │
COMPATIBILITY ADAPTER ──> REST / WebSocket / React Frontend
```

### 11.2 Yaratilgan Modullar (`core/intelligence/`)

1. **`types.py`**: Barcha ichki qatlamlar uchun normalizatsiya qilingan ma'lumotlar modellari (`AIRequest`, `AIResponse`, `Intent`, `Decision`, `RiskLevel`, `IntelligenceResponse`).
2. **`provider.py`**: Provayder-mustaqil `AIProvider` abstraksiyasi va deterministik fallback boshqaruvchisi `ProviderManager`.
3. **`gemini_provider.py`**: Google Gemini REST integratsiyasi (Google Search Grounding, Thinking mode filtri, 429 kvota navbatlari va xatoliklar nazorati).
4. **`openrouter_provider.py`**: OpenRouter fallback integratsiyasi (universal modellar va xavfsiz sarlavhalar).
5. **`context.py`**: `ContextEngine` — faqat kerakli ma'lumotlarni (foydalanuvchi bilimlari, cheklangan suhbat tarixi, selektiv kompyuter spetsifikatsiyalari) xavfsiz va ixcham yig'ish.
6. **`intent.py`**: `IntentEngine` — AI javobi yoki mahalliy qoidalardan niyatni normalizatsiya qilish.
7. **`permission.py`**: `PermissionEngine` — amallarni `LOW`, `MEDIUM`, `HIGH` risk darajalariga ajratish va yuqori xavfli amallarni (`shutdown`, `restart`, `delete`) majburiy tasdiqlash rejimiga o'tkazish.
8. **`decision.py`**: `DecisionEngine` — niyat va ruxsatlar asosida yakuniy qaror turini belgilash (`ANSWER`, `COMMAND`, `TOOL`, `CLARIFICATION`, `CONFIRMATION`, `ERROR`).
9. **`orchestrator.py`**: `IntelligenceOrchestrator` — butun quvurni muvofiqlashtiruvchi, vositalar ijrosini nazorat qiluvchi va natijalarni tekshiruvchi markaziy kognitiv nazoratchi.
10. **`adapter.py`**: `CompatibilityAdapter` — mavjud React frontend va `core/ai_engine.py` funksiyalariga 100% orqaga qaytuvchanlik (backward compatibility) ta'minlovchi ko'prik.

### 11.3 Sinovlar va Ishonchlilik

- **Yangi Testlar:** `tests/test_intelligence_core.py` (27 ta yangi test: provayder normalizatsiyasi, fallback, selektiv kontekst, niyat, ruxsatlar, orkestratsiya, asbob tekshiruvi va adapter).
- **Regressiya Holati:** Barcha 66 ta backend testlari (39 ta oldingi + 27 ta yangi) va 10 ta frontend testlari 100% muvaffaqiyatli o'tdi.
- **Xavfsizlik:** Model chiqishi hech qachon to'g'ridan-to'g'ri `eval`/`exec`/`os.system` ga uzatilmaydi; barcha ijrolar faqat ro'yxatdan o'tgan vositalar va ruxsatlar nazorati orqali amalga oshiriladi.

---

## 12. PHASE 29 — CONTEXT & MEMORY INTELLIGENCE

**Holat:** `Phase 29 — Context & Memory Intelligence Yakunlandi`  
**Tarmoq:** `dev-v7.0.0`  
**Baho:** Production-Grade High-Relevance Context & Memory Intelligence

### 12.1 Arxitektura va Dizayn Prinsiplari

Phase 29 doirasida alohida ikkinchi xotira bazasi (competing database) yaratilmadi; mavjud barqaror `AgentMemory` (`core/agent_memory.py`) kengaytirildi va intellektual modullar bilan chuqurlashtirildi:
- **Evolyutsiya:** "Barcha suhbatlar va bilimlarni o'qish" modelidan "Joriy vazifa uchun faqat eng kerakli, yuqori reytingli kontekstni saralab olish" modeliga o'tildi.
- **Xotira — Ko'rsatma emas, Ma'lumot (DATA ONLY):** Xotira ma'lumotlari tizim promptiga faqat `RELEVANT FOYDALANUVCHI BILIMLARI (DATA ONLY)` ko'rinishida uzatiladi. Xotiradagi hech qanday matn tizim qoidalarini, xavfsizlik darajalarini yoki ruxsatnomalarni bekor qila olmaydi.
- **Maxfiylik va Filtrlash:** API kalitlar (`AIza...`, `sk-...`, `ghp_...`), Bearer tokenlar va parollar xotiraga yozilishidan oldin aniqlanadi va rad etiladi.

```
FOYDALANUVCHI XABARI
       │
TASK CONTEXT MANAGER (Faol vazifalar & 'shunga', 'undagi' havolalari)
       │
MEMORY POLICY (Maxfiy ma'lumotlar filtri, Injection himoyasi, Deduplikatsiya)
       │
AGENT MEMORY (agent_knowledge.json + MemoryItem normalizatsiyasi)
       │
MEMORY RETRIEVER (Ko'p omilli deterministik reyting: Leksik 40% + Muhimlik 20% + Ishonchlilik 15% + Recency 15%)
       │
CONTEXT ENGINE 2.0 (Chegaralangan tarix + Faol vazifa + Saralangan xotiralar + DATA ONLY)
       │
AI PROVAYDER (Gemini / OpenRouter)
```

### 12.2 Yangi va Kengaytirilgan Modullar

1. **`core/intelligence/memory_types.py`**:
   - `MemoryType`: `FACT` (faktlar), `PREFERENCE` (afzalliklar), `CONVERSATION` (suhbat xulosasi), `TASK` (davom etayotgan vazifa), `NOTE` (eslatma).
   - `MemorySource`: `USER`, `CONVERSATION`, `SYSTEM`.
   - `MemoryConfidence`: `HIGH` (1.0), `MEDIUM` (0.6), `LOW` (0.3).
   - `MemoryItem`: Normalizatsiya qilingan xotira modeli (id, key, content, value, type, source, importance, confidence, access_count, superseded_by, metadata).
   - `ActiveTaskContext`: Ko'p qadamli vazifalar uchun faol holat (task_id, goal, entities, last_action, last_result, status).

2. **`core/intelligence/memory_policy.py`**:
   - `MemoryPolicy.contains_sensitive_data()`: Gemini, OpenAI, GitHub tokenlari, Bearer tokenlar va parollarni avtomatik aniqlash va xotiraga saqlanishini bloklash.
   - `MemoryPolicy.sanitize_for_prompt_injection()`: Prompt injection xurujlarini zararsizlantirish.
   - `MemoryPolicy.evaluate_write()`: Duplikatlarni aniqlash va mavjud xotirani yangilash.
   - `MemoryPolicy.resolve_conflict()`: Ziddiyatli yangi foydalanuvchi ma'lumoti kelganda eskisini `superseded_by` bilan belgilash.
   - `MemoryPolicy.classify_type()`: Kalit va matndan xotira turini (`FACT`, `PREFERENCE`, `TASK`, `NOTE`) aniqlash.

3. **`core/intelligence/memory_retriever.py`**:
   - `MemoryRetriever`: Tashqi og'ir vektor ma'lumotlar bazalariga (ChromaDB va h.k.) tayanmasdan, to'liq deterministik va tezkor (<1ms) ko'p omilli kompozit skoring:
     - Leksik qoplash (Lexical overlap): 40%
     - Muhimlik (Importance): 20%
     - Ishonchlilik (Confidence): 15%
     - Yangilik / Vaqt omili (Recency): 15%
     - Xotira turi koeffitsiyenti (Type weight: TASK 1.25, PREFERENCE 1.15, FACT 1.0, NOTE 0.95)
     - Faol vazifa ob'ektlari bonusi (Task entity bonus: +0.25)
   - Bounded retrieval: Belgilangan limit (sukut bo'yicha 6 ta) doirasida eng mos xotiralarni ajratadi.
   - Faol bo'lmagan (`is_active() == False`) xotiralarni avtomatik chetlab o'tadi.

4. **`core/intelligence/task_context.py`**:
   - `TaskContextManager`: Ko'p bosqichli vazifalarning maqsadlari va ob'ektlarini (`entities`) kuzatib boradi.
   - `resolve_reference_hint()`: Foydalanuvchi "shunga", "undagi", "o'sha" kabi olmoshlar ishlatganda, faol vazifa yoki avvalgi suhbat burilishlaridagi ob'ektni (masalan: "telegram", "github") aniqlaydi va tizim promptiga kontekstual bog'lanish ko'rsatmasini qo'shadi.

5. **`core/intelligence/context.py` (Context Engine 2.0)**:
   - Chegaralangan suhbat tarixi (6 ta burilish).
   - Faol vazifa konteksti va havola ko'rsatmasini inyeksiya qilish.
   - Saralangan va chegaralangan xotiralarni `RELEVANT FOYDALANUVCHI BILIMLARI (DATA ONLY)` bo'limiga kiritish.
   - Xotira yoki disk xatolari yuz berganda xavfsiz zaxira (resilience) rejimi.

6. **`core/agent_memory.py`**:
   - `save_knowledge()` metodi `MemoryPolicy` orqali sanitizatsiya, maxfiylik tekshiruvi va duplikat nazoratiga ulandi.
   - `get_memory_items()` va `retrieve_relevant()` metodlari qo'shildi.
   - REST API va React frontend bilan 100% orqaga qaytuvchanlik saqlandi.

### 12.3 Sinovlar va Sifat Ko'rsatkichlari

- **Yangi Testlar:** `tests/test_memory_intelligence.py` — 25 ta to'liq test:
  1. Xotira birligi normalizatsiyasi
  2. Fakt va afzallik klassifikatsiyasi
  3. Aniq xotira saqlash oqimi
  4. Ishonchlilik darajalari
  5. API kalit maxfiyligini rad etish
  6. Parol maxfiyligini rad etish
  7. Duplikat aniqlash (aniq kalit)
  8. Noaniq duplikat aniqlash (sinonim kalit)
  9. Yangilanish oqimi
  10. Leksik moslik reytingi
  11. Yangilik (recency) reytingi
  12. Faol vazifa bonusi
  13. Chegaralangan qidiruv chegarasi
  14. Kontekst byudjetiga rioya qilish
  15. Chegaralangan suhbat tarixi
  16. Faol vazifadan havola ko'rsatmasi
  17. Suhbat tarixidan havola ko'rsatmasi
  18. Faol vazifa hayot sikli
  19. Ziddiyatlarni hal qilish (`superseded_by`)
  20. Faol bo'lmagan xotiralarni qidiruvdan chiqarish
  21. ContextEngine barqarorligi (xatoliklarga chidamlilik)
  22. Xotirani tozalash
  23. Xotiradan bitta elementni o'chirish
  24. `AgentMemory` orqaga qaytuvchanligi
  25. ContextEngine integratsiyasi va anti-injection sarlavhalari
- **Barcha 25 ta test 100% muvaffaqiyatli o'tdi (0.078s).**
- **Phase 28 Intelligence Core testlari:** 27 ta test 100% o'tdi (0.573s).
- **Frontend Testlari:** 10 ta Node.js testi 100% o'tdi (267ms).
- **Frontend Build:** `npm run build` muvaffaqiyatli (270ms, xatosiz).



---

## 13. Phase 30: Memory UX, User Control & Context Observability

### 13.1 Arxitektura Maqsadi va Asosiy Tamoyillar
Phase 30 tizim xotirasini foydalanuvchi to'liq boshqaradigan, shaffof, tushunarli, tahrirlanadigan, o'chiriladigan va kuzatiladigan holatga keltirishga bag'ishlangan.

**ASOSIY TAMOYIL: FOYDALANUVCHI XOTIRANING YAGON QONUNIY EGASIDIR.**
- **DATA ONLY**: Xotira qat'iy ma'lumot (DATA) sifatida ishlatiladi, u hech qachon tizim ko'rsatmasi (system instruction) yoki xavfsizlik cheklovlarini buzuvchi vosita bo'la olmaydi.
- **Explainability**: Har bir tanlangan yoki rad etilgan xotira uchun tushunarli tushuntirish beriladi.
- **User Control**: Foydalanuvchi xotiralarni ko'rishi, qidirishi, filtrlashi, tahrirlashi, o'chirishi, muhim qilib qadashi (pin) va yozishni taqiqlashi (Do-Not-Remember) mumkin.
- **Context Observability**: Har bir so'rovning 11 ta kontekst bosqichi (Context Trace) orqali to'liq kuzatilishi va sirlarni avtomatik niqoblash (Sensitive Redaction).

### 13.2 Yangi Imkoniyatlar va Modullar

1. **`core/intelligence/memory_types.py`**:
   - `pinned: bool = False`: Foydalanuvchi tomonidan doimiy ustuvor deb belgilangan xotiralar uchun bayroq.
   - `WORK_CONTEXT = "work_context"`: Loyiha, ish muhiti yoki joriy dasturlash konteksti uchun yangi xotira turi.
   - `is_active()` metodi: Faol yoki yangi versiya bilan almashtirilgan (`superseded_by`) holatni aniqlash.

2. **`core/intelligence/memory_policy.py`**:
   - **Do-Not-Remember Policy**:
     - `do_not_remember_all`: Butunlay barcha xotiralarni saqlashni to'xtatish.
     - `blocked_types`: Belgilangan xotira turlarini (masalan, `work_context`, `preference`) bloklash.
     - `blocked_keys`: Muayyan kalitlarni (masalan, maxfiy kalitlar) bloklash.
   - `data/memory_policy.json` fayliga atomik (`os.replace`) xavfsiz saqlash.

3. **`core/intelligence/memory_retriever.py`**:
   - **Pinned Boost (+0.35)**: Foydalanuvchi qadagan xotiralar qidiruv reytingida ustuvorlik oladi.
   - `retrieve_with_explanation()`: Xotiralarni saralash bilan birga inson tushunadigan izoh (`reason`) va batafsil ball taqsimotini (`debug_details`) taqdim etadi.

4. **`core/intelligence/observability.py`**:
   - `redact_sensitive_data()`: API kalitlari, tokenlar, parollar va maxfiy ma'lumotlarni izlardan avtomatik niqoblovchi funksiya (`[REDACTED]`).
   - `ContextTrace` & `ContextTraceStage`: Har bir so'rov bo'yicha 11 bosqichli telemetriya zanjiri (`REQUEST`, `LOCAL_DISPATCH`, `TASK_CONTEXT`, `MEMORY_RETRIEVAL`, `SELECTED_MEMORY`, `PROVIDER`, `INTENT`, `PERMISSION`, `DECISION`, `TOOL`, `RESPONSE`).
   - `ObservabilityManager`: So'nggi 25 ta so'rov uchun xotirada cheklangan ring-bufer (Ring Buffer) va xotira metrikalari menejeri (`MemoryMetricsManager`).

5. **`core/agent_memory.py`**:
   - Atomik xavfsiz fayl yozish (`os.replace` orqali ma'lumot yo'qolishining oldini olish).
   - `update_knowledge_item()`: Mavjud bilimning kaliti, qiymati, turi, muhimligi va qadanganlik holatini tahrirlash.
   - `delete_knowledge_item()`: Bitta xotirani kalit yoki ID bo'yicha xavfsiz o'chirish.
   - `pin_knowledge_item()`: Xotirani qadash yoki qadoqdan chiqarish.

6. **REST API & WebSocket (`core/api_server.py`)**:
   - `PUT /api/memory/knowledge/{id}`: Xotira elementini tahrirlash.
   - `DELETE /api/memory/knowledge/{id}`: Xotirani o'chirish.
   - `POST /api/memory/pin`: Xotirani qadash / yechish.
   - `GET /api/memory/policy` & `POST /api/memory/policy`: Maxfiylik siyosatini boshqarish.
   - `GET /api/memory/metrics`: Xotira quyi tizimi metrikalari.
   - `GET /api/context/traces` & `GET /api/context/last-trace`: Kontekst izlari va telemetriyasi.
   - `memory_updated`, `memory_policy_updated` WebSocket real-time hodisalari.

7. **Frontend UX (`mikasa-7/src/pages/MemoryPage.tsx`)**:
   - **Memory Inspector & Filter Bar**: Qidiruv, turlar bo'yicha filtr (`fact`, `preference`, `work_context`, `task`, `note`), qadalganlar filtri va holat filtri (`faol`, `eskirgan`).
   - **Full Metadata Edit Modal**: Kalit, mazmun, tur, muhimlik slayderi (0-100%) va qadash (pin) tanlovi.
   - **Safe Delete Modal**: O'chirilayotgan xotira mazmuni va kaliti bilan tasdiqlash oynasi.
   - **Privacy & Do-Not-Remember Tab**: Global xotirani o'chirish switchi, taqiqlangan turlar va taqiqlangan kalitlar ro'yxatini boshqarish.
   - **Observability & Traces Tab**: Xotira metrikalari kartalari (jami, faol, qadalgan, murojaatlar, hit rate), so'nggi 25 ta kontekst izlari, 11 ta bosqich bo'yicha vaqt va detallar, xotira tanlash izohlari (reasons & scores).

### 13.3 Testlar va Verifikatsiya

- **`tests/test_memory_ux.py` (18 ta test)**:
  - Serializatsiya va to'liq metadatalar mavjudligi
  - ID yoki kalit bo'yicha xavfsiz tahrirlash
  - ID yoki kalit bo'yicha xavfsiz o'chirish
  - Doimiy qadash (pin/unpin)
  - Qadalgan elementlarning qidiruv reytingidagi bonusi (+0.35)
  - Do-Not-Remember global taqiq
  - Do-Not-Remember turlar bo'yicha taqiq
  - Do-Not-Remember kalitlar bo'yicha taqiq
  - Siyosat faylining atomik saqlanishi
  - Faol va qadalgan elementlar statistikasi
  - Atomik fayl saqlash ishonchliligi
- **`tests/test_memory_observability.py` (16 ta test)**:
  - Maxfiy ma'lumotlarni (API kalit, token, parol) izlarda avtomatik niqoblash
  - 11 bosqichli ContextTrace yaratish va vaqt hisobi
  - 25 ta izdan iborat ring-bufer chegaralanganligi
  - Xotira metrikalari hisob-kitobi (hit rate, deletions, pinned, active)
  - Tushunarli o'zbekcha izohlar bilan xotira tanlovi (`retrieve_with_explanation`)
  - REST API orqali izlar va metrikalarni olish
- **`tests/test_memory_intelligence.py` (25 ta test)**: 100% o'tdi.
- **`tests/test_intelligence_core.py` (24 ta test)**: 100% o'tdi.
- **`tests/test_memory_api.py` (7 ta test)**: 100% o'tdi.
- **Frontend Testlari**: 10/10 test muvaffaqiyatli o'tdi.
- **Frontend Build**: `tsc && vite build` 270ms ichida to'liq xatosiz muvaffaqiyatli yakunlandi.

---

## 14. Phase 31: Agentic Multi-Step Intelligence (Mikasa AI v7.1.0-RC2)

Phase 31 da Mikasa AI oddiy bitta buyruqli yordamchidan chegaralangan, xavfsiz va deterministik **ko'p bosqichli agentik tizimga** aylantirildi:
`PLAN → ACT → OBSERVE → VERIFY → CONTINUE → COMPLETE`.

Ushbu tizim avvalgi barcha fazalar (`PermissionEngine`, `DecisionEngine`, `ToolRegistry`, `MemoryPolicy`, `TaskContextManager`, `ContextTrace`) xavfsizlik va kontekst mexanizmlariga to'liq tayangan holda ishlaydi.

### 14.1. Boshqaruv va Xavfsizlik Tamoyillari
1. **Qat'iy Ijro Chegaralari (Bounded Execution)**:
   - `MAX_STEPS = 8`: Reja maksimal 8 qadam bilan cheklangan.
   - `MAX_RETRIES_PER_STEP = 1`: Vaqtinchalik xatolarda qadam ko'pi bilan 1 marta qayta uriniladi.
   - `MAX_TOTAL_EXECUTION_TIME = 60.0s`: Rejaning maksimal bajarilish vaqti 60 soniya.
2. **Reja Tasdiqlanishi != Amal Tasdiqlanishi (Plan Approval != Action Approval)**:
   - Reja tuzilishi barcha amallarga ruxsat berilganligini anglatmaydi.
   - Har bir qadam `PermissionEngine` orqali alohida baholanadi.
   - Yuqori xavfli (HIGH) amallar reja ijrosini darhol to'xtatadi (`WAITING_CONFIRMATION`) va foydalanuvchining ochiq tasdig'ini talab qiladi.
3. **Destruktiv Amallarda Qayta Urinish Taqiqi (`AGENT_RETRY_BLOCKED`)**:
   - `NON_IDEMPOTENT_ACTIONS` to'plamidagi amallar (`shutdown`, `restart`, `clear_memory`, `delete_plugin`, `process_kill`) xato bersa, qayta urinish bloklanadi.
4. **Kod Inyeksiyasi Taqiqi (No Eval/Exec)**:
   - Hech qanday `eval`, `exec` yoki `os.system` chaqirilmaydi.
   - Rejadagi parametrlar inyeksiyalardan qat'iy himoyalangan.
5. **Bir Vaqtda Bitta Faol Reja (Concurrency Safety)**:
   - `RLock` orqali himoyalangan; boshqa reja ishlayotgan paytda yangi reja kelib tushsa `AGENT_ALREADY_RUNNING` xatosi qaytariladi.
6. **Xotira Izolyatsiyasi (DATA ONLY)**:
   - Xotiradagi ma'lumotlar xavfsizlik qoidalarini yoki ruxsatnomalarni o'zgartira olmaydi.

### 14.2. Qadam Verifikatsiyasi Dvigateli (`core/intelligence/verifier.py`)
`AgentVerifier` har bir qadam natijasini deterministik dalillar asosida tekshiradi:
- **Kalkulyator**: Matematik hisob-kitob mavjudligi va sonli qiymat tekshiruvi.
- **Ob-havo**: Harorat, daraja va ob-havo holati kalit so'zlari tekshiruvi.
- **Tizim Ma'lumotlari**: Natijaning bo'sh emasligi va tuzilmasi tekshiruvi.
- **Valyuta**: Kurs, qiymat va valyuta belgisi tekshiruvi.
- **Ilova Tekshiruvi**: O'rnatilganlik yoki topilmaganlik holati tekshiruvi.
- **Brauzer va YouTube**: Jarayon faolligi va ochilganlik holati tekshiruvi.
- **Leksik va Semantik Moslashuv**: Kutilgan natija (`expected_result`) bilan solishtirish.
- **Tri-State Status**: `SUCCESS` (muvaffaqiyatli), `FAILURE` (muvaffaqiyatsiz), `UNKNOWN` (noma'lum/tolerant).
- **Davom Etish Qarori (`should_continue`)**:
  - `SUCCESS` -> `STEP_VERIFIED_SUCCESS` (davom etadi)
  - `UNKNOWN` -> `STEP_VERIFIED_UNKNOWN_PROCEED` (asbob xato bermagan bo'lsa davom etadi)
  - `FAILURE` -> `STEP_VERIFICATION_FAILED` (reja to'xtatiladi yoki qayta uriniladi)

### 14.3. Agent Ijro Sikli (`core/intelligence/agent_loop.py`)
- **Mahalliy Deterministik Dekompozitsiya**: Bog'lovchilar ("va", "keyin", "so'ng", "hamda") orqali murakkab buyruqlarni mahalliy qadamlarga darhol ajratish (LLM kutishisiz).
- **LLM Strukturaviy Rejalashtiruvchi**: Murakkab so'rovlar uchun qat'iy JSON formatdagi reja taklifi.
- **Reja Validatsiyasi (`validate_plan`)**: Qadamlar soni, asboblar mavjudligi, parametrlar xavfsizligi va tsiklik takrorlanish tekshiruvi.
- **Ijro Sikli (`execute_plan`)**: Ketma-ket qadamlarni bajarish, kuzatish (`OBSERVE`), tekshirish (`VERIFY`), TaskContext bilan bog'lash va xulosaviy hisobot tuzish.
- **Tasdiqlash va Davom Ettirish (`confirm_step`)**: Foydalanuvchi tasdiqlasa reja to'xtagan joyidan davom etadi; rad etilsa toza holda bekor qilinadi.
- **Foydalanuvchi Bekor Qilishi (`abort_plan`)**: Faol reja darhol xavfsiz to'xtatiladi.

### 14.4. Kuzatuvchanlik va WebSocket Voqealari
`observability.py` da 10 ta yangi trace bosqichlari qo'shildi:
- `PLAN_CREATED`, `PLAN_VALIDATED`, `STEP_STARTED`, `STEP_COMPLETED`, `STEP_FAILED`, `STEP_VERIFIED`, `PLAN_PAUSED`, `PLAN_RESUMED`, `PLAN_COMPLETED`, `PLAN_ABORTED`.
- Barcha bosqichlarda va parametrlarda konfidentsial ma'lumotlar avtomatik niqoblanadi (`[REDACTED]`).
- Real vaqtda WebSocket hodisalari tarqatiladi: `agent_plan_created`, `agent_step_started`, `agent_step_completed`, `agent_step_failed`, `agent_verification`, `agent_confirmation_required`, `agent_completed`, `agent_aborted`.

### 14.5. REST API Server Integratsiyasi (`core/api_server.py`)
- `POST /api/agent/execute`: Maqsad bo'yicha reja tuzish va uni ijro etish.
- `POST /api/agent/confirm`: Pauza qilingan xavfli amalni tasdiqlash yoki rad etish.
- `POST /api/agent/abort`: Faol rejani xavfsiz to'xtatish.
- `GET /api/agent/state`: Agentning joriy holati va oxirgi reja ijro tafsilotlari.

### 14.6. Frontend Foydalanuvchi Tajribasi (`mikasa-7`)
- **`backendService.ts`**:
  - `executeAgentGoal(goal)`
  - `confirmAgentStep(planId, stepId, approve)`
  - `abortAgentPlan(planId)`
  - `getAgentState()`
  - `onAgentEvent(callback)`
- **`ChatPage.tsx`**:
  - Real vaqtda **Agent Progress Card**:
    - Reja maqsadi va holat nishonlari (Bajarilmoqda, Tasdiqlash kutilmoqda, Muvaffaqiyatli, To'xtatildi).
    - Har bir qadam holati ikonkalari (✅ muvaffaqiyatli, ⏳ bajarilmoqda, ❌ xato, ⚪ kutilmoqda).
    - Yuqori xavfli amallarda interaktiv tasdiqlash bloki:
      - `[ ✅ Tasdiqlash va davom etish ]`
      - `[ ❌ Bekor qilish ]`
    - Faol rejani istalgan paytda to'xtatish tugmasi (`[ ⏹️ To'xtatish ]`).

### 14.7. Test Natijalari
- `tests/test_agent_loop.py` (17 ta test) — 100% o'tdi.
- `tests/test_agent_verifier.py` (15 ta test) — 100% o'tdi.
- `tests/test_agent_security.py` (10 ta test) — 100% o'tdi.
- Phase 31 jami 42 ta yangi test qo'shildi.
- Avvalgi barcha fazalar (Phase 28, 29, 30) regressiya testlari (91 ta test) 100% muvaffaqiyatli o'tdi.
- Jami backend testlari: 133+ test 100% muvaffaqiyatli.
- Frontend testlari (`node --test tests/frontend.test.mjs tests/stress.test.mjs`): 10/10 test 100% o'tdi.
- Frontend Production Build (`tsc && vite build`): 100% xatosiz muvaffaqiyatli.

---

## 15. PHASE 32: TOOL SYSTEM 2.0 — QOBILIYATGA ASOSLANGAN INTELLEKT (CAPABILITY-DRIVEN INTELLIGENCE)

### 15.1. Asosiy Maqsad va Paradigma O'zgarishi
Phase 32 ning asosiy maqsadi shunchaki yangi vositalar qo'shish emas, balki Mikasa AI ning mavjud imkoniyatlaridan to'liq va xatosiz foydalanishini ta'minlashdir:
```
MIKASADA NIMALAR MAVJUD?
        ↓
JORIY VAZIFA NIMANI TALAB QILADI?
        ↓
QAYSI MAVJUD QOBILIYAT UNI YECHA OLADI?
        ↓
QAYSI ASBOB ENG YAXSHI NOMZOD?
        ↓
PARAMETRLAR TO'G'RI VA XAVFSIZMI?
        ↓
IJROGA RUXSAT BERILGANMI?
        ↓
VAQT CHEGARASI (TIMEOUT) BILAN IJRO ETISH
        ↓
NATIJANI TUSHUNISH VA NORMALLASHTIRISH
        ↓
VERIFIKATSIYA VA MOSLASHTIRISH
        ↓
KEYINGI QADAMNI BELGILASH
```

### 15.2. Arxitektura Qismlari va Ishlab Chiqilgan Modullar

#### 1. Tool Contract 2.0 & Normallashtirish (`core/tools/contract.py`)
- **`ToolHealth`**: Asbob salomatligi monitoringi (`AVAILABLE`, `UNAVAILABLE`, `DEGRADED`, `DISABLED`).
- **`ToolErrorCode`**: Standartlashtirilgan xatolik kodlari (`VALIDATION_ERROR`, `PERMISSION_DENIED`, `TOOL_NOT_FOUND`, `TOOL_UNAVAILABLE`, `TIMEOUT`, `EXECUTION_ERROR`, `INVALID_RESULT`, `SECURITY_BLOCKED`, `UNKNOWN_ERROR`).
- **`ToolResult`**: Normallashtirilgan qaytuvchi obyekt (`success`, `code`, `message`, `data`, `error`, `duration_ms`, `tool`, `version`, `trace_id`, `metadata`).
  - To'liq orqaga moslik: `ToolResult` obyekti eski kodlar uchun dict kabi murojaat (`res["result"]`, `res.get("result")`, `"data" in res`) imkoniyatini ta'minlaydi.
  - Avtomatik maxfiylashtirish: `to_dict()` chaqirilganda API tokenlar, parollar va maxfiy kalitlar avtomatik `[REDACTED]` ga almashtiriladi.
- **`ToolContract2`**: Kengaytirilgan asbob shartnomasi (`capabilities`, `aliases`, `required_parameters`, `risk_level`, `timeout`, `idempotent`, `destructive`, `health`, metrikalar).
  - Ketma-ket 3 ta xatolikda salomatlik avtomatik `DEGRADED` ga o'tadi; muvaffaqiyatli ijroda esa `AVAILABLE` ga tiklanadi.

#### 2. Parametrlarni Qat'iy Tekshirish va Himoya Dvigateli (`core/tools/validator.py`)
- **`ParameterValidator`**:
  - Majburiy parametrlarning mavjudligi va bo'sh emasligini tekshirish.
  - Strict rejim: deklaratsiya qilinmagan, kutilmagan parametrlarni rad etish (`VALIDATION_ERROR`).
  - Turlarni qat'iy tekshirish va xavfsiz konvertatsiya (`string`, `integer`, `float`, `boolean`, `dict`, `list`).
  - Kod inyeksiyasidan himoya: oddiy parametrlarga `eval(`, `exec(`, `os.system(`, `__import__(`, `subprocess.` yozilganda zudlik bilan `SECURITY_BLOCKED` qaytariladi (kod yozuvchi maxsus asboblar bundan mustasno).
  - Nol jimjit xatolar (Zero silent failures): nosoz parametrlar asbobga o'tkazilmaydi.

#### 3. Qobiliyatlarni Indekslash va Qidirish Registri (`core/tools/discovery.py`)
- **`CapabilityRegistry`**:
  - Asboblarni semantik qobiliyat teglari (`capabilities`) va taxalluslari (`aliases`) bo'yicha tezkor indekslash.
  - `find_by_capability()`: aniq va qisman moslik bo'yicha qobiliyat egalarini topish.
  - `find_by_alias()`: qisqa va qulay taxalluslar orqali vositani aniqlash.
  - `discover_capabilities_for_text()`: foydalanuvchi so'rovidagi o'zbek va inglizcha tabiiy kalit so'zlar orqali kerakli qobiliyatlarni aniqlash.

#### 4. Aqlli Asbob Tanlash va Tushuntirish Dvigateli (`core/tools/selector.py`)
- **`SmartToolSelector`**:
  - Ko'p omilli nomzodlarni baholash tizimi:
    - Salomatlik omili (Health Factor — 30%): `DISABLED` va `UNAVAILABLE` vositalarga 0 ball; `DEGRADED` vositalarga 50% jarima.
    - Qobiliyat mosligi (Capability Match — 35%): to'liq yoki qisman moslik.
    - Parametrlar mosligi (Parameter Compatibility — 15%): berilgan argumentlarning asbob sxemasiga mosligi.
    - Xavf darajasi afzalligi (Risk Level — 10%): past xavfli asboblarga ustunlik.
    - Ishonchlilik omili (Reliability — 10%): avvalgi muvaffaqiyatli ijrolar ulushi.
    - Task Context yaqinligi: joriy vazifada ilgari muvaffaqiyatli ishlatilgan asbobga 15% bonus.
  - Transparent Observability tushuntirishi: nima uchun aynan shu asbob tanlanganligini ko'rsatuvchi to'liq tahliliy matn (`explanation`) va ballar taqsimoti (`scoring_breakdown`).
  - Zaxira vosita (Fallback resolution): asosiy vosita nosoz bo'lganda mos zaxira vositani avtomatik tanlash.

#### 5. Xavfsiz Asbob Ijro Etish Zanjiri (`core/tools/runner.py`)
- **`SafeToolRunner`**:
  - To'liq zanjirli xavfsiz ijro: `VALIDATE -> PERMISSION -> TIMEOUT RUN -> NORMALIZE -> HEALTH UPDATE`.
  - Alohida oqimlar puli (`ThreadPoolExecutor`) orqali asboblarni izolyatsiya qilish.
  - Qat'iy vaqt chegarasi (`timeout`): qotib qolgan yoki javob bermagan asboblarni to'xtatish va `TIMEOUT` xatosini qaytarish.
  - Destruktiv va no-idempotent amallarda avtomatik qayta urinishni to'xtatish.

#### 6. Mavjud 29 ta O'rnatilgan Vositalarning To'liq Migratsiyasi (`core/agent_tools.py`)
- Barcha 29 ta vosita (`system`, `music`, `weather`, `reminder`, `file`, `knowledge`, `datetime`, `scheduler`, `rag`, `currency`, `translator`, `screen`, `file_write`, `app_check`, `ask_user`, `screen_click`, `keyboard_type`, `keyboard_shortcut`, `clipboard`, `process_manager`, `audio_control`, `system_info`, `window_manager`, `notification`, `vector_search`, `sandbox`, `secret_vault`) yangi `ToolContract2` metadatalari bilan boyitildi.
- `ToolRegistry` qobiliyatlar registri, aqlli tanlash va qobiliyat bo'yicha chaqiruvni to'liq qo'llab-quvvatlaydi.
- Eski kodlar uchun 100% orqaga moslik (`Tool` konstruktori, `func`/`function` mosligi, dict natijalar).

#### 7. AgentLoop va Kuzatuvchanlik (Observability) Integratsiyasi
- `core/intelligence/agent_loop.py`:
  - Qadamlar nafaqat asbob nomi, balki qobiliyat nomi orqali ham qabul qilinadi va avtomatik hal etiladi.
  - Parametrlar ijro oldidan qat'iy tekshiriladi.
  - Idempotentlik qoidasi: xavfsiz amallar qayta uriniladi, destruktiv amallarda esa qayta urinish bloklanadi (`AGENT_RETRY_BLOCKED`).
  - Asosiy asbob ishlamay qolganda avtomatik mos zaxira asbobga (Fallback Tool) o'tish mexanizmi.
  - Qayta urinishda olingan yangi natijalar (`observed_result`, `error`) to'g'ri yangilanishi ta'minlandi.
- `core/intelligence/observability.py`:
  - 9 ta yangi Tool trace bosqichlari: `TOOL_DISCOVERED`, `TOOL_SELECTED`, `TOOL_VALIDATION_FAILED`, `TOOL_PERMISSION_CHECKED`, `TOOL_STARTED`, `TOOL_COMPLETED`, `TOOL_FAILED`, `TOOL_TIMEOUT`, `TOOL_BLOCKED`.

#### 8. Frontend Vizual Ko'rinishi va Tool Inspector (`mikasa-7`)
- `core/api_server.py`: `GET /api/tools/catalog` katalog so'rovi va `handle_plugins_execute` orqali boyitilgan `ToolResult` qaytarilishi.
- `mikasa-7/src/services/backendService.ts`: `PluginItem` interfeysi yangi kontrakt maydonlari bilan kengaytirildi va `getToolsCatalog()` metodi qo'shildi.
- `mikasa-7/src/pages/PluginsPage.tsx`: **Tool Inspector 2.0** yaratildi:
  - Versiya, xavf darajasi (LOW/MED/HIGH) va salomatlik indikatori (AVAILABLE/DEGRADED/DISABLED).
  - Idempotent va Destruktiv amallar nishonlari.
  - Timeout vaqti va Semantik qobiliyatlar (capabilities) teglari.
  - Majburiy va ixtiyoriy parametrlarning aniq ko'rsatilishi.
  - Test modalida bajarilish davomiyligi (`duration_ms`), holat kodi va tozalangan natija ko'rinishi.

### 15.3. Test Natijalari va Verifikatsiya
- Yangi yaratilgan 5 ta test to'plami:
  1. `tests/test_tool_contract.py` (13 ta test) — 100% OK.
  2. `tests/test_tool_capabilities.py` (9 ta test) — 100% OK.
  3. `tests/test_tool_validation.py` (11 ta test) — 100% OK.
  4. `tests/test_tool_execution_safety.py` (9 ta test) — 100% OK.
  5. `tests/test_tool_agent_integration.py` (9 ta test) — 100% OK.
- Phase 32 jami yangi testlar soni: **51 ta test** (talab: 40+).
- Phases 28, 29, 30, 31 va 32 to'liq intellekt regressiya to'plami: **161 ta test — 100% muvaffaqiyatli**.
- Frontend testlari (`npm test`): **10/10 test muvaffaqiyatli**.
- Frontend Production Build (`npm run build`): **267ms da 100% xatosiz yig'ildi**.

---

## 16. Phase 33 — Planning & Reasoning 2.0

### 16.1. Arxitektura Konsepsiyasi va Asosiy Maqsad
Phase 33 doirasida Mikasa AI tizimining rejalashtirish va mantiqiy fikrlash (Planning & Reasoning) arxitekturasi tubdan yangilandi va 2.0 darajasiga ko'tarildi.
Oldingi bosqichlarda rejalashtirish faqat ketma-ket oddiy ro'yxatdan iborat bo'lgan bo'lsa, Planning 2.0 quyidagi to'liq siklni joriy etdi:
```
USER GOAL 
    ↓
UNDERSTAND GOAL 
    ↓
IDENTIFY REQUIRED OUTCOME 
    ↓
DECOMPOSE GOAL (Heuristics / LLM) 
    ↓
IDENTIFY DEPENDENCIES (DAG) 
    ↓
CHOOSE EXECUTION ORDER (Kahn's Topological Sort) 
    ↓
SELECT REQUIRED CAPABILITIES (Tool System 2.0) 
    ↓
EXECUTE STEP (Act) 
    ↓
OBSERVE RESULT 
    ↓
ANALYZE & VERIFY RESULT (Oracle / Heuristic) 
    ↓
REPLAN IF NECESSARY (ReplanningEngine, v1 -> v2) 
    ↓
COMPLETE
```

### 16.2. Amalga Oshirilgan Yangi Komponentlar va O'zgarishlar

#### 1. Planning Model 2.0 (`core/intelligence/types.py`)
- **`PlanStep` yangilanishi**:
  - `description`: Har bir qadamning inson tushunadigan maqsadi.
  - `purpose`: Ushbu qadam umumiy rejaga nima hissa qo'shishi.
  - `dependencies`: Ushbu qadam bajarilishidan oldin yakunlanishi shart bo'lgan qadamlar ID lari ro'yxati.
  - `required_capability`: Kerakli semantik qobiliyat (masalan, `weather`, `browser_navigation`).
  - `selected_tool`: Qobiliyatni bajarish uchun Tool System 2.0 tomonidan tanlangan aniq asbob.
  - `verification_policy`: Qadam natijasini baholash siyosati (`strict`, `lenient`, `oracle_or_heuristic`).
  - `failure_reason`: Xatolik kelib chiqqanda uning sababi.
  - `retry_policy`: Qayta urinish konfiguratsiyasi.
- **`AgentPlan` yangilanishi**:
  - `intent` va `desired_outcome`: Rejadan kutilayotgan aniq yakuniy natija.
  - `assumptions` va `constraints`: Reja tuzishdagi taxminlar va vaqt/resurs cheklovlari.
  - `dependencies`: Reja darajasidagi to'liq bog'liqliklar grafigi (`{step_id: [dep_ids]}`).
  - `execution_order`: Topologik saralangan qadamlar tartibi.
  - `required_capabilities`: Reja talab qiladigan barcha qobiliyatlar ro'yxati.
  - `plan_version`: Rejaning hozirgi versiyasi (boshlang'ich: `1`).
  - `replan_count` va `max_replans`: Qayta rejalashtirish hisoblagichi va chegarasi (`MAX_REPLANS = 2`).
  - `replan_history`: Har bir qayta rejalashtirishning to'liq tarixi (`version`, `reason`, `timestamp`, `changed_steps`).
  - `get_ready_steps()`: Faqat barcha bog'liqliklari muvaffaqiyatli yakunlangan (`COMPLETED`) qadamlarni qaytaruvchi aqlli metod.

#### 2. Goal Decomposer (`core/intelligence/planner.py` - `GoalDecomposer`)
- **Zero Over-Planning**: Oddiy bir harakatli so'rovlar ("vaqt necha", "12 + 88", "youtube ni och") aniqlanadi va ularga keraksiz ko'p bosqichli rejalar tuzilmaydi (1 qadamda tezkor bajariladi).
- **Deterministik Ko'p Qadamli Tahlil**: O'zbek va ingliz tillaridagi bog'lovchilar (`va`, `keyin`, `hamda`, `so'ng`, `and`, `then`) va qoliplar orqali maqsadlar qadamlarga ajratiladi.
- **LLM Structured Decomposition**: Noma'lum va murakkab maqsadlar uchun sun'iy intellekt modeli orqali qat'iy JSON formatdagi reja shakllantiriladi.

#### 3. Dependency Graph & Topological Execution (`DependencyGraph`)
- **Bog'liqliklar grafigini qurish**: Har bir qadamning kirish/chiqish ma'lumotlari asosida qaramliklarni aniqlash.
- **Tsiklik bog'liqliklarni aniqlash (`PLAN_CIRCULAR_DEPENDENCY`)**: Qadamlar orasida cheksiz halqa (`A -> B -> A`) hosil bo'lsa, xavfsizlik yuzasidan reja rad etiladi.
- **Topologik Saralash (Kahn algoritmi)**: Barcha bog'liqliklarga rioya qilgan holda qadamlarning to'g'ri bajarilish tartibini (`execution_order`) hisoblash.

#### 4. Plan Optimizer (`PlanOptimizer`)
- **Dublikatlarni yo'qotish**: Bir xil asbob va parametrlarga ega bo'lgan takroriy qadamlar aniqlanadi, qisqartiriladi va bog'liqliklar oldingi qadamga avtomatik yo'naltiriladi.
- **Kontekst xotirasidan qayta foydalanish (`TaskContext`)**: Agar zarur ma'lumot faol vazifa xotirasida allaqachon mavjud bo'lsa, qadam qayta ishlatilgan deb belgilanadi va ortiqcha operatsiyalar oldi olinadi.

#### 5. Replanning Engine 2.0 (`ReplanningEngine`)
- **Failure-Aware Replanning**: Qadam ijrosi yoki tekshiruvi muvaffaqiyatsiz bo'lganda, Tool System 2.0 orqali mos zaxira asbob (Fallback Tool) qidiriladi.
- **Versiyalash (`v1 -> v2`)**: Qayta rejalashtirishda reja versiyasi oshiriladi, o'zgarish sababi qayd etiladi va frontend uchun `agent_plan_replanned` hodisasi yuboriladi.
- **Qat'iy xavfsizlik va chegaralar**:
  - `SECURITY_BLOCKED` holatida qayta rejalashtirish taqiqlanadi (xavfsizlikni chetlab o'tishning oldi olingan).
  - Tasdiqlash talab etiladigan amallarda avtomatik replan qilinmaydi.
  - `MAX_REPLANS = 2`: cheksiz replan sikllariga yo'l qo'yilmaydi.

#### 6. Observability (Kuzatuvchanlik) Kengaytirilishi (`observability.py`)
Planning 2.0 doirasida 7 ta yangi trace bosqichi joriy etildi:
- `PLAN_OPTIMIZED`: Reja optimallashtirilganda.
- `STEP_DEPENDENCY_RESOLVED`: Qadamning bog'liqligi yechilganda.
- `STEP_READY`: Qadam barcha talablar bajarilib ijroga tayyor bo'lganda.
- `STEP_BLOCKED`: Qadam qaramlik sababli to'xtatilganda.
- `PLAN_REPLAN_REQUIRED`: Xatolik sababli replan talab etilganda.
- `PLAN_REPLANNED`: Reja muvaffaqiyatli qayta tuzilganda.
- `PLAN_VERSION_CREATED`: Yangi reja versiyasi shakllantirilganda.

#### 7. Frontend Vizualizatsiyasi (`mikasa-7`)
- `mikasa-7/src/services/backendService.ts`: `PlanStepData` va `AgentPlanData` yangi Planning 2.0 maydonlari bilan kengaytirildi.
- `mikasa-7/src/pages/ChatPage.tsx`:
  - Agent Progress Card ga **Versiya Nishoni** (`v1`, `v2`) qo'shildi.
  - Qayta rejalashtirilganda **Replan Sababi Banneri** (`Rejalashtirildi vX: sabab`) ko'rsatiladi.
  - Har bir qadam yonida uning kerakli qobiliyati (`capability`) va bog'liqliklari (`deps: s1, s2`) ko'rsatiladi.

### 16.3. Test Natijalari va Verifikatsiya
- Yangi yaratilgan 6 ta test to'plami:
  1. `tests/test_plan_model.py` (6 ta test) — 100% OK.
  2. `tests/test_goal_decomposition.py` (9 ta test) — 100% OK.
  3. `tests/test_dependency_graph.py` (7 ta test) — 100% OK.
  4. `tests/test_plan_optimizer.py` (3 ta test) — 100% OK.
  5. `tests/test_replanning.py` (5 ta test) — 100% OK.
  6. `tests/test_planning_agent_integration.py` (5 ta test) — 100% OK.
- Jami yangi testlar: **35 ta test** (talab: 30+).
- Phases 31, 32 va 33 to'liq intellekt test to'plami: **128 ta test — 100% muvaffaqiyatli**.
- Frontend testlari (`npm test`): **10/10 test muvaffaqiyatli**.
- Frontend Production Build (`npm run build`): **297ms da 100% xatosiz yig'ildi**.

---

## 17. Phase 34 — Real Mikasa UI & Voice Experience

### 17.1. Arxitektura Konsepsiyasi va Asosiy Maqsad
Phase 34 doirasida Mikasa AI oddiy chat interfeysidan **jonli, ovozli va vizual mavjudlikka ega (Voice-First AI Presence)** haqiqiy operatsion tizim muhitiga aylantirildi.
Tizim foydalanuvchi taqdim etgan tog' va ko'l manzarali kinemotografik fon muhitini, 10 xil holatdagi reaktiv Mikasa Orb yadrosini, real vaqtdagi tizim telemetriyasini, to'liq o'zbekcha mahalliylashtirilgan ovoz nazoratini hamda Phase 31–33 intellektual AgentLoop va Planning 2.0 tizimlarini bitta uyg'un bosh sahifada birlashtirdi.

### 17.2. Amalga Oshirilgan Yangi Komponentlar va O'zgarishlar

#### 1. Kinemotografik Fon va Glassmorphism Tizimi (`assets/mikasa-bg.jpg`, `globals.css`)
- **Haqiqiy Ko'l va Tog' Foni**: Rasm `mikasa-7/src/assets/mikasa-bg.jpg` va `public/` papkalariga joylashtirildi.
- **Yumshoq Vinetka (`.cinematic-vignette`)**: Ko'lning sokin suvlari va issiq chiroqlarni to'sib qo'ymaslik uchun radial vinetka shaffofligi muvozanatlashtirildi.
- **Ultra-shaffof Shisha Panellar (`.glass-panel`, `.glass-card-interactive`, `.glass-pill-suggestion`)**: `backdrop-filter: blur(24px)` va `rgba(10, 16, 28, 0.68)` fon orqali yuqori kontrast va o'qilishi oson matnlar yaratildi.

#### 2. 10 Holatli Jonli Mikasa Orb (`components/MikasaOrb.tsx`)
- Orb markaziy vizual yadro sifatida quyidagi 10 ta real holatni qabul qiladi va har biri uchun maxsus vizual uslub va animatsiyani taqdim etadi:
  1. `idle`: Sokit shaffof ko'k nafas olish (`#38BDF8`).
  2. `listening`: Qizil-pushti pulsatsiya va ovoz amplitudasi bo'yicha kengayish (`#F43F5E`).
  3. `thinking`: Binafsha aylanma zarrachalar (`#A855F7`).
  4. `planning`: To'q ko'k kinetik orbital halqalar (`#6366F1`).
  5. `acting`: Moviy aylanuvchi va kinetik maydon (`#06B6D4`).
  6. `verifying`: Oltinrang nurli tekshiruv skaneri (`#F59E0B`).
  7. `replanning`: Qayta rejalashtirish fazasi o'zgarishi (`#EC4899`).
  8. `speaking`: Zumrad yashil tovush to'lqinlari (`#10B981`).
  9. `completed`: Muvaffaqiyatli yakunlash charaqlashi (`#10B981`).
  10. `error`: Qizil xatolik ogohlantirish tebranishi (`#EF4444`).
- Har bir holat tagida mikro-teg va yorug'lik nuri bilan holat nomi aks ettiriladi.

#### 3. Orb Atrofidagi Aylanma Tavsiyalar (Orbiting Suggestions)
- Orb atrofida sekin suzuvchi (floating animation: `orb-float-1` .. `orb-float-6`) 6 ta aqlli tavsiya tugmasi joylashtirildi:
  - `"Ob-havoni tekshir"` (SunIcon)
  - `"Kompyuterimni tekshir"` (CpuIcon)
  - `"Bugungi rejani tuz"` (ClockIcon)
  - `"Pythonni tushuntir"` (CodeIcon)
  - `"Faylni tahlil qil"` (FileTextIcon)
  - `"Internetdan izla"` (GlobeIcon)
- Bosilganda to'g'ridan-to'g'ri AgentLoop / Chat tizimiga so'rov yuboradi.

#### 4. Real Tizim Telemetriyasi — Chap Panel (`core/api_server.py`, `GET /api/system/metrics`)
- Backendda `psutil` orqali tizimning real ko'rsatkichlari olindi:
  - `cpu_percent`: Protsessor yuklamasi (rangli progress bar).
  - `ram_percent`, `ram_used_gb`, `ram_total_gb`: Operativ xotira hajmi va foizi.
  - `disk_percent`, `disk_free_gb`: Qattiq disk bo'sh joyi.
  - `network_sent_kb`, `network_recv_kb`: Tarmoq orqali yuklash va qabul tezligi.
  - `battery_percent`, `battery_plugged`: Batareya darajasi va quvvatlanish holati.
- Frontend har 3.5 soniyada ma'lumotlarni avtomatik yangilab boradi.

#### 5. Mening Vazifalarim — O'ng Panel (`pages/SchedulerPage.tsx` integratsiyasi)
- Rejalashtiruvchi vazifalar ro'yxati real vaqtda aks ettiriladi (`Faol`, `Kutilmoqda`, `Bajarildi`, `Takroriy`).
- Yangi vazifa qo'shish va "Bugungi kun rejasi"ni tuzish tugmalari mavjud.

#### 6. AgentLoop & Planning 2.0 Jonli Vizualizatsiyasi
- Reja tuzilganda markaziy maydonda Agent Rejasi kartasi ochiladi:
  - Reja maqsadi va versiya nishoni (`v1`, `v2`).
  - Qayta rejalashtirish yuz berganda sabab ko'rsatuvchi ogohlantirish banneri.
  - Har bir qadamning holati, ishlatilgan asbob (`tool`), semantik qobiliyati (`capability`) va verifikatsiya natijasi.
  - Tasdiqlash talab etiladigan amallarda "Tasdiqlash" / "Rad etish" interaktiv tugmalari.

#### 7. Ovozli Boshqaruv va O'zbekcha Mahalliylashtirish
- Web Speech API bilan integratsiya va xato yuz berganda aniq o'zbekcha xabar:
  `"Tovushli boshqaruv uchun mikrofon ruxsati kerak."`
- Real vaqtdagi o'zbekcha sana va soat formati:
  `"Seshanba, 15-sentabr • 22:45"`

### 17.3. Test Natijalari va Verifikatsiya
- Backend telemetriya testi: `tests/test_system_metrics_api.py` — 100% OK.
- Jami Python backend testlari (Phases 31–34): **129 ta test — 100% muvaffaqiyatli (0.374s)**.
- Frontend unit va stress testlari (`npm test`): **15/15 test — 100% muvaffaqiyatli**.
- Frontend Production Build (`npm run build`): **494ms da 100% xatosiz yig'ildi**.

---

## 18. PHASE 35–48: LEVEL 8 AUTONOMOUS ARCHITECTURE & RELEASE SYSTEM

Mikasa AI v8.0.0 arxitekturasi yagona mahalliy yordamchini to'liq tarmoqlangan, xavfsiz va avtonom yangilanuvchi shaxsiy AI operatsion tizimiga aylantirdi.

### 18.1. Kriptografik Xavfsizlik va Autentifikatsiya (Phases 40–44)
1. **Supabase Auth & Multi-Tenant**: `auth.users.id` yagona identity, email/parol, email tasdiqlash, parol tiklash va RLS orqali foydalanuvchilar ma'lumotlarini to'liq izolyatsiya qilish.
2. **PC Agent Enrollment & Pairing**: 6-xonali pairing kodi (5 min TTL), bruteforce himoyasi (max 5 urinish), Ed25519 ochiq/yopiq kalitlar juftligi va Windows DPAPI xavfsiz saqlash.
3. **Replay Himoyasi**: 32-bayt bir martalik tasodifiy nonce asosidagi challenge-response protokoli.

### 18.2. Masofaviy Boshqaruv va Gateway (Phases 38–39, 45–47)
1. **Universal Telegram Gateway**: Telegram orqali masofadan buyruq yuborish, status olish, skrinshot so'rash va Wake-on-LAN (WoL) orqali kompyuterni uyg'otish.
2. **Windows Agent & Real Tools**: `PathSecurityValidator` orqali sandboxlangan fayl tizimi boshqaruvi, audio balandligi, ilovalarni boshqarish va ekran tahlili.

### 18.3. Xavfsiz Avto-Yangilanish Tizimi (Phase 48)
1. **SemVer 2.0.0**: Versiyalarni qat'iy semantik taqqoslash (8.0.0 -> 8.1.0).
2. **Ed25519 & SHA-256 Verifikatsiyasi**: Fail-closed prinsipida har bir yuklangan faylning kriptografik imzosi va xeshi tekshiriladi.
3. **Atomik Staging va Avtomatik Rollback**: Nosozlik yuz berganda avtomatik avvalgi ishchi versiyaga qaytish.
4. **Ishlab Chiqarish Paketlari (`release/v8.0.0/`)**: Portable (`.exe`), Setup (`.exe`), Windows MSI (`.msi`), DLL va imzolangan `version_manifest.json`.

### 18.4. Yakuniy Test va Verifikatsiya
- **Backend Testlari**: 242/242 PASS (100% muvaffaqiyatli).
- **Secure Auto-Updater Testlari**: 31/31 PASS (100% muvaffaqiyatli).
- **Frontend Testlari**: 15/15 PASS (100% muvaffaqiyatli).
- **GitHub Release CI/CD**: Avtomatlashtirilgan GitHub Actions reliz pipeline muvaffaqiyatli ishga tushdi va v8.0.0 relizi e'lon qilindi.



