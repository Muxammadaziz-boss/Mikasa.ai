# ========== test_scheduler_api.py ==========
# Phase 13 — Scheduler API & 5-state Lifecycle Unit Tests

import os
import sys
import json
import asyncio
import datetime
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.agent_scheduler import ScheduledTask, AgentScheduler, get_scheduler
from core.api_server import (
    handle_scheduler_list,
    handle_scheduler_add,
    handle_scheduler_edit,
    handle_scheduler_enable,
    handle_scheduler_disable,
    handle_scheduler_execute,
    handle_scheduler_remove,
    handle_scheduler_clear_completed,
)


class MockRequest:
    def __init__(self, json_data=None, query_data=None):
        self._json_data = json_data or {}
        self.query = query_data or {}

    async def json(self):
        return self._json_data


class TestSchedulerCoreAndAPI(unittest.TestCase):
    """Scheduler va uning 5 xil holati bo'yicha testlar"""

    def setUp(self):
        self.sched = get_scheduler()

    def test_task_states_lifecycle(self):
        """ScheduledTask 5 ta holatni (active, repeating, completed, failed, cancelled) to'g'ri hisoblaydi"""
        now = datetime.datetime.now()
        
        # 1. active
        task = ScheduledTask("t1", now, "reminder", {"text": "Hello"}, repeat_seconds=0)
        self.assertEqual(task.get_state(), "active")

        # 2. repeating
        task_rep = ScheduledTask("t2", now, "reminder", {"text": "Repeat"}, repeat_seconds=60)
        self.assertEqual(task_rep.get_state(), "repeating")

        # 3. completed
        task.completed = True
        self.assertEqual(task.get_state(), "completed")

        # 4. failed
        task.last_error = "Connection timeout"
        self.assertEqual(task.get_state(), "failed")

        # 5. cancelled / disabled
        task.cancelled = True
        self.assertEqual(task.get_state(), "cancelled")

        task2 = ScheduledTask("t3", now, "reminder", {"text": "Disabled"})
        task2.enabled = False
        self.assertEqual(task2.get_state(), "cancelled")

    def test_scheduler_add_and_list(self):
        """add va list_tasks to'liq boyitilgan ma'lumotlarni qaytaradi"""
        async def _run():
            req_add = MockRequest({
                "text": "Unit test eslatmasi",
                "delay_minutes": 10,
                "repeat_minutes": 0,
                "type": "reminder"
            })
            resp_add = await handle_scheduler_add(req_add)
            data_add = json.loads(resp_add.text)
            self.assertTrue(data_add.get("ok"))
            task_id = data_add["task_id"]

            resp_list = await handle_scheduler_list(MockRequest())
            data_list = json.loads(resp_list.text)
            self.assertTrue(data_list.get("ok"))
            
            # Yangi qo'shilgan vazifani topish
            matching = [t for t in data_list.get("tasks", []) if t.get("id") == task_id]
            self.assertEqual(len(matching), 1)
            t = matching[0]
            self.assertEqual(t["status"], "active")
            self.assertTrue(t["enabled"])
            self.assertFalse(t["completed"])
            self.assertEqual(t["data"]["text"], "Unit test eslatmasi")

            # Clean up
            await handle_scheduler_remove(MockRequest(query_data={"task_id": task_id}))

        asyncio.run(_run())

    def test_scheduler_edit_flow(self):
        """Vazifani tahrirlash (edit) to'g'ri ishlaydi"""
        async def _run():
            task_id = self.sched.add("reminder", {"text": "Eski matn"}, delay_seconds=120)
            
            edit_req = MockRequest({
                "task_id": task_id,
                "text": "Yangi yangilangan matn",
                "delay_minutes": 30
            })
            resp = await handle_scheduler_edit(edit_req)
            data = json.loads(resp.text)
            self.assertTrue(data.get("ok"))

            task = self.sched._tasks.get(task_id)
            self.assertIsNotNone(task)
            self.assertEqual(task.data["text"], "Yangi yangilangan matn")

            # Clean up
            self.sched.remove(task_id)

        asyncio.run(_run())

    def test_scheduler_disable_enable_execute(self):
        """disable, enable va execute amallari to'g'ri holat almashinuvini ta'minlaydi"""
        async def _run():
            executed_records = []
            self.sched.set_callback(lambda t: executed_records.append(t.task_id))

            task_id = self.sched.add("reminder", {"text": "Test action"}, delay_seconds=300)

            # Disable
            resp_dis = await handle_scheduler_disable(MockRequest({"task_id": task_id}))
            data_dis = json.loads(resp_dis.text)
            self.assertTrue(data_dis.get("ok"))
            self.assertEqual(self.sched._tasks[task_id].get_state(), "cancelled")

            # Enable
            resp_en = await handle_scheduler_enable(MockRequest({"task_id": task_id}))
            data_en = json.loads(resp_en.text)
            self.assertTrue(data_en.get("ok"))
            self.assertEqual(self.sched._tasks[task_id].get_state(), "active")

            # Immediate Execute
            resp_exec = await handle_scheduler_execute(MockRequest({"task_id": task_id}))
            data_exec = json.loads(resp_exec.text)
            self.assertTrue(data_exec.get("ok"))
            self.assertIn(task_id, executed_records)
            self.assertEqual(self.sched._tasks[task_id].get_state(), "completed")

            # Clean up
            self.sched.remove(task_id)

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
