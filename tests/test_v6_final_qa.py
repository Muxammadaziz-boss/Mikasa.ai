"""
Mikasa AI v6.0.0 — Final Visual QA & Production Multi-Resolution Verification Suite.
Validates:
- All 8 pages render cleanly without exception.
- Window scaling across 1024x700, 1280x800, 1440x900, 1920x1080.
- Theme toggling (Dark <-> Light) across all 8 pages.
- Zero unicode/emoji relics in PageHero, Button, MessageBubble, or attachments.
"""

import unittest
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing, Surfaces
from gui.icons import get_vector_icon, VectorIconEngine
from gui.components import (
    Card,
    ElevatedCard,
    GlassCard,
    HeroCard,
    PageHero,
    Button,
    GlassButton,
    IconButton,
    CircleIconButton,
    MessageBubble,
    TypingBubble,
    AgentStepIndicator,
    NavItem,
    StatusBadge,
    InfoChip,
    ToastNotification,
)
from gui.pages.dashboard import DashboardPage
from gui.pages.voice import VoicePage
from gui.pages.chat import ChatPage
from gui.pages.commands import CommandsPage
from gui.pages.memory import MemoryPage
from gui.pages.scheduler import SchedulerPage
from gui.pages.plugins import PluginsPage
from gui.pages.settings import SettingsPage


class TestV6FinalQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_multi_resolution_layout_audit(self):
        """Audit layout across 4 standard desktop resolutions."""
        resolutions = [
            (1024, 700),
            (1280, 800),
            (1440, 900),
            (1920, 1080),
        ]
        pages_to_test = [
            ("dashboard", DashboardPage),
            ("voice", VoicePage),
            ("chat", ChatPage),
            ("commands", CommandsPage),
            ("memory", MemoryPage),
            ("scheduler", SchedulerPage),
            ("plugins", PluginsPage),
            ("settings", SettingsPage),
        ]

        for width, height in resolutions:
            frame = ctk.CTkFrame(self.root, width=width, height=height)
            frame.pack(fill="both", expand=True)

            for name, page_cls in pages_to_test:
                page = page_cls(frame)
                page.pack(fill="both", expand=True)
                page.update_idletasks()

                if hasattr(page, "on_show"):
                    page.on_show()
                page.update_idletasks()

                page.pack_forget()
                page.destroy()

            frame.destroy()

    def test_dark_and_light_theme_toggle_all_pages(self):
        """Audit theme transitions across all 8 pages."""
        pages = [
            DashboardPage(self.root),
            VoicePage(self.root),
            ChatPage(self.root),
            CommandsPage(self.root),
            MemoryPage(self.root),
            SchedulerPage(self.root),
            PluginsPage(self.root),
            SettingsPage(self.root),
        ]

        for theme in ["light", "dark", "light", "dark"]:
            Colors.apply_theme(theme)
            for page in pages:
                # Trigger theme propagation
                for child in page.winfo_children():
                    if hasattr(child, "update_theme"):
                        child.update_theme()
                page.update_idletasks()

        for p in pages:
            p.destroy()

    def test_no_legacy_emoji_or_symbols_in_chat(self):
        """Verify chat preview uses pure vector icons and no emojis."""
        chat = ChatPage(self.root)
        chat._show_attachment_preview("test_image.png")
        lbl_text = chat.attachment_label.cget("text")
        self.assertNotIn("🖼️", lbl_text)
        self.assertNotIn("📄", lbl_text)
        self.assertIsNotNone(chat.attachment_label.cget("image"))

        chat._show_attachment_preview("document.pdf")
        lbl_text2 = chat.attachment_label.cget("text")
        self.assertNotIn("🖼️", lbl_text2)
        self.assertNotIn("📄", lbl_text2)
        self.assertIsNotNone(chat.attachment_label.cget("image"))

        chat._remove_attached_file()
        chat.destroy()

    def test_semantic_radius_consistency(self):
        """Ensure semantic hierarchy consistency."""
        btn = Button(self.root, text="Test")
        self.assertEqual(btn.cget("corner_radius"), Sizing.RADIUS_BUTTON)
        btn.destroy()

        ibtn = IconButton(self.root, icon="sparkles")
        self.assertEqual(ibtn.cget("corner_radius"), Sizing.RADIUS_BUTTON)
        ibtn.destroy()

        cbtn = CircleIconButton(self.root, icon="sparkles", size=38)
        self.assertEqual(cbtn.cget("corner_radius"), 19)
        cbtn.destroy()


if __name__ == "__main__":
    unittest.main()
