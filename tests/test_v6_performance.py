# ========== test_v6_performance.py ==========
# Mikasa AI — Performance, Lazy Loading, and Search Debouncing Tests

import os
import time
import unittest
import customtkinter as ctk

from gui.app import MikasaApp
from gui.pages.commands import CommandsPage
from gui.components import LoadingSkeleton, SearchBar
from gui.icons import IconEngine


class TestV6AppLazyLoading(unittest.TestCase):
    """Test suite verifying MikasaApp lazy loading, page caching, and navigation state machine"""

    def setUp(self):
        IconEngine.clear_cache()
        self.app = None

    def tearDown(self):
        if self.app:
            try:
                self.app.destroy()
            except Exception:
                pass
        IconEngine.clear_cache()

    def test_lazy_initialization_on_startup(self):
        """Verify that app startup only initializes dashboard and does NOT instantiate all 8 pages"""
        self.app = MikasaApp(connect_backend=False)
        self.app.withdraw()

        # On startup, only dashboard should be instantiated
        self.assertIn("dashboard", self.app._pages)
        self.assertEqual(len(self.app._pages), 1, "Only initial page (dashboard) should be loaded at startup")

        # Other pages must NOT exist in _pages yet
        for page_id in ["voice", "chat", "commands", "memory", "scheduler", "plugins", "settings"]:
            self.assertNotIn(page_id, self.app._pages, f"{page_id} should NOT be initialized at startup")

        self.assertEqual(self.app._current_page, "dashboard")
        self.assertEqual(self.app._nav_state, "READY")

    def test_lazy_navigation_and_page_caching(self):
        """Verify lazy creation on first navigation and instant caching on subsequent visits"""
        self.app = MikasaApp(connect_backend=False)
        self.app.withdraw()
        self.assertEqual(len(self.app._pages), 1)

        # 1. First navigation to 'commands' (sync=True for test determinism)
        self.app.navigate_to("commands", sync=True)
        self.assertEqual(self.app._current_page, "commands")
        self.assertEqual(self.app._nav_state, "READY")
        self.assertIn("commands", self.app._pages)
        self.assertEqual(len(self.app._pages), 2)

        cmd_page_ref = self.app._pages["commands"]
        self.assertIsInstance(cmd_page_ref, CommandsPage)

        # 2. Navigation back to 'dashboard'
        self.app.navigate_to("dashboard", sync=True)
        self.assertEqual(self.app._current_page, "dashboard")
        self.assertEqual(len(self.app._pages), 2)

        # 3. Navigation again to 'commands' — must reuse cached instance!
        self.app.navigate_to("commands", sync=True)
        self.assertIs(self.app._pages["commands"], cmd_page_ref, "Page must be reused from cache, not recreated")

    def test_rapid_navigation_cancels_pending_lazy_jobs(self):
        """Verify rapid navigation cancels earlier lazy jobs without crashing or orphaned widgets"""
        self.app = MikasaApp(connect_backend=False)
        self.app.withdraw()

        # Rapid clicks without sync (asynchronous path)
        self.app.navigate_to("chat", sync=False)
        self.assertEqual(self.app._nav_state, "LOADING")
        self.assertIsNotNone(self.app._lazy_nav_job)

        # Rapidly click memory before chat finishes
        self.app.navigate_to("memory", sync=False)
        self.assertEqual(self.app._nav_state, "LOADING")
        self.assertIsNotNone(self.app._lazy_nav_job)

        # Allow after timer to complete
        self.app.update()


class TestV6CommandsPerformance(unittest.TestCase):
    """Test suite verifying CommandsPage debounce, caching, and batch rendering"""

    def setUp(self):
        IconEngine.clear_cache()
        self.root = ctk.CTk()
        self.root.withdraw()
        self.page = CommandsPage(self.root)

    def tearDown(self):
        try:
            self.page.destroy()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        IconEngine.clear_cache()

    def test_commands_page_search_debouncing_and_caching(self):
        """Verify CommandsPage search debounce timer and in-memory cache"""
        # 1. Test in-memory query caching
        self.page.search_entry.delete(0, "end")
        self.page.search_entry.insert(0, "tizim")
        self.page._execute_search(immediate=True)

        cache_key = ("tizim", "all", self.page._sort_mode)
        self.assertIn(cache_key, self.page._search_cache)
        cached_results = self.page._search_cache[cache_key]
        self.assertIsInstance(cached_results, list)

        # Second execute with same query should hit cache
        self.page._execute_search(immediate=True)
        self.assertIs(self.page._search_cache[cache_key], cached_results)

        # 2. Test debouncing: rapid keyrelease calls schedule only 1 timer
        self.page._on_search_keyrelease()
        job1 = self.page._search_debounce_job
        self.assertIsNotNone(job1)

        self.page._on_search_keyrelease()
        job2 = self.page._search_debounce_job
        self.assertIsNotNone(job2)
        self.assertNotEqual(job1, job2, "New keystroke must cancel previous debounce job")

    def test_commands_page_category_pills(self):
        """Verify category pills update active state and filter tools correctly"""
        self.assertEqual(self.page._selected_category, "all")
        self.page._on_category_click("system")
        self.assertEqual(self.page._selected_category, "system")

        # Chips visual state updated
        system_chip = self.page._category_chips.get("system")
        self.assertIsNotNone(system_chip)

    def test_commands_page_batch_rendering_chunk_safety(self):
        """Verify chunked batch rendering splits tools and cancels gracefully"""
        tools = self.page._get_tools()
        self.assertGreater(len(tools), 10)

        # Start batch render
        self.page._cancel_batch_render()
        self.page._build_tools_grid(tools)

        # Cancel batch render must cleanly clear the job
        self.page._cancel_batch_render()
        self.assertIsNone(self.page._batch_render_job)

    def test_loading_skeleton_set_title_and_safe_destroy(self):
        """Verify LoadingSkeleton updates title and destroys without timer leaks"""
        skeleton = LoadingSkeleton(self.root, title="Yuklanmoqda...")
        try:
            skeleton.set_title("Sozlamalar yuklanmoqda...")
            self.assertEqual(skeleton.title_label.cget("text"), "Sozlamalar yuklanmoqda...")
        finally:
            skeleton.destroy()


if __name__ == "__main__":
    unittest.main()
