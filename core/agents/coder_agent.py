# ========== coder_agent.py ==========
# Multi-Agent: CoderAgent
# Kod tahlili va yozish uchun maxsus agent

import os
import re
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CoderAgent(BaseAgent):
    """
    CoderAgent — kod tahlili va yozish mutaxassisi.
    Fayllarni o'qiydi, xatolarni topadi, kod yozadi.
    """

    def __init__(self, ai_call_func):
        super().__init__(
            name="CoderAgent",
            specialty="Kod tahlili va yozish",
            ai_call_func=ai_call_func,
        )

        self._supported_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".scss",
            ".json",
            ".yaml",
            ".yml",
            ".xml",
            ".md",
        }

        self._code_keywords = {
            "code",
            "python",
            "javascript",
            "function",
            "class",
            "def",
            "var",
            "let",
            "const",
            "return",
            "import",
            "export",
            "module",
            "package",
            "debug",
            "error",
            "bug",
            "fix",
            "refactor",
            "write",
            "read",
            "file",
            "syntax",
            "runtime",
            "exception",
            "test",
            "docstring",
        }

    def _build_system_prompt(self) -> str:
        return """Sen CoderAgent — kod tahlili va yozish mutaxassisi.

Senning vazifang:
1. Python, JavaScript, va boshqa kod fayllarini o'qish
2. Kodda xatolarni (bug) topish va tahlil qilish
3. Kod yozish va tahrirlash
4. Docstring va izohlar qo'shish
5. Syntax tekshiruv o'tkazish

Qoidalaring:
- Har doim faylni to'liq o'qib, keyin o'zgartirish kirit
- Syntax xatolarini aniq ko'rsat
- Kod yozishda PEP8 standartlariga rioya qil (Python uchun)
- Xavfli operatsiyalardan qoch (fayl o'chirish, format disk)
- Test qilish uchun sandbox.py dan foydalan

Muloqot tili: O'zbekcha (Asalim uchun)
"""

    def can_handle(self, task: str) -> bool:
        """Kod bilan bog'liq vazifalarmi?"""
        task_lower = task.lower()

        for keyword in self._code_keywords:
            if keyword in task_lower:
                return True

        file_extensions = re.findall(r"\.\w+", task)
        for ext in file_extensions:
            if ext in self._supported_extensions:
                return True

        return False

    def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Vazifani bajarish"""
        context = context or {}

        read_match = re.search(
            r'(o\'qi|faylni ko\'rsat|ko\'r|read|show).*?[`"\']([^`"\']+)[`"\']',
            task,
            re.IGNORECASE,
        )
        if read_match:
            file_path = read_match.group(2)
            return self._read_file(file_path)

        write_match = re.search(
            r'(yoz|yarat|save|write|file).*?[`"\']([^`"\']+)[`"\']', task, re.IGNORECASE
        )
        if write_match:
            file_path = write_match.group(2)
            content_match = re.search(
                r"content[:\s]+(.+)", task, re.IGNORECASE | re.DOTALL
            )
            if content_match:
                content = content_match.group(1).strip()
                return self._write_file(file_path, content)

        analyze_match = re.search(
            r'(tahlil|analyze|debug| tekshir).*?[`"\']([^`"\']+)[`"\']',
            task,
            re.IGNORECASE,
        )
        if analyze_match:
            file_path = analyze_match.group(2)
            return self._analyze_file(file_path)

        return {
            "status": "error",
            "error": "CoderAgent bu formatdagi vazifani tushunmadi",
            "task": task,
        }

    def _read_file(self, file_path: str) -> Dict[str, Any]:
        """Faylni o'qish"""
        try:
            full_path = self._resolve_path(file_path)

            if not os.path.exists(full_path):
                return {"status": "error", "error": f"Fayl topilmadi: {full_path}"}

            ext = os.path.splitext(full_path)[1]
            if ext not in self._supported_extensions:
                return {
                    "status": "error",
                    "error": f"Bu turdagi faylni o'qiy olmayman: {ext}",
                }

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            return {
                "status": "success",
                "file": full_path,
                "lines": len(lines),
                "content_preview": content[:500],
                "full_content": content
                if len(content) < 10000
                else content[:10000] + "\n... (truncated)",
            }

        except Exception as e:
            logger.error(f"Fayl o'qish xatolik: {e}")
            return {"status": "error", "error": str(e)}

    def _write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Faylga yozish"""
        try:
            full_path = self._resolve_path(file_path)

            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "status": "success",
                "file": full_path,
                "message": f"Fayl muvaffaqiyatli yozildi ({len(content)} belgi)",
            }

        except Exception as e:
            logger.error(f"Fayl yozish xatolik: {e}")
            return {"status": "error", "error": str(e)}

    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Faylni tahlil qilish"""
        try:
            full_path = self._resolve_path(file_path)

            if not os.path.exists(full_path):
                return {"status": "error", "error": f"Fayl topilmadi: {full_path}"}

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            issues = self._find_issues(content, file_path)

            return {
                "status": "success",
                "file": full_path,
                "issues_found": len(issues),
                "issues": issues,
                "summary": self._generate_summary(issues),
            }

        except Exception as e:
            logger.error(f"Fayl tahlil xatolik: {e}")
            return {"status": "error", "error": str(e)}

    def _find_issues(self, content: str, file_path: str) -> List[Dict]:
        """Kod muammolarini topish"""
        issues = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if stripped.startswith("# TODO") or stripped.startswith("# FIXME"):
                issues.append({"line": i, "type": "todo", "message": stripped})

            if re.search(r"print\s*\(", stripped) and "debug" not in stripped.lower():
                issues.append(
                    {"line": i, "type": "warning", "message": "Debug print statement"}
                )

            if re.search(r"except\s*:", stripped):
                issues.append(
                    {
                        "line": i,
                        "type": "warning",
                        "message": "Bare except clause — specific exception afzal",
                    }
                )

        return issues

    def _generate_summary(self, issues: List[Dict]) -> str:
        """Muammolar xulosasi"""
        if not issues:
            return "Hech qanday muammo topilmadi ✅"

        by_type = {}
        for issue in issues:
            t = issue["type"]
            by_type[t] = by_type.get(t, 0) + 1

        parts = []
        for t, count in by_type.items():
            parts.append(f"{t}: {count} ta")

        return f"Jami {len(issues)} ta muammo: {', '.join(parts)}"

    def _resolve_path(self, path: str) -> str:
        """Yo'lni to'liq qilish"""
        if os.path.isabs(path):
            return path
        return os.path.join(BASE_DIR, path)
