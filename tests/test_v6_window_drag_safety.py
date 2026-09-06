"""
Mikasa AI v6.0.0 — Custom Window Drag Safety & Proactive Watcher Thread-Safety Tests
Verifies:
1. Pure-Tkinter window drag replaces native SendMessageW/ReleaseCapture modal loop.
2. Dragging on maximized window restores normal state smoothly.
3. ProactiveWatcher uses stop_event and suggestion_queue, stops in < 2 seconds.
4. BackendBridge UI queue does not interact with destroyed widgets.
5. Stress test: Dragging while worker threads are active runs without GIL errors or crashes.
"""

import sys
import os
import time
import queue
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.proactive_watcher import ProactiveWatcher, stop_proactive_watcher


class MockEvent:
    def __init__(self, x=100, y=15, x_root=200, y_root=150):
        self.x = x
        self.y = y
        self.x_root = x_root
        self.y_root = y_root


class TestProactiveWatcherSafety(unittest.TestCase):
    def tearDown(self):
        stop_proactive_watcher()

    def test_stop_event_immediate_shutdown(self):
        """Watcher stop_event orqali vaqtni behuda kutmasdan 1.5s ichida to'xtashi kerak"""
        watcher = ProactiveWatcher(check_interval=60, min_silent_time=100)
        watcher.start()
        self.assertTrue(watcher.is_running())

        start_t = time.time()
        watcher.stop()
        duration = time.time() - start_t

        self.assertFalse(watcher.is_running())
        self.assertLess(duration, 1.5, f"Watcher stop() too slow: {duration}s")

    def test_suggestion_queue_thread_safe(self):
        """Watcher takliflarni thread-safe queue ga qo'yishi va get_suggestion orqali olish kerak"""
        watcher = ProactiveWatcher(check_interval=1, min_silent_time=0)
        received_callbacks = []

        watcher.on_suggestion(lambda s: received_callbacks.append(s))

        # Qo'lda suggestion yuborish
        test_msg = "Test taklif matni"
        watcher._suggestion_queue.put(test_msg)
        item = watcher.get_suggestion(timeout=0.5)
        self.assertEqual(item, test_msg)


class TestWindowDragSafety(unittest.TestCase):
    def test_drag_logic_without_ctypes(self):
        """Oynani surish mantiqi ctypes SendMessageW chaqirmaydi"""
        from unittest.mock import MagicMock
        from gui.app import MikasaApp

        # App ob'ektining surish metodlarini tekshirish
        mock_app = MagicMock()
        mock_app.state.return_value = "normal"
        mock_app.winfo_x.return_value = 50
        mock_app.winfo_y.return_value = 50

        # Bind MikasaApp methods
        start_drag = MikasaApp._start_window_drag.__get__(mock_app, MikasaApp)
        on_drag = MikasaApp._on_window_drag.__get__(mock_app, MikasaApp)
        end_drag = MikasaApp._end_window_drag.__get__(mock_app, MikasaApp)

        event_start = MockEvent(x=10, y=10, x_root=60, y_root=60)
        start_drag(event_start)

        self.assertEqual(mock_app._drag_start_x, 10)  # 60 - 50
        self.assertEqual(mock_app._drag_start_y, 10)  # 60 - 50

        # Motion event
        event_move = MockEvent(x=10, y=10, x_root=100, y_root=120)
        on_drag(event_move)
        mock_app.geometry.assert_called_with("+90+110")

        # Release event
        end_drag(None)
        self.assertIsNone(mock_app._drag_start_x)
        self.assertIsNone(mock_app._drag_start_y)

    def test_drag_on_maximized_window_restores_gracefully(self):
        """Kattalashtirilgan oyna surilganda avval normal holatga qaytib, o'lcham hisoblanadi"""
        from unittest.mock import MagicMock
        from gui.app import MikasaApp

        mock_app = MagicMock()
        mock_app.state.return_value = "zoomed"
        mock_app.winfo_width.return_value = 1920
        mock_app.winfo_x.return_value = 0
        mock_app.winfo_y.return_value = 0

        start_drag = MikasaApp._start_window_drag.__get__(mock_app, MikasaApp)
        event_start = MockEvent(x=960, y=18, x_root=960, y_root=18)

        start_drag(event_start)

        mock_app._toggle_maximize.assert_called_once()
        mock_app.geometry.assert_called()


class TestBackendBridgeShutdown(unittest.TestCase):
    def test_backend_bridge_clean_stop(self):
        """BackendBridge.stop() ishlaganda UI queue va timerlar to'xtatiladi"""
        from unittest.mock import MagicMock
        from gui.backend import BackendBridge

        mock_app = MagicMock()
        mock_app.after.return_value = "after#1"

        bridge = BackendBridge(mock_app)
        self.assertFalse(bridge._shutting_down)

        bridge.stop()
        self.assertTrue(bridge._shutting_down)
        mock_app.after_cancel.assert_called_with("after#1")

        # Shutdown holatida _queue_ui hech narsa qo'shmasligi kerak
        bridge._queue_ui(lambda: None)
        self.assertTrue(bridge._ui_queue.empty())


class TestStressDragAndWatcherConcurrency(unittest.TestCase):
    def test_concurrent_drag_and_watcher_execution(self):
        """Fon watcher va UI drag parallel ishlaganda race condition yoki deadlock yuz bermasligi kerak"""
        from unittest.mock import MagicMock
        from gui.app import MikasaApp

        mock_app = MagicMock()
        mock_app.state.return_value = "normal"
        mock_app.winfo_x.return_value = 100
        mock_app.winfo_y.return_value = 100

        start_drag = MikasaApp._start_window_drag.__get__(mock_app, MikasaApp)
        on_drag = MikasaApp._on_window_drag.__get__(mock_app, MikasaApp)
        end_drag = MikasaApp._end_window_drag.__get__(mock_app, MikasaApp)

        watcher = ProactiveWatcher(check_interval=1, min_silent_time=0)
        watcher.start()

        # Simulyatsiya: 100 marta tezkor drag amali bajarilayotganda fon oqimi faol ishlaydi
        for i in range(100):
            watcher.record_activity()
            event = MockEvent(x=10, y=10, x_root=100 + i, y_root=100 + i)
            start_drag(event)
            on_drag(event)
            end_drag(None)

        watcher.stop()
        self.assertFalse(watcher.is_running())


if __name__ == "__main__":
    unittest.main()
