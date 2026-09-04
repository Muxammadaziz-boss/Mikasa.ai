# ========== agent_plugins.py ==========
# Plugin tizimi — JSON yoki Python fayl orqali yangi tool'lar qo'shish
# Proaktiv Agent — foydalanuvchiga taklif berish

import os
import json
import logging
import datetime
import importlib.util

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Loyiha ildizi
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")


# ========================================================
# PLUGIN MANAGER — JSON va Python plugin'larni yuklash
# ========================================================

class PluginManager:
    """JSON va Python plugin'larni yuklash va tool registry ga qo'shish.
    
    JSON plugin formati (plugins/my_tool.json):
    {
        "name": "my_tool",
        "description": "Mening tool'im",
        "category": "custom",
        "type": "url",  // "url" yoki "command"
        "url": "https://example.com/{query}",
        "parameters": {
            "query": {"type": "string", "description": "Qidiruv"}
        }
    }
    
    Python plugin formati (plugins/my_tool.py):
    TOOL_NAME = "my_tool"
    TOOL_DESCRIPTION = "Mening tool'im"
    TOOL_PARAMS = {"text": {"type": "string", "description": "Matn"}}
    TOOL_CATEGORY = "custom"
    
    def run(**kwargs):
        return {"message": "Natija!"}
    """
    
    def __init__(self, plugins_dir: str = None):
        self.plugins_dir = plugins_dir or PLUGINS_DIR
        self._loaded = []
    
    def load_all(self, registry) -> int:
        """Barcha plugin'larni yuklash va registry ga qo'shish.
        Returns: yuklangan plugin'lar soni
        """
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            self._create_example_plugin()
            logger.debug(f"Plugins papkasi yaratildi: {self.plugins_dir}")
            return 0
        
        count = 0
        for fname in os.listdir(self.plugins_dir):
            fpath = os.path.join(self.plugins_dir, fname)
            
            if fname.endswith(".json"):
                if self._load_json_plugin(fpath, registry):
                    count += 1
            elif fname.endswith(".py") and not fname.startswith("_"):
                if self._load_python_plugin(fpath, registry):
                    count += 1
        
        logger.info(f"PluginManager: {count} ta plugin yuklandi")
        return count
    
    def _load_json_plugin(self, path: str, registry) -> bool:
        """JSON plugin yuklash"""
        from core.agent_tools import Tool
        import webbrowser
        from urllib.parse import quote_plus
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            name = config.get("name", "")
            if not name:
                logger.warning(f"Plugin nomsiz: {path}")
                return False
            
            desc = config.get("description", "Custom tool")
            params = config.get("parameters", {})
            plugin_type = config.get("type", "url")
            category = config.get("category", "custom")
            
            if plugin_type == "url":
                url_template = config.get("url", "")
                
                def url_runner(url_tpl=url_template, **kwargs):
                    url = url_tpl
                    for key, value in kwargs.items():
                        url = url.replace(f"{{{key}}}", quote_plus(str(value)))
                    webbrowser.open(url)
                    return {"message": f"Ochildi: {url}", "url": url}
                
                tool = Tool(name=name, description=desc, parameters=params,
                           function=url_runner, category=category)
            
            elif plugin_type == "command":
                import subprocess
                cmd_template = config.get("command", "")
                
                def cmd_runner(cmd_tpl=cmd_template, **kwargs):
                    cmd = cmd_tpl
                    for key, value in kwargs.items():
                        cmd = cmd.replace(f"{{{key}}}", str(value))
                    # Xavfsizlik: shell=False
                    result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
                    return {"message": result.stdout[:500], "returncode": result.returncode}
                
                tool = Tool(name=name, description=desc, parameters=params,
                           function=cmd_runner, category=category)
            else:
                logger.warning(f"Noma'lum plugin turi: {plugin_type}")
                return False
            
            registry.register(tool)
            self._loaded.append(name)
            logger.info(f"JSON plugin yuklandi: {name}")
            return True
            
        except Exception as e:
            logger.error(f"JSON plugin xatolik ({path}): {e}")
            return False
    
    def _load_python_plugin(self, path: str, registry) -> bool:
        """Python plugin yuklash (OGOHLANTIRISH: ixtiyoriy kod bajariladi!)"""
        from core.agent_tools import Tool
        
        try:
            # Xavfsizlik ogohlantiruvi
            fname = os.path.basename(path)
            logger.warning(f"⚠️ Python plugin yuklanmoqda: {fname} — ixtiyoriy kod bajariladi!")
            
            # Faqat plugins papkasidan yuklashga ruxsat
            real_path = os.path.realpath(path)
            real_plugins = os.path.realpath(self.plugins_dir)
            if not real_path.startswith(real_plugins):
                logger.error(f"Plugin plugins/ papkasidan tashqarida: {path}")
                return False
            
            spec = importlib.util.spec_from_file_location("plugin", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            name = getattr(module, "TOOL_NAME", "")
            if not name:
                logger.warning(f"Python plugin TOOL_NAME yo'q: {path}")
                return False
            
            desc = getattr(module, "TOOL_DESCRIPTION", "Custom Python tool")
            params = getattr(module, "TOOL_PARAMS", {})
            category = getattr(module, "TOOL_CATEGORY", "custom")
            run_func = getattr(module, "run", None)
            
            if not run_func:
                logger.warning(f"Python plugin run() yo'q: {path}")
                return False
            
            tool = Tool(name=name, description=desc, parameters=params,
                       function=run_func, category=category)
            registry.register(tool)
            self._loaded.append(name)
            logger.info(f"Python plugin yuklandi: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Python plugin xatolik ({path}): {e}")
            return False
    
    def _create_example_plugin(self):
        """Namuna plugin yaratish"""
        example = {
            "name": "github_search",
            "description": "GitHub da kod qidirish",
            "category": "development",
            "type": "url",
            "url": "https://github.com/search?q={query}&type=repositories",
            "parameters": {
                "query": {"type": "string", "description": "Qidiruv so'rovi"}
            }
        }
        path = os.path.join(self.plugins_dir, "_example_github.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(example, f, ensure_ascii=False, indent=2)
    
    @property
    def loaded_plugins(self) -> list:
        return self._loaded.copy()


# ========================================================
# PROACTIVE AGENT — O'zi taklif berish
# ========================================================

class ProactiveAgent:
    """Foydalanuvchiga proaktiv takliflar berish.
    
    - Har kuni birinchi "salom" da ob-havo va eslatmalar xabar qilish
    - Foydalanuvchi odatlariga qarab taklif berish
    - Uzoq vaqt jimlik bo'lsa taklif berish
    """
    
    def __init__(self, memory=None):
        self.memory = memory
        self._last_greeting = None
        self._suggestions_today = 0
        self._max_suggestions_per_day = 3
    
    def get_greeting_suggestions(self) -> list:
        """Salom aytganda takliflar.
        
        Returns:
            List of suggestion strings
        """
        now = datetime.datetime.now()
        suggestions = []
        
        # Bugun birinchi marta bo'lsa
        if self._last_greeting is None or self._last_greeting.date() != now.date():
            self._last_greeting = now
            self._suggestions_today = 0  # Yangi kun — counter reset
            
            # Vaqtga qarab salomlash
            hour = now.hour
            if hour < 6:
                suggestions.append("Erta turibsiz! Yaxshi uyqu oling.")
            elif hour < 12:
                suggestions.append("Xayrli tong! Bugun qanday rejalar bor?")
            elif hour < 18:
                suggestions.append("Xayrli kun! Biror narsa yordam beraymi?")
            else:
                suggestions.append("Xayrli kech! Bugun qanday o'tdi?")
            
            # Eslatmalar bormi?
            try:
                from core.agent_scheduler import get_scheduler
                scheduler = get_scheduler()
                active = scheduler.active_count
                if active > 0:
                    suggestions.append(f"📋 {active} ta rejalashtirilgan vazifangiz bor.")
            except Exception:
                pass
            
            # Foydalanuvchi bilimi bormi?
            if self.memory:
                knowledge = self.memory.get_knowledge()
                if knowledge:
                    # Eng oxirgi saqlangan bilim
                    recent = sorted(knowledge.items(), 
                                   key=lambda x: x[1].get("saved_at", ""), reverse=True)
                    if recent:
                        key, data = recent[0]
                        suggestions.append(f"💡 Eslatma: {key} = {data['value']}")
        
        return suggestions
    
    def get_idle_suggestion(self, idle_seconds: int = 300) -> str:
        """Uzoq vaqt jimlik bo'lganda taklif.
        
        Args:
            idle_seconds: Necha soniya jim turgan
        Returns:
            Taklif matni yoki bo'sh string
        """
        if self._suggestions_today >= self._max_suggestions_per_day:
            return ""
        
        now = datetime.datetime.now()
        hour = now.hour
        
        suggestions = [
            "Biror narsa qidirib beraymi?",
            "Musiqaga nima deraysiz? 🎵",
            "Hisob-kitob kerakmi? 🧮",
        ]
        
        if 12 <= hour <= 13:
            return "Tushlik vaqti! Dam oling. 🍽️"
        
        if idle_seconds > 600:
            self._suggestions_today += 1
            import random
            return random.choice(suggestions)
        
        return ""
    
    def get_context_suggestion(self, last_command: str) -> str:
        """Oxirgi buyruqqa asoslangan taklif.
        
        Args:
            last_command: Oxirgi bajarilgan buyruq
        Returns:
            Taklif matni
        """
        # Markov chain ga o'xshash — buyruqdan keyin nima taklif qilish
        suggestions_map = {
            "open_youtube": "YouTube'dan musiqa qidirib beraymi? 🎵",
            "weather": "Ob-havo ma'lumotini eslatib qo'yaymi? ⏰",
            "calculator": "Yana hisob-kitob kerakmi? 🧮",
            "open_telegram": "Telegramda kimga yozmoqchisiz?",
            "music_search": "Boshqa qo'shiq qidiraylikmi? 🎶",
        }
        
        return suggestions_map.get(last_command, "")


# Global singleton
_plugin_manager = None
_proactive_agent = None

def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager

def get_proactive_agent(memory=None) -> ProactiveAgent:
    global _proactive_agent
    if _proactive_agent is None:
        _proactive_agent = ProactiveAgent(memory)
    return _proactive_agent
