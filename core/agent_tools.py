# ========== agent_tools.py ==========
# AI Agent Tool/Plugin tizimi
# Har bir tool — agent chaqira oladigan funksiya

import os
import re
import json
import math
import logging
import datetime
import webbrowser
from urllib.parse import quote_plus
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Loyiha ildizi


# ========================================================
# TOOL DATACLASS
# ========================================================

@dataclass
class Tool:
    """Bitta tool/plugin tavsifi"""
    name: str
    description: str  # AI uchun — tool nima qilishini tushuntirish
    parameters: dict   # {"param_name": {"type": "string", "description": "...", "required": True}}
    function: Callable  # Haqiqiy funksiya
    category: str = "general"
    
    def to_dict(self):
        """AI prompt uchun dict formatda"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                k: {"type": v.get("type", "string"), "description": v.get("description", "")}
                for k, v in self.parameters.items()
            }
        }
    
    def call(self, **kwargs):
        """Toolni chaqirish"""
        try:
            logger.info(f"Tool '{self.name}' chaqirildi: {kwargs}")
            result = self.function(**kwargs)
            logger.info(f"Tool '{self.name}' natija: {str(result)[:200]}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool '{self.name}' xatolik: {e}")
            return {"success": False, "error": str(e)}


# ========================================================
# TOOL REGISTRY
# ========================================================

class ToolRegistry:
    """Tool'larni ro'yxatdan o'tkazish va boshqarish"""
    
    def __init__(self):
        self._tools = {}
    
    def register(self, tool: Tool):
        """Yangi tool qo'shish"""
        self._tools[tool.name] = tool
        logger.debug(f"Tool ro'yxatdan o'tdi: {tool.name}")
    
    def get(self, name: str) -> Optional[Tool]:
        """Tool ni nomi bo'yicha olish"""
        return self._tools.get(name)
    
    def call(self, name: str, **kwargs) -> dict:
        """Tool ni nomi bo'yicha chaqirish"""
        tool = self.get(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' topilmadi"}
        return tool.call(**kwargs)
    
    def list_tools(self) -> list:
        """Barcha tool'larni ro'yxati"""
        return [t.to_dict() for t in self._tools.values()]
    
    def list_names(self) -> list:
        """Faqat nomlar"""
        return list(self._tools.keys())
    
    def tools_prompt(self) -> str:
        """AI prompt uchun tool'lar tavsifi"""
        lines = []
        for tool in self._tools.values():
            params_str = ", ".join(
                f"{k}: {v.get('type', 'string')}" 
                for k, v in tool.parameters.items()
            )
            lines.append(f"- {tool.name}({params_str}) — {tool.description}")
        return "\n".join(lines)
    
    @property
    def count(self):
        return len(self._tools)


# ========================================================
# O'RNATILGAN TOOL'LAR
# ========================================================

# --- 1. WEB SEARCH (Haqiqiy natijali!) ---
def _web_search(query: str, platform: str = "google") -> dict:
    """Internetda qidirish — haqiqiy natija qaytaradi (DuckDuckGo API)"""
    import requests
    
    # YouTube va Wikipedia — brauzerda ochish
    if platform in ("youtube", "wikipedia"):
        urls = {
            "youtube": f"https://www.youtube.com/results?search_query={quote_plus(query)}",
            "wikipedia": f"https://uz.wikipedia.org/w/index.php?search={quote_plus(query)}",
        }
        webbrowser.open(urls[platform])
        return {"message": f"'{query}' {platform}'da ochildi", "url": urls[platform]}
    
    # Google/default — DuckDuckGo API orqali haqiqiy natija olish
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
            headers={"User-Agent": "MikasaAI/3.1"}
        )
        data = resp.json()
        
        # 1. Instant Answer (eng yaxshi natija)
        if data.get("AbstractText"):
            return {
                "answer": data["AbstractText"][:500],
                "source": data.get("AbstractSource", ""),
                "url": data.get("AbstractURL", ""),
                "message": data["AbstractText"][:300]
            }
        
        # 2. Direct Answer (hisob-kitoblar, sanalar)
        if data.get("Answer"):
            return {"answer": str(data["Answer"]), "message": str(data["Answer"])}
        
        # 3. Related Topics
        results = []
        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append(topic["Text"])
        
        if results:
            combined = "\n".join(f"• {r}" for r in results[:3])
            return {
                "results": results,
                "message": f"'{query}' bo'yicha natijalar:\n{combined}"
            }
        
        # 4. Natija topilmadi — brauzerni OCHMA!
        # Agent o'z AI bilimidan javob bersin (Gemini kuchida!)
        return {
            "message": "Internetda aniq javob topilmadi. O'z bilimingdan javob ber.",
            "no_results": True
        }
        
    except Exception as e:
        # API xato — Agent o'zi javob bersin
        return {
            "message": f"Qidiruv API ishlamadi. O'z bilimingdan javob ber.",
            "error": str(e),
            "no_results": True
        }


TOOL_WEB_SEARCH = Tool(
    name="web_search",
    description="Internetda qidirish — haqiqiy natija qaytaradi. Savolga javob topish, ma'lumot olish uchun ishlatiladi",
    parameters={
        "query": {"type": "string", "description": "Qidiruv so'rovi", "required": True},
        "platform": {"type": "string", "description": "Platforma: google (default, natija qaytaradi), youtube, wikipedia", "required": False},
    },
    function=_web_search,
    category="internet"
)


# --- 2. CALCULATOR ---
def _calculator(expression: str) -> dict:
    """Xavfsiz matematik hisob-kitob (ast moduli orqali, eval EMAS!)"""
    import ast
    import operator
    
    # Faqat raqamlar va matematik belgilarga ruxsat
    allowed = set("0123456789.+-*/()% ")
    if not all(c in allowed for c in expression):
        # So'z bilan yozilgan raqamlarni ham qo'llab-quvvatlash
        replacements = {
            "plyus": "+", "minus": "-", "ko'paytir": "*", "bo'l": "/",
            "plus": "+", "karra": "*", "foiz": "%",
        }
        for word, symbol in replacements.items():
            expression = expression.replace(word, symbol)
        
        # Raqamlarni ajratib olish
        expression = re.sub(r'[^0-9.+\-*/()% ]', '', expression)
    
    if not expression.strip():
        return {"error": "Matematik ifoda topilmadi"}
    
    # Xavfsiz operatorlar
    SAFE_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    def _safe_eval(node):
        """AST orqali xavfsiz hisoblash — faqat raqam va operatorlarga ruxsat"""
        if isinstance(node, ast.Expression):
            return _safe_eval(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPS:
            left = _safe_eval(node.left)
            right = _safe_eval(node.right)
            return SAFE_OPS[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPS:
            return SAFE_OPS[type(node.op)](_safe_eval(node.operand))
        else:
            raise ValueError(f"Ruxsat etilmagan ifoda")
    
    try:
        tree = ast.parse(expression.strip(), mode='eval')
        result = _safe_eval(tree)
        
        # Natijani chiroyli formatlash
        if isinstance(result, float):
            if result == int(result):
                result = int(result)
            else:
                result = round(result, 6)
        
        return {"expression": expression.strip(), "result": result, "message": f"{expression.strip()} = {result}"}
    except ZeroDivisionError:
        return {"error": "Nolga bo'lib bo'lmaydi"}
    except Exception as e:
        return {"error": f"Hisoblash xatolik: {e}"}


TOOL_CALCULATOR = Tool(
    name="calculator",
    description="Matematik hisob-kitob qilish (qo'shish, ayirish, ko'paytirish, bo'lish, foiz)",
    parameters={
        "expression": {"type": "string", "description": "Matematik ifoda, masalan: '2 + 2', '100 * 15 / 100'", "required": True},
    },
    function=_calculator,
    category="utility"
)


# --- 3. SYSTEM CONTROL ---
def _system_control(action: str, value: str = "") -> dict:
    """Tizim boshqaruvi — ilova ochish (aqlli: ishlayaptimi tekshiradi), ekran qulflash"""
    import subprocess
    import ctypes
    
    actions = {
        "lock": lambda: subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], shell=False),
        "open_youtube": lambda: webbrowser.open("https://www.youtube.com"),
        "open_telegram": lambda: webbrowser.open("telegram:"),
        "open_chrome": lambda: webbrowser.open("https://google.com"),
        "open_discord": lambda: webbrowser.open("discord:"),
        "open_vscode": lambda: subprocess.Popen(["code"], shell=True),
        "open_explorer": lambda: subprocess.Popen(["explorer"], shell=False),
        "open_cmd": lambda: subprocess.Popen(["cmd"], creationflags=subprocess.CREATE_NEW_CONSOLE),
    }
    
    # Ilova → oyna nomi mapping (fokusga olish uchun)
    APP_WINDOW_NAMES = {
        "open_telegram": ["telegram"],
        "open_chrome": ["chrome", "google chrome"],
        "open_discord": ["discord"],
        "open_vscode": ["visual studio code", "vs code"],
    }
    
    if action in actions:
        # Ilova ochish — avval ishlayaptimi tekshir
        if action in APP_WINDOW_NAMES:
            try:
                import psutil
                window_names = APP_WINDOW_NAMES[action]
                is_running = False
                for proc in psutil.process_iter(['name']):
                    proc_name = (proc.info['name'] or '').lower()
                    if any(wn in proc_name for wn in window_names):
                        is_running = True
                        break
                        
                if is_running:
                    # Ishlayapti — oynani fokusga olish
                    try:
                        import ctypes
                        from ctypes import wintypes
                        
                        user32 = ctypes.windll.user32
                        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
                        
                        # Xavfsiz xotira tiplari bilan ishlash (Crashes oldini oladi)
                        user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
                        user32.IsWindowVisible.argtypes = [wintypes.HWND]
                        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
                        user32.GetWindowTextW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
                        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
                        
                        hwnd_list = []
                        def enum_cb(hwnd, _):
                            if user32.IsWindowVisible(hwnd):
                                length = user32.GetWindowTextLengthW(hwnd)
                                if length > 0:
                                    buf = ctypes.create_unicode_buffer(length + 1)
                                    user32.GetWindowTextW(hwnd, buf, length + 1)
                                    title = buf.value.lower()
                                    if any(wn in title for wn in window_names):
                                        hwnd_list.append(hwnd)
                            return True
                            
                        # Python GC'dan himoyalash
                        safe_cb = WNDENUMPROC(enum_cb)
                        user32.EnumWindows(safe_cb, 0)
                        
                        if hwnd_list:
                            user32.SetForegroundWindow(hwnd_list[0]) # Birinchi oynani fokusga olish
                            return {"message": f"{action}: allaqachon ochiq, fokusga olindi", "was_running": True}
                    except Exception:
                        pass
            except ImportError:
                pass
        
        actions[action]()
        return {"message": f"{action} bajarildi", "action": action, "was_running": False}
    
    elif action == "open_app" and value:
        # Xavfsiz ilova ochish — PowerShell Start-Process orqali
        # Umumiy ilova nomlari mapping
        APP_ALIASES = {
            "steam": "steam",
            "notepad": "notepad",
            "paint": "mspaint",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "calculator": "calc",
            "kalkulyator": "calc",
            "bloknotni": "notepad",
            "bloknot": "notepad",
            "spotify": "spotify",
            "obs": "obs64",
        }
        app_cmd = APP_ALIASES.get(value.lower().strip(), value)
        
        try:
            # PowerShell Start-Process — xavfsiz, shell injection yo'q
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", f"Start-Process '{app_cmd}'"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return {"message": f"'{value}' ochildi", "app": app_cmd}
        except Exception as e:
            return {"error": f"'{value}' ochilmadi: {e}"}
    else:
        return {"error": f"Noma'lum harakat: {action}", "available": list(actions.keys()) + ["open_app"]}


TOOL_SYSTEM = Tool(
    name="system_control",
    description="Kompyuter tizimini boshqarish — ilova ochish, ekranni qulflash",
    parameters={
        "action": {"type": "string", "description": "Harakat: lock, open_youtube, open_telegram, open_chrome, open_discord, open_vscode, open_explorer, open_cmd", "required": True},
        "value": {"type": "string", "description": "Qo'shimcha qiymat (ixtiyoriy)", "required": False},
    },
    function=_system_control,
    category="system"
)


# --- 4. MUSIC PLAYER ---
def _music_player(action: str, query: str = "", platform: str = "youtube") -> dict:
    """Musiqa qidirish va boshqarish"""
    import ctypes
    
    if action == "search":
        if not query:
            return {"error": "Qo'shiq nomi kerak"}
        
        urls = {
            "youtube": f"https://www.youtube.com/results?search_query={quote_plus(query)}+music",
            "yandex": f"https://music.yandex.ru/search?text={quote_plus(query)}",
            "spotify": f"https://open.spotify.com/search/{quote_plus(query)}",
        }
        url = urls.get(platform, urls["youtube"])
        webbrowser.open(url)
        return {"message": f"'{query}' {platform}'da qidirilmoqda", "url": url}
    
    elif action == "play":
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)  # MEDIA_PLAY_PAUSE
        ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
        return {"message": "Musiqa ijro etilmoqda"}
    
    elif action == "pause":
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
        return {"message": "Musiqa to'xtatildi"}
    
    elif action == "next":
        ctypes.windll.user32.keybd_event(0xB0, 0, 0, 0)  # MEDIA_NEXT
        ctypes.windll.user32.keybd_event(0xB0, 0, 2, 0)
        return {"message": "Keyingi trek"}
    
    elif action == "previous":
        ctypes.windll.user32.keybd_event(0xB1, 0, 0, 0)  # MEDIA_PREV
        ctypes.windll.user32.keybd_event(0xB1, 0, 2, 0)
        return {"message": "Oldingi trek"}
    
    else:
        return {"error": f"Noma'lum: {action}", "available": ["search", "play", "pause", "next", "previous"]}


TOOL_MUSIC = Tool(
    name="music_player",
    description="Musiqa qidirish (YouTube, Yandex, Spotify) va boshqarish (play, pause, next, previous)",
    parameters={
        "action": {"type": "string", "description": "Harakat: search, play, pause, next, previous", "required": True},
        "query": {"type": "string", "description": "Qo'shiq nomi (faqat search uchun kerak)", "required": False},
        "platform": {"type": "string", "description": "Platforma: youtube, yandex, spotify. Default: youtube", "required": False},
    },
    function=_music_player,
    category="media"
)


# --- 5. WEATHER ---
def _weather(city: str = "Tashkent") -> dict:
    """Ob-havo ma'lumotini olish"""
    import requests
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return {"error": "Ob-havo API kaliti topilmadi"}
    
    # O'zbek shahar nomlari
    SHAHAR = {
        "toshkent": "Tashkent", "samarqand": "Samarkand", "buxoro": "Bukhara",
        "andijon": "Andijan", "namangan": "Namangan", "fargona": "Fergana",
        "navoiy": "Navoi", "nukus": "Nukus", "qarshi": "Karshi",
        "jizzax": "Jizzakh", "termiz": "Termez", "urganch": "Urgench",
    }
    city_en = SHAHAR.get(city.lower().strip(), city)
    
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city_en, "appid": api_key, "units": "metric", "lang": "en"},
            timeout=10
        )
        if resp.status_code != 200:
            return {"error": f"Ob-havo olinmadi: {resp.status_code}"}
        
        data = resp.json()
        return {
            "city": city,
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "wind": round(data["wind"]["speed"], 1),
            "description": data["weather"][0]["description"],
            "message": f"{city}: {round(data['main']['temp'])}°C, {data['weather'][0]['description']}"
        }
    except Exception as e:
        return {"error": f"Ob-havo xatolik: {e}"}


TOOL_WEATHER = Tool(
    name="weather",
    description="Ob-havo ma'lumotini olish — harorat, namlik, shamol. O'zbekiston va dunyo shaharlari",
    parameters={
        "city": {"type": "string", "description": "Shahar nomi, masalan: Toshkent, Farg'ona, Samarqand. Default: Tashkent", "required": False},
    },
    function=_weather,
    category="info"
)


# --- 6. REMINDER ---
def _reminder(action: str, text: str = "", number: int = 0) -> dict:
    """Eslatmalar boshqaruvi"""
    fayl = os.path.join(BASE_DIR, "eslatmalar.txt")
    
    if action == "add":
        if not text:
            return {"error": "Eslatma matni kerak"}
        sana = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(fayl, "a", encoding="utf-8") as f:
            f.write(f"[{sana}] {text}\n")
        return {"message": f"Eslatma saqlandi: {text}"}
    
    elif action == "list":
        if not os.path.exists(fayl):
            return {"message": "Eslatmalar yo'q", "reminders": []}
        with open(fayl, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        return {"message": f"{len(lines)} ta eslatma", "reminders": lines[-10:]}
    
    elif action == "delete":
        if not os.path.exists(fayl):
            return {"error": "Eslatmalar yo'q"}
        with open(fayl, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return {"error": "Eslatmalar yo'q"}
        
        idx = (number - 1) if number > 0 else -1
        removed = lines.pop(idx).strip()
        with open(fayl, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return {"message": f"O'chirildi: {removed}"}
    
    else:
        return {"error": f"Noma'lum: {action}", "available": ["add", "list", "delete"]}


TOOL_REMINDER = Tool(
    name="reminder",
    description="Eslatmalar: yangi qo'shish, ro'yxatini ko'rish, o'chirish",
    parameters={
        "action": {"type": "string", "description": "Harakat: add, list, delete", "required": True},
        "text": {"type": "string", "description": "Eslatma matni (add uchun)", "required": False},
        "number": {"type": "integer", "description": "O'chiriladigan eslatma raqami (delete uchun)", "required": False},
    },
    function=_reminder,
    category="productivity"
)


# --- 7. FILE MANAGER ---
def _file_manager(action: str, path: str = "", query: str = "") -> dict:
    """Fayl boshqaruvi"""
    import subprocess
    
    if action == "open":
        if not path:
            return {"error": "Fayl yo'li kerak"}
        if os.path.exists(path):
            os.startfile(path)
            return {"message": f"Ochildi: {path}"}
        else:
            return {"error": f"Topilmadi: {path}"}
    
    elif action == "open_folder":
        target = path or os.path.expanduser("~\\Desktop")
        subprocess.Popen(["explorer", target], shell=False)
        return {"message": f"Papka ochildi: {target}"}
    
    elif action == "list":
        target = path or BASE_DIR
        if not os.path.isdir(target):
            return {"error": f"Papka emas: {target}"}
        items = os.listdir(target)[:30]
        return {"message": f"{len(items)} ta element", "items": items}
    
    elif action == "search":
        if not query:
            return {"error": "Qidiruv so'rovi kerak"}
        target = path or os.path.expanduser("~\\Desktop")
        results = []
        for root, dirs, files in os.walk(target):
            for f in files:
                if query.lower() in f.lower():
                    results.append(os.path.join(root, f))
                    if len(results) >= 10:
                        break
            if len(results) >= 10:
                break
        return {"message": f"{len(results)} ta topildi", "results": results}
    
    else:
        return {"error": f"Noma'lum: {action}", "available": ["open", "open_folder", "list", "search"]}


TOOL_FILE = Tool(
    name="file_manager",
    description="Fayl boshqaruvi: ochish, papka ochish, ro'yxat ko'rish, fayl qidirish",
    parameters={
        "action": {"type": "string", "description": "Harakat: open, open_folder, list, search", "required": True},
        "path": {"type": "string", "description": "Fayl/papka yo'li (ixtiyoriy)", "required": False},
        "query": {"type": "string", "description": "Qidiruv so'rovi (search uchun)", "required": False},
    },
    function=_file_manager,
    category="utility"
)


# --- 8. KNOWLEDGE (User Memory) ---
def _knowledge(action: str, key: str = "", value: str = "") -> dict:
    """Foydalanuvchi haqida bilimlarni saqlash va o'qish"""
    fayl = os.path.join(BASE_DIR, "agent_knowledge.json")
    
    # Mavjud bilimlarni yuklash
    data = {}
    if os.path.exists(fayl):
        try:
            with open(fayl, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    
    if action == "save":
        if not key or not value:
            return {"error": "Key va value kerak"}
        data[key] = {
            "value": value,
            "saved_at": datetime.datetime.now().isoformat()
        }
        with open(fayl, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"message": f"Saqlandi: {key} = {value}"}
    
    elif action == "get":
        if key and key in data:
            return {"key": key, "value": data[key]["value"], "saved_at": data[key]["saved_at"]}
        elif not key:
            # Barcha bilimlar
            summary = {k: v["value"] for k, v in data.items()}
            return {"message": f"{len(summary)} ta bilim", "knowledge": summary}
        else:
            return {"error": f"'{key}' topilmadi"}
    
    elif action == "delete":
        if key in data:
            del data[key]
            with open(fayl, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return {"message": f"O'chirildi: {key}"}
        return {"error": f"'{key}' topilmadi"}
    
    else:
        return {"error": f"Noma'lum: {action}", "available": ["save", "get", "delete"]}


TOOL_KNOWLEDGE = Tool(
    name="knowledge",
    description="Foydalanuvchi haqida ma'lumotlarni eslab qolish va esga olish. Masalan: yoqtirgan til, ism, qiziqishlari",
    parameters={
        "action": {"type": "string", "description": "Harakat: save (saqlash), get (o'qish), delete (o'chirish)", "required": True},
        "key": {"type": "string", "description": "Bilim kaliti, masalan: 'favorite_language', 'hobby'", "required": False},
        "value": {"type": "string", "description": "Bilim qiymati (save uchun)", "required": False},
    },
    function=_knowledge,
    category="memory"
)


# --- 9. DATETIME ---
def _datetime_tool(action: str = "now") -> dict:
    """Sana va vaqt ma'lumoti"""
    now = datetime.datetime.now()
    
    if action == "time":
        return {"message": f"Hozir soat {now.strftime('%H:%M')}", "time": now.strftime('%H:%M:%S')}
    elif action == "date":
        return {"message": f"Bugun {now.strftime('%Y-yil %d-%B')}", "date": now.strftime('%Y-%m-%d')}
    elif action == "now":
        return {
            "message": f"{now.strftime('%Y-yil %d-%B, %H:%M')}",
            "date": now.strftime('%Y-%m-%d'),
            "time": now.strftime('%H:%M:%S'),
            "weekday": now.strftime('%A')
        }
    else:
        return {"error": f"Noma'lum: {action}", "available": ["time", "date", "now"]}


TOOL_DATETIME = Tool(
    name="datetime",
    description="Hozirgi sana va vaqtni olish",
    parameters={
        "action": {"type": "string", "description": "Harakat: time (vaqt), date (sana), now (ikkalasi). Default: now", "required": False},
    },
    function=_datetime_tool,
    category="info"
)


# --- 10. SCHEDULER (Vaqtli vazifalar) ---
def _scheduler_tool(action: str, text: str = "", time_expr: str = "") -> dict:
    """Vaqtli vazifalar — eslatma, buyruq"""
    from core.agent_scheduler import get_scheduler, parse_time_expression
    
    scheduler = get_scheduler()
    
    if action == "add":
        if not text:
            return {"error": "Vazifa matni kerak"}
        
        # Vaqtni parse qilish
        time_info = parse_time_expression(time_expr) if time_expr else None
        
        if time_info and "delay_seconds" in time_info:
            task_id = scheduler.add("reminder", {"text": text}, delay_seconds=time_info["delay_seconds"])
            daqiqa = time_info["delay_seconds"] // 60
            return {"message": f"Eslatma {daqiqa} daqiqadan keyin: '{text}'", "task_id": task_id}
        elif time_info and "run_at" in time_info:
            task_id = scheduler.add("reminder", {"text": text}, run_at=time_info["run_at"])
            vaqt = time_info["run_at"].strftime("%H:%M")
            return {"message": f"Eslatma soat {vaqt} da: '{text}'", "task_id": task_id}
        elif time_info and "repeat_seconds" in time_info:
            task_id = scheduler.add("reminder", {"text": text}, 
                                    delay_seconds=time_info["repeat_seconds"],
                                    repeat_seconds=time_info["repeat_seconds"])
            return {"message": f"Takroriy eslatma: '{text}'", "task_id": task_id}
        else:
            # Default: 5 daqiqadan keyin
            task_id = scheduler.add("reminder", {"text": text}, delay_seconds=300)
            return {"message": f"Eslatma 5 daqiqadan keyin: '{text}'", "task_id": task_id}
    
    elif action == "list":
        tasks = scheduler.list_tasks()
        return {"message": f"{len(tasks)} ta vazifa", "tasks": tasks}
    
    elif action == "delete":
        if text:
            ok = scheduler.remove(text)
            return {"message": f"O'chirildi" if ok else "Topilmadi"}
        return {"error": "Vazifa ID kerak"}
    
    else:
        return {"error": f"Noma'lum: {action}", "available": ["add", "list", "delete"]}


TOOL_SCHEDULER = Tool(
    name="scheduler",
    description="Vaqtli vazifalar: eslatma qo'yish (X daqiqadan keyin, soat X da), ro'yxat ko'rish, o'chirish",
    parameters={
        "action": {"type": "string", "description": "Harakat: add, list, delete", "required": True},
        "text": {"type": "string", "description": "Eslatma matni (add uchun) yoki vazifa ID (delete uchun)", "required": False},
        "time_expr": {"type": "string", "description": "Vaqt ifodasi: '5 daqiqadan keyin', 'soat 14:00', 'har 30 daqiqada'", "required": False},
    },
    function=_scheduler_tool,
    category="productivity"
)


# --- 11. RAG READER (Fayl o'qish) ---
def _rag_reader(action: str, path: str = "", query: str = "") -> dict:
    """Lokal fayllarni o'qish — .txt, .py, .json, .md, .csv"""
    RUXSAT_KENGAYTMALAR = {".txt", ".py", ".json", ".md", ".csv", ".log", ".ini", ".cfg", ".toml", ".yaml", ".yml", ".html", ".css", ".js"}
    MAX_SIZE = 3000  # Maksimal belgilar soni
    
    if action == "read":
        if not path:
            return {"error": "Fayl yo'li kerak"}
        if not os.path.exists(path):
            return {"error": f"Fayl topilmadi: {path}"}
        
        _, ext = os.path.splitext(path)
        if ext.lower() not in RUXSAT_KENGAYTMALAR:
            return {"error": f"Bu fayl turi qo'llab-quvvatlanmaydi: {ext}. Faqat: {', '.join(RUXSAT_KENGAYTMALAR)}"}
        
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(MAX_SIZE)
            
            total_lines = content.count('\n') + 1
            truncated = len(content) >= MAX_SIZE
            
            return {
                "path": path,
                "lines": total_lines,
                "truncated": truncated,
                "content": content,
                "message": f"{os.path.basename(path)}: {total_lines} qator" + (" (qisqartirildi)" if truncated else "")
            }
        except Exception as e:
            return {"error": f"O'qish xatolik: {e}"}
    
    elif action == "search":
        if not query:
            return {"error": "Qidiruv so'rovi kerak"}
        target = path or BASE_DIR
        
        results = []
        try:
            for root, dirs, files in os.walk(target):
                # .git, __pycache__ dan o'tish
                dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'node_modules'}]
                for fname in files:
                    _, ext = os.path.splitext(fname)
                    if ext.lower() not in RUXSAT_KENGAYTMALAR:
                        continue
                    
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            for i, line in enumerate(f, 1):
                                if query.lower() in line.lower():
                                    results.append({
                                        "file": fpath,
                                        "line": i,
                                        "text": line.strip()[:100]
                                    })
                                    if len(results) >= 15:
                                        break
                    except Exception:
                        pass
                    if len(results) >= 15:
                        break
                if len(results) >= 15:
                    break
        except Exception as e:
            return {"error": f"Qidirish xatolik: {e}"}
        
        return {"message": f"'{query}': {len(results)} ta natija", "results": results}
    
    elif action == "info":
        target = path or BASE_DIR
        if not os.path.exists(target):
            return {"error": f"Topilmadi: {target}"}
        
        if os.path.isfile(target):
            size = os.path.getsize(target)
            return {
                "path": target,
                "type": "file",
                "size": size,
                "size_human": f"{size / 1024:.1f} KB",
                "message": f"{os.path.basename(target)}: {size / 1024:.1f} KB"
            }
        elif os.path.isdir(target):
            files = [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
            dirs = [d for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))]
            return {
                "path": target,
                "type": "directory",
                "files": len(files),
                "dirs": len(dirs),
                "items": files[:20] + [d + "/" for d in dirs[:10]],
                "message": f"{len(files)} fayl, {len(dirs)} papka"
            }
    
    else:
        return {"error": f"Noma'lum: {action}", "available": ["read", "search", "info"]}


TOOL_RAG = Tool(
    name="rag_reader",
    description="Lokal fayllarni o'qish va ichidan qidirish. .py, .txt, .json, .md fayllarni o'qiy oladi",
    parameters={
        "action": {"type": "string", "description": "Harakat: read (o'qish), search (ichidan qidirish), info (ma'lumot)", "required": True},
        "path": {"type": "string", "description": "Fayl yoki papka yo'li", "required": False},
        "query": {"type": "string", "description": "Qidiruv so'rovi (search uchun)", "required": False},
    },
    function=_rag_reader,
    category="utility"
)


# --- 12. CURRENCY (Valyuta kurslari) ---
def _currency(from_currency: str = "USD", to_currency: str = "UZS") -> dict:
    """Valyuta kurslarini olish (CBU API)"""
    import requests
    
    try:
        resp = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/", timeout=10)
        if resp.status_code != 200:
            return {"error": f"CBU API xatolik: {resp.status_code}"}
        
        data = resp.json()
        
        # Valyuta kodlari
        kursi = {}
        for item in data:
            code = item.get("Ccy", "")
            rate = float(item.get("Rate", 0))
            name = item.get("CcyNm_UZ", "")
            kursi[code] = {"rate": rate, "name": name}
        
        if from_currency.upper() == "UZS":
            return {"message": "UZS bazaviy valyuta (1 UZS = 1 UZS)", "rate": 1}
        
        target = from_currency.upper()
        if target in kursi:
            rate = kursi[target]["rate"]
            name = kursi[target]["name"]
            return {
                "from": target,
                "to": "UZS",
                "rate": rate,
                "name": name,
                "message": f"1 {target} = {rate:,.2f} UZS ({name})"
            }
        
        # Eng ko'p so'raladigan valyutalar
        popular = ["USD", "EUR", "RUB", "GBP", "JPY", "KRW", "CNY", "TRY"]
        available = [c for c in popular if c in kursi]
        return {"error": f"'{target}' topilmadi", "available": available}
    
    except Exception as e:
        return {"error": f"Valyuta kursi xatolik: {e}"}


TOOL_CURRENCY = Tool(
    name="currency",
    description="Valyuta kurslarini olish — Dollar, Yevro, Rubl, va boshqalar (CBU.uz)",
    parameters={
        "from_currency": {"type": "string", "description": "Valyuta kodi: USD, EUR, RUB, GBP. Default: USD", "required": False},
        "to_currency": {"type": "string", "description": "Maqsad valyuta. Default: UZS", "required": False},
    },
    function=_currency,
    category="info"
)


# --- 13. TRANSLATOR (Tarjima) ---
def _translator(text: str, to_lang: str = "uz", from_lang: str = "auto") -> dict:
    """Matnni tarjima qilish (Google Translate orqali)"""
    import requests
    
    lang_map = {
        "uz": "uz", "uzbek": "uz", "o'zbek": "uz",
        "en": "en", "ingliz": "en", "english": "en",
        "ru": "ru", "rus": "ru", "russian": "ru",
    }
    
    target = lang_map.get(to_lang.lower(), to_lang)
    source = lang_map.get(from_lang.lower(), from_lang) if from_lang != "auto" else "auto"
    
    try:
        # Google Translate API (bepul, cheklangan)
        resp = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text
            },
            timeout=10
        )
        
        if resp.status_code != 200:
            return {"error": f"Tarjima xatolik: {resp.status_code}"}
        
        data = resp.json()
        translated = "".join(part[0] for part in data[0] if part[0])
        detected = data[2] if len(data) > 2 else source
        
        return {
            "original": text,
            "translated": translated,
            "from_lang": detected,
            "to_lang": target,
            "message": f"[{detected}→{target}] {translated}"
        }
    except Exception as e:
        return {"error": f"Tarjima xatolik: {e}"}


TOOL_TRANSLATOR = Tool(
    name="translator",
    description="Matnni tarjima qilish — o'zbek, ingliz, rus tillari orasida",
    parameters={
        "text": {"type": "string", "description": "Tarjima qilinadigan matn", "required": True},
        "to_lang": {"type": "string", "description": "Maqsad til: uz, en, ru. Default: uz", "required": False},
        "from_lang": {"type": "string", "description": "Manba til: auto, uz, en, ru. Default: auto", "required": False},
    },
    function=_translator,
    category="utility"
)


# --- 14. SCREEN ANALYZE (Ekran tahlil) ---
def _screen_analyze(question: str = "Ekranda nima bor?") -> dict:
    """Ekranni screenshot olib, AI bilan tahlil qilish"""
    try:
        from ai_engine import ekran_tahlil
        result = ekran_tahlil(question)
        if result:
            return {"message": result, "question": question}
        else:
            return {"error": "Ekran tahlil qilinmadi"}
    except ImportError:
        return {"error": "ai_engine moduli topilmadi"}
    except Exception as e:
        return {"error": f"Ekran tahlil xatolik: {e}"}


TOOL_SCREEN = Tool(
    name="screen_analyze",
    description="Ekranni screenshot olib, AI bilan tahlil qilish. Ekranda nima borligini ko'rish",
    parameters={
        "question": {"type": "string", "description": "Ekran haqida savol, masalan: 'Ekranda qaysi ilova ochiq?'. Default: 'Ekranda nima bor?'", "required": False},
    },
    function=_screen_analyze,
    category="system"
)


# --- 15. FILE WRITE (Fayl yozish) ---
def _file_write(path: str, content: str, mode: str = "write") -> dict:
    """Fayl yaratish yoki yozish — kod, HTML, CSS, JSON, matn fayllar"""
    import shutil
    
    MAX_FILE_SIZE = 50000  # 50KB limit
    
    # Xavfsizlik — faqat matn fayllariga ruxsat
    RUXSAT_KENGAYTMALAR = {
        ".txt", ".py", ".js", ".ts", ".html", ".css", ".json", ".md",
        ".csv", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        ".sh", ".bat", ".ps1", ".sql", ".env", ".gitignore",
        ".jsx", ".tsx", ".vue", ".svelte", ".php", ".rb", ".go",
        ".java", ".c", ".cpp", ".h", ".hpp", ".rs", ".swift",
    }
    
    if not path:
        return {"error": "Fayl yo'li kerak"}
    
    if len(content) > MAX_FILE_SIZE:
        return {"error": f"Fayl juda katta ({len(content)} belgi). Maksimal: {MAX_FILE_SIZE}"}
    
    # Kengaytmani tekshirish
    _, ext = os.path.splitext(path)
    if ext.lower() not in RUXSAT_KENGAYTMALAR:
        return {"error": f"'{ext}' fayl turi qo'llab-quvvatlanmaydi. Ruxsat: {', '.join(sorted(RUXSAT_KENGAYTMALAR)[:10])}..."}
    
    # To'liq yo'l yaratish (nisbiy yo'l bo'lsa, Desktop ga yozadi)
    if not os.path.isabs(path):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, path)
    
    try:
        # Papkani yaratish (agar yo'q bo'lsa)
        papka = os.path.dirname(path)
        if papka:
            os.makedirs(papka, exist_ok=True)
        
        if mode == "append":
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": path, "message": f"Qo'shildi: {os.path.basename(path)}", "size": len(content)}
        else:
            # Mavjud faylni backup qilish
            if os.path.exists(path):
                backup = path + ".bak"
                shutil.copy2(path, backup)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": path, "message": f"Yaratildi: {os.path.basename(path)}", "size": len(content)}
    except PermissionError:
        return {"error": f"Ruxsat yo'q: {path}"}
    except Exception as e:
        return {"error": f"Yozish xatolik: {e}"}


TOOL_FILE_WRITE = Tool(
    name="file_write",
    description="Fayl yaratish yoki yozish. Kod, HTML, CSS, Python, JavaScript va boshqa matn fayllarni yaratadi. Nisbiy yo'l berilsa Desktop ga yozadi.",
    parameters={
        "path": {"type": "string", "description": "Fayl yo'li. Masalan: 'login.html', 'styles.css', yoki to'liq yo'l", "required": True},
        "content": {"type": "string", "description": "Faylga yoziladigan mazmun (kod, matn)", "required": True},
        "mode": {"type": "string", "description": "Rejim: 'write' (yangi yozish) yoki 'append' (qo'shish). Default: write", "required": False},
    },
    function=_file_write,
    category="coding"
)


def _app_check(category: str = "code_editor", app_name: str = "") -> dict:
    """Kompyuterda o'rnatilgan ilovalarni tekshirish + ishlayaptimi (process check)"""
    import subprocess
    import glob
    import psutil
    
    # Mashhur ilovalar bazasi
    APP_DATABASE = {
        "code_editor": {
            "cursor":     {"cmd": "cursor", "paths": [r"C:\Users\*\AppData\Local\Programs\cursor\Cursor.exe"], "priority": 1},
            "vscode":     {"cmd": "code", "paths": [r"C:\Program Files\Microsoft VS Code\Code.exe", r"C:\Users\*\AppData\Local\Programs\Microsoft VS Code\Code.exe"], "priority": 2},
            "sublime":    {"cmd": "subl", "paths": [r"C:\Program Files\Sublime Text\sublime_text.exe", r"C:\Program Files\Sublime Text 3\sublime_text.exe"], "priority": 3},
            "notepad++":  {"cmd": "notepad++", "paths": [r"C:\Program Files\Notepad++\notepad++.exe", r"C:\Program Files (x86)\Notepad++\notepad++.exe"], "priority": 4},
            "pycharm":    {"cmd": None, "paths": [r"C:\Program Files\JetBrains\PyCharm*\bin\pycharm64.exe"], "priority": 5},
            "webstorm":   {"cmd": None, "paths": [r"C:\Program Files\JetBrains\WebStorm*\bin\webstorm64.exe"], "priority": 6},
            "vim":        {"cmd": "vim", "paths": [], "priority": 7},
            "notepad":    {"cmd": "notepad", "paths": [r"C:\Windows\notepad.exe"], "priority": 99},
        },
        "browser": {
            "chrome":     {"cmd": "chrome", "paths": [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"], "priority": 1},
            "brave":      {"cmd": "brave", "paths": [r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"], "priority": 2},
            "firefox":    {"cmd": "firefox", "paths": [r"C:\Program Files\Mozilla Firefox\firefox.exe"], "priority": 3},
            "edge":       {"cmd": "msedge", "paths": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"], "priority": 4},
        },
        "terminal": {
            "windows_terminal": {"cmd": "wt", "paths": [r"C:\Users\*\AppData\Local\Microsoft\WindowsApps\wt.exe"], "priority": 1},
            "powershell": {"cmd": "powershell", "paths": [r"C:\Windows\System32\WindowsPowerShell\*\powershell.exe"], "priority": 2},
            "cmd":        {"cmd": "cmd", "paths": [r"C:\Windows\System32\cmd.exe"], "priority": 3},
            "git_bash":   {"cmd": "bash", "paths": [r"C:\Program Files\Git\bin\bash.exe"], "priority": 4},
        },
        "dev_tools": {
            "node":       {"cmd": "node", "paths": [], "priority": 1},
            "python":     {"cmd": "python", "paths": [], "priority": 2},
            "git":        {"cmd": "git", "paths": [r"C:\Program Files\Git\bin\git.exe"], "priority": 3},
            "npm":        {"cmd": "npm", "paths": [], "priority": 4},
            "pip":        {"cmd": "pip", "paths": [], "priority": 5},
        }
    }
    
    # Process nomlari — ishlayaptimi tekshirish uchun
    PROCESS_NAMES = {
        "vscode": ["code.exe"], "cursor": ["cursor.exe"], "sublime": ["sublime_text.exe"],
        "notepad++": ["notepad++.exe"], "pycharm": ["pycharm64.exe"],
        "chrome": ["chrome.exe"], "brave": ["brave.exe"], "firefox": ["firefox.exe"],
        "edge": ["msedge.exe"], "telegram": ["telegram.exe"], "discord": ["discord.exe"],
        "node": ["node.exe"], "python": ["python.exe"],
    }
    
    def _is_running(name):
        """Process ishlayaptimi tekshirish"""
        proc_names = PROCESS_NAMES.get(name, [f"{name}.exe"])
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if (proc.info['name'] or '').lower() in [p.lower() for p in proc_names]:
                    return {"running": True, "pid": proc.info['pid']}
        except Exception:
            pass
        return {"running": False, "pid": None}
    
    def _check_app(name, info):
        """Bitta ilovani tekshirish (o'rnatilganmi + ishlayaptimi)"""
        running_info = _is_running(name)
        
        # 1. PATH da bormi? (cmd orqali)
        if info.get("cmd"):
            try:
                result = subprocess.run(
                    ["where", info["cmd"]], 
                    capture_output=True, text=True, timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                if result.returncode == 0:
                    found_path = result.stdout.strip().split('\n')[0]
                    return {"name": name, "found": True, "path": found_path, "method": "PATH", **running_info}
            except Exception:
                pass
        
        # 2. Standart o'rnatish joylarida bormi?
        for pattern in info.get("paths", []):
            matches = glob.glob(pattern)
            if matches:
                return {"name": name, "found": True, "path": matches[0], "method": "path_scan", **running_info}
        
        # 3. Process ishlayapti lekin PATH da yo'q
        if running_info["running"]:
            return {"name": name, "found": True, "path": "(process)", "method": "process", **running_info}
        
        return {"name": name, "found": False, **running_info}
    
    # Aniq ilova nomi berilgan bo'lsa
    if app_name:
        app_name_lower = app_name.lower().strip()
        for cat_name, apps in APP_DATABASE.items():
            if app_name_lower in apps:
                result = _check_app(app_name_lower, apps[app_name_lower])
                return result
        # Bazada yo'q — where bilan tekshiramiz
        try:
            result = subprocess.run(["where", app_name], capture_output=True, text=True, timeout=3,
                                     creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            if result.returncode == 0:
                return {"name": app_name, "found": True, "path": result.stdout.strip().split('\n')[0]}
        except Exception:
            pass
        return {"name": app_name, "found": False}
    
    # Kategoriya bo'yicha barcha ilovalarni tekshirish
    if category not in APP_DATABASE:
        return {"error": f"Kategoriya topilmadi: {category}", "available": list(APP_DATABASE.keys())}
    
    found = []
    not_found = []
    
    for name, info in APP_DATABASE[category].items():
        result = _check_app(name, info)
        if result["found"]:
            result["priority"] = info["priority"]
            found.append(result)
        else:
            not_found.append(name)
    
    # Priority bo'yicha tartiblash
    found.sort(key=lambda x: x.get("priority", 99))
    best = found[0]["name"] if found else None
    
    return {
        "category": category,
        "found": [f["name"] for f in found],
        "found_details": found,
        "not_found": not_found,
        "best": best,
        "message": f"{category}: {len(found)} ta topildi — {', '.join(f['name'] for f in found)}" if found else f"{category}: hech narsa topilmadi"
    }


TOOL_APP_CHECK = Tool(
    name="app_check",
    description="Kompyuterda o'rnatilgan ilovalarni tekshirish. Code editorlar, brauzerlar, terminallar, dev tools — barchasini topadi",
    parameters={
        "category": {"type": "string", "description": "Kategoriya: code_editor, browser, terminal, dev_tools. Default: code_editor", "required": False},
        "app_name": {"type": "string", "description": "Aniq ilova nomi: vscode, cursor, chrome, node, python. Berilsa faqat shu tekshiriladi", "required": False},
    },
    function=_app_check,
    category="system"
)


# --- 17. ASK USER (Foydalanuvchidan so'rash) ---
_ask_user_callback = None  # main.py dan o'rnatiladi

def set_ask_user_callback(callback):
    """main.py dan tingla() funksiyasini o'rnatish"""
    global _ask_user_callback
    _ask_user_callback = callback

def _ask_user(question: str) -> dict:
    """Foydalanuvchidan savol so'rash va javobni kutish"""
    global _ask_user_callback
    
    if not question:
        return {"error": "Savol matni kerak"}
    
    # GUI ga savolni ko'rsatish
    try:
        # main.py dagi gui_ga_xabar_yuborish va tingla() orqali
        if _ask_user_callback:
            answer = _ask_user_callback(question)
            if answer:
                return {"question": question, "answer": answer, "message": f"User javobi: {answer}"}
            else:
                return {"question": question, "answer": "", "message": "User javob bermadi", "timeout": True}
        else:
            # Fallback — input() orqali (GUI bo'lmasa)
            logger.warning("ask_user: callback o'rnatilmagan, input() ishlatilmoqda")
            return {"question": question, "answer": "", "no_callback": True, 
                    "message": f"Savolni foydalanuvchiga aytib bering: {question}"}
    except Exception as e:
        return {"error": f"Savol so'rash xatolik: {e}"}


TOOL_ASK_USER = Tool(
    name="ask_user",
    description="Foydalanuvchidan savol so'rash va javobini kutish. Masalan: 'Qaysi tilda yozayin?', 'Bootstrap ishlatayinmi?', 'O'rnatayinmi?'",
    parameters={
        "question": {"type": "string", "description": "Foydalanuvchiga beriladigan savol", "required": True},
    },
    function=_ask_user,
    category="interaction"
)


# --- 18. SCREEN CLICK (Ekranda bosish) ---
def _screen_click(action: str = "click", x: int = 0, y: int = 0, window: str = "", text: str = "") -> dict:
    """Ekranda sichqoncha bilan bosish, oyna fokusga olish"""
    import ctypes
    import pyautogui
    
    if action == "click":
        if x <= 0 or y <= 0:
            return {"error": "x va y koordinatalar kerak (0 dan katta)"}
        screen_w, screen_h = pyautogui.size()
        if x > screen_w or y > screen_h:
            return {"error": f"Koordinata ekrandan tashqarida. Ekran: {screen_w}x{screen_h}"}
        pyautogui.click(x, y)
        return {"message": f"Bosildi: ({x}, {y})", "x": x, "y": y}
    
    elif action == "double_click":
        if x <= 0 or y <= 0:
            return {"error": "x va y koordinatalar kerak"}
        pyautogui.doubleClick(x, y)
        return {"message": f"Ikki marta bosildi: ({x}, {y})", "x": x, "y": y}
    
    elif action == "right_click":
        if x <= 0 or y <= 0:
            return {"error": "x va y koordinatalar kerak"}
        pyautogui.rightClick(x, y)
        return {"message": f"O'ng tugma bosildi: ({x}, {y})", "x": x, "y": y}
    
    elif action == "focus_window":
        if not window:
            return {"error": "window nomi kerak"}
        window_lower = window.lower()
        try:
            hwnd_list = []
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            def enum_cb(hwnd, _):
                if ctypes.windll.user32.IsWindowVisible(hwnd):
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                        title = buf.value.lower()
                        if window_lower in title:
                            hwnd_list.append((hwnd, buf.value))
                return True
            ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            
            if hwnd_list:
                hwnd, title = hwnd_list[0]
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                return {"message": f"Oyna fokusga olindi: {title}", "window": title, "found": True}
            else:
                return {"message": f"'{window}' oynasi topilmadi", "found": False}
        except Exception as e:
            return {"error": f"Fokus xatolik: {e}"}
    
    elif action == "list_windows":
        # Barcha ochiq oynalarni ro'yxati
        try:
            windows = []
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            def enum_cb(hwnd, _):
                if ctypes.windll.user32.IsWindowVisible(hwnd):
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                        if buf.value.strip():
                            windows.append(buf.value)
                return True
            ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            return {"message": f"{len(windows)} ta oyna ochiq", "windows": windows[:20]}
        except Exception as e:
            return {"error": f"Oynalar ro'yxati xatolik: {e}"}
    
    elif action == "scroll":
        amount = y if y != 0 else -3  # y = scroll miqdori (manfiy = pastga)
        pyautogui.scroll(amount)
        direction = "yuqoriga" if amount > 0 else "pastga"
        return {"message": f"Scroll {direction}: {abs(amount)}", "amount": amount}
    
    else:
        return {"error": f"Noma'lum: {action}", "available": ["click", "double_click", "right_click", "focus_window", "list_windows", "scroll"]}


TOOL_SCREEN_CLICK = Tool(
    name="screen_click",
    description="Ekranda sichqoncha bilan bosish, oynani fokusga olish, ochiq oynalar ro'yxati. Koordinatalarni screen_analyze dan oling",
    parameters={
        "action": {"type": "string", "description": "Harakat: click, double_click, right_click, focus_window, list_windows, scroll", "required": True},
        "x": {"type": "integer", "description": "X koordinata (click/double_click/right_click uchun)", "required": False},
        "y": {"type": "integer", "description": "Y koordinata (click uchun) yoki scroll miqdori (scroll uchun)", "required": False},
        "window": {"type": "string", "description": "Oyna nomi (focus_window uchun). Masalan: 'Telegram', 'Chrome'", "required": False},
    },
    function=_screen_click,
    category="interaction"
)


# --- 19. KEYBOARD TYPE (Matn yozish) ---
def _keyboard_type(text: str, interval: float = 0.02) -> dict:
    """Fokuslanagan ilovaga matn yozish"""
    import pyautogui
    import time
    
    if not text:
        return {"error": "Matn kerak"}
    
    if len(text) > 5000:
        return {"error": f"Matn juda uzun ({len(text)} belgi). Maksimal: 5000"}
    
    try:
        time.sleep(0.3)  # Ilova tayyorlanishi uchun
        pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text)
        return {"message": f"Yozildi: {text[:50]}{'...' if len(text) > 50 else ''}", "length": len(text)}
    except Exception as e:
        return {"error": f"Yozish xatolik: {e}"}


TOOL_KEYBOARD_TYPE = Tool(
    name="keyboard_type",
    description="Fokuslanagan ilovaga matn yozish. Masalan: qidiruv maydoniga matn kiritish, fayl nomi yozish",
    parameters={
        "text": {"type": "string", "description": "Yoziladigan matn", "required": True},
        "interval": {"type": "number", "description": "Harflar orasidagi pauza (soniya). Default: 0.02", "required": False},
    },
    function=_keyboard_type,
    category="interaction"
)


# --- 20. KEYBOARD SHORTCUT (Tugma bosish) ---
def _keyboard_shortcut(keys: str, repeat: int = 1) -> dict:
    """Klaviatura shortcutlari — Ctrl+F, Enter, Alt+Tab va boshqalar"""
    import keyboard as kb
    import time
    
    if not keys:
        return {"error": "Tugma kerak"}
    
    # Mashhur shortcutlar lug'ati (o'zbekcha -> shortcut)
    SHORTCUT_MAP = {
        "qidirish": "ctrl+f", "qidir": "ctrl+f",
        "saqlash": "ctrl+s", "saqla": "ctrl+s",
        "nusxalash": "ctrl+c", "nusxa": "ctrl+c",
        "joylash": "ctrl+v",
        "qaytarish": "ctrl+z",
        "barchasi": "ctrl+a",
        "yangi": "ctrl+n",
        "yopish": "alt+f4",
        "oyna_almash": "alt+tab",
    }
    
    actual_keys = SHORTCUT_MAP.get(keys.lower(), keys)
    
    try:
        for i in range(repeat):
            kb.send(actual_keys)
            if repeat > 1:
                time.sleep(0.1)
        return {"message": f"'{actual_keys}' bosildi" + (f" ({repeat} marta)" if repeat > 1 else ""), "keys": actual_keys}
    except Exception as e:
        return {"error": f"Shortcut xatolik: {e}"}


TOOL_KEYBOARD_SHORTCUT = Tool(
    name="keyboard_shortcut",
    description="Klaviatura shortcutlari yuborish. Masalan: 'ctrl+f' (qidirish), 'enter', 'alt+tab' (oyna almash), 'ctrl+s' (saqlash), 'escape'",
    parameters={
        "keys": {"type": "string", "description": "Tugma yoki shortcut: 'enter', 'ctrl+f', 'alt+tab', 'escape', 'tab', 'ctrl+s'. O'zbekcha ham bo'ladi: 'qidirish', 'saqlash'", "required": True},
        "repeat": {"type": "integer", "description": "Necha marta bosish. Default: 1", "required": False},
    },
    function=_keyboard_shortcut,
    category="interaction"
)


# ========================================================
# GLOBAL REGISTRY — Barcha tool'lar
# ========================================================

def create_default_registry() -> ToolRegistry:
    """Standart tool'lar bilan registry yaratish"""
    registry = ToolRegistry()
    # Asosiy tool'lar (v2)
    registry.register(TOOL_WEB_SEARCH)
    registry.register(TOOL_CALCULATOR)
    registry.register(TOOL_SYSTEM)
    registry.register(TOOL_MUSIC)
    registry.register(TOOL_WEATHER)
    registry.register(TOOL_REMINDER)
    registry.register(TOOL_FILE)
    registry.register(TOOL_KNOWLEDGE)
    registry.register(TOOL_DATETIME)
    # Yangi tool'lar (v3)
    registry.register(TOOL_SCHEDULER)
    registry.register(TOOL_RAG)
    registry.register(TOOL_CURRENCY)
    registry.register(TOOL_TRANSLATOR)
    registry.register(TOOL_SCREEN)
    # Yangi tool'lar (v3.1 — Autonomous Agent)
    registry.register(TOOL_FILE_WRITE)
    registry.register(TOOL_APP_CHECK)
    registry.register(TOOL_ASK_USER)
    # Vision + Input tool'lar (v3.2 — Desktop Agent)
    registry.register(TOOL_SCREEN_CLICK)
    registry.register(TOOL_KEYBOARD_TYPE)
    registry.register(TOOL_KEYBOARD_SHORTCUT)
    logger.info(f"Tool Registry: {registry.count} ta tool ro'yxatdan o'tdi")
    return registry


# Global registry singleton
_registry = None

def get_registry() -> ToolRegistry:
    """Global registry olish"""
    global _registry
    if _registry is None:
        _registry = create_default_registry()
    return _registry

