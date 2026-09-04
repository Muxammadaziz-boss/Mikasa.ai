# ========== research_agent.py ==========
# Multi-Agent: ResearchAgent
# Web qidiruv va tadqiqot uchun maxsus agent

import os
import re
import logging
import subprocess
import webbrowser
from typing import Dict, Any, List
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ResearchAgent(BaseAgent):
    """
    ResearchAgent — web qidiruv va tadqiqot mutaxassisi.
    Brauzer ochish, qidiruv tizimlari, va ma'lumot yig'ish.
    """

    def __init__(self, ai_call_func):
        super().__init__(
            name="ResearchAgent",
            specialty="Web qidiruv va tadqiqot",
            ai_call_func=ai_call_func,
        )

        self._search_keywords = {
            "qidir",
            "search",
            "google",
            "bing",
            "yandex",
            "youtube",
            "wikipedia",
            "github",
            "stack",
            "overflow",
            "ma'lumot",
            "info",
            "article",
            "document",
            "news",
            "yangilik",
            "news",
            "qanday",
            "how",
            "what",
            "why",
        }

        self._search_engines = {
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "yandex": "https://yandex.com/search/?text=",
            "youtube": "https://www.youtube.com/results?search_query=",
            "github": "https://github.com/search?q=",
            "stackoverflow": "https://stackoverflow.com/search?q=",
            "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search=",
        }

    def _build_system_prompt(self) -> str:
        return """Sen ResearchAgent — web qidiruv va tadqiqot mutaxassisi.

Senning vazifang:
1. Web sahifalarni ochish
2. Turli qidiruv tizimlarida qidiruv o'tkazish
3. Ma'lumot yig'ish va tartiblash
4. YouTube, GitHub, StackOverflow kabi sahifalarda qidirish

Qoidalaring:
- Foydalanuvchi tilida qidir (O'zbekcha)
- Natijalarni qisqa xulosa bilan taqdim et
- Faqat foydali havolalarni ko'rsat
- Ruxsat etilmagan kontentdan qoch

Muloqot tili: O'zbekcha (Asalim uchun)
"""

    def can_handle(self, task: str) -> bool:
        """Qidiruv bilan bog'liq vazifalarmi?"""
        task_lower = task.lower()

        for keyword in self._search_keywords:
            if keyword in task_lower:
                return True

        return False

    def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Vazifani bajarish"""
        context = context or {}

        search_match = re.search(
            r'(qidir|search|top|izla).*?["\']([^"\']+)["\']', task, re.IGNORECASE
        )
        if search_match:
            query = search_match.group(2)
            engine = self._detect_engine(task)
            return self._search_web(query, engine)

        url_match = re.search(
            r'(och|open|ko\'r).*?["\'](https?://[^"\']+)["\']', task, re.IGNORECASE
        )
        if url_match:
            url = url_match.group(2)
            return self._open_url(url)

        youtube_match = re.search(
            r'(video|musiga|qoshq|qidir|search).*?["\']([^"\']+)["\']',
            task,
            re.IGNORECASE,
        )
        if youtube_match and any(
            x in task.lower() for x in ["youtube", "yutub", "video"]
        ):
            query = youtube_match.group(2)
            return self._search_youtube(query)

        github_match = re.search(r'github.*?["\']([^"\']+)["\']', task, re.IGNORECASE)
        if github_match:
            query = github_match.group(1)
            return self._search_github(query)

        return {
            "status": "error",
            "error": "ResearchAgent bu turdagi vazifani tushunmadi",
            "task": task,
        }

    def _detect_engine(self, task: str) -> str:
        """Qidiruv tizimini aniqlash"""
        task_lower = task.lower()

        if "youtube" in task_lower or "yutub" in task_lower:
            return "youtube"
        if "github" in task_lower:
            return "github"
        if "yandex" in task_lower:
            return "yandex"
        if "wiki" in task_lower:
            return "wikipedia"
        if "stackoverflow" in task_lower or "stack overflow" in task_lower:
            return "stackoverflow"
        if "bing" in task_lower:
            return "bing"

        return "google"

    def _search_web(self, query: str, engine: str = "google") -> Dict[str, Any]:
        """Web qidiruv"""
        try:
            base_url = self._search_engines.get(engine, self._search_engines["google"])
            url = base_url + query.replace(" ", "+")

            webbrowser.open(url)

            return {
                "status": "success",
                "engine": engine,
                "query": query,
                "url": url,
                "message": f"{engine.capitalize()} da '{query}' qidirilmoqda...",
            }

        except Exception as e:
            logger.error(f"Web qidiruv xatolik: {e}")
            return {"status": "error", "error": str(e)}

    def _open_url(self, url: str) -> Dict[str, Any]:
        """URL ochish"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            webbrowser.open(url)

            return {
                "status": "success",
                "url": url,
                "message": f"Sahifa ochilmoqda: {url}",
            }

        except Exception as e:
            logger.error(f"URL ochish xatolik: {e}")
            return {"status": "error", "error": str(e)}

    def _search_youtube(self, query: str) -> Dict[str, Any]:
        """YouTube qidiruv"""
        try:
            url = self._search_engines["youtube"] + query.replace(" ", "+")
            webbrowser.open(url)

            return {
                "status": "success",
                "platform": "YouTube",
                "query": query,
                "url": url,
                "message": f"YouTube da '{query}' qidirilmoqda...",
            }

        except Exception as e:
            logger.error(f"YouTube qidiruv xatolik: {e}")
            return {"status": "error", "error": str(e)}

    def _search_github(self, query: str) -> Dict[str, Any]:
        """GitHub qidiruv"""
        try:
            url = self._search_engines["github"] + query.replace(" ", "+")
            webbrowser.open(url)

            return {
                "status": "success",
                "platform": "GitHub",
                "query": query,
                "url": url,
                "message": f"GitHub da '{query}' qidirilmoqda...",
            }

        except Exception as e:
            logger.error(f"GitHub qidiruv xatolik: {e}")
            return {"status": "error", "error": str(e)}

    def get_search_engines(self) -> List[str]:
        """Mavjud qidiruv tizimlari"""
        return list(self._search_engines.keys())
