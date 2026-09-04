# ========== manager_agent.py ==========
# Multi-Agent: ManagerAgent
# Asosiy agent — vazifalarni sub-agentlarga bo'lib beradi

import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from .base_agent import BaseAgent
from .coder_agent import CoderAgent
from .research_agent import ResearchAgent

logger = logging.getLogger(__name__)


class Task:
    """Vazifa — sub-agentga beriladigan ish birligi"""

    def __init__(self, description: str, assigned_to: Optional[str] = None):
        self.description = description
        self.assigned_to = assigned_to
        self.status = "pending"
        self.result = None


class ManagerAgent(BaseAgent):
    """
    ManagerAgent — asosiy koordinator.
    Kelgan vazifalarni tahlil qiladi va to'g'ri sub-agentga yo'naltiradi.
    """

    def __init__(self, ai_call_func: Callable):
        super().__init__(
            name="ManagerAgent",
            specialty="Vazifa taqsimlash va koordinatsiya",
            ai_call_func=ai_call_func,
        )

        self._sub_agents: Dict[str, BaseAgent] = {}
        self._tasks: List[Task] = []
        self._init_sub_agents(ai_call_func)

    def _init_sub_agents(self, ai_call_func: Callable):
        """Sub-agentlarni ishga tushirish"""
        try:
            self._sub_agents["coder"] = CoderAgent(ai_call_func)
            self._sub_agents["research"] = ResearchAgent(ai_call_func)
            logger.info("Sub-agents initialized: coder, research")
        except Exception as e:
            logger.error(f"Sub-agents init xatolik: {e}")

    def _build_system_prompt(self) -> str:
        return """Sen ManagerAgent — Mikasa AI'ning asosiy koordinatoris.

Senning vazifang:
1. Kelgan vazifalarni tahlil qilish
2. Ularni to'g'ri sub-agentlarga yo'naltirish
3. Natijalarni birlashtirish

Mavjud sub-agentlar:
- CoderAgent: kod tahlili va yozish
- ResearchAgent: web qidiruv va tadqiqot

Qoidalaring:
- Har bir vazifa uchun eng mos agentni tanla
- murakkab vazifalarni kichik qismlarga bo'l
- Natijalarni foydalanuvchiga tushunarli qil

Muloqot tili: O'zbekcha (Asalim uchun)
"""

    def can_handle(self, task: str) -> bool:
        """Barcha vazifalarni Manager qabul qiladi"""
        return True

    def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Vazifani bajarish — sub-agentlarga yo'naltirish"""
        context = context or {}

        coder_keywords = [
            "code",
            "python",
            "javascript",
            "fayl",
            "file",
            "yoz",
            "debug",
        ]
        research_keywords = ["qidir", "search", "web", "internet", "youtube", "github"]

        task_lower = task.lower()

        if any(k in task_lower for k in coder_keywords):
            return self._delegate_to_agent("coder", task, context)

        if any(k in task_lower for k in research_keywords):
            return self._delegate_to_agent("research", task, context)

        return self._direct_execute(task, context)

    def _delegate_to_agent(
        self, agent_name: str, task: str, context: Dict
    ) -> Dict[str, Any]:
        """Sub-agentga vazifa berish"""
        agent = self._sub_agents.get(agent_name)

        if not agent:
            return {"status": "error", "error": f"{agent_name} topilmadi"}

        if not agent.can_handle(task):
            return {
                "status": "error",
                "error": f"{agent_name} bu vazifani bajara olmaydi",
                "suggestion": "Boshqa agentga yo'naltiring",
            }

        task_record = Task(description=task, assigned_to=agent_name)
        self._tasks.append(task_record)

        try:
            result = agent.run(task, context)
            task_record.result = result
            task_record.status = "completed"

            return {
                "status": "success",
                "delegated_to": agent_name,
                "result": result,
                "task_id": len(self._tasks) - 1,
            }

        except Exception as e:
            task_record.status = "failed"
            logger.error(f"Agent delegation xatolik: {e}")
            return {"status": "error", "error": str(e), "delegated_to": agent_name}

    def _direct_execute(self, task: str, context: Dict) -> Dict[str, Any]:
        """To'g'ridan-to'g'ri bajarish — AI orqali"""
        try:
            result = self.ai_call_func(task, context)
            return {"status": "success", "direct": True, "result": result}
        except Exception as e:
            logger.error(f"Direct execute xatolik: {e}")
            return {"status": "error", "error": str(e)}

    def get_sub_agents(self) -> List[str]:
        """Mavjud sub-agentlar ro'yxati"""
        return list(self._sub_agents.keys())

    def get_sub_agent_stats(self) -> Dict[str, Dict]:
        """Barcha sub-agentlar statistikasi"""
        return {name: agent.get_stats() for name, agent in self._sub_agents.items()}

    def get_tasks(self) -> List[Dict]:
        """Bajarilgan vazifalar ro'yxati"""
        return [
            {
                "description": t.description,
                "assigned_to": t.assigned_to,
                "status": t.status,
            }
            for t in self._tasks[-20:]
        ]
