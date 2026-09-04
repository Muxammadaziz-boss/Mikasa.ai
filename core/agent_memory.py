# ========== agent_memory.py ==========
# Agent uzoq muddatli xotira tizimi
# Suhbat tarixi + Foydalanuvchi profili + Bilimlar bazasi

import os
import json
import logging
import datetime
from collections import deque
from threading import RLock

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Loyiha ildizi


class AgentMemory:
    """Agent xotirasi — 3 darajali:
    
    1. Qisqa muddatli (RAM) — joriy suhbat konteksti
    2. O'rta muddatli (fayl) — suhbat tarixi
    3. Uzoq muddatli (fayl) — foydalanuvchi profili va bilimlar
    """
    
    def __init__(self, max_short_term=20, max_conversations=100):
        self._lock = RLock()
        
        # Qisqa muddatli xotira (RAM)
        self._short_term = deque(maxlen=max_short_term)
        
        # Fayl yo'llari
        self._conversations_file = os.path.join(BASE_DIR, "agent_conversations.json")
        self._profile_file = os.path.join(BASE_DIR, "agent_profile.json")
        self._knowledge_file = os.path.join(BASE_DIR, "agent_knowledge.json")
        
        self._max_conversations = max_conversations
        
        # Yuklash
        self._profile = self._load_json(self._profile_file, {
            "ism": "",
            "ovoz_turi": "erkak",
            "til": "uz",
            "qiziqishlar": [],
            "yoqtirgan_platformalar": [],
            "yaratilgan": datetime.datetime.now().isoformat()
        })
        self._knowledge = self._load_json(self._knowledge_file, {})
        self._conversations = self._load_json(self._conversations_file, [])
        
        logger.info(f"AgentMemory yuklandi: {len(self._conversations)} suhbat, {len(self._knowledge)} bilim")
    
    # ========== QISQA MUDDATLI XOTIRA ==========
    
    def add_to_context(self, role: str, content: str):
        """Joriy suhbatga xabar qo'shish"""
        with self._lock:
            self._short_term.append({
                "role": role,
                "content": content,
                "time": datetime.datetime.now().isoformat()
            })
    
    def get_context(self, last_n: int = 10) -> list:
        """Joriy suhbat kontekstini olish"""
        with self._lock:
            items = list(self._short_term)
            return items[-last_n:]
    
    def clear_context(self):
        """Joriy suhbatni tozalash"""
        with self._lock:
            self._short_term.clear()
    
    # ========== SUHBAT TARIXI ==========
    
    def add_conversation(self, user_input: str, agent_response: str):
        """Suhbatni tarixga qo'shish"""
        with self._lock:
            self._conversations.append({
                "user": user_input,
                "agent": agent_response,
                "time": datetime.datetime.now().isoformat()
            })
            
            # Cheklanishdan oshsa eski suhbatlarni o'chirish
            while len(self._conversations) > self._max_conversations:
                self._conversations.pop(0)
            
            # Har 5 ta suhbatda faylga saqlash
            if len(self._conversations) % 5 == 0:
                self._save_conversations()
    
    def get_conversations(self, last_n: int = 20) -> list:
        """Oxirgi N ta suhbat"""
        with self._lock:
            return self._conversations[-last_n:]
    
    def search_conversations(self, query: str, limit: int = 5) -> list:
        """Suhbatlardan qidirish"""
        with self._lock:
            query_lower = query.lower()
            results = []
            for conv in reversed(self._conversations):
                if (query_lower in conv["user"].lower() or 
                    query_lower in conv["agent"].lower()):
                    results.append(conv)
                    if len(results) >= limit:
                        break
            return results
    
    def get_history_for_ai(self, last_n: int = 6) -> list:
        """AI uchun suhbat tarixi formatda"""
        conversations = self.get_conversations(last_n)
        history = []
        for conv in conversations:
            history.append({"role": "user", "content": conv["user"]})
            history.append({"role": "assistant", "content": conv["agent"]})
        return history
    
    # ========== FOYDALANUVCHI PROFILI ==========
    
    def set_profile(self, key: str, value):
        """Profil ma'lumotini o'zgartirish"""
        with self._lock:
            self._profile[key] = value
            self._save_json(self._profile_file, self._profile)
            logger.debug(f"Profil yangilandi: {key} = {value}")
    
    def get_profile(self, key: str = None, default=None):
        """Profil ma'lumotini olish"""
        with self._lock:
            if key:
                return self._profile.get(key, default)
            return self._profile.copy()
    
    # ========== BILIMLAR BAZASI ==========
    
    def save_knowledge(self, key: str, value: str):
        """Yangi bilim saqlash"""
        with self._lock:
            self._knowledge[key] = {
                "value": value,
                "saved_at": datetime.datetime.now().isoformat(),
                "access_count": 0
            }
            self._save_json(self._knowledge_file, self._knowledge)
            logger.debug(f"Bilim saqlandi: {key} = {value}")
    
    def get_knowledge(self, key: str = None) -> dict:
        """Bilim olish"""
        with self._lock:
            if key:
                if key in self._knowledge:
                    self._knowledge[key]["access_count"] += 1
                    return self._knowledge[key]
                return None
            return self._knowledge.copy()
    
    def get_knowledge_summary(self) -> str:
        """AI prompt uchun bilimlar xulosasi"""
        with self._lock:
            if not self._knowledge:
                return ""
            
            lines = []
            for key, data in self._knowledge.items():
                lines.append(f"- {key}: {data['value']}")
            return "\n".join(lines)
    
    def delete_knowledge(self, key: str) -> bool:
        """Bilimni o'chirish"""
        with self._lock:
            if key in self._knowledge:
                del self._knowledge[key]
                self._save_json(self._knowledge_file, self._knowledge)
                return True
            return False
    
    # ========== STATISTIKA ==========
    
    @property
    def stats(self) -> dict:
        """Xotira statistikasi"""
        with self._lock:
            return {
                "kontekst_hajmi": len(self._short_term),
                "suhbatlar_soni": len(self._conversations),
                "bilimlar_soni": len(self._knowledge),
                "profil_toliq": bool(self._profile.get("ism"))
            }
    
    # ========== ICHKI FUNKSIYALAR ==========
    
    def _load_json(self, path: str, default):
        """JSON faylni yuklash"""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"JSON yuklash xatolik ({path}): {e}")
        return default
    
    def _save_json(self, path: str, data):
        """JSON faylga saqlash"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"JSON saqlash xatolik ({path}): {e}")
    
    def _save_conversations(self):
        """Suhbatlarni faylga saqlash"""
        self._save_json(self._conversations_file, self._conversations)
    
    def save_all(self):
        """Barchasini faylga saqlash"""
        with self._lock:
            self._save_conversations()
            self._save_json(self._profile_file, self._profile)
            self._save_json(self._knowledge_file, self._knowledge)
            logger.info("AgentMemory: barcha ma'lumotlar saqlandi")


# Global singleton
_memory = None

def get_memory() -> AgentMemory:
    """Global AgentMemory olish (singleton — duplikat yaratmaydi)"""
    global _memory
    if _memory is None:
        _memory = AgentMemory()
    return _memory
