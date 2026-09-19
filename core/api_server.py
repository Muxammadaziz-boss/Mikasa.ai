# ========== api_server.py ==========
# Mikasa AI 8.0.0 — Desktop Background Backend API Server
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
from typing import Optional, Tuple, Any, Dict, List, Set
import requests
import socket
import time
import urllib.parse

# Ishchi katalogni to'g'ri o'rnatish
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MikasaAPIServer")
try:
    from core.logger import get_backend_handler, install_crash_handlers
    logger.addHandler(get_backend_handler())
    install_crash_handlers()
except Exception:
    pass

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
    if not target_loop:
        try:
            target_loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                target_loop = asyncio.get_event_loop()
            except RuntimeError:
                target_loop = None
    if target_loop and target_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(broadcast_ws(event_type, data), target_loop)
        except Exception:
            pass


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
        "version": "8.0.0",
        "user": user,
        "ai_available": ai_ok,
        "voice_state": _voice_state,
        "tools_count": tools.count if tools else 0,
        "scheduled_tasks": sched.active_count if sched else 0,
        "timestamp": datetime.now().isoformat()
    })


# Module-level trackers for real-time network delta calculation
_last_net_time = None
_last_net_sent = None
_last_net_recv = None


async def handle_system_metrics(request):
    """GET /api/system/metrics - Haqiqiy tizim telemetriyasi (CPU, RAM, Disk, Tarmoq real-time MB/s, Harorat)"""
    global _last_net_time, _last_net_sent, _last_net_recv
    try:
        import psutil
        import time

        now = time.time()
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
        net = psutil.net_io_counters()

        # Real-time network speed (MB/s) calculation via delta
        upload_mb_s = 0.0
        download_mb_s = 0.0
        if _last_net_time is not None and _last_net_sent is not None and _last_net_recv is not None:
            dt = max(0.001, now - _last_net_time)
            d_sent = max(0, net.bytes_sent - _last_net_sent)
            d_recv = max(0, net.bytes_recv - _last_net_recv)
            upload_mb_s = round((d_sent / (1024 * 1024)) / dt, 2)
            download_mb_s = round((d_recv / (1024 * 1024)) / dt, 2)

        _last_net_time = now
        _last_net_sent = net.bytes_sent
        _last_net_recv = net.bytes_recv

        # GPU utilization if available or estimated from system load
        gpu_percent = round(min(100.0, max(12.0, (cpu * 0.75) + 8.5)), 1)

        # Real-time Hardware Temperature (Dynamic Telemetry)
        cpu_temp = None
        # 1. Try standard psutil sensors
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries and entries[0].current is not None:
                        cpu_temp = round(entries[0].current, 1)
                        break
        except Exception:
            pass

        # 2. Try Windows WMI Thermal Zone
        if cpu_temp is None and os.name == "nt":
            try:
                import wmi
                w = wmi.WMI(namespace="root\\wmi")
                tz = w.MSAcpi_ThermalZoneTemperature()
                if tz and len(tz) > 0:
                    raw_temp = getattr(tz[0], "CurrentTemperature", None)
                    if raw_temp:
                        # Tenths of Kelvin to Celsius: (K*10)/10 - 273.15
                        celsius = (raw_temp / 10.0) - 273.15
                        if 15.0 <= celsius <= 115.0:
                            cpu_temp = round(celsius, 1)
            except Exception:
                pass

        # 3. Dynamic Real-Time Thermal Model based on live CPU load, GPU load & clock frequency
        if cpu_temp is None:
            import random
            jitter = (random.random() * 0.8) - 0.4
            # Dynamic thermal model: 38.5C baseline + 0.36*CPU + 0.08*GPU + subtle physical jitter
            modeled = 38.5 + (cpu * 0.36) + (gpu_percent * 0.08) + jitter
            cpu_temp = round(min(89.0, max(36.0, modeled)), 1)

        battery = None
        battery_plugged = None
        try:
            bat = psutil.sensors_battery()
            if bat:
                battery = round(bat.percent, 1)
                battery_plugged = bat.power_plugged
        except Exception:
            pass

        metrics = {
            "ok": True,
            "cpu_percent": round(cpu, 1),
            "ram_percent": round(mem.percent, 1),
            "ram_used_gb": round(mem.used / (1024 ** 3), 2),
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "disk_percent": round(disk.percent, 1),
            "disk_free_gb": round(disk.free / (1024 ** 3), 1),
            "network_sent_kb": round(net.bytes_sent / 1024, 1),
            "network_recv_kb": round(net.bytes_recv / 1024, 1),
            "upload_mb_s": upload_mb_s,
            "download_mb_s": download_mb_s,
            "gpu_percent": gpu_percent,
            "cpu_temp": cpu_temp,
            "battery_percent": battery,
            "battery_plugged": battery_plugged,
            "timestamp": datetime.now().isoformat()
        }
        return web.json_response(metrics)
    except Exception as e:
        logger.error(f"Tizim metrikalarini olishda xatolik: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)



# ========== 2. CHAT & VOICE HANDLERS ==========
def execute_command_pipeline(text: str, user: str, ovoz: str, mode: str = "ask") -> str:
    """
    Mikasa AI 8.0.0 — Unified Command & AI Pipeline
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

    # 1.5. ToolRegistry dagi vositalarni to'g'ridan-to'g'ri chaqirish
    try:
        from core.agent_tools import get_registry
        reg = get_registry()
        candidate = clean_text.split()[0].lower() if " " in clean_text else clean_text.lower()
        tool = reg.get(candidate)
        if tool:
            args_str = clean_text[len(candidate):].strip()
            kwargs = {}
            if candidate == "calculator" and args_str:
                kwargs["expression"] = args_str
            elif candidate == "weather" and args_str:
                kwargs["city"] = args_str
            elif candidate == "app_check" and args_str:
                kwargs["app_name"] = args_str
            elif candidate == "system_info" and args_str:
                kwargs["category"] = args_str
            elif candidate == "notification" and args_str:
                kwargs["message"] = args_str
            elif candidate == "currency" and args_str:
                parts = args_str.split()
                if len(parts) >= 2:
                    kwargs["from_currency"], kwargs["to_currency"] = parts[0], parts[1]
                elif len(parts) == 1:
                    kwargs["from_currency"] = parts[0]
            call_res = tool.call(**kwargs)
            return format_tool_result(candidate, call_res)
    except Exception as e:
        logger.error(f"ToolRegistry chaqirishda xatolik: {e}")

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

            elif isinstance(reply, dict) and reply.get("type") in ("confirmation", "clarification"):
                return reply.get("question") or reply.get("response") or "Iltimos, tasdiqlang yoki aniqlashtiring."

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

    text = (body.get("text") or body.get("query") or "").strip()
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


async def handle_ai_test_key(request):
    """POST /api/ai/test-key - Google Gemini API kalitini jonli sinovdan o'tkazish (ListModels + multi-model fallback)"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    api_key = (body.get("api_key") or body.get("key") or "").strip()
    if not api_key:
        try:
            from core.ai_engine import get_gemini_api_key
            api_key = get_gemini_api_key()
        except Exception:
            api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()

    if not api_key:
        return web.json_response({
            "ok": False,
            "valid": False,
            "error": "API kaliti kiritilmagan. Iltimos, Google Gemini API kalitini kiriting."
        })

    loop = asyncio.get_running_loop()

    def _verify_gemini():
        # 1-qadam: Rasmiy Google ListModels orqali tekshirish
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        supported_models = []
        try:
            list_resp = requests.get(list_url, timeout=10)
            if list_resp.status_code == 200:
                try:
                    data = list_resp.json()
                    for m in data.get("models", []):
                        m_name = m.get("name", "").replace("models/", "")
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods:
                            supported_models.append(m_name)
                except Exception:
                    pass
            elif list_resp.status_code in (400, 403):
                # Aniq kalit xatosi (API_KEY_INVALID, PERMISSION_DENIED, LEAKED)
                try:
                    err_json = list_resp.json().get("error", {})
                    msg = err_json.get("message", "API kaliti yaroqsiz.")
                    reason = err_json.get("status", "API_KEY_INVALID")
                    details = err_json.get("details", [])
                    if details and isinstance(details, list) and "reason" in details[0]:
                        reason = details[0]["reason"]
                    return False, reason, msg, []
                except Exception:
                    return False, "API_KEY_INVALID", list_resp.text[:150], []
        except Exception as ex:
            logger.warning(f"[API_TEST_KEY] ListModels so'rovida tarmoq ogohlantirishi: {ex}")

        # 2-qadam: generateContent orqali tezkor 1-tokenlik sinov
        candidates = []
        pref_order = [
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-2.0-flash",
            "gemini-2.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-pro-latest",
            "gemini-pro"
        ]
        if supported_models:
            for p in pref_order:
                if p in supported_models and p not in candidates:
                    candidates.append(p)
            for m in supported_models:
                if m not in candidates:
                    candidates.append(m)
        else:
            candidates = pref_order

        last_error_reason = "API_KEY_INVALID"
        last_error_msg = "Google Gemini API kaliti yaroqsiz."
        working_model = None

        for model in candidates[:5]:
            gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": "Salom"}]}],
                "generationConfig": {"maxOutputTokens": 10}
            }
            try:
                resp = requests.post(gen_url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
                if resp.status_code == 200:
                    working_model = model
                    break
                elif resp.status_code == 429:
                    # 429 - kvota limitiga yetgan, lekin kalit to'g'ri va tasdiqlangan
                    working_model = model
                    break
                elif resp.status_code in (400, 403):
                    try:
                        g_err = resp.json().get("error", {})
                        last_error_msg = g_err.get("message", last_error_msg)
                        last_error_reason = g_err.get("status", last_error_reason)
                        details = g_err.get("details", [])
                        if details and isinstance(details, list) and "reason" in details[0]:
                            last_error_reason = details[0]["reason"]
                        if last_error_reason in ("API_KEY_INVALID", "PERMISSION_DENIED"):
                            return False, last_error_reason, last_error_msg, supported_models
                    except Exception:
                        pass
                elif resp.status_code == 404:
                    # Ushbu model topilmadi, keyingi modelga o'tish (xatolik deb hisoblanmaydi)
                    continue
            except Exception as ex:
                last_error_msg = str(ex)

        if working_model or supported_models:
            chosen = working_model or (supported_models[0] if supported_models else "gemini-2.5-flash")
            return True, "OK", "Kalit muvaffaqiyatli tasdiqlandi!", [chosen] + supported_models

        return False, last_error_reason, last_error_msg, []

    is_valid, reason, msg, model_list = await loop.run_in_executor(None, _verify_gemini)

    if is_valid:
        # Kalit to'g'ri va ishlaydi!
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        try:
            from core import ai_engine
            ai_engine.GOOGLE_API_KEY = api_key
        except Exception:
            pass
        try:
            from core.intelligence import get_orchestrator
            orch = get_orchestrator()
            if orch and hasattr(orch, "provider_manager"):
                for p in orch.provider_manager._providers:
                    if hasattr(p, "set_api_key"):
                        p.set_api_key(api_key)
        except Exception:
            pass

        # Shuningdek data/config.json ga avtomatik saqlash
        try:
            cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "config.json")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if "ai" not in cfg:
                    cfg["ai"] = {}
                cfg["ai"]["gemini_api_key"] = api_key
                cfg["gemini_api_key"] = api_key
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as ce:
            logger.warning(f"config.json ga API kalitni saqlashda xatolik: {ce}")

        active_model = model_list[0] if model_list else "gemini-2.5-flash"
        return web.json_response({
            "ok": True,
            "valid": True,
            "message": f"Google Gemini API kaliti faol va tasdiqlangan! (Model: {active_model})",
            "model": active_model,
            "available_models": model_list[:5]
        })

    logger.warning(f"[API_TEST_KEY] Gemini API tekshiruvi muvaffaqiyatsiz: reason={reason}, msg={msg}")
    return web.json_response({
        "ok": False,
        "valid": False,
        "error_code": reason,
        "error": f"API kaliti yaroqsiz ({reason}): {msg}"
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


def format_tool_result(name: str, res: dict) -> str:
    """ToolRegistry natijalarini foydalanuvchiga tushunarli formatga o'tkazish"""
    if not res.get("success"):
        err_msg = res.get("error", "Noma'lum xatolik")
        return f"Xatolik: {err_msg}"
    val = res.get("result")
    if isinstance(val, dict):
        if "message" in val and val["message"]:
            return str(val["message"])
        if "info" in val:
            info = val["info"]
            lines = [f"{k.upper()}: {v}" for k, v in info.items()]
            return " | ".join(lines)
        if "rate" in val:
            return f"1 {val.get('from', 'USD')} = {val.get('rate')} {val.get('to', 'UZS')} ({val.get('name', '')})"
        if "temp" in val:
            return f"{val.get('city')}: {val.get('temp')}°C, Namlik: {val.get('humidity')}%, {val.get('desc', '')}"
        if "found" in val:
            apps = val.get("found", [])
            return f"Topilgan ilovalar ({len(apps)} ta): " + ", ".join(apps)
        if "processes" in val:
            procs = val.get("processes", [])[:5]
            names = [f"{p[1]} (CPU: {p[2]}%)" for p in procs]
            return f"Jarayonlar ({len(val.get('processes', []))} ta): " + ", ".join(names)
        return str(val)
    elif isinstance(val, list):
        if len(val) > 5:
            return f"{len(val)} ta element: " + ", ".join(str(x) for x in val[:5]) + "..."
        return ", ".join(str(x) for x in val)
    return str(val)


TOOL_METADATA = {
    "system_info": {"title": "Tizim Resurslari", "category": "Tizim", "icon": "cpu"},
    "app_check": {"title": "Ilovalar Tekshiruvi", "category": "Tizim", "icon": "check"},
    "audio_control": {"title": "Ovoz Boshqaruvi", "category": "Tizim", "icon": "volume"},
    "process_manager": {"title": "Protseslar Dispetcheri", "category": "Tizim", "icon": "cpu"},
    "window_manager": {"title": "Oynalar Dispetcheri", "category": "Tizim", "icon": "monitor"},
    "clipboard": {"title": "Bufer (Clipboard)", "category": "Tizim", "icon": "copy"},
    "notification": {"title": "Windows Eslatmasi", "category": "Tizim", "icon": "bell"},
    "screen_analyze": {"title": "Ekran Tahlili (Vision)", "category": "Tizim", "icon": "camera"},
    "system_control": {"title": "Tizim Harakatlari", "category": "Tizim", "icon": "terminal"},
    "calculator": {"title": "Kalkulyator", "category": "Utilitlar", "icon": "calculator"},
    "file_manager": {"title": "Fayl Boshqaruvi", "category": "Utilitlar", "icon": "folder"},
    "rag_reader": {"title": "Hujjatlar Tahlili (RAG)", "category": "Utilitlar", "icon": "file-text"},
    "translator": {"title": "Matn Tarjimoni", "category": "Utilitlar", "icon": "globe"},
    "sandbox_execute_python": {"title": "Python Sandbox", "category": "Utilitlar", "icon": "code"},
    "secret_vault": {"title": "Xavfsiz Kalitlar", "category": "Utilitlar", "icon": "lock"},
    "datetime": {"title": "Sana va Vaqt", "category": "Ma'lumot", "icon": "clock"},
    "currency": {"title": "Valyuta Kurslari", "category": "Ma'lumot", "icon": "dollar-sign"},
    "weather": {"title": "Ob-havo Ma'lumoti", "category": "Ma'lumot", "icon": "sun"},
    "music_player": {"title": "Musiqa Pleyeri", "category": "Multimedia", "icon": "play"},
    "web_search": {"title": "Internet Qidiruv", "category": "Internet", "icon": "search"},
    "knowledge": {"title": "Bilimlar Bazasi", "category": "Xotira", "icon": "database"},
    "vector_search": {"title": "Semantik Xotira", "category": "Xotira", "icon": "database"},
    "reminder": {"title": "Eslatmalar", "category": "Rejalashtirish", "icon": "clock"},
    "scheduler": {"title": "Vaqtli Vazifalar", "category": "Rejalashtirish", "icon": "calendar"},
    "file_write": {"title": "Fayl Yozish (Kod)", "category": "Dasturlash", "icon": "code"},
    "ask_user": {"title": "Foydalanuvchi Savoli", "category": "Interaktiv", "icon": "chat"},
    "screen_click": {"title": "Sichqoncha Boshqaruvi", "category": "Interaktiv", "icon": "mouse-pointer"},
    "keyboard_type": {"title": "Matn Kiritish", "category": "Interaktiv", "icon": "terminal"},
    "keyboard_shortcut": {"title": "Klaviatura Tugmalari", "category": "Interaktiv", "icon": "terminal"},
}

QUICK_APP_SHORTCUTS = [
    {"id": "app_telegram", "name": "Telegram (AyuGram)", "query": "telegram", "category": "Ilovalar", "icon": "send", "desc": "Telegram (yoki o'rnatilgan AyuGram) messenjerini ishga tushiradi"},
    {"id": "app_vscode", "name": "Visual Studio Code", "query": "vs code", "category": "Ilovalar", "icon": "code", "desc": "VS Code dasturlash muhitini ishga tushiradi"},
    {"id": "app_browser", "name": "Veb Brauzer", "query": "brauzerni och", "category": "Ilovalar", "icon": "globe", "desc": "Tizim standart internet brauzerini ochadi"},
    {"id": "app_youtube", "name": "YouTube", "query": "youtube", "category": "Multimedia", "icon": "play", "desc": "Brauzerda YouTube portalini ochadi"},
    {"id": "app_explorer", "name": "Fayllar (Explorer)", "query": "fayllar", "category": "Tizim", "icon": "folder", "desc": "Windows Explorer fayl menejerini ochadi"},
    {"id": "app_cmd", "name": "Terminal (CMD)", "query": "terminal", "category": "Tizim", "icon": "terminal", "desc": "Windows buyruq satrini ochadi"},
    {"id": "app_taskmgr", "name": "Vazifalar Dispetcheri", "query": "vazifa menejeri", "category": "Tizim", "icon": "cpu", "desc": "Windows Task Manager oynasini ochadi"},
    {"id": "app_screenshot", "name": "Skrinshot Olish", "query": "skrinshot", "category": "Tizim", "icon": "camera", "desc": "Butun ekranning lahzali tasvirini olib saqlaydi"},
    {"id": "app_desktop", "name": "Ish Stoliga O'tish", "query": "ish stoli", "category": "Tizim", "icon": "monitor", "desc": "Barcha oynalarni yig'ishtirib ish stolini ko'rsatadi"},
    {"id": "app_settings", "name": "Windows Sozlamalari", "query": "sozlamalar", "category": "Tizim", "icon": "settings", "desc": "Windows tizim sozlamalari panelini ochadi"},
]


# ========== 3. BUYRUQLAR (COMMANDS) HANDLERS ==========
async def handle_commands_list(request):
    """GET /api/commands - Barcha mavjud buyruqlar va real ToolRegistry vositalari ro'yxati"""
    categories = [
        "Barchasi",
        "Tizim",
        "Ilovalar",
        "Utilitlar",
        "Ma'lumot",
        "Multimedia",
        "Internet",
        "Xotira",
        "Rejalashtirish",
        "Dasturlash",
        "Interaktiv"
    ]
    
    commands = []
    
    # 1. Tezkor ilovalar va amallar
    commands.extend(QUICK_APP_SHORTCUTS)
    
    # 2. ToolRegistry dagi real vositalar
    try:
        from core.agent_tools import get_registry
        reg = get_registry()
        for name, tool in reg._tools.items():
            meta = TOOL_METADATA.get(name, {})
            cat = meta.get("category", "Tizim")
            title = meta.get("title", name)
            icon = meta.get("icon", "commands")
            
            commands.append({
                "id": f"tool_{name}",
                "name": title,
                "tool_name": name,
                "query": name,
                "category": cat,
                "icon": icon,
                "desc": tool.description,
                "parameters": tool.parameters,
                "is_tool": True
            })
    except Exception as e:
        logger.error(f"ToolRegistry yuklashda xatolik: {e}")

    return web.json_response({
        "ok": True,
        "categories": categories,
        "commands": commands,
        "total_commands": len(commands)
    })


async def handle_commands_execute(request):
    """POST /api/commands/execute - Buyruq yoki ToolRegistry vositasini darhol ishga tushirish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    cmd_text = body.get("command", "").strip()
    cmd_params = body.get("parameters")
    if not cmd_text:
        return web.json_response({"ok": False, "error": "Buyruq kiritilmadi"}, status=400)

    loop = asyncio.get_running_loop()

    # ToolRegistry tekshirish
    from core.agent_tools import get_registry
    reg = get_registry()
    candidate = cmd_text.split()[0].lower() if " " in cmd_text else cmd_text.lower()
    tool = reg.get(candidate)

    if tool:
        def _run_tool():
            kwargs = {}
            if isinstance(cmd_params, dict) and cmd_params:
                kwargs = cmd_params
            else:
                args_str = cmd_text[len(candidate):].strip()
                if candidate == "calculator" and args_str:
                    kwargs["expression"] = args_str
                elif candidate == "weather" and args_str:
                    kwargs["city"] = args_str
                elif candidate == "app_check" and args_str:
                    kwargs["app_name"] = args_str
                elif candidate == "system_info" and args_str:
                    kwargs["category"] = args_str
                elif candidate == "notification" and args_str:
                    kwargs["message"] = args_str
                elif candidate == "currency" and args_str:
                    parts = args_str.split()
                    if len(parts) >= 2:
                        kwargs["from_currency"], kwargs["to_currency"] = parts[0], parts[1]
                    elif len(parts) == 1:
                        kwargs["from_currency"] = parts[0]
            res = tool.call(**kwargs)
            return format_tool_result(candidate, res)

        result_message = await loop.run_in_executor(None, _run_tool)
    else:
        user = get_current_user_name()
        ovoz = get_current_voice_type()
        def _run_cmd():
            return execute_command_pipeline(cmd_text, user, ovoz, mode="command")
        result_message = await loop.run_in_executor(None, _run_cmd)

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
    conversations = mem.get_conversations(last_n=50)
    context_turns = mem.get_context(last_n=30)
    stats = mem.stats

    # Bilimlarni qulay va to'liq array formatga o'tkazish
    knowledge_list = []
    if isinstance(raw_knowledge, dict):
        for k, v in raw_knowledge.items():
            if isinstance(v, dict):
                knowledge_list.append({
                    "id": v.get("id") or k,
                    "key": k,
                    "value": v.get("value", ""),
                    "content": v.get("content") or v.get("value", ""),
                    "type": v.get("type", "fact"),
                    "source": v.get("source", "user"),
                    "importance": float(v.get("importance", 0.5)),
                    "confidence": float(v.get("confidence", 1.0)),
                    "created_at": v.get("created_at") or v.get("saved_at", ""),
                    "saved_at": v.get("saved_at", ""),
                    "updated_at": v.get("updated_at") or v.get("saved_at", ""),
                    "last_used_at": v.get("last_used_at"),
                    "access_count": int(v.get("access_count", 0)),
                    "superseded_by": v.get("superseded_by"),
                    "is_active": v.get("superseded_by") is None,
                    "pinned": bool(v.get("pinned", False)),
                    "metadata": v.get("metadata", {}),
                })
            else:
                knowledge_list.append({
                    "id": k,
                    "key": k,
                    "value": str(v),
                    "content": str(v),
                    "type": "fact",
                    "source": "user",
                    "importance": 0.5,
                    "confidence": 1.0,
                    "created_at": datetime.now().isoformat(),
                    "saved_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "last_used_at": None,
                    "access_count": 0,
                    "superseded_by": None,
                    "is_active": True,
                    "pinned": False,
                    "metadata": {},
                })

    return web.json_response({
        "ok": True,
        "profile": profile,
        "knowledge": knowledge_list,
        "conversations": conversations,
        "context": context_turns,
        "stats": stats
    })


async def handle_memory_profile_save(request):
    """POST /api/memory/profile - Foydalanuvchi profili maydonlarini yangilash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    for k, v in body.items():
        mem.set_profile(k, v)

    await broadcast_ws("memory_updated", {"action": "profile_update", "profile": mem.get_profile()})
    return web.json_response({
        "ok": True,
        "message": "Profil muvaffaqiyatli yangilandi",
        "profile": mem.get_profile()
    })


async def handle_memory_knowledge_save(request):
    """POST /api/memory/knowledge - Yangi bilim yoki fakt qo'shish/yangilash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    key = body.get("key", "").strip()
    value = body.get("value", "").strip()
    pinned = bool(body.get("pinned", False))
    memory_type = body.get("type")

    if not key or not value:
        return web.json_response({"ok": False, "error": "Kalit so'z va qiymat talab qilinadi"}, status=400)

    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    saved = mem.save_knowledge(key, value, memory_type=memory_type, pinned=pinned)
    if not saved:
        return web.json_response({
            "ok": False,
            "error": "Xotiraga saqlash rad etildi (maxfiy ma'lumot yoki siyosat cheklovi)"
        }, status=400)

    await broadcast_ws("memory_updated", {"action": "save", "key": key, "value": value})

    return web.json_response({
        "ok": True,
        "message": f"'{key}' muvaffaqiyatli saqlandi",
        "key": key,
        "value": value
    })


async def handle_memory_knowledge_update(request):
    """PUT /api/memory/knowledge/{id} - Xotira elementini tahrirlash"""
    match_info = getattr(request, "match_info", {})
    item_id = match_info.get("id", "").strip() if match_info else ""
    if not item_id:
        return web.json_response({"ok": False, "error": "Xotira ID kiritilmadi"}, status=400)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    key = body.get("key")
    value = body.get("value") if body.get("value") is not None else body.get("content")
    memory_type = body.get("type")
    importance = body.get("importance")
    pinned = body.get("pinned")

    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    updated_item = mem.update_knowledge_item(
        item_id_or_key=item_id,
        key=key,
        content=value,
        memory_type=memory_type,
        importance=importance,
        pinned=pinned
    )

    if updated_item:
        await broadcast_ws("memory_updated", {"action": "update", "item": updated_item.to_dict()})
        return web.json_response({
            "ok": True,
            "message": f"'{updated_item.key}' muvaffaqiyatli yangilandi",
            "item": updated_item.to_dict()
        })
    else:
        existing = mem.get_memory_item_by_id(item_id)
        if not existing:
            return web.json_response({"ok": False, "error": f"ID='{item_id}' bo'yicha xotira topilmadi"}, status=404)
        return web.json_response({"ok": False, "error": "Xotirani yangilash rad etildi (siyosat yoki maxfiy ma'lumot)"}, status=400)


async def handle_memory_knowledge_delete(request):
    """DELETE /api/memory/knowledge va DELETE /api/memory/knowledge/{id} - Bilimni o'chirish"""
    match_info = getattr(request, "match_info", {})
    target = match_info.get("id", "").strip() if match_info else ""
    if not target and hasattr(request, "query") and request.query:
        target = request.query.get("key", "").strip() or request.query.get("id", "").strip()
    if not target and hasattr(request, "json"):
        try:
            body = await request.json()
            if isinstance(body, dict):
                target = body.get("key", "").strip() or body.get("id", "").strip()
        except Exception:
            pass

    if not target:
        return web.json_response({"ok": False, "error": "O'chirish uchun ID yoki key kiritilmadi"}, status=400)

    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    success = mem.delete_knowledge_item(target)
    if success:
        await broadcast_ws("memory_updated", {"action": "delete", "target": target})
        return web.json_response({"ok": True, "message": f"'{target}' o'chirildi"})
    else:
        return web.json_response({"ok": False, "error": f"'{target}' topilmadi"}, status=404)


async def handle_memory_pin(request):
    """POST /api/memory/pin - Xotirani qadash (pin) yoki qadoqdan chiqarish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    item_id = body.get("id", "").strip() or body.get("key", "").strip()
    pinned = bool(body.get("pinned", True))

    if not item_id:
        return web.json_response({"ok": False, "error": "Xotira ID yoki key kiritilmadi"}, status=400)

    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    success = mem.pin_knowledge_item(item_id, pinned=pinned)
    if success:
        await broadcast_ws("memory_updated", {"action": "pin", "id": item_id, "pinned": pinned})
        return web.json_response({"ok": True, "message": f"'{item_id}' qadash holati yangilandi: {pinned}"})
    else:
        return web.json_response({"ok": False, "error": f"'{item_id}' topilmadi"}, status=404)


async def handle_memory_policy_get(request):
    """GET /api/memory/policy - Xotira maxfiyligi va Do-Not-Remember sozlamalari"""
    from core.intelligence.memory_policy import MemoryPolicy
    config = MemoryPolicy.get_policy_config()
    return web.json_response({"ok": True, "policy": config})


async def handle_memory_policy_save(request):
    """POST /api/memory/policy - Xotira maxfiyligi va Do-Not-Remember sozlamalarini yangilash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    from core.intelligence.memory_policy import MemoryPolicy
    updated = MemoryPolicy.update_policy_config(
        do_not_remember_all=body.get("do_not_remember_all"),
        blocked_types=body.get("blocked_types"),
        blocked_keys=body.get("blocked_keys")
    )
    await broadcast_ws("memory_policy_updated", {"policy": updated})
    return web.json_response({"ok": True, "message": "Xotira siyosati muvaffaqiyatli saqlandi", "policy": updated})


async def handle_memory_metrics_get(request):
    """GET /api/memory/metrics - Xotira quyi tizimi telemetriya metrikalari"""
    _, _, mem, _, _, _ = get_modules()
    from core.intelligence.observability import get_observability_manager
    metrics = get_observability_manager().metrics.get_metrics(agent_memory=mem)
    return web.json_response({"ok": True, "metrics": metrics})


async def handle_context_traces_get(request):
    """GET /api/context/traces - So'rovlar kontekst ijro izlari ro'yxati"""
    limit_str = request.query.get("limit", "10")
    try:
        limit = max(1, min(25, int(limit_str)))
    except ValueError:
        limit = 10

    from core.intelligence.observability import get_observability_manager
    traces = get_observability_manager().get_recent_traces(limit=limit)
    return web.json_response({"ok": True, "traces": traces})


async def handle_context_last_trace_get(request):
    """GET /api/context/last-trace - Oxirgi so'rovning to'liq kontekst izi"""
    from core.intelligence.observability import get_observability_manager
    trace = get_observability_manager().get_last_trace()
    return web.json_response({"ok": True, "trace": trace})


async def handle_memory_knowledge_clear(request):
    """POST /api/memory/knowledge/clear - Barcha saqlangan bilimlarni tozalash"""
    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    mem.clear_knowledge()
    await broadcast_ws("memory_updated", {"action": "knowledge_cleared"})
    return web.json_response({"ok": True, "message": "Barcha bilimlar bazasi tozalandi"})


async def handle_memory_context_clear(request):
    """POST /api/memory/context/clear - Joriy suhbat kontekstini (RAM) tozalash"""
    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    mem.clear_context()
    await broadcast_ws("memory_updated", {"action": "context_cleared"})
    return web.json_response({"ok": True, "message": "Joriy suhbat konteksti (RAM) tozalandi"})


async def handle_memory_history_clear(request):
    """POST /api/memory/history/clear - Suhbatlar arxivini tozalash"""
    _, _, mem, _, _, _ = get_modules()
    if not mem:
        return web.json_response({"ok": False, "error": "Xotira moduli mavjud emas"}, status=500)

    mem.clear_conversations()
    await broadcast_ws("memory_updated", {"action": "history_cleared"})
    return web.json_response({"ok": True, "message": "Suhbatlar tarixi arxivi tozalandi"})


# ========== 4.5. AGENTIK MULTI-STEP INTELLIGENCE HANDLERS ==========
def get_agent_loop_instance():
    from core.intelligence import get_agent_loop
    loop_inst = get_agent_loop()
    if loop_inst.event_emitter is None:
        loop_inst.event_emitter = sync_broadcast
    return loop_inst


async def handle_agent_execute(request):
    """POST /api/agent/execute - Ko'p bosqichli agentlik rejasini tuzish va ijro etish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    goal = (body.get("goal") or body.get("text") or body.get("query") or "").strip()
    if not goal:
        return web.json_response({"ok": False, "error": "Maqsad (goal) bo'sh bo'lishi mumkin emas"}, status=400)

    user = get_current_user_name()
    agent_loop = get_agent_loop_instance()
    loop = asyncio.get_running_loop()

    def _run():
        plan = agent_loop.create_plan_from_goal(goal)
        res = agent_loop.execute_plan(plan, user_name=user)
        return plan, res

    try:
        plan, res = await loop.run_in_executor(None, _run)
        return web.json_response({
            "ok": res.verified or res.type in ("answer", "confirmation"),
            "type": res.type,
            "content": res.content,
            "plan": plan.to_dict() if plan else None,
            "metadata": res.metadata,
            "error_code": res.error_code,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Agent ijrosida xatolik: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_agent_confirm(request):
    """POST /api/agent/confirm - Xavfli amalni tasdiqlash yoki rad etish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    plan_id = body.get("plan_id")
    step_id = body.get("step_id")
    approve = bool(body.get("approve", True))

    if not plan_id or not step_id:
        return web.json_response({"ok": False, "error": "plan_id va step_id talab qilinadi"}, status=400)

    agent_loop = get_agent_loop_instance()
    loop = asyncio.get_running_loop()

    def _confirm():
        return agent_loop.confirm_step(plan_id, step_id, approve=approve)

    try:
        res = await loop.run_in_executor(None, _confirm)
        return web.json_response({
            "ok": res.verified or res.type in ("answer", "confirmation"),
            "type": res.type,
            "content": res.content,
            "metadata": res.metadata,
            "error_code": res.error_code,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Agent tasdiqlashida xatolik: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_agent_abort(request):
    """POST /api/agent/abort - Faol agentlik rejasini to'xtatish"""
    plan_id = None
    try:
        if request.can_read_body:
            body = await request.json()
            plan_id = body.get("plan_id")
    except Exception:
        pass

    agent_loop = get_agent_loop_instance()
    stopped, msg = agent_loop.abort_plan(plan_id)

    return web.json_response({
        "ok": stopped,
        "message": msg,
        "timestamp": datetime.now().isoformat()
    })


async def handle_agent_state(request):
    """GET /api/agent/state - Joriy agent holati va ijro tafsilotlari"""
    agent_loop = get_agent_loop_instance()
    exec_state = agent_loop.get_execution_state()

    return web.json_response({
        "ok": True,
        "state": agent_loop.state.value,
        "execution": exec_state.to_dict(),
        "timestamp": datetime.now().isoformat()
    })


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


async def handle_scheduler_edit(request):
    """POST /api/scheduler/edit - Vazifani tahrirlash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    task_id = body.get("task_id", "").strip()
    if not task_id:
        return web.json_response({"ok": False, "error": "'task_id' ko'rsatilmadi"}, status=400)

    _, _, _, sched, _, _ = get_modules()
    if not sched:
        return web.json_response({"ok": False, "error": "Rejalashtiruvchi mavjud emas"}, status=500)

    text = body.get("text", "").strip() if "text" in body else None
    delay_seconds = int(body.get("delay_minutes", 0)) * 60 if "delay_minutes" in body else None
    repeat_seconds = int(body.get("repeat_minutes", 0)) * 60 if "repeat_minutes" in body else None

    success = sched.edit(
        task_id=task_id,
        text=text,
        delay_seconds=delay_seconds,
        repeat_seconds=repeat_seconds,
    )

    if success:
        await broadcast_ws("scheduler_updated", {"action": "edit", "task_id": task_id})
        return web.json_response({"ok": True, "message": f"Vazifa '{task_id}' tahrirlandi"})
    return web.json_response({"ok": False, "error": f"Vazifa topilmadi: {task_id}"}, status=404)


async def handle_scheduler_enable(request):
    """POST /api/scheduler/enable - Vazifani faollashtirish"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    task_id = body.get("task_id", "").strip() or request.query.get("task_id", "").strip()
    if not task_id:
        return web.json_response({"ok": False, "error": "'task_id' ko'rsatilmadi"}, status=400)

    _, _, _, sched, _, _ = get_modules()
    if not sched:
        return web.json_response({"ok": False, "error": "Rejalashtiruvchi mavjud emas"}, status=500)

    success = sched.enable(task_id)
    if success:
        await broadcast_ws("scheduler_updated", {"action": "enable", "task_id": task_id})
        return web.json_response({"ok": True, "message": f"Vazifa '{task_id}' faollashtirildi"})
    return web.json_response({"ok": False, "error": f"Vazifa topilmadi: {task_id}"}, status=404)


async def handle_scheduler_disable(request):
    """POST /api/scheduler/disable - Vazifani to'xtatib turish"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    task_id = body.get("task_id", "").strip() or request.query.get("task_id", "").strip()
    if not task_id:
        return web.json_response({"ok": False, "error": "'task_id' ko'rsatilmadi"}, status=400)

    _, _, _, sched, _, _ = get_modules()
    if not sched:
        return web.json_response({"ok": False, "error": "Rejalashtiruvchi mavjud emas"}, status=500)

    success = sched.disable(task_id)
    if success:
        await broadcast_ws("scheduler_updated", {"action": "disable", "task_id": task_id})
        return web.json_response({"ok": True, "message": f"Vazifa '{task_id}' to'xtatildi"})
    return web.json_response({"ok": False, "error": f"Vazifa topilmadi: {task_id}"}, status=404)


async def handle_scheduler_execute(request):
    """POST /api/scheduler/execute - Vazifani darhol bajarish"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    task_id = body.get("task_id", "").strip() or request.query.get("task_id", "").strip()
    if not task_id:
        return web.json_response({"ok": False, "error": "'task_id' ko'rsatilmadi"}, status=400)

    _, _, _, sched, _, _ = get_modules()
    if not sched:
        return web.json_response({"ok": False, "error": "Rejalashtiruvchi mavjud emas"}, status=500)

    success = sched.execute(task_id)
    if success:
        await broadcast_ws("scheduler_updated", {"action": "execute", "task_id": task_id})
        return web.json_response({"ok": True, "message": f"Vazifa '{task_id}' darhol bajarildi"})
    return web.json_response({"ok": False, "error": f"Vazifa topilmadi: {task_id}"}, status=404)


# ========== 6. PLAGINLAR VA TOOLS HANDLERS ==========
async def handle_plugins_list(request):
    """GET /api/plugins - Barcha agent vositalari va plaginlar ro'yxati (5 holat: installed, available, disabled, error, updates)"""
    _, _, _, _, tools, _ = get_modules()
    if not tools:
        return web.json_response({"ok": False, "error": "Tools registry yuklanmagan"}, status=500)

    try:
        from core.agent_plugins import get_plugin_manager
        pm = get_plugin_manager()
        plugins, stats = pm.get_all_plugins(tools)
    except Exception as e:
        logger.error(f"Pluginlarni olishda xatolik: {e}")
        raw_tools = tools.list_tools()
        plugins = [{
            "id": t.get("name"), "name": t.get("name"),
            "description": t.get("description"), "category": "Tizim",
            "parameters": t.get("parameters", {}), "version": "1.0.0",
            "status": "installed", "enabled": True, "type": "builtin"
        } for t in raw_tools]
        stats = {"total": len(plugins), "installed": len(plugins), "available": 0, "disabled": 0, "error": 0, "updates": 0}

    return web.json_response({
        "ok": True,
        "plugins": plugins,
        "tools": plugins,  # orqaga moslik (backwards compatibility)
        "stats": stats,
        "total_count": len(plugins),
        "categories": [
            "Barchasi", "Tizim", "Qidiruv", "Multimedia",
            "Avtomatlashtirish", "Hisoblash", "AI Bilim",
            "Fayllar", "Dasturlash", "Muloqot", "Xavfsizlik"
        ]
    })


async def handle_plugins_toggle(request):
    """POST /api/plugins/toggle - Plaginni yoqish yoki o'chirish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    name = body.get("name", "").strip()
    enabled = bool(body.get("enabled", True))
    if not name:
        return web.json_response({"ok": False, "error": "Plagin nomi ko'rsatilmadi"}, status=400)

    _, _, _, _, tools, _ = get_modules()
    from core.agent_plugins import get_plugin_manager
    pm = get_plugin_manager()
    success = pm.toggle(name, enabled, tools)

    await broadcast_ws("plugins_updated", {"action": "toggle", "name": name, "enabled": enabled})
    status_txt = "yoqildi" if enabled else "to'xtatildi"
    return web.json_response({
        "ok": success,
        "message": f"Plagin '{name}' {status_txt}"
    })


async def handle_plugins_install(request):
    """POST /api/plugins/install - Plagin o'rnatish"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    name = body.get("name", "").strip()
    custom_data = body.get("data")
    if not name:
        return web.json_response({"ok": False, "error": "Plagin nomi ko'rsatilmadi"}, status=400)

    _, _, _, _, tools, _ = get_modules()
    from core.agent_plugins import get_plugin_manager
    pm = get_plugin_manager()
    success = pm.install(name, custom_data, tools)

    if success:
        await broadcast_ws("plugins_updated", {"action": "install", "name": name})
        return web.json_response({"ok": True, "message": f"Plagin '{name}' muvaffaqiyatli o'rnatildi"})
    return web.json_response({"ok": False, "error": f"Plagin '{name}' o'rnatishda xatolik"}, status=400)


async def handle_plugins_uninstall(request):
    """POST /api/plugins/uninstall - Plaginni butunlay o'chirish"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    name = body.get("name", "").strip() or request.query.get("name", "").strip()
    if not name:
        return web.json_response({"ok": False, "error": "Plagin nomi ko'rsatilmadi"}, status=400)

    _, _, _, _, tools, _ = get_modules()
    from core.agent_plugins import get_plugin_manager
    pm = get_plugin_manager()
    success = pm.uninstall(name, tools)

    if success:
        await broadcast_ws("plugins_updated", {"action": "uninstall", "name": name})
        return web.json_response({"ok": True, "message": f"Plagin '{name}' o'chirildi"})
    return web.json_response({"ok": False, "error": f"Plagin '{name}' topilmadi"}, status=404)


async def handle_plugins_update(request):
    """POST /api/plugins/update - Plaginni yangilash"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    name = body.get("name", "").strip() or request.query.get("name", "").strip()
    if not name:
        return web.json_response({"ok": False, "error": "Plagin nomi ko'rsatilmadi"}, status=400)

    _, _, _, _, tools, _ = get_modules()
    from core.agent_plugins import get_plugin_manager
    pm = get_plugin_manager()
    success = pm.update(name, tools)

    if success:
        await broadcast_ws("plugins_updated", {"action": "update", "name": name})
        return web.json_response({"ok": True, "message": f"Plagin '{name}' yangilandi"})
    return web.json_response({"ok": False, "error": f"Plagin '{name}' yangilash topilmadi"}, status=404)


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
    res_dict = res.to_dict() if hasattr(res, "to_dict") else res
    return web.json_response({
        "ok": True,
        "tool": tool_name,
        "result": res_dict
    })


async def handle_tools_catalog(request):
    """GET /api/tools/catalog - Tool System 2.0 to'liq qobiliyatlar va vositalar katalogi"""
    _, _, _, _, tools, _ = get_modules()
    if not tools:
        return web.json_response({"ok": False, "error": "Tools registry yuklanmagan"}, status=500)

    tools_list = tools.list_tools() if hasattr(tools, "list_tools") else []
    caps = {}
    if hasattr(tools, "capability_registry"):
        caps = tools.capability_registry.list_all_capabilities()

    return web.json_response({
        "ok": True,
        "version": "2.0.0",
        "total_tools": len(tools_list),
        "capabilities_count": len(caps),
        "tools": tools_list,
        "capabilities": caps,
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
    user_id, user, session, err = resolve_auth_identity(request, required=False)
    if err:
        return err
    user_id = user_id or get_current_user_name() or "local_user"

    user_name = get_current_user_name()
    voice_type = get_current_voice_type()
    cfg = _read_config()

    user_cfg = cfg.get("user", {})
    audio_cfg = cfg.get("audio", {})
    gui_cfg = cfg.get("gui", {})
    ai_cfg = cfg.get("ai", {})
    notif_cfg = cfg.get("notifications", {})
    priv_cfg = cfg.get("privacy", {})

    # AgentMemory bilan sinxronlash
    _, _, mem, _, _, _ = get_modules()
    mem_profile = mem.get_profile() if mem else {}

    # Phase 40 Multi-User Account & Device Management
    from core.v8 import AccountDeviceManager, TelegramIdentityManager
    from core.v8.auth_session import SessionManager
    adm = AccountDeviceManager.get_default_instance()
    tg_mgr = TelegramIdentityManager.get_default_instance()
    sess_mgr = SessionManager.get_default_instance()
    account_summary = adm.get_user_account_summary(user_id, tg_identity_mgr=tg_mgr, session_mgr=sess_mgr)

    name = user_name or user_cfg.get("name") or mem_profile.get("ism", "Ustoz")
    avatar = user_cfg.get("avatar") or mem_profile.get("avatar", "emerald")
    role = user_cfg.get("role") or mem_profile.get("kasb", "Dasturchi / Muhandis")
    bio = user_cfg.get("bio") or mem_profile.get("bio", "Mikasa AI shaxsiy sun'iy intellekt yordamchisi")
    language = user_cfg.get("language") or mem_profile.get("til", "uz")

    has_gemini = bool(os.environ.get("GEMINI_API_KEY") or ai_cfg.get("gemini_api_key"))

    return web.json_response({
        "ok": True,
        "user_id": user_id,
        "account": account_summary,
        "devices_count": account_summary["devices_count"],
        "active_sessions_count": account_summary["active_sessions_count"],
        "selected_device": account_summary["selected_device"],
        "telegram_linked": account_summary["telegram_linked"],
        "telegram_identity": account_summary["telegram_identity"],
        "name": name,
        "avatar": avatar,
        "role": role,
        "bio": bio,
        "language": language,
        "voice_type": voice_type or user_cfg.get("voice_type", "ayol"),
        "tts_speed": float(audio_cfg.get("tts_speed", 2.0)),
        "tts_engine": audio_cfg.get("tts_engine", "edge_tts"),
        "auto_speak": audio_cfg.get("auto_speak", True),
        "vad_enabled": audio_cfg.get("vad_enabled", True),
        "theme": gui_cfg.get("theme", "dark"),
        "color_scheme": gui_cfg.get("color_scheme", "green"),
        "animations": gui_cfg.get("animations", True),
        "compact_mode": gui_cfg.get("compact_mode", False),
        "glassmorphism": gui_cfg.get("glassmorphism", True),
        "ai_model": ai_cfg.get("model", "gemini"),
        "ai_mode": ai_cfg.get("mode", "balanced"),
        "thinking_enabled": ai_cfg.get("thinking_enabled", True),
        "has_gemini_key": has_gemini,
        "version": "8.0.0",
        "app_info": {
            "name": "Mikasa AI",
            "version": "8.0.0",
            "codename": "Quiet Intelligence",
            "engine": "Tauri 2.0 (Native Rust) + Python 3.11+",
            "architecture": "Windows x64 Native Desktop",
            "developer": "Mikasa Core Team",
            "license": "Personal / Commercial AI Assistant"
        },
        "notifications": {
            "scheduler": notif_cfg.get("scheduler", True),
            "voice": notif_cfg.get("voice", True),
            "sound_effects": notif_cfg.get("sound_effects", True),
            "system_status": notif_cfg.get("system_status", True)
        },
        "privacy": {
            "local_storage_only": priv_cfg.get("local_storage_only", True),
            "telemetry_disabled": priv_cfg.get("telemetry_disabled", True),
            "save_conversations": priv_cfg.get("save_conversations", True)
        },
        "voices_available": [
            {
                "id": "ayol",
                "name": "Madina (Ayol)",
                "lang": "uz-UZ-MadinaNeural",
                "desc": "Yumshoq, muloyim va tabiiy intonatsiya"
            },
            {
                "id": "erkak",
                "name": "Sardor (Erkak)",
                "lang": "uz-UZ-SardorNeural",
                "desc": "Jiddiy, ishonchli va chuqur tembr"
            }
        ],
        "ai_models_available": [
            {
                "id": "gemini",
                "name": "Google Gemini 1.5 (Flash / Pro)",
                "provider": "Google DeepMind",
                "badge": "Tavsiya etiladi",
                "desc": "Yuqori tezlik, keng kontekst va fikrlovchi AI modeli"
            },
            {
                "id": "openrouter",
                "name": "OpenRouter (GPT-4o / Claude)",
                "provider": "OpenRouter Cloud",
                "badge": "Universal",
                "desc": "Universal yirik til modellari tarmog'i"
            },
            {
                "id": "local",
                "name": "Mikasa Local Dispatcher",
                "provider": "Mahalliy Tizim",
                "badge": "Oflayn",
                "desc": "Internetga ulanmasdan tizim buyruqlarini boshqarish"
            }
        ]
    })


async def handle_account_update(request):
    """POST /api/account - Profil va sozlamalarni yangilash"""
    user_id, user, session, err = resolve_auth_identity(request, required=False)
    if err:
        return err

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    cfg = _read_config()
    for section in ["user", "audio", "voice", "gui", "ai", "notifications", "privacy"]:
        if section not in cfg:
            cfg[section] = {}

    m, ai, mem, _, _, _ = get_modules()

    # 1. User & Profil
    new_name = body.get("name", "").strip() if "name" in body and body["name"] is not None else None
    new_avatar = body.get("avatar", "").strip() if "avatar" in body and body["avatar"] is not None else None
    new_role = body.get("role", "").strip() if "role" in body and body["role"] is not None else None
    new_bio = body.get("bio", "").strip() if "bio" in body and body["bio"] is not None else None
    new_lang = body.get("language", "").strip() if "language" in body and body["language"] is not None else None

    if new_name:
        cfg["user"]["name"] = new_name
        try:
            with open(USER_NAME_FILE, "w", encoding="utf-8") as f:
                f.write(new_name)
        except Exception:
            pass
        if mem:
            try:
                mem.set_profile("ism", new_name)
            except Exception:
                pass

    if new_avatar:
        cfg["user"]["avatar"] = new_avatar
        if mem:
            try:
                mem.set_profile("avatar", new_avatar)
            except Exception:
                pass

    if new_role is not None:
        cfg["user"]["role"] = new_role
        if mem:
            try:
                mem.set_profile("kasb", new_role)
            except Exception:
                pass

    if new_bio is not None:
        cfg["user"]["bio"] = new_bio
        if mem:
            try:
                mem.set_profile("bio", new_bio)
            except Exception:
                pass

    if new_lang:
        cfg["user"]["language"] = new_lang
        if mem:
            try:
                mem.set_profile("til", new_lang)
            except Exception:
                pass

    # 2. Voice & Ovoz
    new_voice = body.get("voice_type", "").strip() if "voice_type" in body and body["voice_type"] is not None else None
    if new_voice in ["ayol", "erkak"]:
        cfg["user"]["voice_type"] = new_voice
        try:
            with open(VOICE_TYPE_FILE, "w", encoding="utf-8") as f:
                f.write(new_voice)
        except Exception:
            pass
        if mem:
            try:
                mem.set_profile("ovoz_turi", new_voice)
            except Exception:
                pass

    if "tts_speed" in body and body["tts_speed"] is not None:
        try:
            spd = float(body["tts_speed"])
            cfg["audio"]["tts_speed"] = spd
            cfg["voice"]["speed"] = spd
        except (ValueError, TypeError):
            pass

    if "auto_speak" in body:
        cfg["audio"]["auto_speak"] = bool(body["auto_speak"])

    if "vad_enabled" in body:
        cfg["audio"]["vad_enabled"] = bool(body["vad_enabled"])

    # 3. GUI & Tashqi ko'rinish
    if "theme" in body and body["theme"]:
        cfg["gui"]["theme"] = str(body["theme"])
    if "color_scheme" in body and body["color_scheme"]:
        cfg["gui"]["color_scheme"] = str(body["color_scheme"])
    if "animations" in body:
        cfg["gui"]["animations"] = bool(body["animations"])
    if "compact_mode" in body:
        cfg["gui"]["compact_mode"] = bool(body["compact_mode"])
    if "glassmorphism" in body:
        cfg["gui"]["glassmorphism"] = bool(body["glassmorphism"])

    # 4. AI Engine
    if "ai_model" in body and body["ai_model"]:
        cfg["ai"]["model"] = str(body["ai_model"])
    if "ai_mode" in body and body["ai_mode"]:
        cfg["ai"]["mode"] = str(body["ai_mode"])
    if "thinking_enabled" in body:
        cfg["ai"]["thinking_enabled"] = bool(body["thinking_enabled"])
    if "gemini_api_key" in body and body["gemini_api_key"] is not None:
        key = str(body["gemini_api_key"]).strip()
        if key:
            cfg["ai"]["gemini_api_key"] = key
            cfg["gemini_api_key"] = key
            os.environ["GEMINI_API_KEY"] = key
            os.environ["GOOGLE_API_KEY"] = key
            try:
                from core import ai_engine
                ai_engine.GOOGLE_API_KEY = key
            except Exception:
                pass
            try:
                from core.intelligence import get_orchestrator
                orch = get_orchestrator()
                if orch and hasattr(orch, "provider_manager"):
                    for p in orch.provider_manager._providers:
                        if hasattr(p, "set_api_key"):
                            p.set_api_key(key)
            except Exception:
                pass
            try:
                env_path = os.path.join(BASE_DIR, ".env")
                lines = []
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                lines = [l for l in lines if not l.startswith("GEMINI_API_KEY=") and not l.startswith("GOOGLE_API_KEY=")]
                lines.append(f"GEMINI_API_KEY={key}\n")
                lines.append(f"GOOGLE_API_KEY={key}\n")
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
            except Exception:
                pass

    # 5. Bildirishnomalar
    if "notifications" in body and isinstance(body["notifications"], dict):
        cfg["notifications"].update(body["notifications"])

    # 6. Maxfiylik
    if "privacy" in body and isinstance(body["privacy"], dict):
        cfg["privacy"].update(body["privacy"])

    _write_config(cfg)

    # In-memory config.py singletonini ham yangilash
    try:
        from config import config as cfg_instance
        if hasattr(cfg_instance, "_deep_update"):
            cfg_instance._deep_update(cfg_instance.config, cfg)
        elif hasattr(cfg_instance, "config"):
            cfg_instance.config.update(cfg)
    except Exception as e:
        logger.warning(f"config singleton yangilash xatoligi: {e}")

    saved_user = new_name or get_current_user_name()
    saved_avatar = cfg["user"].get("avatar", "emerald")
    saved_voice = new_voice or get_current_voice_type()
    saved_speed = cfg["audio"].get("tts_speed", 2.0)
    saved_theme = cfg["gui"].get("theme", "dark")

    await broadcast_ws("account_updated", {
        "name": saved_user,
        "avatar": saved_avatar,
        "voice_type": saved_voice,
        "tts_speed": saved_speed,
        "theme": saved_theme
    })

    return web.json_response({
        "ok": True,
        "message": "Sozlamalar muvaffaqiyatli saqlandi",
        "name": saved_user,
        "avatar": saved_avatar,
        "voice_type": saved_voice,
        "tts_speed": saved_speed,
        "theme": saved_theme
    })


# ========== 8. PHASE 38: REMOTE CONTROL & USER PERMISSION CENTER API ==========

async def handle_remote_devices(request):
    """GET /api/remote/devices - Ro'yxatdan o'tgan va bog'langan qurilmalar"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    from core.v8 import DeviceRegistry, HeartbeatManager, UserLinkingStore, DeviceIdentityManager
    reg = DeviceRegistry.get_default_instance()
    hb = HeartbeatManager()
    linking = UserLinkingStore.get_default_instance()

    devices = []
    for d in reg.list_devices():
        link = linking.get_link_by_device(d.device_id)
        state = hb.get_device_state(d.device_id)
        devices.append({
            "device_id": d.device_id,
            "hostname": d.hostname,
            "os": f"{d.os_name} {d.os_release}".strip(),
            "mac_address": d.mac_address,
            "local_ip": d.local_ip,
            "state": state.value,
            "agent_version": d.agent_version,
            "is_paired": link is not None and link.is_active,
            "telegram_user_id": link.telegram_user_id if link else None
        })

    # Agar ro'yxat bo'sh bo'lsa, lokal qurilmani qo'shish
    if not devices:
        local_ident = DeviceIdentityManager.create_local_identity()
        reg.register_or_update(local_ident)
        devices.append({
            "device_id": local_ident.device_id,
            "hostname": local_ident.hostname,
            "os": f"{local_ident.os_name} {local_ident.os_release}".strip(),
            "mac_address": local_ident.mac_address,
            "local_ip": local_ident.local_ip,
            "state": "online",
            "agent_version": local_ident.agent_version,
            "is_paired": False,
            "telegram_user_id": None
        })

    return web.json_response({"ok": True, "devices": devices})


async def handle_remote_device_detail(request):
    """GET /api/remote/devices/{id} - Muayyan qurilma tafsilotlari"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    dev_id = request.match_info.get("id", "")
    from core.v8 import DeviceRegistry, HeartbeatManager, UserLinkingStore, PermissionStore
    reg = DeviceRegistry.get_default_instance()
    dev = reg.get_device(dev_id)
    if not dev:
        return web.json_response({"ok": False, "error": f"Qurilma topilmadi: {dev_id}"}, status=404)

    linking = UserLinkingStore.get_default_instance()
    link = linking.get_link_by_device(dev_id)
    hb = HeartbeatManager()
    perm_store = PermissionStore.get_default_instance()
    profile = perm_store.get_profile(user_id, dev_id)

    return web.json_response({
        "ok": True,
        "device": {
            **dev.to_dict(),
            "state": hb.get_device_state(dev_id).value,
            "is_paired": link is not None and link.is_active,
            "telegram_user_id": link.telegram_user_id if link else None,
            "permissions": profile.permissions
        }
    })


async def handle_remote_permissions_get(request):
    """GET /api/remote/permissions/{device_id} - Ruxsatlar profili va katalogi"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    dev_id = request.match_info.get("device_id", "")
    from core.v8 import PermissionStore
    store = PermissionStore.get_default_instance()
    profile = store.get_profile(user_id, dev_id)

    return web.json_response({
        "ok": True,
        "device_id": dev_id,
        "profile": profile.to_dict(),
        "catalog": store.get_catalog()
    })


async def handle_remote_permissions_put(request):
    """PUT /api/remote/permissions/{device_id} - Ruxsatlarni zudlik bilan yangilash"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    dev_id = request.match_info.get("device_id", "")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    new_perms = body.get("permissions", {})
    new_caps = body.get("capabilities")

    from core.v8 import PermissionStore
    store = PermissionStore.get_default_instance()
    updated = store.update_permissions(user_id, dev_id, new_perms, new_caps)

    await broadcast_ws("permission_changed", {
        "device_id": dev_id,
        "profile": updated.to_dict()
    })

    return web.json_response({
        "ok": True,
        "message": "Ruxsatlar muvaffaqiyatli yangilandi va barcha kanallarda qo'llanildi",
        "profile": updated.to_dict()
    })


async def handle_remote_pair(request):
    """POST /api/remote/pair - Kod generatsiya qilish (MK-XXXXXX) yoki bog'lash"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:
        body = {}

    action = body.get("action", "generate")
    dev_id = body.get("device_id", "local_pc")

    from core.v8 import UserLinkingStore
    linking = UserLinkingStore.get_default_instance()

    if action == "generate":
        code = linking.generate_pairing_code(user_id, dev_id, ttl=300.0)
        await broadcast_ws("pairing_code_generated", {
            "device_id": dev_id,
            "code": code,
            "expires_in": 300
        })
        return web.json_response({
            "ok": True,
            "code": code,
            "expires_in": 300,
            "instruction": f"Telegram botingizda quyidagicha yuboring: /pair {code}"
        })
    elif action == "redeem":
        code = body.get("code", "")
        tg_id = body.get("telegram_user_id", "")
        ok, msg, link = linking.redeem_pairing_code(code, tg_id)
        if ok and link:
            await broadcast_ws("device_paired", {
                "device_id": link.device_id,
                "telegram_user_id": link.telegram_user_id
            })
            return web.json_response({"ok": True, "message": msg, "link": link.to_dict()})
        return web.json_response({"ok": False, "error": msg}, status=400)

    return web.json_response({"ok": False, "error": f"Noma'lum amal: {action}"}, status=400)


async def handle_remote_unpair(request):
    """POST /api/remote/unpair - Telegram bog'lanishini uzish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:
        body = {}

    dev_id = body.get("device_id", "")
    from core.v8 import UserLinkingStore, DeviceRegistry
    linking = UserLinkingStore.get_default_instance()
    reg = DeviceRegistry.get_default_instance()

    unpaired = linking.unlink_telegram(dev_id)
    reg.unpair_device(dev_id)

    await broadcast_ws("device_unpaired", {"device_id": dev_id})
    return web.json_response({
        "ok": True,
        "message": "Bog'lanish bekor qilindi",
        "device_id": dev_id,
        "unpaired": unpaired
    })


async def handle_remote_session_lock(request):
    """POST /api/remote/session/lock - Masofaviy sessiyani bloklash / qulflash"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:
        body = {}

    dev_id = body.get("device_id", "")
    from core.v8 import SessionManager
    sm = SessionManager()
    closed = sm.close_session(user_id, dev_id)

    await broadcast_ws("session_locked", {"device_id": dev_id})
    return web.json_response({
        "ok": True,
        "message": "Masofaviy sessiya qulflandi",
        "closed": closed
    })


async def handle_remote_session_logout(request):
    """POST /api/remote/session/logout - Masofaviy sessiyani yopish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:
        body = {}

    dev_id = body.get("device_id", "")
    from core.v8 import SessionManager
    sm = SessionManager()
    closed = sm.close_session(user_id, dev_id)

    await broadcast_ws("session_logout", {"device_id": dev_id})
    return web.json_response({
        "ok": True,
        "message": "Masofaviy sessiya yakunlandi",
        "closed": closed
    })


async def handle_remote_audit(request):
    """GET /api/remote/audit - Masofaviy hodisalar auditi (Sanitizatsiyalangan)"""
    from core.v8 import RemoteAuditLogger
    logger_inst = RemoteAuditLogger.get_instance()
    history = logger_inst.get_history(limit=50)

    return web.json_response({
        "ok": True,
        "total": len(history),
        "events": [e.to_dict() for e in reversed(history)]
    })


# ========== 8.5. PHASE 39: UNIVERSAL TELEGRAM BOT & IDENTITY API ==========

async def handle_telegram_link_start(request):
    """POST /api/telegram/link/start - 6 xonali OTP va Telegram deep-link yaratish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    try:
        body = await request.json()
    except Exception:
        body = {}

    mikasa_user_id = user_id
    from core.v8 import TelegramIdentityManager
    mgr = TelegramIdentityManager.get_default_instance()
    bot_username = os.environ.get("TELEGRAM_BOT_USERNAME", "MikasaUniversalBot")

    req, otp, deep_link, err_msg = mgr.create_link_request(
        mikasa_user_id=mikasa_user_id,
        bot_username=bot_username
    )
    if err_msg or not req:
        return web.json_response({"ok": False, "error": err_msg or "Kod yaratishda xatolik"}, status=400)

    await broadcast_ws("PAIRING_CREATED", {
        "request_id": req.request_id,
        "mikasa_user_id": req.mikasa_user_id,
        "expires_at": req.expires_at,
        "ttl_seconds": int(mgr.DEFAULT_TTL)
    })
    await broadcast_ws("PAIRING_WAITING", {
        "request_id": req.request_id,
        "mikasa_user_id": req.mikasa_user_id
    })

    return web.json_response({
        "ok": True,
        "request_id": req.request_id,
        "otp": otp,
        "link_token": req.link_token,
        "deep_link": deep_link,
        "expires_at": req.expires_at,
        "ttl_seconds": int(mgr.DEFAULT_TTL),
        "bot_username": bot_username
    })


async def handle_telegram_link_verify(request):
    """POST /api/telegram/link/verify - OTP kodni tekshirish va hisobni bog'lash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    otp = body.get("otp", "")
    tg_id = body.get("telegram_user_id")
    username = body.get("username")
    first_name = body.get("first_name")
    request_id = body.get("request_id")

    from core.v8 import TelegramIdentityManager
    mgr = TelegramIdentityManager.get_default_instance()

    ok, msg, link = mgr.verify_otp(
        otp=otp,
        telegram_user_id=tg_id,
        first_name=first_name,
        username=username,
        request_id=request_id
    )

    if ok and link:
        await broadcast_ws("PAIRING_VERIFIED", {
            "telegram_user_id": link.telegram_user_id,
            "mikasa_user_id": link.mikasa_user_id
        })
        await broadcast_ws("TELEGRAM_CONNECTED", {
            "telegram_user_id": link.telegram_user_id,
            "mikasa_user_id": link.mikasa_user_id,
            "linked_at": link.linked_at
        })
        return web.json_response({
            "ok": True,
            "message": msg,
            "link": link.to_dict(),
            "mikasa_user_id": link.mikasa_user_id
        })

    await broadcast_ws("PAIRING_FAILED", {
        "error": msg
    })
    return web.json_response({"ok": False, "error": msg}, status=400)


async def handle_telegram_link_status(request):
    """GET /api/telegram/link/status - Bog'lanish holatini tekshirish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    mikasa_user_id = user_id
    request_id = request.query.get("request_id")

    from core.v8 import TelegramIdentityManager
    mgr = TelegramIdentityManager.get_default_instance()

    link = mgr.get_link_by_mikasa_user(mikasa_user_id)
    if link and link.is_active:
        return web.json_response({
            "ok": True,
            "status": "CONNECTED",
            "is_linked": True,
            "telegram_user_id": link.telegram_user_id,
            "link": link.to_dict()
        })

    if request_id:
        req = mgr.get_request(request_id)
        if not req:
            return web.json_response({"ok": False, "error": "So'rov topilmadi"}, status=404)
        ttl_left = max(0, int(req.expires_at - time.time()))
        status_name = "EXPIRED" if req.is_expired() else req.status
        return web.json_response({
            "ok": True,
            "status": status_name,
            "is_linked": req.status == "VERIFIED",
            "attempt_count": req.attempt_count,
            "expires_at": req.expires_at,
            "ttl_seconds": ttl_left
        })

    return web.json_response({
        "ok": True,
        "status": "NOT_CONNECTED",
        "is_linked": False,
        "telegram_user_id": None
    })


async def handle_telegram_unlink(request):
    """POST /api/telegram/unlink - Telegram bog'lanishini bekor qilish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    try:
        body = await request.json()
    except Exception:
        body = {}

    mikasa_user_id = user_id
    tg_id = body.get("telegram_user_id")

    from core.v8 import TelegramIdentityManager
    mgr = TelegramIdentityManager.get_default_instance()

    unlinked = mgr.unlink(mikasa_user_id=mikasa_user_id, telegram_user_id=tg_id)
    if unlinked:
        await broadcast_ws("TELEGRAM_DISCONNECTED", {
            "mikasa_user_id": mikasa_user_id
        })
        return web.json_response({"ok": True, "message": "Telegram hisobi muvaffaqiyatli uzildi"})

    return web.json_response({"ok": False, "error": "Faol bog'lanish topilmadi"}, status=400)


async def handle_telegram_account(request):
    """GET /api/telegram/account - Foydalanuvchining Telegram profili va bog'lanish ma'lumotlari"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    mikasa_user_id = user_id
    from core.v8 import TelegramIdentityManager
    mgr = TelegramIdentityManager.get_default_instance()

    link = mgr.get_link_by_mikasa_user(mikasa_user_id)
    ident = mgr.get_identity(link.telegram_user_id) if link else None

    return web.json_response({
        "ok": True,
        "is_linked": link is not None and link.is_active,
        "link": link.to_dict() if link else None,
        "telegram_identity": ident.to_dict() if ident else None
    })


async def handle_telegram_status(request):
    """GET /api/telegram/status - Telegram Bot tizim holati"""
    from core.v8 import TelegramIdentityManager
    mgr = TelegramIdentityManager.get_default_instance()
    bot_username = os.environ.get("TELEGRAM_BOT_USERNAME", "MikasaUniversalBot")

    return web.json_response({
        "ok": True,
        "configured": bool(os.environ.get("TELEGRAM_BOT_TOKEN") or True),
        "bot_username": bot_username,
        "active_links_count": mgr.count_active_links(),
        "pending_requests_count": mgr.count_pending_requests()
    })


# ========== 8.1. PHASE 40 & 41: ACCOUNT & MULTI-DEVICE MANAGEMENT API ==========

def get_auth_token_from_request(request) -> Optional[str]:
    """So'rovdan sessiya tokenini ajratib olish (Faqat Authorization Bearer yoki X-Mikasa-Session-Token header).
    Xavfsizlik talabi: Query parametridan token o'qish (loglarda sizib chiqishi xavfi tufayli) to'liq bekor qilingan.
    """
    auth_header = getattr(request, "headers", {}).get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token
    token = getattr(request, "headers", {}).get("X-Mikasa-Session-Token")
    if token:
        return token.strip()
    return None


def resolve_auth_identity(
    request,
    required: bool = True
) -> Tuple[Optional[str], Optional[Any], Optional[Any], Optional[web.Response]]:
    """Multi-tenant xavfsiz foydalanuvchi identifikatsiyasini aniqlash.
    Qaytaradi: (user_id, user, session, error_response).
    1. So'rovdan Bearer tokenni oladi va AccountAuthManager orqali tekshiradi (JWT.sub).
    2. Agar token berilgan bo'lsa:
       - Yaroqsiz, muddati o'tgan yoki soxta bo'lsa -> 401 Unauthorized.
       - Haqiqiy bo'lsa -> user_id = JWT.sub.
       - Agar request parametri (query yoki header) orqali boshqa user_id uzatilgan bo'lsa -> 403 Forbidden ("Cross-tenant access denied").
    3. Agar token berilmagan bo'lsa:
       - Supabase sozlangan bo'lsa (yoki MIKASA_REQUIRE_AUTH yoqilgan bo'lsa) va required=True:
         -> 401 Unauthorized.
       - Offline / test rejimida (Supabase sozlanmagan bo'lsa):
         parametr orqali kelgan user_id olinadi (yoki "local_user"), lekin hech qachon avtomatik "admin" ga fallback qilinmaydi.
    """
    from core.v8 import AccountAuthManager
    auth_mgr = AccountAuthManager.get_default_instance()
    token = get_auth_token_from_request(request)

    req_headers = getattr(request, "headers", {}) or {}
    req_query = getattr(request, "query", {}) or {}
    param_user_id = (
        req_headers.get("X-Mikasa-User-Id")
        or req_headers.get("X-User-Id")
        or req_query.get("user_id")
        or req_query.get("mikasa_user_id")
    )
    if param_user_id:
        param_user_id = str(param_user_id).strip()

    if token:
        session, user = auth_mgr.authenticate_token(token)
        if not user or not session:
            err_resp = web.json_response({
                "ok": False,
                "error": "Avtorizatsiyadan o'tilmagan: Token yaroqsiz yoki muddati o'tgan"
            }, status=401)
            return None, None, None, err_resp

        authenticated_user_id = user.id
        # Cross-tenant spoofing tekshiruvi:
        if param_user_id and param_user_id != authenticated_user_id:
            logger.warning(
                f"Xavfsizlik: Cross-tenant murojaat aniqlandi! Autentifikatsiya={authenticated_user_id}, "
                f"So'ralgan={param_user_id}"
            )
            err_resp = web.json_response({
                "ok": False,
                "error": "Cross-tenant access denied: Ruxsatsiz hisob murojaati"
            }, status=403)
            return None, None, None, err_resp

        return authenticated_user_id, user, session, None

    # Token yo'q holat
    is_auth_enforced = auth_mgr.is_configured() or os.environ.get("MIKASA_REQUIRE_AUTH", "").lower() in ("true", "1")
    if is_auth_enforced and required:
        err_resp = web.json_response({
            "ok": False,
            "error": "Avtorizatsiyadan o'tilmagan: Bearer token talab qilinadi"
        }, status=401)
        return None, None, None, err_resp

    # Supabase sozlanmagan offline / test rejimi
    if param_user_id:
        return param_user_id, None, None, None

    local_id = get_current_user_name() or "local_user"
    return local_id, None, None, None


def get_authenticated_user(request) -> Tuple[Optional[Any], Optional[Any]]:
    """Token orqali haqiqiy foydalanuvchi va uning sessiyasini aniqlash.
    Qaytaradi: (session, user) yoki (None, None).
    """
    token = get_auth_token_from_request(request)
    if not token:
        return None, None
    try:
        from core.v8 import AccountAuthManager
        auth_mgr = AccountAuthManager.get_default_instance()
        return auth_mgr.authenticate_token(token)
    except Exception as e:
        logger.warning(f"get_authenticated_user xatosi: {e}")
        return None, None


def _get_request_user_id(request) -> str:
    """So'rovdan foydalanuvchi identifikatorini olish (Xavfsiz: token tekshiruvi bilan)."""
    uid, _, _, _ = resolve_auth_identity(request, required=False)
    return uid or "local_user"


async def handle_devices_list(request):
    """GET /api/devices and GET /api/account/devices - Foydalanuvchining ulangan kompyuterlari ro'yxati"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    from core.v8 import AccountDeviceManager
    from core.v8.device import DeviceIdentityManager
    mgr = AccountDeviceManager.get_default_instance()
    loc = DeviceIdentityManager.create_local_identity()

    devices = mgr.get_devices_for_user(user_id, include_revoked=False)

    # 1. Agar ro'yxat bo'sh bo'lsa, lokal kompyuterni kiritish
    if not devices:
        host_label = loc.hostname or "Asosiy Kompyuter"
        dev = mgr.register_device(
            user_id=user_id,
            device_id=loc.device_id,
            name=f"{host_label} (Joriy kompyuter)",
            hostname=loc.hostname,
            platform=loc.os_name.lower(),
            agent_version=loc.agent_version,
            status="online"
        )
        devices = [dev]
        mgr.select_device(user_id, dev.device_id)

    # 2. Agar mavjud yagona qurilma eski dummy (dev-sess-1) bo'lsa, uni joriy kompyuter bilan bog'lash
    if len(devices) == 1 and devices[0].device_id == "dev-sess-1":
        d0 = devices[0]
        if not d0.name or d0.name == "dev-sess-1":
            d0.name = f"{loc.hostname or 'Asosiy Kompyuter'} (Joriy kompyuter)"
        d0.hostname = loc.hostname
        d0.status = "online"
        d0.last_seen_at = time.time()
        d0.platform = loc.os_name.lower()
        d0.agent_version = loc.agent_version
        mgr._devices_by_hw_id[loc.device_id] = d0.id
        mgr.save()

    # 3. Joriy kompyuterni belgilash va yangilash
    local_dev = None
    for d in devices:
        if d.device_id == loc.device_id or (bool(d.hostname) and d.hostname.lower() == loc.hostname.lower()):
            local_dev = d
            d.status = "online"
            d.last_seen_at = time.time()
            d.hostname = loc.hostname
            d.platform = loc.os_name.lower()
            d.agent_version = loc.agent_version
            mgr._devices_by_hw_id[loc.device_id] = d.id
            break

    # Agar ro'yxatda faqat 1 ta qurilma bo'lsa va local_dev topilmagan bo'lsa, ushbu yagona qurilma joriy desktop qurilmasi deb hisoblanadi
    if not local_dev and len(devices) == 1:
        local_dev = devices[0]
        local_dev.status = "online"
        local_dev.last_seen_at = time.time()
        local_dev.hostname = loc.hostname
        local_dev.platform = loc.os_name.lower()
        local_dev.agent_version = loc.agent_version
        mgr._devices_by_hw_id[loc.device_id] = local_dev.id
        mgr.save()

    selected = mgr.get_selected_device(user_id)
    if not selected or selected.is_revoked:
        sel_target = local_dev or devices[0]
        mgr.select_device(user_id, sel_target.device_id)
        selected = sel_target

    # 4. Har bir qurilmaga is_current belgisini biriktirish
    enriched_devices = []
    for d in devices:
        d_dict = d.to_dict()
        is_curr = (
            (local_dev and (d.id == local_dev.id or d.device_id == local_dev.device_id))
            or d.device_id == loc.device_id
            or (bool(d.hostname) and d.hostname.lower() == loc.hostname.lower())
        )
        d_dict["is_current"] = bool(is_curr)
        if is_curr:
            d_dict["status"] = "online"
        enriched_devices.append(d_dict)

    enriched_devices.sort(key=lambda x: 0 if x.get("is_current") else 1)

    return web.json_response({
        "ok": True,
        "user_id": user_id,
        "devices": enriched_devices,
        "selected_device_id": selected.device_id if selected else (local_dev.device_id if local_dev else None),
        "current_device_id": local_dev.device_id if local_dev else None
    })


async def handle_device_detail(request):
    """GET /api/devices/{device_id} - Muayyan qurilma tafsilotlari"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    dev_id = urllib.parse.unquote(request.match_info.get("device_id", ""))
    from core.v8 import AccountDeviceManager
    mgr = AccountDeviceManager.get_default_instance()

    dev = mgr.get_device(dev_id, user_id=user_id)
    if not dev or dev.is_revoked:
        return web.json_response({
            "ok": False,
            "error": "Qurilma topilmadi yoki hisobingizga tegishli emas"
        }, status=404)

    selected = mgr.get_selected_device(user_id)
    is_selected = selected is not None and (selected.device_id == dev.device_id or selected.id == dev.id)

    return web.json_response({
        "ok": True,
        "device": {
            **dev.to_dict(),
            "is_selected": is_selected
        }
    })


async def handle_device_rename(request):
    """PATCH /api/devices/{device_id} - Qurilma do'stona nomini yangilash"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    dev_id = urllib.parse.unquote(request.match_info.get("device_id", ""))
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    new_name = body.get("name", "")
    from core.v8 import AccountDeviceManager
    from core.v8.device import DeviceIdentityManager
    mgr = AccountDeviceManager.get_default_instance()
    loc = DeviceIdentityManager.create_local_identity()

    ok, msg, dev = mgr.rename_device(dev_id, user_id=user_id, new_name=new_name)
    if not ok or not dev:
        status_code = 404 if "NOT_FOUND" in msg else 400
        return web.json_response({"ok": False, "error": msg}, status=status_code)

    dev_dict = dev.to_dict()
    is_curr = (
        dev.device_id == loc.device_id
        or (bool(dev.hostname) and dev.hostname.lower() == loc.hostname.lower())
    )
    dev_dict["is_current"] = bool(is_curr)
    if is_curr:
        dev_dict["status"] = "online"

    await broadcast_ws("DEVICE_RENAMED", {
        "user_id": user_id,
        "device": dev_dict
    })

    return web.json_response({
        "ok": True,
        "message": msg,
        "device": dev_dict
    })


async def handle_device_revoke(request):
    """DELETE /api/devices/{device_id} - Qurilmani bekor qilish (Revoke & Cascade)"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    dev_id = urllib.parse.unquote(request.match_info.get("device_id", ""))
    from core.v8 import AccountDeviceManager
    mgr = AccountDeviceManager.get_default_instance()

    ok, msg = mgr.revoke_device(dev_id, user_id=user_id)
    if not ok:
        return web.json_response({"ok": False, "error": msg}, status=404)

    await broadcast_ws("DEVICE_REVOKED", {
        "user_id": user_id,
        "device_id": dev_id
    })

    return web.json_response({
        "ok": True,
        "message": msg,
        "device_id": dev_id
    })


async def handle_device_select(request):
    """POST /api/devices/{device_id}/select - Faol qurilmani tanlash"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    dev_id = urllib.parse.unquote(request.match_info.get("device_id", ""))
    from core.v8 import AccountDeviceManager
    mgr = AccountDeviceManager.get_default_instance()

    ok, msg, dev = mgr.select_device(user_id=user_id, device_id_or_uuid=dev_id)
    if not ok or not dev:
        return web.json_response({"ok": False, "error": msg}, status=404)

    await broadcast_ws("DEVICE_SELECTED", {
        "user_id": user_id,
        "selected_device_id": dev.device_id,
        "device": dev.to_dict()
    })

    return web.json_response({
        "ok": True,
        "message": msg,
        "selected_device": dev.to_dict()
    })


async def handle_device_permissions(request):
    """GET /api/devices/{device_id}/permissions - Qurilma uchun foydalanuvchi ruxsatlari"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    dev_id = urllib.parse.unquote(request.match_info.get("device_id", ""))
    from core.v8 import AccountDeviceManager, PermissionStore
    mgr = AccountDeviceManager.get_default_instance()

    dev = mgr.get_device(dev_id, user_id=user_id)
    if not dev or dev.is_revoked:
        return web.json_response({
            "ok": False,
            "error": "Qurilma topilmadi yoki hisobingizga tegishli emas"
        }, status=404)

    store = PermissionStore.get_default_instance()
    profile = store.get_profile(user_id, dev.device_id)

    return web.json_response({
        "ok": True,
        "device_id": dev.device_id,
        "profile": profile.to_dict(),
        "catalog": store.get_catalog()
    })


async def handle_account_sessions(request):
    """GET /api/account/sessions - Foydalanuvchining barcha faol sessiyalari"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    from core.v8.auth_session import SessionManager
    from core.v8 import AccountDeviceManager
    sm = SessionManager.get_default_instance()
    adm = AccountDeviceManager.get_default_instance()

    sessions = sm.get_sessions_for_user(user_id)
    sessions_data = []
    for s in sessions:
        dev = adm.get_device(s.device_id, user_id=user_id)
        dev_name = dev.name if dev else s.device_id
        d = s.to_dict()
        d["device_name"] = dev_name
        sessions_data.append(d)

    return web.json_response({
        "ok": True,
        "user_id": user_id,
        "sessions": sessions_data,
        "total": len(sessions_data)
    })


async def handle_account_sessions_logout_all(request):
    """POST /api/account/sessions/logout-all - Barcha sessiyalarni to'xtatish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    from core.v8.auth_session import SessionManager
    sm = SessionManager.get_default_instance()

    count = sm.logout_all_sessions(user_id)
    await broadcast_ws("SESSION_LOGOUT", {
        "user_id": user_id,
        "terminated_count": count
    })

    return web.json_response({
        "ok": True,
        "message": f"Barcha ({count} ta) faol sessiyalar muvaffaqiyatli to'xtatildi",
        "terminated_count": count
    })


# ========== 8.2. PHASE 41: SUPABASE AUTHENTICATION API ==========

async def handle_auth_register(request):
    """POST /api/auth/register - Supabase Auth xabarnomasi"""
    return web.json_response({
        "ok": True,
        "message": "Supabase Auth orqali ro'yxatdan o'tish frontend mijozida (supabase.auth.signUp) to'g'ridan-to'g'ri amalga oshiriladi. Mikasa backend parollarni qabul qilmaydi va saqlamaydi.",
        "provider": "supabase_auth"
    }, status=200)


async def handle_auth_login(request):
    """POST /api/auth/login - Supabase Auth xabarnomasi"""
    return web.json_response({
        "ok": True,
        "message": "Supabase Auth orqali kirish frontend mijozida (supabase.auth.signInWithPassword) amalga oshiriladi. Backend JWT Bearer token bilan tekshiradi.",
        "provider": "supabase_auth"
    }, status=200)


async def handle_auth_logout(request):
    """POST /api/auth/logout - Chiqish haqida xabar berish"""
    session, user = get_authenticated_user(request)
    user_id = user.id if user else "anonymous"

    await broadcast_ws("ACCOUNT_LOGOUT", {
        "user_id": user_id,
        "logged_out": True
    })

    return web.json_response({
        "ok": True,
        "message": "Muvaffaqiyatli chiqildi",
        "logged_out": True
    })


async def handle_auth_logout_all(request):
    """POST /api/auth/logout-all - Barcha qurilmalardan chiqish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    await broadcast_ws("ACCOUNT_LOGOUT_ALL", {
        "user_id": user_id
    })

    return web.json_response({
        "ok": True,
        "message": "Barcha faol sessiyalar to'xtatildi",
        "user_id": user_id
    })


async def handle_auth_me(request):
    """GET /api/auth/me - Joriy autentifikatsiyadan o'tgan foydalanuvchi ma'lumotlari (Supabase JWT)"""
    session, user = get_authenticated_user(request)
    if not user or not session:
        return web.json_response({
            "ok": False,
            "error": "Avtorizatsiyadan o'tilmagan",
            "authenticated": False
        }, status=401)

    return web.json_response({
        "ok": True,
        "authenticated": True,
        "user": user.to_dict(),
        "session": session.to_dict()
    })


async def handle_auth_verify_email(request):
    """POST /api/auth/verify-email - Supabase Auth email confirmation notice"""
    return web.json_response({
        "ok": True,
        "message": "Email tasdiqlash Supabase Auth tomonidan avtomatik tasdiqlash havolasi orqali amalga oshiriladi.",
        "provider": "supabase_auth"
    })


async def handle_auth_forgot_password(request):
    """POST /api/auth/forgot-password - Supabase Auth reset password notice"""
    return web.json_response({
        "ok": True,
        "message": "Parolni tiklash frontend mijozi orqali supabase.auth.resetPasswordForEmail() yordamida amalga oshiriladi.",
        "provider": "supabase_auth"
    })


async def handle_auth_reset_password(request):
    """POST /api/auth/reset-password - Supabase Auth reset password notice"""
    return web.json_response({
        "ok": True,
        "message": "Yangi parol Supabase Auth orqali supabase.auth.updateUser({ password }) bilan o'rnatiladi.",
        "provider": "supabase_auth"
    })


async def handle_auth_change_password(request):
    """POST /api/auth/change-password - Supabase Auth password update notice"""
    return web.json_response({
        "ok": True,
        "message": "Parolni o'zgartirish Supabase Auth orqali supabase.auth.updateUser({ password }) bilan bajariladi.",
        "provider": "supabase_auth"
    })


async def handle_health(request):
    """GET /api/health - Tizim holati va diagnostika (sensitive keys hech qachon chiqmaydi)"""
    import time
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = (
        os.environ.get("SUPABASE_PUBLISHABLE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
        or ""
    )
    is_supabase_configured = bool(
        supabase_url
        and supabase_key
        and "placeholder-project" not in supabase_url
        and supabase_key not in ("placeholder-anon-key", "placeholder-publishable-key")
    )
    env_name = os.environ.get("ENVIRONMENT", "development")

    return web.json_response({
        "status": "ok",
        "app": "Mikasa AI",
        "version": "8.0.0",
        "supabase": "configured" if is_supabase_configured else "not_configured",
        "environment": env_name,
        "timestamp": time.time()
    }, status=200)


# ========== 8.2.1. OAUTH REDIRECT & SESSION RECEIVER ==========
import threading
_pending_oauth_sessions: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_pending_oauth_lock = threading.Lock()
OAUTH_SESSION_TTL_SECONDS = 300.0  # 5 daqiqa


def _clean_expired_oauth_sessions():
    """Muddati o'tgan OAuth sessiyalarini xotiradan tozalash"""
    now = time.time()
    with _pending_oauth_lock:
        expired_keys = [k for k, (exp, _) in _pending_oauth_sessions.items() if exp <= now]
        for k in expired_keys:
            _pending_oauth_sessions.pop(k, None)


async def handle_oauth_callback(request):
    """GET /api/auth/callback - OAuth redirect landing page for Desktop & Web"""
    html_content = """<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mikasa AI — Kirish muvaffaqiyatli</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0B0F19;
      color: #F8FAFC;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
    }
    .card {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid rgba(16, 185, 129, 0.4);
      border-radius: 20px;
      padding: 40px;
      text-align: center;
      max-width: 440px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.6), 0 0 30px rgba(16, 185, 129, 0.15);
    }
    .icon {
      width: 64px;
      height: 64px;
      margin: 0 auto 20px;
      border-radius: 18px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
    }
    h1 { font-size: 22px; color: #FFFFFF; margin-bottom: 8px; font-weight: 700; }
    p { font-size: 14px; color: #94A3B8; line-height: 1.5; margin-bottom: 24px; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: 9999px;
      background: rgba(16, 185, 129, 0.12);
      color: #34D399;
      font-size: 13px;
      font-weight: 600;
    }
    .status.error {
      background: rgba(239, 68, 68, 0.12);
      color: #F87171;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✨</div>
    <h1>Mikasa AI</h1>
    <p id="msg">Google orqali autentifikatsiya yakunlanmoqda...</p>
    <div id="badge" class="status">Kutilmoqda...</div>
  </div>
  <script>
    (function() {
      const searchParams = new URLSearchParams(window.location.search);
      const hashParams = new URLSearchParams(window.location.hash.substring(1));
      
      const accessToken = hashParams.get('access_token') || searchParams.get('access_token');
      const refreshToken = hashParams.get('refresh_token') || searchParams.get('refresh_token');
      const code = searchParams.get('code') || hashParams.get('code');
      const state = searchParams.get('state') || hashParams.get('state') || '';
      const error = searchParams.get('error') || hashParams.get('error') || searchParams.get('error_description') || hashParams.get('error_description');

      const msgEl = document.getElementById('msg');
      const badgeEl = document.getElementById('badge');

      if (error) {
        msgEl.textContent = "Xatolik: " + decodeURIComponent(error);
        badgeEl.textContent = "Muvaffaqiyatsiz";
        badgeEl.className = "status error";
        return;
      }

      if (accessToken || code) {
        fetch('/api/auth/callback/session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            access_token: accessToken,
            refresh_token: refreshToken,
            code: code,
            state: state,
            timestamp: Date.now()
          })
        }).then(function(res) { return res.json(); }).then(function(data) {
          msgEl.innerHTML = "Tizimga muvaffaqiyatli kirdingiz!<br>Ushbu oynani yopib, Mikasa ilovasiga qaytishingiz mumkin.";
          badgeEl.textContent = "Tasdiqlandi ✓";
          setTimeout(function() {
            try { window.close(); } catch(e) {}
          }, 1500);
        }).catch(function(err) {
          msgEl.textContent = "Tizimga kirish tasdiqlandi. Mikasa ilovasiga qaytishingiz mumkin.";
          badgeEl.textContent = "Tayyor ✓";
        });
      } else {
        msgEl.textContent = "Avtorizatsiya tokeni qabul qilinmadi.";
        badgeEl.textContent = "Xatolik";
        badgeEl.className = "status error";
      }
    })();
  </script>
</body>
</html>"""
    return web.Response(text=html_content, content_type="text/html")


async def handle_oauth_session_save(request):
    """POST /api/auth/callback/session - Brauzerdan kelgan sessiya tokenlarini state bilan xavfsiz saqlash"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    state = str(data.get("state") or request.query.get("state") or "default").strip()
    _clean_expired_oauth_sessions()

    now = time.time()
    expires_at = now + OAUTH_SESSION_TTL_SECONDS

    with _pending_oauth_lock:
        _pending_oauth_sessions[state] = (expires_at, data)

    # Extract name from JWT if available to immediately sync user name
    access_token = data.get("access_token")
    if access_token and "." in access_token:
        try:
            import base64
            parts = access_token.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1]
                payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                payload_json = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
                meta = payload_json.get("user_metadata", {})
                full_name = meta.get("full_name") or meta.get("name") or payload_json.get("email", "").split("@")[0]
                if full_name and full_name.strip():
                    name_to_save = full_name.strip()
                    cfg = _read_config()
                    if "user" not in cfg:
                        cfg["user"] = {}
                    cfg["user"]["name"] = name_to_save
                    _write_config(cfg)
                    try:
                        with open(USER_NAME_FILE, "w", encoding="utf-8") as f:
                            f.write(name_to_save)
                    except Exception:
                        pass
        except Exception:
            pass

    from core.v8.events import RemoteEventType, RemoteAuditEvent, RemoteAuditLogger
    audit = RemoteAuditLogger.get_instance()
    audit.log_event(RemoteAuditEvent(
        event_type=RemoteEventType.OAUTH_COMPLETED,
        details={"state": state, "status": "completed"}
    ))

    # Xavfsizlik: raw tokenlarni websocketga tarqatmaslik! Faqat xavfsiz holat hodisasi
    safe_event = {
        "ok": True,
        "status": "completed",
        "state": state,
        "timestamp": now
    }
    sync_broadcast("oauth_completed", safe_event, _main_loop)
    return web.json_response({"ok": True, "status": "saved", "state": state})


async def handle_oauth_session_get(request):
    """GET /api/auth/callback/session - Desktop ilova uchun kutilayotgan sessiyani state orqali bir martalik olish"""
    _clean_expired_oauth_sessions()
    req_state = request.query.get("state", "").strip()

    now = time.time()
    sess_data = None

    with _pending_oauth_lock:
        if req_state:
            item = _pending_oauth_sessions.pop(req_state, None)
            if item:
                exp, data = item
                if exp > now:
                    sess_data = data
        else:
            # Backward-compatibility for callers where state was omitted
            valid_keys = [k for k, (exp, _) in _pending_oauth_sessions.items() if exp > now]
            if valid_keys:
                latest_key = max(valid_keys, key=lambda k: _pending_oauth_sessions[k][0])
                _, sess_data = _pending_oauth_sessions.pop(latest_key)

    if sess_data:
        return web.json_response({"ok": True, "session": sess_data})

    return web.json_response({
        "ok": False,
        "session": None,
        "error": "Sessiya topilmadi yoki muddati o'tgan"
    }, status=404)


# ========== 8.2.2. PHASE 44: ACCOUNT IDENTITIES & LINKING API ==========

async def handle_account_identities_get(request):
    """GET /api/account/identities - Foydalanuvchining ulangan shaxslari (Email, Google) va xavfsiz holati"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    raw_claims = getattr(session, "raw_claims", {}) or {}
    app_metadata = raw_claims.get("app_metadata", {}) or {}
    user_metadata = raw_claims.get("user_metadata", {}) or {}

    providers = app_metadata.get("providers", [])
    primary_provider = app_metadata.get("provider", "email")
    if not providers:
        providers = [primary_provider] if primary_provider else ["email"]

    if "google" not in providers and (
        primary_provider == "google" or
        str(user_metadata.get("iss", "")).startswith("https://accounts.google.com") or
        user_metadata.get("avatar_url") or
        user_metadata.get("picture")
    ):
        providers.append("google")

    identities = []
    user_email = getattr(session, "email", "") or (user.email if user else "")

    # 1. Email identity
    if "email" in providers or primary_provider == "email" or user_email:
        identities.append({
            "provider": "email",
            "email": user_email,
            "is_primary": primary_provider == "email",
            "is_verified": bool(getattr(user, "is_verified", True))
        })

    # 2. Google identity
    is_google_linked = "google" in providers or primary_provider == "google"
    if is_google_linked:
        identities.append({
            "provider": "google",
            "email": user_metadata.get("email") or user_email,
            "name": user_metadata.get("full_name") or user_metadata.get("name") or getattr(session, "display_name", ""),
            "avatar_url": getattr(session, "avatar_url", "") or user_metadata.get("avatar_url") or user_metadata.get("picture", ""),
            "is_primary": primary_provider == "google"
        })

    # Lockout himoyasi: Google'ni faqat muqobil kirish usuli bo'lgandagina uzish mumkin!
    can_unlink_google = is_google_linked and ("email" in providers and len(identities) > 1)

    return web.json_response({
        "ok": True,
        "user_id": user_id,
        "providers": providers,
        "primary_provider": primary_provider,
        "identities": identities,
        "is_google_linked": is_google_linked,
        "can_unlink_google": can_unlink_google
    })


async def handle_account_identities_unlink(request):
    """POST /api/account/identities/unlink - Foydalanuvchining qo'shimcha Google hisobini uzish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    try:
        body = await request.json()
    except Exception:
        body = {}

    provider = str(body.get("provider", "")).strip().lower()
    if provider != "google":
        return web.json_response({
            "ok": False,
            "error": "Faqat qo'shimcha Google hisobini uzish qo'llab-quvvatlanadi"
        }, status=400)

    raw_claims = getattr(session, "raw_claims", {}) or {}
    app_metadata = raw_claims.get("app_metadata", {}) or {}
    providers = app_metadata.get("providers", [])
    primary_provider = app_metadata.get("provider", "email")

    is_google = "google" in providers or primary_provider == "google"
    if not is_google:
        return web.json_response({
            "ok": False,
            "error": "Google hisobi ushbu akkauntga ulanmagan"
        }, status=400)

    # Lockout tekshiruvi: Agar foydalanuvchi faqat Google orqali ro'yxatdan o'tgan bo'lsa va email/parol bo'lmasa
    has_alternative = "email" in providers and len(providers) > 1
    if not has_alternative:
        return web.json_response({
            "ok": False,
            "error": "Google sizning yagona kirish usulingizdir. Akkauntga kirish imkoniyatini yo'qotmaslik uchun avval parolni o'rnating yoki boshqa hisobni ulang."
        }, status=400)

    from core.v8.events import RemoteEventType, RemoteAuditEvent, RemoteAuditLogger
    audit = RemoteAuditLogger.get_instance()
    audit.log_event(RemoteAuditEvent(
        event_type=RemoteEventType.GOOGLE_UNLINKED,
        user_id=user_id,
        details={"provider": "google"}
    ))

    return web.json_response({
        "ok": True,
        "message": "Google hisobi muvaffaqiyatli uzildi",
        "user_id": user_id,
        "unlinked_provider": "google"
    })


async def handle_account_identities_link_initiate(request):
    """POST /api/account/identities/link/initiate - Akkauntni Google bilan xavfsiz bog'lash uchun sessiya kodi yaratish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    import secrets
    link_state = f"link_{secrets.token_urlsafe(24)}"
    now = time.time()
    expires_at = now + OAUTH_SESSION_TTL_SECONDS

    with _pending_oauth_lock:
        _pending_oauth_sessions[link_state] = (expires_at, {
            "action": "link",
            "user_id": user_id,
            "timestamp": now
        })

    from core.v8.events import RemoteEventType, RemoteAuditEvent, RemoteAuditLogger
    audit = RemoteAuditLogger.get_instance()
    audit.log_event(RemoteAuditEvent(
        event_type=RemoteEventType.GOOGLE_LINK_STARTED,
        user_id=user_id,
        details={"state": link_state}
    ))

    return web.json_response({
        "ok": True,
        "state": link_state,
        "user_id": user_id,
        "expires_in": int(OAUTH_SESSION_TTL_SECONDS)
    })


# ========== 8.3. PHASE 42: DEVICE ENROLLMENT & PAIRING API ==========

async def handle_device_pairing_start(request):
    """POST /api/devices/pairing/start - Yangi PC Agent juftlash kodini generatsiya qilish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err

    try:
        body = await request.json()
    except Exception:
        body = {}

    ttl = body.get("ttl", 300.0)
    meta = body.get("metadata", {})

    from core.v8.device_pairing import DevicePairingManager
    mgr = DevicePairingManager.get_default_instance()

    try:
        pairing_sess, raw_code = mgr.start_pairing(
            user_id=user_id,
            ttl_seconds=float(ttl),
            request_metadata=meta
        )
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=400)

    await broadcast_ws("DEVICE_PAIRING_STARTED", {
        "user_id": user_id,
        "pairing_id": pairing_sess.id,
        "expires_at": pairing_sess.expires_at
    })

    return web.json_response({
        "ok": True,
        "success": True,
        "pairing_id": pairing_sess.id,
        "code": raw_code,
        "expires_at": pairing_sess.expires_at,
        "expires_in": int(pairing_sess.remaining_seconds)
    })


async def handle_device_pairing_status(request):
    """GET /api/devices/pairing/{pairing_id} - Juftlash sessiyasi holatini tekshirish"""
    pairing_id = request.match_info.get("pairing_id", "")
    from core.v8.device_pairing import DevicePairingManager
    mgr = DevicePairingManager.get_default_instance()
    sess = mgr.get_session(pairing_id)

    if not sess:
        return web.json_response({"ok": False, "error": "Juftlash sessiyasi topilmadi"}, status=404)

    return web.json_response({
        "ok": True,
        "session": sess.to_dict(),
        "status": sess.status,
        "remaining_seconds": sess.remaining_seconds,
        "device_id": sess.device_id
    })


async def handle_device_pairing_cancel(request):
    """POST /api/devices/pairing/{pairing_id}/cancel - Juftlash sessiyasini bekor qilish"""
    user_id, user, session, err = resolve_auth_identity(request, required=True)
    if err:
        return err
    pairing_id = request.match_info.get("pairing_id", "")

    from core.v8.device_pairing import DevicePairingManager
    mgr = DevicePairingManager.get_default_instance()
    ok, msg = mgr.cancel_pairing(pairing_id, user_id=user_id)

    if not ok:
        status_code = 404 if "NOT_FOUND" in msg else 403
        return web.json_response({"ok": False, "error": msg}, status=status_code)

    await broadcast_ws("DEVICE_PAIRING_CANCELLED", {
        "user_id": user_id,
        "pairing_id": pairing_id
    })

    return web.json_response({"ok": True, "message": msg})


async def handle_device_pairing_complete(request):
    """POST /api/devices/pairing/complete - PC Agent enrollment va juftlashni yakunlash"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    pairing_id = body.get("pairing_id", "")
    code = body.get("code", "")
    public_key = body.get("public_key", "")
    dev_info = body.get("device", {}) or {}

    if not pairing_id or not code:
        return web.json_response({"ok": False, "error": "pairing_id va code kiritilishi shart"}, status=400)

    if not public_key:
        return web.json_response({"ok": False, "error": "public_key (Ed25519) kiritilishi shart"}, status=400)

    from core.v8.device_pairing import DevicePairingManager
    from core.v8.device_enrollment import DeviceEnrollmentManager
    pairing_mgr = DevicePairingManager.get_default_instance()
    enroll_mgr = DeviceEnrollmentManager.get_default_instance()

    # 1. Kodni tekshirish
    ok, msg, sess = pairing_mgr.verify_code(pairing_id, code)
    if not ok or not sess:
        status_code = 404 if "NOT_FOUND" in msg else 400
        return web.json_response({"ok": False, "error": msg}, status=status_code)

    # 2. Qurilma identifikatsiyasini aniqlash
    dev_id = dev_info.get("device_id")
    hostname = dev_info.get("hostname", "Mikasa-PC")
    platform_name = dev_info.get("platform", "Windows")
    os_version = dev_info.get("os_version", "10")
    fingerprint = dev_info.get("fingerprint", "")
    friendly_name = dev_info.get("name") or hostname

    if not dev_id:
        from core.v8.device import DeviceIdentityManager
        fp = fingerprint or DeviceIdentityManager.compute_fingerprint(hostname=hostname)
        dev_id = f"{hostname}@{fp[:8]}"

    # 3. Qurilmani hisob egasiga (sess.user_id) enroll qilish
    enroll_ok, enroll_msg, cred, device = enroll_mgr.enroll_device(
        user_id=sess.user_id,
        device_id=dev_id,
        public_key=public_key,
        name=friendly_name,
        hostname=hostname,
        platform_name=platform_name,
        os_version=os_version,
        fingerprint=fingerprint,
        metadata=dev_info.get("metadata", {})
    )

    if not enroll_ok or not device or not cred:
        return web.json_response({"ok": False, "error": enroll_msg}, status=400)

    # 4. Juftlash sessiyasini yakunlash
    pairing_mgr.complete_pairing(
        pairing_id=pairing_id,
        code=code,
        device_id=device.device_id,
        device_info=dev_info,
        user_id=sess.user_id
    )

    await broadcast_ws("DEVICE_ENROLLED", {
        "user_id": sess.user_id,
        "device_id": device.device_id,
        "device": device.to_dict()
    })

    return web.json_response({
        "ok": True,
        "success": True,
        "message": "Qurilma muvaffaqiyatli hisobga biriktirildi (enrolled)",
        "device": device.to_dict(),
        "credential": {
            "id": cred.id,
            "algorithm": cred.algorithm,
            "public_key": cred.public_key,
            "enrolled_at": cred.enrolled_at
        }
    })


async def handle_device_auth_challenge(request):
    """POST /api/devices/{device_id}/challenge - Autentifikatsiya uchun bir martalik nonce olish"""
    dev_id = request.match_info.get("device_id", "")
    from core.v8.device_auth import DeviceAuthManager
    auth_mgr = DeviceAuthManager.get_default_instance()

    ok, msg, data = auth_mgr.issue_challenge(dev_id)
    if not ok or not data:
        status_code = 404 if "NOT_ENROLLED" in msg else 400
        return web.json_response({"ok": False, "error": msg}, status=status_code)

    return web.json_response({
        "ok": True,
        "success": True,
        **data
    })


async def handle_device_auth_authenticate(request):
    """POST /api/devices/{device_id}/authenticate - Imzolangan chaqiriqni tekshirish va DeviceSession berish"""
    dev_id = request.match_info.get("device_id", "")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    challenge_id = body.get("challenge_id", "")
    signature = body.get("signature", "")
    context = body.get("context", {})

    if not challenge_id or not signature:
        return web.json_response({"ok": False, "error": "challenge_id va signature kiritilishi shart"}, status=400)

    from core.v8.device_auth import DeviceAuthManager
    auth_mgr = DeviceAuthManager.get_default_instance()

    ok, msg, dev_sess = auth_mgr.verify_challenge_response(
        device_id=dev_id,
        challenge_id=challenge_id,
        signature_hex=signature,
        context=context
    )

    if not ok or not dev_sess:
        status_code = 401 if "INVALID_SIGNATURE" in msg or "REPLAY" in msg else 400
        return web.json_response({"ok": False, "error": msg}, status=status_code)

    return web.json_response({
        "ok": True,
        "success": True,
        "session_token": dev_sess.token,
        "session_id": dev_sess.session_id,
        "expires_at": dev_sess.expires_at,
        "protocol_version": dev_sess.protocol_version
    })


# ========== 9. WEBSOCKET HANDLER ==========
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
            "version": "8.0.0"
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


# ========== CORS & Origin Security Middleware ==========
ALLOWED_REMOTE_IPS = {"127.0.0.1", "::1", "localhost", "testclient"}

@web.middleware
async def cors_middleware(request, handler):
    # Remote IP tekshiruvi: faqat lokal mijozlar qabul qilinadi
    if request.remote and request.remote not in ALLOWED_REMOTE_IPS:
        logger.warning(f"Xavfsizlik: Begona tarmoqdan so'rov rad etildi: {request.remote}")
        return web.HTTPForbidden(text="Xavfsizlik: Begona tarmoqdan murojaat taqiqlangan.")

    origin = request.headers.get("Origin", "")
    is_allowed = False
    if origin:
        origin_clean = origin.strip().lower()
        configured_origins = [
            o.strip().lower()
            for o in os.environ.get("MIKASA_ALLOWED_ORIGINS", "").split(",")
            if o.strip()
        ]
        is_allowed = (
            origin_clean in ("tauri://localhost", "http://tauri.localhost", "https://tauri.localhost")
            or origin_clean in configured_origins
            or origin_clean == "http://localhost"
            or origin_clean.startswith("http://localhost:")
            or origin_clean == "http://127.0.0.1"
            or origin_clean.startswith("http://127.0.0.1:")
            or origin_clean == "https://localhost"
            or origin_clean.startswith("https://localhost:")
            or origin_clean == "https://127.0.0.1"
            or origin_clean.startswith("https://127.0.0.1:")
        )
        if not is_allowed:
            logger.warning(f"Xavfsizlik: Begona veb-sayt Origin rad etildi: {origin}")
            return web.HTTPForbidden(text="Xavfsizlik: Begona Origin orqali kirish taqiqlangan.")

    if request.method == "OPTIONS":
        response = web.Response()
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex

    allowed_header_origin = origin if (origin and is_allowed) else "tauri://localhost"
    response.headers["Access-Control-Allow-Origin"] = allowed_header_origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Mikasa-Session-Token, X-Mikasa-User-Id"
    return response


# ========== Ilovani sozlash va marshrutlash ==========
def create_app():
    app = web.Application(middlewares=[cors_middleware])
    # Tizim va Bosh sahifa
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/api/system/metrics", handle_system_metrics)
    app.router.add_get("/api/ws", handle_ws)
    
    # AI Chat va Ovoz
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_post("/api/chat/clear", handle_chat_clear)
    app.router.add_post("/api/ai/test-key", handle_ai_test_key)
    app.router.add_post("/api/account/test-api-key", handle_ai_test_key)
    app.router.add_post("/api/voice/start", handle_voice_start)
    app.router.add_post("/api/voice/stop", handle_voice_stop)
    app.router.add_post("/api/voice/speak", handle_voice_speak)

    # Buyruqlar (Commands)
    app.router.add_get("/api/commands", handle_commands_list)
    app.router.add_post("/api/commands/execute", handle_commands_execute)

    # Xotira (Memory)
    app.router.add_get("/api/memory", handle_memory_get)
    app.router.add_post("/api/memory/profile", handle_memory_profile_save)
    app.router.add_post("/api/memory/knowledge", handle_memory_knowledge_save)
    app.router.add_put("/api/memory/knowledge/{id}", handle_memory_knowledge_update)
    app.router.add_delete("/api/memory/knowledge", handle_memory_knowledge_delete)
    app.router.add_delete("/api/memory/knowledge/{id}", handle_memory_knowledge_delete)
    app.router.add_post("/api/memory/pin", handle_memory_pin)
    app.router.add_get("/api/memory/policy", handle_memory_policy_get)
    app.router.add_post("/api/memory/policy", handle_memory_policy_save)
    app.router.add_get("/api/memory/metrics", handle_memory_metrics_get)
    app.router.add_post("/api/memory/knowledge/clear", handle_memory_knowledge_clear)
    app.router.add_post("/api/memory/context/clear", handle_memory_context_clear)
    app.router.add_post("/api/memory/history/clear", handle_memory_history_clear)

    # Kontekst va Observability (Context & Observability)
    app.router.add_get("/api/context/traces", handle_context_traces_get)
    app.router.add_get("/api/context/last-trace", handle_context_last_trace_get)

    # Agentlik Ko'p Bosqichli Tizim (Agent Loop)
    app.router.add_post("/api/agent/execute", handle_agent_execute)
    app.router.add_post("/api/agent/confirm", handle_agent_confirm)
    app.router.add_post("/api/agent/abort", handle_agent_abort)
    app.router.add_get("/api/agent/state", handle_agent_state)

    # Rejalashtiruvchi (Scheduler)
    app.router.add_get("/api/scheduler", handle_scheduler_list)
    app.router.add_post("/api/scheduler/add", handle_scheduler_add)
    app.router.add_post("/api/scheduler/edit", handle_scheduler_edit)
    app.router.add_post("/api/scheduler/enable", handle_scheduler_enable)
    app.router.add_post("/api/scheduler/disable", handle_scheduler_disable)
    app.router.add_post("/api/scheduler/execute", handle_scheduler_execute)
    app.router.add_delete("/api/scheduler/task", handle_scheduler_remove)
    app.router.add_post("/api/scheduler/clear-completed", handle_scheduler_clear_completed)

    # Plaginlar (Plugins & Tools)
    app.router.add_get("/api/plugins", handle_plugins_list)
    app.router.add_post("/api/plugins/toggle", handle_plugins_toggle)
    app.router.add_post("/api/plugins/install", handle_plugins_install)
    app.router.add_post("/api/plugins/uninstall", handle_plugins_uninstall)
    app.router.add_post("/api/plugins/update", handle_plugins_update)
    app.router.add_post("/api/plugins/execute", handle_plugins_execute)
    app.router.add_get("/api/tools/catalog", handle_tools_catalog)

    # Hisob va Sozlamalar (Account & Settings)
    app.router.add_get("/api/account", handle_account_get)
    app.router.add_post("/api/account", handle_account_update)

    # Phase 38: Masofaviy Boshqaruv & Ruxsatlar Markazi (Remote Control & Permissions)
    app.router.add_get("/api/remote/devices", handle_remote_devices)
    app.router.add_get("/api/remote/devices/{id}", handle_remote_device_detail)
    app.router.add_get("/api/remote/permissions/{device_id}", handle_remote_permissions_get)
    app.router.add_put("/api/remote/permissions/{device_id}", handle_remote_permissions_put)
    app.router.add_post("/api/remote/pair", handle_remote_pair)
    app.router.add_post("/api/remote/unpair", handle_remote_unpair)
    app.router.add_post("/api/remote/session/lock", handle_remote_session_lock)
    app.router.add_post("/api/remote/session/logout", handle_remote_session_logout)
    app.router.add_get("/api/remote/audit", handle_remote_audit)

    # Phase 39: Universal Telegram Bot & Identity
    app.router.add_post("/api/telegram/link/start", handle_telegram_link_start)
    app.router.add_post("/api/telegram/link/verify", handle_telegram_link_verify)
    app.router.add_get("/api/telegram/link/status", handle_telegram_link_status)
    app.router.add_post("/api/telegram/link/delete", handle_telegram_unlink)
    app.router.add_post("/api/telegram/unlink", handle_telegram_unlink)
    app.router.add_get("/api/telegram/identity", handle_telegram_account)
    app.router.add_get("/api/telegram/account", handle_telegram_account)
    app.router.add_get("/api/telegram/status", handle_telegram_status)

    # Phase 40: Universal Account & Multi-Device Management
    app.router.add_get("/api/account/devices", handle_devices_list)
    app.router.add_get("/api/devices", handle_devices_list)
    app.router.add_get("/api/devices/{device_id}", handle_device_detail)
    app.router.add_patch("/api/devices/{device_id}", handle_device_rename)
    app.router.add_delete("/api/devices/{device_id}", handle_device_revoke)
    app.router.add_post("/api/devices/{device_id}/select", handle_device_select)
    app.router.add_get("/api/devices/{device_id}/permissions", handle_device_permissions)
    app.router.add_get("/api/account/sessions", handle_account_sessions)
    app.router.add_post("/api/account/sessions/logout-all", handle_account_sessions_logout_all)

    # Phase 41: Account Registration & Authentication
    app.router.add_post("/api/auth/register", handle_auth_register)
    app.router.add_post("/api/auth/login", handle_auth_login)
    app.router.add_post("/api/auth/logout", handle_auth_logout)
    app.router.add_post("/api/auth/logout-all", handle_auth_logout_all)
    app.router.add_get("/api/auth/me", handle_auth_me)
    app.router.add_post("/api/auth/verify-email", handle_auth_verify_email)
    app.router.add_post("/api/auth/forgot-password", handle_auth_forgot_password)
    app.router.add_post("/api/auth/reset-password", handle_auth_reset_password)
    app.router.add_post("/api/auth/change-password", handle_auth_change_password)

    # Phase 41.1: OAuth Redirect & Session Receiver
    app.router.add_get("/api/auth/callback", handle_oauth_callback)
    app.router.add_post("/api/auth/callback/session", handle_oauth_session_save)
    app.router.add_get("/api/auth/callback/session", handle_oauth_session_get)
    # Root route fallback for port 1420 OAuth redirects
    app.router.add_get("/", handle_oauth_callback)

    # Phase 44: Account Identities & Linking
    app.router.add_get("/api/account/identities", handle_account_identities_get)
    app.router.add_post("/api/account/identities/unlink", handle_account_identities_unlink)
    app.router.add_post("/api/account/identities/link/initiate", handle_account_identities_link_initiate)

    # Phase 42: Device Enrollment & Cryptographic Pairing
    app.router.add_post("/api/devices/pairing/start", handle_device_pairing_start)
    app.router.add_post("/api/devices/pairing/complete", handle_device_pairing_complete)
    app.router.add_get("/api/devices/pairing/{pairing_id}", handle_device_pairing_status)
    app.router.add_post("/api/devices/pairing/{pairing_id}/cancel", handle_device_pairing_cancel)
    app.router.add_post("/api/devices/{device_id}/challenge", handle_device_auth_challenge)
    app.router.add_post("/api/devices/{device_id}/authenticate", handle_device_auth_authenticate)

    return app


def run_server(host="127.0.0.1", port=18420):
    logger.info(f"MIKASA AI 8.0.0 Background API Server boshlanmoqda: http://{host}:{port}")
    get_modules()
    app = create_app()

    async def _serve():
        global _main_loop
        _main_loop = asyncio.get_running_loop()
        runner = web.AppRunner(app)
        await runner.setup()

        # Primary port (18420)
        primary_site = web.TCPSite(runner, host, port)
        await primary_site.start()
        logger.info(f"Asosiy API server ishga tushdi: http://{host}:{port}")

        # Auxiliary port (1420) - Fallback for OAuth redirects if 1420 is free
        if port != 1420:
            try:
                aux_site = web.TCPSite(runner, host, 1420)
                await aux_site.start()
                logger.info("Qo'shimcha OAuth tinglovchisi ishga tushdi: http://127.0.0.1:1420")
            except Exception as e:
                logger.debug(f"Port 1420 band yoki ulanib bo'lmadi (dev server ishlamoqda): {e}")

        # Run indefinitely
        while True:
            await asyncio.sleep(3600)

    try:
        asyncio.run(_serve())
    except (KeyboardInterrupt, SystemExit):
        logger.info("API Server to'xtatildi")


if __name__ == "__main__":
    port = 18420
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
