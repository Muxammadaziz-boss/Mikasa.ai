# ========== test_agent_v3.py ==========
# Async, Retry, Plugin, Proactive agent testlari

import unittest
import os
import sys
import json
import time
import tempfile
import shutil
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Loyiha ildizi

from core.agent_tools import Tool, ToolRegistry, create_default_registry
from core.agent_planner import ReActAgent
from core.agent_plugins import PluginManager, ProactiveAgent


class TestAsyncRun(unittest.TestCase):
    """Async agent testlari"""
    
    def test_run_async(self):
        """Background thread da ishga tushish"""
        reg = create_default_registry()
        results = []
        event = threading.Event()
        
        def mock_ai(prompt, system_prompt):
            return '{"action": "final_answer", "response": "Async done!"}'
        
        agent = ReActAgent(reg, mock_ai)
        agent.on_complete(lambda r: (results.append(r), event.set()))
        
        agent.run_async("test")
        event.wait(timeout=5)
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"])
        self.assertIn("Async done", results[0]["response"])
    
    def test_is_running(self):
        """is_running holati"""
        reg = create_default_registry()
        
        def mock_ai(prompt, system_prompt):
            time.sleep(0.5)
            return '{"action": "final_answer", "response": "done"}'
        
        agent = ReActAgent(reg, mock_ai)
        event = threading.Event()
        agent.on_complete(lambda r: event.set())
        
        agent.run_async("test")
        self.assertTrue(agent.is_running)
        event.wait(timeout=5)
        time.sleep(0.1)
        self.assertFalse(agent.is_running)
    
    def test_duplicate_run_protection(self):
        """Ikki marta async ishga tushirishdan himoya"""
        reg = create_default_registry()
        
        def slow_ai(prompt, system_prompt):
            time.sleep(1)
            return '{"action": "final_answer", "response": "done"}'
        
        agent = ReActAgent(reg, slow_ai)
        event = threading.Event()
        agent.on_complete(lambda r: event.set())
        
        agent.run_async("test1")
        agent.run_async("test2")  # Bu ishlamasligi kerak
        event.wait(timeout=5)


class TestRetryLogic(unittest.TestCase):
    """Retry logic testlari"""
    
    def test_ai_retry(self):
        """AI xato bo'lsa qayta urinish"""
        reg = create_default_registry()
        calls = [0]
        
        def failing_ai(prompt, system_prompt):
            calls[0] += 1
            if calls[0] <= 2:
                raise Exception("AI xatolik")
            return '{"action": "final_answer", "response": "3-urinishda ishladi!"}'
        
        agent = ReActAgent(reg, failing_ai)
        result = agent.run("test")
        self.assertTrue(result["success"])
        self.assertEqual(calls[0], 3)
    
    def test_tool_retry(self):
        """Tool xato bo'lsa qayta urinish"""
        reg = ToolRegistry()
        call_count = [0]
        
        def failing_tool():
            call_count[0] += 1
            if call_count[0] <= 1:
                raise Exception("Tool xatolik")
            return {"message": "OK"}
        
        reg.register(Tool("flaky", "Xato tool", {}, failing_tool))
        
        ai_calls = [0]
        def mock_ai(prompt, system_prompt):
            ai_calls[0] += 1
            if ai_calls[0] == 1:
                return '{"action": "tool_call", "tool": "flaky", "params": {}, "thought": "test"}'
            return '{"action": "final_answer", "response": "OK"}'
        
        agent = ReActAgent(reg, mock_ai)
        result = agent.run("test")
        # Tool 2 marta urinilishi kerak
        self.assertGreater(call_count[0], 1)


class TestPluginManager(unittest.TestCase):
    """Plugin manager testlari"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.pm = PluginManager(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_json_plugin(self):
        """JSON plugin yuklash"""
        plugin = {
            "name": "test_url",
            "description": "Test URL tool",
            "type": "url",
            "url": "https://example.com/{query}",
            "parameters": {"query": {"type": "string", "description": "Qidiruv"}}
        }
        with open(os.path.join(self.temp_dir, "test.json"), "w") as f:
            json.dump(plugin, f)
        
        reg = ToolRegistry()
        loaded = self.pm.load_all(reg)
        self.assertEqual(loaded, 1)
        self.assertIn("test_url", reg.list_names())
    
    def test_python_plugin(self):
        """Python plugin yuklash"""
        code = '''
TOOL_NAME = "my_custom"
TOOL_DESCRIPTION = "Test Python tool"
TOOL_PARAMS = {"text": {"type": "string"}}
TOOL_CATEGORY = "test"

def run(text="hello"):
    return {"message": f"Echo: {text}"}
'''
        with open(os.path.join(self.temp_dir, "test_plugin.py"), "w") as f:
            f.write(code)
        
        reg = ToolRegistry()
        loaded = self.pm.load_all(reg)
        self.assertEqual(loaded, 1)
        
        result = reg.call("my_custom", text="salom")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["message"], "Echo: salom")
    
    def test_empty_dir(self):
        """Bo'sh papka"""
        empty_dir = tempfile.mkdtemp()
        pm = PluginManager(empty_dir)
        reg = ToolRegistry()
        loaded = pm.load_all(reg)
        self.assertEqual(loaded, 0)
        shutil.rmtree(empty_dir, ignore_errors=True)
    
    def test_auto_create_dir(self):
        """Plugins papkasi avtomatik yaratiladi"""
        new_dir = os.path.join(self.temp_dir, "new_plugins")
        pm = PluginManager(new_dir)
        reg = ToolRegistry()
        pm.load_all(reg)
        self.assertTrue(os.path.exists(new_dir))


class TestProactiveAgent(unittest.TestCase):
    """Proaktiv agent testlari"""
    
    def test_greeting(self):
        """Salomlash takliflari"""
        pa = ProactiveAgent()
        suggestions = pa.get_greeting_suggestions()
        self.assertGreater(len(suggestions), 0)
    
    def test_greeting_once_per_day(self):
        """Kuniga bir marta salomlash"""
        pa = ProactiveAgent()
        s1 = pa.get_greeting_suggestions()
        s2 = pa.get_greeting_suggestions()
        self.assertGreater(len(s1), 0)
        self.assertEqual(len(s2), 0)
    
    def test_context_suggestion(self):
        """Kontekstga asoslangan taklif"""
        pa = ProactiveAgent()
        s = pa.get_context_suggestion("open_youtube")
        self.assertIn("musiqa", s.lower())
    
    def test_context_empty(self):
        """Noma'lum buyruq"""
        pa = ProactiveAgent()
        s = pa.get_context_suggestion("unknown_command")
        self.assertEqual(s, "")
    
    def test_idle_suggestion(self):
        """Uzoq jimlik taklifi"""
        pa = ProactiveAgent()
        s = pa.get_idle_suggestion(idle_seconds=700)
        self.assertIsInstance(s, str)


if __name__ == '__main__':
    unittest.main(verbosity=2)
