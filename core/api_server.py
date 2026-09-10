# ========== api_server.py ==========
# Mikasa AI 7.0 — Desktop Background Backend API Server
# Ushbu server Tauri frontend (React) va Python AI yadrosi (main.py, ai_engine)
# orasidagi asinxron ko'prik (REST + WebSocket) hisoblanadi.
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

# Backend modullarini yuklash
_main = None
_ai_engine = None
_agent_memory = None
_active_ws_clients = set()
_voice_state = "idle"  # idle | listening | thinking | speaking
_lock = threading.Lock()

def get_modules():
    global _main, _ai_engine, _agent_memory
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
        except Exception:
            pass

    return _main, _ai_engine, _agent_memory


# ========== WebSocket Broadcaster ==========
async def broadcast_ws(event_type: str, data: dict):
    if not _active_ws_clients:
        return
    message = json.dumps({"type": event_type, "data": data, "timestamp": datetime.now().isoformat()})
    dead_clients = set()
    for ws in _active_ws_clients:
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
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_ws(event_type, data), loop)


# ========== HTTP Handlers ==========
async def handle_status(request):
    """GET /api/status - Tizim holati"""
    m, ai, _ = get_modules()
    user = m.foydalanuvchi_ismi_ol() if m else "Muxammadaziz"
    ai_ok = ai.ai_mavjudmi() if ai else False
    
    return web.json_response({
        "status": "online",
        "app": "MIKASA AI",
        "version": getattr(m, "VERSION", "7.0.0") if m else "7.0.0",
        "user": user,
        "ai_available": ai_ok,
        "voice_state": _voice_state,
        "timestamp": datetime.now().isoformat()
    })


async def handle_chat(request):
    """
    POST /api/chat - Matnli savol yoki buyruq yuborish
    Body: {"text": "...", "mode": "ask" | "command" | "summary"}
    """
    global _voice_state
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Noto'g'ri JSON formati"}, status=400)

    text = body.get("text", "").strip()
    mode = body.get("mode", "ask")

    if not text:
        return web.json_response({"ok": False, "error": "Matn bo'sh bo'lishi mumkin emas"}, status=400)

    m, ai, _ = get_modules()
    user = m.foydalanuvchi_ismi_ol() if m else "Muxammadaziz"
    ovoz = m.ovoz_turi_ol() if m else "ayol"

    loop = asyncio.get_running_loop()
    _voice_state = "thinking"
    sync_broadcast("voice_state", {"state": "thinking"}, loop)

    def _execute():
        global _voice_state
        try:
            if mode == "command" and m:
                # Buyruqni tushun va bajar
                res = m.buyruqni_tushun(text, user, ovoz)
                reply = res if isinstance(res, str) and res else "Buyruq bajarildi."
            elif mode == "summary" and ai:
                prompt = f"Quyidagi matnni tahlil qilib, eng muhim jihatlarini qisqa va aniq xulosalab ber:\n\n{text}"
                reply = ai.ai_savol_yuborish(prompt, user)
            else:
                # Standart AI savoli
                if ai:
                    reply = ai.ai_savol_yuborish(text, user)
                else:
                    reply = "Kechirasiz, sun'iy intellekt moduli mavjud emas."
        except Exception as e:
            logger.error(f"Chat bajarishda xatolik: {e}")
            reply = f"Xatolik yuz berdi: {str(e)}"
        finally:
            _voice_state = "idle"
            sync_broadcast("voice_state", {"state": "idle"}, loop)
        
        # Javobni toza matn ko'rinishiga keltirish
        if isinstance(reply, dict):
            reply_text = reply.get("response") or reply.get("javob") or reply.get("text") or str(reply)
        else:
            reply_text = str(reply)
        return reply_text

    response_text = await loop.run_in_executor(None, _execute)

    # Natijani broadcast qilish
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
    m, _, _ = get_modules()
    if not m:
        return web.json_response({"ok": False, "error": "Backend moduli yuklanmagan"}, status=500)

    loop = asyncio.get_running_loop()
    _voice_state = "listening"
    await broadcast_ws("voice_state", {"state": "listening"})

    def _voice_callback(msg):
        sync_broadcast("voice_event", {"message": str(msg)}, loop)

    def _listen():
        global _voice_state
        try:
            user = m.foydalanuvchi_ismi_ol()
            ovoz = m.ovoz_turi_ol()
            m.global_state.tinglash_faol = True
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
    m, _, _ = get_modules()
    if m:
        m.global_state.tinglash_faol = False
    _voice_state = "idle"
    await broadcast_ws("voice_state", {"state": "idle"})
    return web.json_response({"ok": True, "status": "stopped"})


async def handle_chat_clear(request):
    """POST /api/chat/clear - Suhbat tarixini tozalash"""
    _, ai, _ = get_modules()
    if ai:
        ai.suhbat_tarixini_tozalash()
    await broadcast_ws("chat_cleared", {})
    return web.json_response({"ok": True, "message": "Suhbat tarixi tozalandi"})


async def handle_ws(request):
    """WS /api/ws - Jonli WebSocket aloqa"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    _active_ws_clients.add(ws)
    logger.info(f"Yangi WebSocket mijozi ulandi. Jami: {len(_active_ws_clients)}")

    # Boshlang'ich holatni yuborish
    await ws.send_str(json.dumps({
        "type": "init",
        "data": {"status": "online", "voice_state": _voice_state},
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


# ========== Ilovani sozlash va ishga tushirish ==========
def create_app():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/api/status", handle_status)
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_post("/api/voice/start", handle_voice_start)
    app.router.add_post("/api/voice/stop", handle_voice_stop)
    app.router.add_post("/api/chat/clear", handle_chat_clear)
    app.router.add_get("/api/ws", handle_ws)
    return app


def run_server(host="127.0.0.1", port=18420):
    logger.info(f"MIKASA AI 7.0 Background API Server boshlanmoqda: http://{host}:{port}")
    get_modules()
    app = create_app()
    web.run_app(app, host=host, port=port, print=None)


if __name__ == "__main__":
    port = 18420
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
