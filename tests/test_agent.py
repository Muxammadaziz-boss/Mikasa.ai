# ========== test_agent.py ==========
# Agent modullari uchun unit testlar

import unittest
import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Loyiha ildizi

from core.agent_tools import Tool, ToolRegistry, create_default_registry, get_registry
from core.agent_tools import _calculator, _datetime_tool, _reminder, _knowledge
from core.agent_planner import ReActAgent, agent_system_prompt
from core.agent_memory import AgentMemory


class TestTool(unittest.TestCase):
    """Tool dataclass testlari"""
    
    def test_tool_yaratish(self):
        """Tool yaratish"""
        tool = Tool(
            name="test_tool",
            description="Test tool",
            parameters={"x": {"type": "string", "description": "Test param"}},
            function=lambda x="": {"result": x}
        )
        self.assertEqual(tool.name, "test_tool")
    
    def test_tool_chaqirish(self):
        """Tool chaqirish"""
        tool = Tool(
            name="echo",
            description="Echo tool",
            parameters={"msg": {"type": "string"}},
            function=lambda msg="hello": {"echo": msg}
        )
        result = tool.call(msg="salom")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["echo"], "salom")
    
    def test_tool_xatolik(self):
        """Tool xatolik"""
        tool = Tool(
            name="error_tool",
            description="Error tool",
            parameters={},
            function=lambda: 1/0
        )
        result = tool.call()
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_tool_to_dict(self):
        """Tool to_dict"""
        tool = Tool(
            name="test",
            description="Test",
            parameters={"x": {"type": "string", "description": "X param"}},
            function=lambda: None
        )
        d = tool.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertIn("x", d["parameters"])


class TestToolRegistry(unittest.TestCase):
    """ToolRegistry testlari"""
    
    def test_register_get(self):
        """Tool ro'yxatdan o'tkazish va olish"""
        reg = ToolRegistry()
        tool = Tool("test", "desc", {}, lambda: "ok")
        reg.register(tool)
        self.assertEqual(reg.get("test").name, "test")
    
    def test_call(self):
        """Registry orqali tool chaqirish"""
        reg = ToolRegistry()
        reg.register(Tool("greet", "Salom", {"who": {"type": "string"}}, lambda who="": f"Salom {who}"))
        result = reg.call("greet", who="Aziz")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "Salom Aziz")
    
    def test_call_not_found(self):
        """Mavjud bo'lmagan tool"""
        reg = ToolRegistry()
        result = reg.call("nonexistent")
        self.assertFalse(result["success"])
    
    def test_default_registry(self):
        """Standart registry 20 ta tool bilan"""
        reg = create_default_registry()
        self.assertEqual(reg.count, 20)
        self.assertIn("calculator", reg.list_names())
        self.assertIn("weather", reg.list_names())
        self.assertIn("web_search", reg.list_names())
        self.assertIn("scheduler", reg.list_names())
        self.assertIn("rag_reader", reg.list_names())
    
    def test_tools_prompt(self):
        """AI uchun tool tavsifi"""
        reg = create_default_registry()
        prompt = reg.tools_prompt()
        self.assertIn("calculator", prompt)
        self.assertIn("weather", prompt)


class TestCalculator(unittest.TestCase):
    """Calculator tool testlari"""
    
    def test_oddiy_qoshish(self):
        result = _calculator("2 + 2")
        self.assertEqual(result["result"], 4)
    
    def test_murakkab_ifoda(self):
        result = _calculator("(10 + 5) * 3")
        self.assertEqual(result["result"], 45)
    
    def test_foiz(self):
        result = _calculator("100 * 15 / 100")
        self.assertEqual(result["result"], 15)
    
    def test_xavfsiz_eval(self):
        """Xavfli ifodalarni bloklash"""
        result = _calculator("__import__('os').system('dir')")
        self.assertIn("error", result)
    
    def test_bosh_ifoda(self):
        result = _calculator("abc")
        self.assertIn("error", result)


class TestDatetime(unittest.TestCase):
    """Datetime tool testlari"""
    
    def test_vaqt(self):
        result = _datetime_tool("time")
        self.assertIn("time", result)
    
    def test_sana(self):
        result = _datetime_tool("date")
        self.assertIn("date", result)
    
    def test_now(self):
        result = _datetime_tool("now")
        self.assertIn("date", result)
        self.assertIn("time", result)


class TestKnowledge(unittest.TestCase):
    """Knowledge tool testlari"""
    
    def setUp(self):
        # Test uchun vaqtinchalik fayl
        self.original_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_file = os.path.join(tempfile.gettempdir(), "test_knowledge.json")
    
    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_save_get(self):
        """Bilim saqlash va olish"""
        # Vaqtinchalik fayl bilan test
        result = _knowledge("save", key="test_key", value="test_value")
        self.assertIn("message", result)
        
        result = _knowledge("get", key="test_key")
        self.assertEqual(result["value"], "test_value")


class TestAgentMemory(unittest.TestCase):
    """AgentMemory testlari"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory = AgentMemory()
        # Test fayllari uchun vaqtinchalik yo'llar
        self.memory._conversations_file = os.path.join(self.temp_dir, "conv.json")
        self.memory._profile_file = os.path.join(self.temp_dir, "profile.json")
        self.memory._knowledge_file = os.path.join(self.temp_dir, "knowledge.json")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_short_term(self):
        """Qisqa muddatli xotira"""
        self.memory.add_to_context("user", "salom")
        self.memory.add_to_context("assistant", "salom!")
        ctx = self.memory.get_context()
        self.assertEqual(len(ctx), 2)
    
    def test_conversation(self):
        """Suhbat tarixi"""
        # Clear existing history since this uses actual file system
        self.memory._conversations = []
        self.memory.add_conversation("salom", "salom!")
        self.memory.add_conversation("youtube och", "YouTube ochildi")
        convs = self.memory.get_conversations()
        self.assertEqual(len(convs), 2)
    
    def test_search_conversations(self):
        """Suhbat qidirish"""
        # Clear existing history since this uses actual file system
        self.memory._conversations = []
        self.memory.add_conversation("youtube och", "Ochildi")
        self.memory.add_conversation("telegram och", "Ochildi")
        results = self.memory.search_conversations("youtube")
        self.assertEqual(len(results), 1)
    
    def test_profile(self):
        """Foydalanuvchi profili"""
        self.memory.set_profile("ism", "Aziz")
        self.assertEqual(self.memory.get_profile("ism"), "Aziz")
    
    def test_knowledge(self):
        """Bilimlar bazasi"""
        self.memory.save_knowledge("til", "Python")
        k = self.memory.get_knowledge("til")
        self.assertEqual(k["value"], "Python")
    
    def test_knowledge_summary(self):
        """AI uchun bilimlar xulosasi"""
        self.memory.save_knowledge("til", "Python")
        self.memory.save_knowledge("shahar", "Toshkent")
        summary = self.memory.get_knowledge_summary()
        self.assertIn("Python", summary)
        self.assertIn("Toshkent", summary)
    
    def test_stats(self):
        """Statistika"""
        stats = self.memory.stats
        self.assertIn("kontekst_hajmi", stats)
        self.assertIn("suhbatlar_soni", stats)


class TestReActAgent(unittest.TestCase):
    """ReAct Agent testlari"""
    
    def setUp(self):
        self.registry = create_default_registry()
    
    def test_agent_yaratish(self):
        """Agent yaratish"""
        def mock_ai(prompt, system_prompt):
            return '{"action": "final_answer", "response": "Salom!"}'
        
        agent = ReActAgent(self.registry, mock_ai)
        self.assertIsNotNone(agent)
    
    def test_oddiy_javob(self):
        """Oddiy matnli javob (tool kerak emas)"""
        def mock_ai(prompt, system_prompt):
            return '{"action": "final_answer", "response": "Salom, do\'stim!"}'
        
        agent = ReActAgent(self.registry, mock_ai)
        result = agent.run("salom")
        self.assertTrue(result["success"])
        self.assertIn("Salom", result["response"])
    
    def test_tool_chaqirish(self):
        """Tool chaqirish bilan vazifa"""
        call_count = [0]
        
        def mock_ai(prompt, system_prompt):
            call_count[0] += 1
            if call_count[0] == 1:
                return '{"action": "tool_call", "tool": "calculator", "params": {"expression": "2 + 2"}, "thought": "Hisoblash kerak"}'
            else:
                return '{"action": "final_answer", "response": "2 + 2 = 4", "tools_used": ["calculator"]}'
        
        agent = ReActAgent(self.registry, mock_ai)
        result = agent.run("2 + 2 necha?")
        self.assertTrue(result["success"])
        self.assertIn("calculator", result["tools_used"])
    
    def test_max_steps_himoya(self):
        """Cheksiz loop dan himoya"""
        def mock_ai(prompt, system_prompt):
            return '{"action": "tool_call", "tool": "datetime", "params": {"action": "now"}, "thought": "Vaqt"}'
        
        agent = ReActAgent(self.registry, mock_ai)
        agent.MAX_STEPS = 3  # Tezroq test uchun
        result = agent.run("loop test")
        # 3 ta qadamdan keyin to'xtashi kerak
        self.assertLessEqual(len(result["steps"]), 3)
    
    def test_step_callback(self):
        """Qadam callback ishlashi"""
        callbacks_received = []
        
        def mock_ai(prompt, system_prompt):
            return '{"action": "final_answer", "response": "Tayyor!"}'
        
        agent = ReActAgent(self.registry, mock_ai)
        agent.on_step(lambda step, stype, data: callbacks_received.append(stype))
        agent.run("test")
        self.assertIn("final_answer", callbacks_received)
    
    def test_system_prompt(self):
        """System prompt yaratish"""
        reg = create_default_registry()
        prompt = agent_system_prompt(reg.tools_prompt(), "- til: Python")
        self.assertIn("calculator", prompt)
        self.assertIn("Python", prompt)
        self.assertIn("tool", prompt.lower())


class TestAgentSystemPrompt(unittest.TestCase):
    """Agent system prompt testlari"""
    
    def test_tools_ichida(self):
        prompt = agent_system_prompt("- calculator(expression) — hisoblash")
        self.assertIn("calculator", prompt)
    
    def test_knowledge_ichida(self):
        prompt = agent_system_prompt("tools...", "- favorite_lang: Python")
        self.assertIn("Python", prompt)


if __name__ == '__main__':
    unittest.main(verbosity=2)
