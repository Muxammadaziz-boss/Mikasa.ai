# 🤖 MIKASA AI AGENT UPGRADE — DAVOM ETTIRISH UCHUN PROMPT

> **Maqsad:** Mikasa AI ni Level 2 (Tool-Calling Chatbot) dan Level 4 (Autonomous Desktop Agent) ga o'tkazish.
> **Loyiha:** `d:\Ishchi stoli\Mikasa\yordamchi_3.1.0\`
> **Til:** Python 3.10+, Windows, O'zbek tili

---

## 📍 HOZIRGI HOLAT (qaerga yetildi)

Task.md ni ko'ring: `C:\Users\user\.gemini\antigravity\brain\b4888c6c-a65d-4823-8acb-772c6650f1ac\task.md`

Quyidagi faza **HALI BOSHLANMAGAN** bo'lsa, shu fazadan boshlang.
Agar faza **YARIM QOLGAN** bo'lsa, task.md dagi [/] belgili itemlarni davom eting.

---

## 🏗️ ARXITEKTURA (muhim fayllar)

```
main.py              — 2100+ qator, asosiy pipeline: tingla() → buyruqni_tushun() → _intent_bajar()
ai_engine.py         — Gemini/OpenRouter API, SYSTEM_PROMPT, ai_savol_yuborish()
config.py            — Konfiguratsiya (config.json), logging

core/
  agent_planner.py   — ReActAgent class, ReAct loop (15 qadam, retry)
  agent_tools.py     — 20 ta tool (ToolRegistry, Tool dataclass)
  agent_memory.py    — AgentMemory (3 darajali: RAM, fayl, bilim)
  agent_scheduler.py — Vaqtli vazifalar (eslatmalar)
  agent_plugins.py   — Plugin tizimi (JSON/Python)
  smart_algorithms.py — TF-IDF intent classification
  tts_manager.py     — Silero TTS boshqaruvi

gui/
  app.py             — CustomTkinter GUI (8 sahifa)
  pages/chat.py      — AI chat sahifasi
```

---

## 📋 8 FAZA — KETMA-KET BAJARISH

### FAZA 1: UNIFIED PIPELINE (Eng muhim!)

**Fayl:** `main.py`

**Hozirgi muammo:** `buyruqni_tushun()` funksiyasi 3 ta alohida tizimni chaqiradi:
1. `buyruqni_aniqla(matn)` — regex pattern matching  
2. `smart_algorithms.buyruqni_tushun_v2(matn)` — TF-IDF classification
3. `ai_savol_yuborish(matn)` — Gemini API (AI intent detection)
4. `agent_pipeline_run(matn)` — Agent (agar hech biri ishlamasa)

**QILISH KERAK:**
1. `buyruqni_tushun()` ni **soddalashtirish:**
   ```python
   def buyruqni_tushun(matn):
       # 1-qadam: TEZKOR buyruqlar (regex FAQAT aniq pattern uchun)
       tezkor = buyruqni_aniqla(matn)  # volume_up, play_video, pause kabilar
       if tezkor and tezkor != "unknown":
           return _intent_bajar(tezkor, matn)
       
       # 2-qadam: QOLGAN HAMMASI → Agent pipeline
       return agent_pipeline_run(matn)
   ```
2. `ai_savol_yuborish()` ni OLIB TASHLASH (Agent o'zi Gemini chaqiradi `agent_ai_call` orqali)
3. TF-IDF ni faqat tezkor buyruqlar uchun qoldirish (yoki olib tashlash)
4. `_intent_bajar()` da AI-generated intent parsing ni olib tashlash

**TEST:** 
- "ovozni baland qil" → regex topadi → tezkor bajar ✅
- "dollar kursi" → regex topmaydi → Agent pipeline ✅
- "login sahifa yoz" → Agent pipeline ✅

---

### FAZA 2: PLANNING MODULE

**Fayl:** `core/agent_planner.py`

**Hozirgi holat:** `_run_internal()` da agent har bir qadamda AI dan "keyingi nima?" deb so'raydi. Plan yo'q.

**QILISH KERAK:**
1. `_run_internal()` boshiga PLANNING PHASE qo'shish:
   ```python
   def _run_internal(self, user_input, conversation_history=None):
       # ===== FAZA 0: PLAN TUZISH =====
       plan = self._create_plan(user_input, conversation_history)
       self._notify(0, "plan", {"plan": plan})
       
       # ===== FAZA 1-N: PLAN BO'YICHA BAJARISH =====
       for i, step in enumerate(plan, 1):
           result = self._execute_step(step, i)
           if result.get("error"):
               # RE-PLAN: xato bo'lsa plan qayta tuziladi
               plan = self._replan(user_input, plan, i, result)
               ...
   ```

2. System prompt ga plan formati qo'shish:
   ```
   AVVAL plan tuz, keyin bajar. Plan formati:
   {"action": "plan", "steps": [
     {"tool": "app_check", "params": {...}, "reason": "Chrome bormi tekshirish"},
     {"tool": "system_control", "params": {...}, "reason": "Chrome ochish"},
     {"tool": "screen_analyze", "params": {...}, "reason": "Ochildimi tekshirish"}
   ]}
   ```

3. `_create_plan()` metodi — AI dan plan olish
4. `_replan()` metodi — xato bo'lganda qayta rejalashtirish
5. `_execute_step()` — bitta qadamni bajarish

---

### FAZA 3: VERIFY LOOP

**Fayl:** `core/agent_planner.py`

**QILISH KERAK:**
1. `VERIFIABLE_TOOLS` set yaratish:
   ```python
   VERIFIABLE_TOOLS = {"system_control", "file_write", "keyboard_shortcut", "screen_click"}
   ```

2. `_execute_step()` ichida tool natijasidan keyin:
   ```python
   if tool_name in VERIFIABLE_TOOLS and result.get("success"):
       verify = self.tools.call("screen_analyze", 
           question=f"Hozir {tool_name} muvaffaqiyatli bajarildimi?")
       if "muvaffaqiyatsiz" in verify.get("message", "").lower():
           return {"success": False, "error": "Tekshiruv muvaffaqiyatsiz"}
   ```

---

### FAZA 4: YANGI TOOL'LAR (6 ta)

**Fayl:** `core/agent_tools.py` — faylning oxiriga qo'shish, `create_default_registry()` ga register qilish.

#### Tool 1: clipboard
```python
def _clipboard(action="get", text=""):
    import win32clipboard  # yoki ctypes
    if action == "get":
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData()
            return {"message": data[:500], "content": data}
        except: return {"message": "Clipboard bo'sh", "content": ""}
        finally: win32clipboard.CloseClipboard()
    elif action == "set":
        import pyperclip
        pyperclip.copy(text)
        return {"message": f"Nusxalandi: {text[:50]}"}
```

#### Tool 2: process_manager
```python
def _process_manager(action="list", name="", pid=0):
    import psutil
    if action == "list":
        procs = [(p.pid, p.name(), p.cpu_percent()) for p in psutil.process_iter(['name','cpu_percent'])]
        return {"processes": procs[:30], "message": f"{len(procs)} ta process"}
    elif action == "kill":
        for p in psutil.process_iter(['name','pid']):
            if name.lower() in (p.info['name'] or '').lower():
                p.terminate()
                return {"message": f"{name} to'xtatildi"}
```

#### Tool 3: audio_control
```python
def _audio_control(action="get", level=50):
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    if action == "get":
        current = int(volume.GetMasterVolumeLevelScalar() * 100)
        return {"level": current, "message": f"Ovoz: {current}%"}
    elif action == "set":
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return {"message": f"Ovoz {level}% ga qo'yildi"}
    elif action == "mute": volume.SetMute(1, None)
    elif action == "unmute": volume.SetMute(0, None)
```

#### Tool 4: system_info
```python
def _system_info(category="all"):
    import psutil
    info = {}
    if category in ("all", "cpu"): info["cpu"] = f"{psutil.cpu_percent()}%"
    if category in ("all", "ram"):
        mem = psutil.virtual_memory()
        info["ram"] = f"{mem.percent}% ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)"
    if category in ("all", "disk"):
        disk = psutil.disk_usage('/')
        info["disk"] = f"{disk.percent}% ({disk.free // (1024**3)}GB bo'sh)"
    if category in ("all", "battery"):
        bat = psutil.sensors_battery()
        if bat: info["battery"] = f"{bat.percent}%{' (zaryadda)' if bat.power_plugged else ''}"
    return {"info": info, "message": " | ".join(f"{k}: {v}" for k,v in info.items())}
```

#### Tool 5: window_manager
```python
def _window_manager(action="list", window="", width=0, height=0):
    import ctypes
    # EnumWindows → find window → ShowWindow/MoveWindow
    # action: minimize, maximize, restore, resize, close, list
```

#### Tool 6: notification
```python
def _notification(title="Mikasa AI", message="", duration=5):
    try:
        from plyer import notification as notif
        notif.notify(title=title, message=message, timeout=duration)
    except ImportError:
        # Fallback: PowerShell toast
        import subprocess
        ps = f'''[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$template.GetElementsByTagName('text')[0].AppendChild($template.CreateTextNode('{title}'))
$template.GetElementsByTagName('text')[1].AppendChild($template.CreateTextNode('{message}'))
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Mikasa AI').Show([Windows.UI.Notifications.ToastNotification]::new($template))'''
        subprocess.run(["powershell", "-Command", ps], capture_output=True)
```

---

### FAZA 5: REFLECTIVE MEMORY

**Yangi fayl:** `core/agent_lessons.py`
```python
class AgentLessons:
    def __init__(self):
        self._file = os.path.join(BASE_DIR, "agent_lessons.json")
        self._lessons = self._load()
    
    def save_lesson(self, situation, wrong_action, correct_action, tool=""):
        self._lessons.append({
            "situation": situation,
            "wrong": wrong_action,
            "correct": correct_action,
            "tool": tool,
            "time": datetime.now().isoformat()
        })
        self._save()
    
    def get_relevant(self, task, limit=3):
        # Oddiy keyword match (kelajakda embedding bilan)
        matches = []
        for lesson in self._lessons:
            if any(w in task.lower() for w in lesson["situation"].lower().split()):
                matches.append(lesson)
        return matches[-limit:]
    
    def format_for_prompt(self, task):
        lessons = self.get_relevant(task)
        if not lessons:
            return ""
        lines = ["OLDINGI SABOQLAR (xatolardan o'rgangan):"]
        for l in lessons:
            lines.append(f"- Vaziyat: {l['situation']}")
            lines.append(f"  NOTO'G'RI: {l['wrong']}")
            lines.append(f"  TO'G'RI: {l['correct']}")
        return "\n".join(lines)
```

**O'zgartirish:** `agent_planner.py` → system prompt ga `lessons.format_for_prompt(user_input)` qo'shish.
**O'zgartirish:** `_tool_call_with_retry()` → oxirgi urinish ham xato bo'lsa `save_lesson()` chaqirish.

---

### FAZA 6: CONTEXT WINDOW MANAGEMENT

**Fayl:** `core/agent_planner.py`

```python
MAX_HISTORY_CHARS = 8000  # ~2000 token

def _trim_history(self, history):
    total = sum(len(m["content"]) for m in history)
    while total > MAX_HISTORY_CHARS and len(history) > 2:
        removed = history.pop(0)
        total -= len(removed["content"])
    return history
```

`_build_prompt()` ichida `self._trim_history(history)` chaqirish.

**Fayl:** `ai_engine.py` — `suhbat_tarixi_gemini` ni ham shu usulda cheklash.

---

### FAZA 7: INTERRUPT + CANCEL

**Fayl:** `core/agent_planner.py`
```python
class ReActAgent:
    def __init__(self, ...):
        ...
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def _run_internal(self, ...):
        self._cancelled = False
        for step_num in range(...):
            if self._cancelled:
                return {"response": "Agent to'xtatildi", "success": False, ...}
            ...
```

**Fayl:** `gui/pages/chat.py` — Agent ishlayotganda "❌ To'xtatish" tugmasi ko'rinadi, bosganda `agent.cancel()` chaqiriladi.

---

### FAZA 8: STREAMING TTS

**Fayl:** `main.py` → `ovoz_chiqar_tez()`
```python
def ovoz_chiqar_tez(matn):
    # Gaplarni ajratish
    gaplar = re.split(r'[.!?।]', matn)
    gaplar = [g.strip() for g in gaplar if g.strip()]
    
    # Birinchi gapni darhol gapirib, qolganlarini parallel tayyorlash
    for gap in gaplar:
        _gapirib_ber(gap)  # Blokirovka qiluvchi TTS
```

---

## 🔧 MUHIM TEXNIK ESLATMALAR

1. **`re` import** — `main.py` da 4-qatorda bor, `agent_planner.py` da 5-qatorda bor
2. **`psutil`** — allaqachon ishlatilmoqda (main.py:53)
3. **`pycaw`** — allaqachon ishlatilmoqda (main.py:60-70)
4. **`pyautogui`** — allaqachon ishlatilmoqda (main.py:42, agent_tools.py)
5. **`keyboard`** — allaqachon ishlatilmoqda (main.py:41)
6. **`ctypes`** — Windows API uchun (EnumWindows, SetForegroundWindow)
7. **Test:** `python -m py_compile <fayl>` — har bir faza tugaganda syntax tekshiring
8. **Thread safety:** `GlobalState` da `RLock` bor — yangi o'zgarishlar ham thread-safe bo'lsin
9. **Tool register:** Har bir yangi Tool `create_default_registry()` ga qo'shilsin (agent_tools.py:1456)

## ⚠️ XAVFSIZLIK

1. `process_manager.kill()` — faqat user tasdiqlashidan keyin
2. `file_write` — `.exe`, `.dll`, `.bat` yozishga RUXSAT BERMANG
3. `keyboard_shortcut` — "delete", "format" kabi xavfli shortcutlarni BLOKLANG
4. `shell=True` — HECH QACHON ishlatmang
5. `eval()` — HECH QACHON ishlatmang

---

## ✅ TASK.MD FORMATI

Har bir faza boshlanganida `task.md` ni yangilang:
```markdown
- [x] Faza 1: Unified Pipeline ✅
- [/] Faza 2: Planning Module (hozir ishlayapman)
  - [x] _create_plan() metodi
  - [/] _replan() metodi
  - [ ] System prompt yangilash
- [ ] Faza 3: Verify Loop
...
```
