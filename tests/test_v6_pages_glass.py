# ========== test_v6_pages_glass.py ==========
# Mikasa AI v6.0.0 — Barcha sahifalardagi Glass tugmalar va navigatsiya testi

import unittest
import customtkinter as ctk

from gui.theme import Colors
from gui.components import GlassButton, CircleIconButton, GlowButton, SecondaryButton
from gui.pages.dashboard import DashboardPage
from gui.pages.voice import VoicePage
from gui.pages.chat import ChatPage
from gui.pages.commands import CommandsPage
from gui.pages.memory import MemoryPage
from gui.pages.scheduler import SchedulerPage
from gui.pages.plugins import PluginsPage
from gui.pages.settings import SettingsPage


class TestV6AllPagesGlassButtons(unittest.TestCase):
    """Barcha sahifalarda Glass dizayni va tugmalar ishlashini tekshirish"""

    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        cls.root.withdraw()
        cls.container = ctk.CTkFrame(cls.root)
        cls.container.pack(fill="both", expand=True)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_dashboard_buttons(self):
        page = DashboardPage(self.container)
        page.pack(fill="both", expand=True)
        self.root.update()

        def find_buttons(widget):
            btns = []
            for child in widget.winfo_children():
                if isinstance(child, (GlassButton, GlowButton)):
                    btns.append(child)
                btns.extend(find_buttons(child))
            return btns

        all_btns = find_buttons(page)
        self.assertGreaterEqual(len(all_btns), 6, "Dashboardda kamida 6 ta quick action tugmasi bo'lishi kerak")
        
        hero_btns = [b for b in all_btns if isinstance(b, GlowButton)]
        glass_btns = [b for b in all_btns if isinstance(b, GlassButton)]
        self.assertGreaterEqual(len(hero_btns), 1)
        self.assertGreaterEqual(len(glass_btns), 5)

        page.pack_forget()
        page.destroy()

    def test_voice_page_mic_button(self):
        page = VoicePage(self.container)
        page.pack(fill="both", expand=True)
        self.root.update()

        self.assertEqual(page.mic_btn.cget("border_width"), 2)
        self.assertEqual(page.mic_btn.cget("border_color"), Colors.GLASS_HERO_BORDER)
        self.assertEqual(page.mic_btn.cget("corner_radius"), 28)

        page.pack_forget()
        page.destroy()

    def test_chat_page_buttons(self):
        page = ChatPage(self.container)
        page.pack(fill="both", expand=True)
        self.root.update()

        self.assertIsInstance(page.attach_btn, CircleIconButton)
        self.assertIsInstance(page.action_btn, CircleIconButton)
        self.assertEqual(page.attach_btn.cget("border_width"), 1)
        self.assertEqual(page.action_btn.cget("border_width"), 1)

        page.pack_forget()
        page.destroy()

    def test_commands_page_buttons(self):
        page = CommandsPage(self.container)
        page.pack(fill="both", expand=True)
        self.root.update()

        page._build_tools_grid([
            {"name": "test_tool", "description": "Tavsif", "category": "utility", "icon": "🔧", "color": "#30D158"}
        ])
        self.root.update()

        def find_buttons(widget):
            btns = []
            for child in widget.winfo_children():
                if isinstance(child, (GlassButton, GlowButton, SecondaryButton)):
                    btns.append(child)
                btns.extend(find_buttons(child))
            return btns

        btns = find_buttons(page)
        self.assertGreaterEqual(len(btns), 1)
        self.assertEqual(btns[0].cget("text"), "→  Foydalanish")

        page.pack_forget()
        page.destroy()

    def test_scheduler_page_buttons(self):
        page = SchedulerPage(self.container)
        page.pack(fill="both", expand=True)
        self.root.update()

        from unittest.mock import MagicMock
        page.app = MagicMock()
        page.app.bridge.get_scheduler_tasks.return_value = [{
            "id": "task_1",
            "type": "reminder",
            "data": "Eslatma sinovi",
            "execution_time": 9999999999,
            "recurring": False,
        }]
        page._refresh_task_list()
        self.root.update()

        def find_buttons(widget):
            btns = []
            for child in widget.winfo_children():
                if isinstance(child, (GlassButton, GlowButton, SecondaryButton)):
                    btns.append(child)
                btns.extend(find_buttons(child))
            return btns

        btns = find_buttons(page)
        self.assertGreaterEqual(len(btns), 1)
        cancel_btns = [b for b in btns if "Bekor qilish" in b.cget("text")]
        self.assertGreaterEqual(len(cancel_btns), 1)
        self.assertEqual(cancel_btns[0].cget("text"), "🗑️  Bekor qilish")

        page.pack_forget()
        page.destroy()

    def test_settings_page_buttons(self):
        page = SettingsPage(self.container)
        page.pack(fill="both", expand=True)
        self.root.update()

        self.assertIsInstance(page.save_btn, GlowButton)
        self.assertEqual(page.save_btn.cget("border_width"), 1)
        self.assertEqual(page.save_btn.cget("border_color"), Colors.GLASS_HERO_BORDER)

        page.pack_forget()
        page.destroy()

    def test_memory_and_plugins_page(self):
        m_page = MemoryPage(self.container)
        m_page.pack(fill="both", expand=True)
        self.root.update()
        self.assertIsInstance(m_page.profile_save_btn, GlowButton)
        m_page.pack_forget()
        m_page.destroy()

        p_page = PluginsPage(self.container)
        p_page.pack(fill="both", expand=True)
        self.root.update()
        p_page.pack_forget()
        p_page.destroy()


if __name__ == "__main__":
    unittest.main()
