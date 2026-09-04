# ========== test_agent_v2.py ==========
# Yangi tool'lar va scheduler uchun unit testlar

import unittest
import os
import sys
import json
import time
import tempfile
import shutil
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Loyiha ildizi

from core.agent_tools import (
    create_default_registry, _calculator, _datetime_tool,
    _rag_reader, _currency, _translator, _scheduler_tool
)
from core.agent_scheduler import AgentScheduler, ScheduledTask, parse_time_expression


class TestScheduledTask(unittest.TestCase):
    """ScheduledTask testlari"""
    
    def test_yaratish(self):
        task = ScheduledTask("t1", datetime.datetime.now(), "reminder", {"text": "test"})
        self.assertEqual(task.task_id, "t1")
        self.assertFalse(task.completed)
    
    def test_is_due(self):
        """Vaqti kelgan vazifa"""
        past = datetime.datetime.now() - datetime.timedelta(seconds=10)
        task = ScheduledTask("t1", past, "reminder", {"text": "test"})
        self.assertTrue(task.is_due())
    
    def test_not_due(self):
        """Vaqti kelmagan vazifa"""
        future = datetime.datetime.now() + datetime.timedelta(hours=1)
        task = ScheduledTask("t1", future, "reminder", {"text": "test"})
        self.assertFalse(task.is_due())
    
    def test_to_from_dict(self):
        """Serializatsiya"""
        task = ScheduledTask("t1", datetime.datetime.now(), "reminder", {"text": "test"}, repeat_seconds=60)
        d = task.to_dict()
        restored = ScheduledTask.from_dict(d)
        self.assertEqual(restored.task_id, "t1")
        self.assertEqual(restored.repeat_seconds, 60)


class TestAgentScheduler(unittest.TestCase):
    """AgentScheduler testlari"""
    
    def setUp(self):
        self.scheduler = AgentScheduler()
        self.scheduler._file = os.path.join(tempfile.gettempdir(), "test_sched.json")
    
    def tearDown(self):
        self.scheduler.stop()
        if os.path.exists(self.scheduler._file):
            os.remove(self.scheduler._file)
    
    def test_add(self):
        """Vazifa qo'shish"""
        task_id = self.scheduler.add("reminder", {"text": "test"}, delay_seconds=300)
        self.assertIsNotNone(task_id)
        self.assertEqual(self.scheduler.active_count, 1)
    
    def test_list(self):
        """Vazifalar ro'yxati"""
        self.scheduler.add("reminder", {"text": "a"}, delay_seconds=60)
        self.scheduler.add("reminder", {"text": "b"}, delay_seconds=120)
        tasks = self.scheduler.list_tasks()
        self.assertEqual(len(tasks), 2)
    
    def test_remove(self):
        """Vazifa o'chirish"""
        task_id = self.scheduler.add("reminder", {"text": "test"}, delay_seconds=60)
        self.assertTrue(self.scheduler.remove(task_id))
        self.assertEqual(self.scheduler.active_count, 0)
    
    def test_callback(self):
        """Callback ishlashi"""
        results = []
        self.scheduler.set_callback(lambda task: results.append(task.data["text"]))
        # O'tgan vaqtli vazifa
        self.scheduler.add("reminder", {"text": "done!"}, delay_seconds=0)
        self.scheduler._check_tasks()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "done!")


class TestParseTimeExpression(unittest.TestCase):
    """Vaqt parsing testlari"""
    
    def test_daqiqa(self):
        result = parse_time_expression("5 daqiqadan keyin")
        self.assertEqual(result["delay_seconds"], 300)
    
    def test_soniya(self):
        result = parse_time_expression("30 soniyadan keyin")
        self.assertEqual(result["delay_seconds"], 30)
    
    def test_soat(self):
        result = parse_time_expression("2 soatdan keyin")
        self.assertEqual(result["delay_seconds"], 7200)
    
    def test_aniq_vaqt(self):
        result = parse_time_expression("soat 14:30 da")
        self.assertIn("run_at", result)
        self.assertEqual(result["run_at"].hour, 14)
        self.assertEqual(result["run_at"].minute, 30)
    
    def test_takroriy(self):
        result = parse_time_expression("har 10 daqiqada")
        self.assertEqual(result["repeat_seconds"], 600)
    
    def test_noma_lum(self):
        result = parse_time_expression("unknown text")
        self.assertIsNone(result)


class TestRAGReader(unittest.TestCase):
    """RAG Reader testlari"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("Salom dunyo\nIkkinchi qator\nUchinchi qator\n")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_read(self):
        """Faylni o'qish"""
        result = _rag_reader("read", path=self.test_file)
        self.assertIn("content", result)
        self.assertEqual(result["lines"], 4)
        self.assertIn("Salom dunyo", result["content"])
    
    def test_read_not_found(self):
        """Fayl topilmasa"""
        result = _rag_reader("read", path="/nope/missing.txt")
        self.assertIn("error", result)
    
    def test_search(self):
        """Fayl ichidan qidirish"""
        result = _rag_reader("search", path=self.temp_dir, query="Ikkinchi")
        self.assertGreater(len(result.get("results", [])), 0)
    
    def test_info_file(self):
        """Fayl info"""
        result = _rag_reader("info", path=self.test_file)
        self.assertEqual(result["type"], "file")
    
    def test_info_dir(self):
        """Papka info"""
        result = _rag_reader("info", path=self.temp_dir)
        self.assertEqual(result["type"], "directory")
    
    def test_taqiqlangan_kengaytma(self):
        """Taqiqlangan fayl turi"""
        exe_file = os.path.join(self.temp_dir, "test.exe")
        with open(exe_file, "w") as f:
            f.write("data")
        result = _rag_reader("read", path=exe_file)
        self.assertIn("error", result)


class TestRegistryV2(unittest.TestCase):
    """Yangilangan registry testlari"""
    
    def test_20_tool(self):
        """20 ta tool bo'lishi kerak"""
        reg = create_default_registry()
        self.assertEqual(reg.count, 20)
    
    def test_yangi_toollar_bor(self):
        """Yangi tool'lar ro'yxatda"""
        reg = create_default_registry()
        names = reg.list_names()
        self.assertIn("scheduler", names)
        self.assertIn("rag_reader", names)
        self.assertIn("currency", names)
        self.assertIn("translator", names)
        self.assertIn("screen_analyze", names)
    
    def test_prompt_yaratish(self):
        """AI prompt ichida yangi tool'lar bor"""
        reg = create_default_registry()
        prompt = reg.tools_prompt()
        self.assertIn("scheduler", prompt)
        self.assertIn("rag_reader", prompt)
        self.assertIn("currency", prompt)
        self.assertIn("translator", prompt)


if __name__ == '__main__':
    unittest.main(verbosity=2)
