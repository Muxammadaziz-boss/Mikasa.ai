# ========== api_server.py ==========
# Mikasa AI 7.1.0 — Desktop Background Backend API Server
# Ushbu server Tauri frontend (React) va Python AI yadrosi (main.py, ai_engine,
# agent_memory, agent_scheduler, agent_tools, command_dispatcher) orasidagi
# to'liq asinxron ko'prik (REST + WebSocket) hisoblanadi.
# Port: 127.0.0.1:18420

import os
import sys
import json
import asyncio
import logging
import threading
from datetime import datetime
from aiohttp import web

# Ishchi katalogni to'g'ri o'rnatish
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MikasaAPIServer")

# Backend modullari kesh singletonlari
_main = None
_ai_engine = None
_agent_memory = None
_agent_scheduler = None
_tool_registry = None
_command_dispatcher = None

_active_ws_clients = set()
_voice_state = "idle"  # idle | listening | thinking | speaking
_main_loop = None

def get_modules():
    global _main, _ai_engine, _agent_memory, _agent_scheduler, _tool_registry, _command_dispatcher
    if _main is None:
        try:
            import main as m
            _main = m
        except Exception as e:
            logger.error(f"main.py yuklashda xatolik: {e}")

    if _ai_engine is None:
        try:
            from core import ai_engine
            _ai_engine = ai_engine
        except Exception as e:
            logger.error(f"ai_engine yuklashda xatolik: {e}")

    if _agent_memory is None:
        try:
            from core.agent_memory import get_memory
            _agent_memory = get_memory()
        except Exception as e:
            logger.error(f"agent_memory yuklashda xatolik: {e}")

    if _agent_scheduler is None:
        try:
            from core.agent_scheduler import get_scheduler
            _agent_scheduler = get_scheduler()
            _agent_scheduler.start()
            
            def _scheduler_callback(task):
                text = task.data.get("text", "Eslatma!")
                logger.info(f"Rejalashtirilgan vazifa bajarildi: {task.task_id} -> {text}")
                sync_broadcast("scheduler_alarm", {
                    "id": task.task_id,
                    "text": text,
                    "type": task.task_type,
                    "time": datetime.now().isoformat()
                }, _main_loop)
                if _main and hasattr(_main, "gui_ga_xabar_yuborish"):
                    try:
                        _main.gui_ga_xabar_yuborish(f"⏰ Eslatma: {text}", ovoz=True)
                    except Exception:
                        pass

            _agent_scheduler.set_callback(_scheduler_callback)
        except Exception as e:
            logger.error(f"agent_scheduler yuklashda xatolik: {e}")

    if _tool_registry is None:
        try:
            from core.agent_tools import get_registry
            _tool_registry = get_registry()
        except Exception as e:
            logger.error(f"tool_registry yuklashda xatolik: {e}")

    if _command_dispatcher is None:
        try:
            from core.command_dispatcher import CommandDispatcher
            _command_dispatcher = CommandDispatcher()
        except Exception as e:
            logger.error(f"command_dispatcher yuklashda xatolik: {e}")

    return _main, _ai_engine, _agent_memory, _agent_scheduler, _tool_registry, _command_dispatcher


# ========== WebSocket Broadcaster ==========
async def broadcast_ws(event_type: str, data: dict):
    if not _active_ws_clients:
        return
    message = json.dumps({"type": event_type, "data": data, "timestamp": datetime.now().isoformat()})
    dead_clients = set()
    for ws in list(_active_ws_clients):
        try:
            if not ws.closed:
                await ws.send_str(message)
            else:
                dead_clients.add(ws)
        except Exception:
            dead_clients.add(ws)
    _active_ws_clients.difference_update(dead_clients)


def sync_broadcast(event_type: str, data: dict, loop=None):
    """Thread-safe usulda WebSocket xabar tarqatish"""
    target_loop = loop or _main_loop
    if target_loop and target_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_ws(event_type, data), target_loop)


# ========== Helper functions for User & Voice ==========
def get_current_user_name() -> str:
    """Foydalanuvchi ismini olish (birinchi navbatda foydalanuvchi_ismi.txt, keyin config.json)"""
    txt_file = os.path.join(BASE_DIR, "data", "foydalanuvchi_ismi.txt")
    if os.path.exists(txt_file):
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                name = f.read().strip()
                if name:
                    return name
        except Exception:
            pass
    cfg = _read_config()
    cfg_name = cfg.get("user", {}).get("name")
    if cfg_name:
        return cfg_name
    m, _, _, _, _, _ = get_modules()
    if m and hasattr(m, "foydalanuvchi_ismi_ol"):
        try:
            m_name = m.foydalanuvchi_ismi_ol()
            if m_name:
                return m_name
        except Exception:
            pass
    return "Ustoz"


def get_current_voice_type() -> str:
    """Ovoz turini olish (ayol yoki erkak)"""
    txt_file = os.path.join(BASE_DIR, "data", "ovoz_turi.txt")
    if os.path.exists(txt_file):
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                voice = f.read().strip()
                if voice in ["ayol", "erkak"]:
                    return voice
        except Exception:
            pass
    cfg = _read_config()
    cfg_voice = cfg.get("user", {}).get("voice_type")
    if cfg_voice in ["ayol", "erkak"]:
        return cfg_voice
    return "ayol"


# ========== 1. STATUS HANDLER ==========
async def handle_status(request):
    """GET /api/status - Tizim holati"""
    m, ai, mem, sched, tools, _ = get_modules()
    user = get_current_user_name()
    ai_ok = ai.ai_mavjudmi() if ai else False
    
    return web.json_response({
        "status": "online",
        "app": "MIKASA AI",
        "version": "7.1.0",
        "user": user,
        "ai_available": ai_ok,
        "voice_state": _voice_state,
        "tools_count": tools.count if tools else 0,
        "scheduled_tasks": sched.active_count if sched else 0,
        "timestamp": datetime.now().isoformat()
    })



# ========== 2. CHAT & VOICE HANDLERS ==========
def execute_command_pipeline(text: str, user: str, ovoz: str, mode: str = "ask") -> str:
    """
    Mikasa AI 7.1.0 — Unified Command & AI Pipeline
    Mahalliy buyruqlarni darhol kompyuterda bajaradi, murakkab savollarni AI ga yo'naltiradi.
    """
    clean_text = text.strip()
    if not clean_text:
        return "Bo'sh so'rov."

    m, ai, mem, _, _, dispatcher = get_modules()
    last_gui_messages = []

    def _gui_collector(msg):
        last_gui_messages.append(str(msg))

    if m and hasattr(m, "gui_bilan_integratsiya"):
        m.gui_bilan_integratsiya(_gui_collector)

    # 1. Tezkor Mahalliy Buyruqlar Dispatcheri (command_dispatcher)
    if dispatcher:
        try:
            handled, res_msg = dispatcher.dispatch_local(clean_text)
            if handled and res_msg:
                logger.info(f"CommandDispatcher bajardi: '{clean_text}' -> {res_msg}")
                return res_msg
        except Exception as e:
            logger.warning(f"Dispatcher xatosi: {e}")

    # 2. Mahalliy Intent tekshirish (buyruqni_aniqla) — faqat BUYRUQLAR uchun, savollar AI ga yo'naltiriladi
    has_question = "?" in clean_text or any(w in clean_text for w in [
        "bormi", "bormikan", "o'rnatilganmi", "ornatilganmi", "mavjudmi",
        "shunga o'xshash", "shunga oxshash", "o'xshash", "oxshash",
        "nima", "qanday", "qanaqa", "necha", "qachon", "kim", "nega",
        "haqida", "tavsiya", "maslahat", "fikr", "bilasanmi"
    ])

    intent = "unknown"
    if not has_question and m and hasattr(m, "buyruqni_aniqla"):
        try:
            intent = m.buyruqni_aniqla(clean_text)
        except Exception:
            intent = "unknown"

    if isinstance(intent, tuple):
        cmd, val = intent[0], intent[1]
        try:
            if cmd == "volume_set" and hasattr(m, "ovoz_sozlash"):
                m.ovoz_sozlash(val)
                return f"🔊 Ovoz {val}% ga sozlandi."
            elif cmd == "volume_up" and hasattr(m, "ovoz_oshir"):
                m.ovoz_oshir(val)
                return f"🔊 Ovoz {val}% oshirildi."
            elif cmd == "volume_down" and hasattr(m, "ovoz_pasaytir"):
                m.ovoz_pasaytir(val)
                return f"🔉 Ovoz {val}% pasaytirildi."
            elif cmd == "video_number" and hasattr(m, "youtube_video_boshla_koordinata"):
                m.youtube_video_boshla_koordinata(val)
                return f"▶️ {val}-video ochilmoqda."
        except Exception as e:
            return f"Ovozni sozlashda xatolik: {e}"

    if intent != "unknown" and m and hasattr(m, "_intent_bajar"):
        try:
            logger.info(f"Mahalliy intent bajarilmoqda: {intent} (matn: '{clean_text}')")
            m._intent_bajar(intent, params=None, matn=clean_text, foydalanuvchi_ismi=user)
            if last_gui_messages:
                return last_gui_messages[-1]
            
            intent_messages = {
                "open_youtube": "✅ YouTube ochildi.",
                "open_telegram": "✅ Telegram ochildi.",
                "open_chrome": "✅ Chrome ochildi.",
                "open_code": "✅ VS Code ochildi.",
                "open_brave": "✅ Brave brauzeri ochildi.",
                "open_discord": "✅ Discord ochildi.",
                "music_play": "▶️ Musiqa davom etmoqda.",
                "music_pause": "⏸️ Musiqa to'xtatildi.",
                "music_restart": "🔄 Musiqa boshidan boshlandi.",
                "play_video": "▶️ Video qo'yildi.",
                "pause_video": "⏸️ Video to'xtatildi.",
                "next_video": "⏭️ Keyingi videoga o'tildi.",
                "prev_video": "⏮️ Oldingi videoga o'tildi.",
                "show_desktop": "🖥️ Ish stoli ko'rsatildi.",
                "switch_window": "🔄 Oyna almashtirildi.",
                "open_explorer": "📁 Fayl menejeri ochildi.",
                "open_cmd": "💻 Terminal ochildi.",
                "open_taskmanager": "📊 Vazifa menejeri ochildi.",
                "take_screenshot": "📸 Ekran rasmi olindi.",
                "minimize_all": "🗕 Barcha oynalar kichraytirildi.",
                "close_window": "❌ Oyna yopildi.",
                "close_chrome": "🗑️ Chrome oynasi yopildi.",
                "open_settings": "⚙️ Sozlamalar paneli ochildi."
            }
            return intent_messages.get(intent, f"✅ Buyruq muvaffaqiyatli bajarildi ({intent}).")
        except Exception as e:
            logger.error(f"Intent bajarishda xatolik: {e}")
            return f"Buyruq bajarishda xatolik: {e}"

    # 3. AI ga yo'naltirish
    if mode == "summary" and ai:
        prompt = f"Quyidagi matnni tahlil qilib, eng muhim jihatlarini qisqa va aniq xulosalab ber:\n\n{clean_text}"
        reply = ai.ai_savol_yuborish(prompt, user)
        return reply if isinstance(reply, str) else str(reply)
    elif ai:
        try:
            reply = ai.ai_savol_yuborish(clean_text, user)
            
            # Agar AI bu buyruq deb topsa, kompyuterda haqiqatdan bajarish!
            if isinstance(reply, dict) and reply.get("type") == "command":
                ai_intent = reply.get("intent")
                ai_params = reply.get("params", {})
                ai_resp = reply.get("response", "Buyruq bajarildi.")
                
                if m and hasattr(m, "_intent_bajar") and ai_intent:
                    try:
                        logger.info(f"AI command bajarilmoqda: {ai_intent} (params: {ai_params})")
                        m._intent_bajar(ai_intent, params=ai_params, matn=clean_text, foydalanuvchi_ismi=user)
                        if last_gui_messages:
                            return last_gui_messages[-1]
                    except Exception as e:
                        logger.error(f"AI intent bajarishda xatolik: {e}")
                
                return ai_resp

            elif isinstance(reply, dict):
                return reply.get("response") or reply.get("javob") or str(reply)
            elif reply:
                return str(reply)
        except Exception as e:
            logger.error(f"AI savolida xatolik: {e}")
            return f"Xatolik yuz berdi: {e}"
    else:
        return "Kechirasiz, sun'iy intellekt moduli mavjud emas."

    return "Kechirasiz, buyruqni tushunib bo'lmadi."


async def handle_chat(request):
    """POST /api/chat - Matnli savol yoki buyruq yuborish"""
    global _voice_state
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    text = body.get("text", "").strip()
    mode = body.get("mode", "ask")
    speak_out = body.get("speak", False) or mode == "voice"

    if not text:
        return web.json_response({"ok": False, "error": "Matn bo'sh bo'lishi mumkin emas"}, status=400)

    m, _, mem, _, _, _ = get_modules()
    user = get_current_user_name()
    ovoz = get_current_voice_type()

    loop = asyncio.get_running_loop()
    _voice_state = "thinking"
    sync_broadcast("voice_state", {"state": "thinking"}, loop)

    def _execute():
        global _voice_state
        try:
            reply_text = execute_command_pipeline(text, user, ovoz, mode)
            if mem:
                try:
                    mem.add_conversation(text, reply_text[:500])
                except Exception:
                    pass

            if speak_out and m and hasattr(m, "ovoz_chiqar_tez"):
                sync_broadcast("voice_state", {"state": "speaking"}, loop)
                m.ovoz_chiqar_tez(reply_text)

            return reply_text
        except Exception as e:
            logger.error(f"Chat bajarishda xatolik: {e}")
            return f"Xatolik yuz berdi: {e}"
        finally:
            if not speak_out:
                _voice_state = "idle"
                sync_broadcast("voice_state", {"state": "idle"}, loop)

    response_text = await loop.run_in_executor(None, _execute)
    await broadcast_ws("ai_response", {"text": response_text, "mode": mode})

    return web.json_response({
        "ok": True,
        "response": response_text,
        "user": user,
        "mode": mode,
        "timestamp": datetime.now().isoformat()
    })


async def handle_voice_start(request):
    """POST /api/voice/start - Ovozli tinglashni boshlash"""
    global _voice_state
    m, _, _, _, _, _ = get_modules()
    if not m:
        return web.json_response({"ok": False, "error": "Backend moduli yuklanmagan"}, status=500)

    loop = asyncio.get_running_loop()
    _voice_state = "listening"
    await broadcast_ws("voice_state", {"state": "listening"})

    def _voice_callback(msg):
        import re
        msg_str = str(msg).strip()
        sync_broadcast("voice_event", {"message": msg_str}, loop)

        # 1. Foydalanuvchi gapirganini aniqlash
        if "🗣️ Siz:" in msg_str:
            user_text = msg_str.split("🗣️ Siz:", 1)[1].strip()
            sync_broadcast("voice_state", {"state": "thinking"}, loop)
            sync_broadcast("voice_transcript", {"text": user_text, "sender": "user"}, loop)
        # 2. Agent yoki AI javobi
        elif any(marker in msg_str for marker in ["🤖 Agent:", "🤖 AI:", "✨", "✅", "👋 Salom"]):
            clean_reply = re.sub(r"^[🤖✨✅⚠️❌]\s*(?:Agent:|AI:)?\s*", "", msg_str).strip()
            sync_broadcast("voice_state", {"state": "speaking"}, loop)
            sync_broadcast("ai_response", {"text": clean_reply, "mode": "voice"}, loop)
            sync_broadcast("voice_transcript", {"text": clean_reply, "sender": "mikasa"}, loop)
        # 3. Tinglash holatiga qaytish
        elif "🎙️ Tinglash boshlandi" in msg_str or "Tinglash davom" in msg_str:
            sync_broadcast("voice_state", {"state": "listening"}, loop)
        elif "🛑 Tinglash to'xtatildi" in msg_str:
            sync_broadcast("voice_state", {"state": "idle"}, loop)

    def _listen():
        global _voice_state
        try:
            user = get_current_user_name()
            ovoz = get_current_voice_type()
            m.global_state.tinglash_faol = True
            m.global_state.gapirmoqda = False
            m.fon_xizmat(user, ovoz, _voice_callback)
        except Exception as e:
            logger.error(f"Ovozli tinglashda xato: {e}")
        finally:
            _voice_state = "idle"
            sync_broadcast("voice_state", {"state": "idle"}, loop)

    t = threading.Thread(target=_listen, daemon=True, name="ApiVoiceThread")
    t.start()
    return web.json_response({"ok": True, "status": "listening"})


async def handle_voice_stop(request):
    """POST /api/voice/stop - Ovozli tinglashni to'xtatish"""
    global _voice_state
    m, _, _, _, _, _ = get_modules()
    if m:
        m.global_state.tinglash_faol = False
        m.global_state.gapirmoqda = False
    _voice_state = "idle"
    await broadcast_ws("voice_state", {"state": "idle"})
    return web.json_response({"ok": True, "status": "stopped"})


async def handle_voice_speak(request):
    """POST /api/voice/speak - Istalgan matnni ovoz chiqarib o'qish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    text = body.get("text", "").strip()
    if not text:
        return web.json_response({"ok": False, "error": "Matn kiritilmadi"}, status=400)

    m, _, _, _, _, _ = get_modules()
    if m and hasattr(m, "ovoz_chiqar_tez"):
        loop = asyncio.get_running_loop()
        sync_broadcast("voice_state", {"state": "speaking"}, loop)
        m.ovoz_chiqar_tez(text)
        return web.json_response({"ok": True, "message": "Ovoz chiqarilmoqda"})
    return web.json_response({"ok": False, "error": "Audio moduli mavjud emas"}, status=500)


async def handle_chat_clear(request):
    """POST /api/chat/clear - Suhbat tarixini tozalash"""
    _, ai, mem, _, _, _ = get_modules()
    if ai:
        ai.suhbat_tarixini_tozalash()
    if mem:
        mem.clear_context()
    await broadcast_ws("chat_cleared", {})
    return web.json_response({"ok": True, "message": "Suhbat tarixi tozalandi"})


# ========== 3. BUYRUQLAR (COMMANDS) HANDLERS ==========
DEFAULT_COMMANDS_CATALOG = [
    {"id": "c1", "name": "Telegramni och", "query": "telegram", "category": "Ilovalar", "icon": "send", "desc": "Telegram messenjerini ishga tushiradi"},
    {"id": "c2", "name": "YouTube-ni och", "query": "youtube", "category": "Multimedia", "icon": "video", "desc": "Brauzerda YouTube portalini ochadi"},
    {"id": "c3", "name": "VS Code-ni och", "query": "vs code", "category": "Ilovalar", "icon": "code", "desc": "Dasturlash muhitini ishga tushiradi"},
    {"id": "c4", "name": "Brauzerni och", "query": "brauzerni och", "category": "Ilovalar", "icon": "globe", "desc": "Standart internet brauzerini ishga tushiradi"},
    {"id": "c5", "name": "Fayl menejeri", "query": "fayllar", "category": "Tizim", "icon": "folder", "desc": "Windows Explorer fayl menejerini ochadi"},
    {"id": "c6", "name": "Task Menejer", "query": "vazifa menejeri", "category": "Tizim", "icon": "activity", "desc": "Tizim jarayonlari dispetcherini ochadi"},
    {"id": "c7", "name": "Terminal (CMD)", "query": "terminal", "category": "Tizim", "icon": "terminal", "desc": "Windows buyruq satrini ochadi"},
    {"id": "c8", "name": "Skrinshot olish", "query": "skrinshot", "category": "Tizim", "icon": "camera", "desc": "Butun ekranni rasmga olib saqlaydi"},
    {"id": "c9", "name": "Ish stoli", "query": "ish stoli", "category": "Tizim", "icon": "monitor", "desc": "Barcha oynalarni yashirib ish stolini ko'rsatadi"},
    {"id": "c10", "name": "Ovoz 50%", "query": "ovoz 50", "category": "Ovoz", "icon": "volume-2", "desc": "Kompyuter tovush darajasini 50% ga sozlaydi"},
    {"id": "c11", "name": "Ovozni oshir", "query": "ovozni oshir 20", "category": "Ovoz", "icon": "volume-1", "desc": "Tovush balandligini 20 foizga ko'taradi"},
    {"id": "c12", "name": "Ovozni pasaytir", "query": "ovozni pasaytir 20", "category": "Ovoz", "icon": "volume-x", "desc": "Tovush balandligini 20 foizga pasaytiradi"},
    {"id": "c13", "name": "Musiqani to'xtat", "query": "musiqani to'xtat", "category": "Multimedia", "icon": "pause", "desc": "Ijro etilayotgan musiqani to'xtatadi"},
    {"id": "c14", "name": "Musiqani davom et", "query": "davom et", "category": "Multimedia", "icon": "play", "desc": "To'xtatilgan musiqani qayta ijro etadi"},
    {"id": "c15", "name": "Soat necha", "query": "soat necha", "category": "Vaqt", "icon": "clock", "desc": "Hozirgi aniq vaqtni aytadi"},
    {"id": "c16", "name": "Bugungi sana", "query": "bugungi sana", "category": "Vaqt", "icon": "calendar", "desc": "Bugungi kun, oy va yilni aytadi"},
    {"id": "c17", "name": "Ob-havo ma'lumoti", "query": "ob-havo", "category": "Qidiruv", "icon": "cloud", "desc": "Joriy shahar bo'yicha ob-havoni aytadi"},
    {"id": "c18", "name": "Tizim sozlamalari", "query": "sozlamalar", "category": "Tizim", "icon": "settings", "desc": "Windows tizim sozlamalari panelini ochadi"}
]

async def handle_commands_list(request):
    """GET /api/commands - Barcha mavjud buyruqlar ro'yxati"""
    categories = ["Barchasi", "Ilovalar", "Tizim", "Multimedia", "Ovoz", "Vaqt", "Qidiruv"]
    
    # commands.json dan ham qo'shimchalarni yuklash
    commands_file = os.path.join(BASE_DIR, "data", "commands.json")
    custom_count = 0
    if os.path.exists(commands_file):
        try:
            with open(commands_file, "r", encoding="utf-8") as f:
                c_data = json.load(f)
                custom_count = len(c_data)
        except Exception:
            pass

    return web.json_response({
        "ok": True,
        "categories": categories,
        "commands": DEFAULT_COMMANDS_CATALOG,
        "total_commands": max(len(DEFAULT_COMMANDS_CATALOG), custom_count)
    })


async def handle_commands_execute(request):
    """POST /api/commands/execute - Buyruqni darhol ishga tushirish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    cmd_text = body.get("command", "").strip()
    if not cmd_text:
        return web.json_response({"ok": False, "error": "Buyruq kiritilmadi"}, status=400)

    m, _, _, _, _, dispatcher = get_modules()
    user = get_current_user_name()
    ovoz = get_current_voice_type()

    loop = asyncio.get_running_loop()

    def _run():
        return execute_command_pipeline(cmd_text, user, ovoz, mode="command")

    result_message = await loop.run_in_executor(None, _run)
    await broadcast_ws("command_executed", {"command": cmd_text, "result": result_message})

    return web.json_response({
        "ok": True,
        "command": cmd_text,
        "result": result_message,
        "timestamp": datetime.now().isoformat()
    })


# ========== 4. XOTIRA (MEMORY) HANDLERS ==========
async def handle_memory_get(request):
    """GET /api/memory - Xotira, bilimlar bazasi va suhbatlar tarixi"""
    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli yuklanmagan"}, status=500)

    profile = mem.get_profile()
    raw_knowledge = mem.get_knowledge()
    conversations = mem.get_conversations(last_n=30)
    stats = mem.stats

    # Bilimlarni qulay array formatga o'tkazish
    knowledge_list = []
    if isinstance(raw_knowledge, dict):
        for k, v in raw_knowledge.items():
            if isinstance(v, dict):
                knowledge_list.append({
                    "key": k,
                    "value": v.get("value", ""),
                    "saved_at": v.get("saved_at", ""),
                    "access_count": v.get("access_count", 0)
                })
            else:
                knowledge_list.append({
                    "key": k,
                    "value": str(v),
                    "saved_at": datetime.now().isoformat(),
                    "access_count": 0
                })

    return web.json_response({
        "ok": True,
        "profile": profile,
        "knowledge": knowledge_list,
        "conversations": conversations,
        "stats": stats
    })


async def handle_memory_knowledge_save(request):
    """POST /api/memory/knowledge - Yangi bilim yoki fakt qo'shish/yangilash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    key = body.get("key", "").strip()
    value = body.get("value", "").strip()

    if not key or not value:
        return web.json_response({"ok": False, "error": "Kalit so'z va qiymat talab qilinadi"}, status=400)

    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    mem.save_knowledge(key, value)
    await broadcast_ws("memory_updated", {"action": "save", "key": key, "value": value})

    return web.json_response({
        "ok": True,
        "message": f"'{key}' muvaffaqiyatli saqlandi",
        "key": key,
        "value": value
    })


async def handle_memory_knowledge_delete(request):
    """DELETE /api/memory/knowledge - Bilimni o'chirish"""
    key = request.query.get("key", "").strip()
    if not key:
        try:
            body = await request.json()
            key = body.get("key", "").strip()
        except Exception:
            pass

    if not key:
        return web.json_response({"ok": False, "error": "O'chirish uchun 'key' kiritilmadi"}, status=400)

    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    success = mem.delete_knowledge(key)
    if success:
        await broadcast_ws("memory_updated", {"action": "delete", "key": key})
        return web.json_response({"ok": True, "message": f"'{key}' o'chirildi"})
    else:
        return web.json_response({"ok": False, "error": f"'{key}' topilmadi"}, status=404)


# ========== 5. REJALASHTIRUVCHI (SCHEDULER) HANDLERS ==========
async def handle_scheduler_list(request):
    """GET /api/scheduler - Vazifalar va eslatmalar ro'yxati"""
    _, _, _, sched, _, _ = get_modules()
    if not sched:
        return web.json_response({"ok": False, "error": "Rejalashtiruvchi yuklanmagan"}, status=500)

    tasks = sched.list_tasks(include_completed=True)
    return web.json_response({
        "ok": True,
        "tasks": tasks,
        "active_count": sched.active_count
    })


async def handle_scheduler_add(request):
    """POST /api/scheduler/add - Yangi eslatma yoki vaqtli vazifa qo'shish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    text = body.get("text", "").strip()
    delay_minutes = int(body.get("delay_minutes", 15))
    repeat_minutes = int(body.get("repeat_minutes", 0))
    task_type = body.get("type", "reminder")

    if not text:
        return web.json_response({"ok": False, "error": "Eslatma matni kiritilmadi"}, status=400)

    _, _, _, sched, _, _ = get_modules()
    if not sched:
        return web.json_response({"ok": False, "error": "Rejalashtiruvchi mavjud emas"}, status=500)

    delay_seconds = max(5, delay_minutes * 60)
    repeat_seconds = max(0, repeat_minutes * 60)

    task_id = sched.add(
        task_type=task_type,
        data={"text": text},
        delay_seconds=delay_seconds,
        repeat_seconds=repeat_seconds
    )

    await broadcast_ws("scheduler_updated", {"action": "add", "task_id": task_id, "text": text})

    return web.json_response({
        "ok": True,
        "task_id": task_id,
        "message": f"Vazifa muvaffaqiyatli rejalashtirildi ({delay_minutes} daqiqadan keyin)",
        "delay_minutes": delay_minutes,
        "repeat_minutes": repeat_minutes
    })


async def handle_scheduler_remove(request):
    """DELETE /api/scheduler/task - Vazifani o'chirish"""
    task_id = request.query.get("task_id", "").strip()
    if not task_id:
        try:
            body = await request.json()
            task_id = body.get("task_id", "").strip()
        except Exception:
            pass

    if not task_id:
        return web.json_response({"ok": False, "error": "'task_id' ko'rsatilmadi"}, status=400)

    _, _, _, sched, _, _ = get_modules()
    if not sched:
        return web.json_response({"ok": False, "error": "Rejalashtiruvchi mavjud emas"}, status=500)

    success = sched.remove(task_id)
    if success:
        await broadcast_ws("scheduler_updated", {"action": "remove", "task_id": task_id})
        return web.json_response({"ok": True, "message": f"Vazifa '{task_id}' o'chirildi"})
    else:
        return web.json_response({"ok": False, "error": f"Vazifa topilmadi: {task_id}"}, status=404)


async def handle_scheduler_clear_completed(request):
    """POST /api/scheduler/clear-completed - Bajarilgan vazifalarni tozalash"""
    _, _, _, sched, _, _ = get_modules()
    if sched:
        sched.clear_completed()
    await broadcast_ws("scheduler_updated", {"action": "clear_completed"})
    return web.json_response({"ok": True, "message": "Bajarilgan vazifalar tozalandi"})


# ========== 6. PLAGINLAR VA TOOLS HANDLERS ==========
async def handle_plugins_list(request):
    """GET /api/plugins - Barcha agent vositalari va plaginlar ro'yxati"""
    _, _, _, _, tools, _ = get_modules()
    if not tools:
        return web.json_response({"ok": False, "error": "Tools registry yuklanmagan"}, status=500)

    raw_tools = tools.list_tools()
    
    # Har bir tool uchun toifa va status belgilash
    category_map = {
        "web_search": "Qidiruv", "calculator": "Hisoblash", "system_control": "Tizim",
        "music": "Multimedia", "weather": "Qidiruv", "reminder": "Rejalashtirish",
        "file_manager": "Fayllar", "knowledge": "Xotira", "datetime": "Tizim",
        "scheduler": "Rejalashtirish", "rag": "AI Bilim", "currency": "Hisoblash",
        "translator": "AI Bilim", "screenshot": "Multimedia", "file_write": "Fayllar",
        "app_check": "Tizim", "ask_user": "Muloqot", "screen_click": "Avtomatlashtirish",
        "keyboard_type": "Avtomatlashtirish", "keyboard_shortcut": "Avtomatlashtirish",
        "clipboard": "Tizim", "process_manager": "Tizim", "audio_control": "Tizim",
        "system_info": "Tizim", "window_manager": "Tizim", "notification": "Tizim",
        "vector_search": "AI Bilim", "sandbox": "Xavfsizlik", "secret_vault": "Xavfsizlik"
    }

    enriched_tools = []
    for t in raw_tools:
        name = t.get("name", "")
        cat = category_map.get(name, "Umumiy")
        enriched_tools.append({
            "name": name,
            "description": t.get("description", ""),
            "parameters": t.get("parameters", {}),
            "category": cat,
            "enabled": True,
            "version": "1.0.0"
        })

    return web.json_response({
        "ok": True,
        "tools": enriched_tools,
        "total_count": len(enriched_tools),
        "categories": ["Barchasi", "Tizim", "Qidiruv", "Multimedia", "Avtomatlashtirish", "Hisoblash", "AI Bilim", "Fayllar", "Xavfsizlik"]
    })


async def handle_plugins_execute(request):
    """POST /api/plugins/execute - Toolni bevosita chaqirib sinash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    tool_name = body.get("name", "").strip()
    params = body.get("params", {})

    if not tool_name:
        return web.json_response({"ok": False, "error": "Tool nomi ko'rsatilmadi"}, status=400)

    _, _, _, _, tools, _ = get_modules()
    if not tools:
        return web.json_response({"ok": False, "error": "Tools registry mavjud emas"}, status=500)

    loop = asyncio.get_running_loop()
    
    def _call():
        return tools.call(tool_name, **params)

    res = await loop.run_in_executor(None, _call)
    return web.json_response({
        "ok": True,
        "tool": tool_name,
        "result": res
    })


# ========== 7. HISOB VA SOZLAMALAR (ACCOUNT) HANDLERS ==========
CONFIG_FILE = os.path.join(BASE_DIR, "data", "config.json")
USER_NAME_FILE = os.path.join(BASE_DIR, "data", "foydalanuvchi_ismi.txt")
VOICE_TYPE_FILE = os.path.join(BASE_DIR, "data", "ovoz_turi.txt")

def _read_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _write_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Config saqlash xatosi: {e}")

async def handle_account_get(request):
    """GET /api/account - Foydalanuvchi profili va tizim sozlamalari"""
    user_name = get_current_user_name()
    voice_type = get_current_voice_type()
    cfg = _read_config()

    user_cfg = cfg.get("user", {})
    audio_cfg = cfg.get("audio", {})
    gui_cfg = cfg.get("gui", {})

    return web.json_response({
        "ok": True,
        "name": user_name or user_cfg.get("name", "Ustoz"),
        "voice_type": voice_type or user_cfg.get("voice_type", "ayol"),
        "theme": gui_cfg.get("theme", "dark"),
        "tts_speed": audio_cfg.get("tts_speed", 2.0),
        "ai_model": cfg.get("ai", {}).get("model", "gemini"),
        "version": "7.1.0",
        "voices_available": [
            {"id": "ayol", "name": "Madina (Ayol)", "lang": "uz-UZ-MadinaNeural"},
            {"id": "erkak", "name": "Sardor (Erkak)", "lang": "uz-UZ-SardorNeural"}
        ]
    })


async def handle_account_update(request):
    """POST /api/account - Profil va sozlamalarni yangilash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    new_name = body.get("name", "").strip()
    new_voice = body.get("voice_type", "").strip()
    new_speed = body.get("tts_speed")
    new_theme = body.get("theme", "dark")

    cfg = _read_config()
    if "user" not in cfg:
        cfg["user"] = {}
    if "audio" not in cfg:
        cfg["audio"] = {}
    if "gui" not in cfg:
        cfg["gui"] = {}

    if new_name:
        cfg["user"]["name"] = new_name
        try:
            with open(USER_NAME_FILE, "w", encoding="utf-8") as f:
                f.write(new_name)
        except Exception:
            pass

    if new_voice in ["ayol", "erkak"]:
        cfg["user"]["voice_type"] = new_voice
        try:
            with open(VOICE_TYPE_FILE, "w", encoding="utf-8") as f:
                f.write(new_voice)
        except Exception:
            pass

    if new_speed is not None:
        try:
            cfg["audio"]["tts_speed"] = float(new_speed)
        except ValueError:
            pass

    if new_theme:
        cfg["gui"]["theme"] = new_theme

    _write_config(cfg)

    # In-memory config.py singletonini ham yangilash
    try:
        from config import set_config
        if new_name:
            set_config("user.name", new_name)
        if new_voice in ["ayol", "erkak"]:
            set_config("user.voice_type", new_voice)
        if new_speed is not None:
            try:
                set_config("audio.tts_speed", float(new_speed))
            except Exception:
                pass
        if new_theme:
            set_config("gui.theme", new_theme)
    except Exception as e:
        logger.warning(f"config.set_config xatoligi: {e}")

    # Runtime state ni ham yangilash
    m, _, mem, _, _, _ = get_modules()
    if mem and new_name:
        try:
            mem.set_profile("ism", new_name)
        except Exception:
            pass

    saved_user = new_name or get_current_user_name()
    saved_voice = new_voice or get_current_voice_type()

    await broadcast_ws("account_updated", {
        "name": saved_user,
        "voice_type": saved_voice,
        "tts_speed": new_speed
    })

    return web.json_response({
        "ok": True,
        "message": "Sozlamalar muvaffaqiyatli saqlandi",
        "name": saved_user,
        "voice_type": saved_voice,
        "tts_speed": cfg["audio"].get("tts_speed", 2.0)
    })


# ========== 8. WEBSOCKET HANDLER ==========
async def handle_ws(request):
    """WS /api/ws - Jonli WebSocket aloqa"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    _active_ws_clients.add(ws)
    logger.info(f"Yangi WebSocket mijozi ulandi. Jami: {len(_active_ws_clients)}")

    await ws.send_str(json.dumps({
        "type": "init",
        "data": {
            "status": "online",
            "voice_state": _voice_state,
            "version": "7.1.0"
        },
        "timestamp": datetime.now().isoformat()
    }))

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    action = data.get("action")
                    if action == "ping":
                        await ws.send_str(json.dumps({"type": "pong"}))
                except Exception:
                    pass
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WebSocket xatosi: {ws.exception()}")
    finally:
        _active_ws_clients.discard(ws)
        logger.info(f"WebSocket mijozi uzildi. Qolgan: {len(_active_ws_clients)}")

    return ws


# ========== CORS Middleware ==========
@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# ========== Ilovani sozlash va marshrutlash ==========
def create_app():
    app = web.Application(middlewares=[cors_middleware])
    # Tizim va Bosh sahifa
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/ws", handle_ws)
    
    # AI Chat va Ovoz
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_post("/api/chat/clear", handle_chat_clear)
    app.router.add_post("/api/voice/start", handle_voice_start)
    app.router.add_post("/api/voice/stop", handle_voice_stop)
    app.router.add_post("/api/voice/speak", handle_voice_speak)

    # Buyruqlar (Commands)
    app.router.add_get("/api/commands", handle_commands_list)
    app.router.add_post("/api/commands/execute", handle_commands_execute)

    # Xotira (Memory)
    app.router.add_get("/api/memory", handle_memory_get)
    app.router.add_post("/api/memory/knowledge", handle_memory_knowledge_save)
    app.router.add_delete("/api/memory/knowledge", handle_memory_knowledge_delete)

    # Rejalashtiruvchi (Scheduler)
    app.router.add_get("/api/scheduler", handle_scheduler_list)
    app.router.add_post("/api/scheduler/add", handle_scheduler_add)
    app.router.add_delete("/api/scheduler/task", handle_scheduler_remove)
    app.router.add_post("/api/scheduler/clear-completed", handle_scheduler_clear_completed)

    # Plaginlar (Plugins & Tools)
    app.router.add_get("/api/plugins", handle_plugins_list)
    app.router.add_post("/api/plugins/execute", handle_plugins_execute)

    # Hisob va Sozlamalar (Account & Settings)
    app.router.add_get("/api/account", handle_account_get)
    app.router.add_post("/api/account", handle_account_update)

    return app


def run_server(host="127.0.0.1", port=18420):
    global _main_loop
    logger.info(f"MIKASA AI 7.1.0 Background API Server boshlanmoqda: http://{host}:{port}")
    get_modules()
    app = create_app()
    _main_loop = asyncio.get_event_loop()
    web.run_app(app, host=host, port=port, print=None)


if __name__ == "__main__":
    port = 18420
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
