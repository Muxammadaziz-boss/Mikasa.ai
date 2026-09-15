# ========== tests/test_v7_landing.py ==========
# Mikasa AI 7.0 — Landing Page & Startup Flow Tests

import unittest
import customtkinter as ctk
from gui.app import MikasaApp
from gui.pages.landing import LandingPage, QuickActionCard
from gui.orb import MikasaOrb
from gui.icons import VectorIconEngine


class TestLandingPageComponents(unittest.TestCase):
    """LandingPage komponentlari va arxitekturasi testi"""

    def setUp(self):
        self.root = ctk.CTk()
        self.root.geometry("1280x800")
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        VectorIconEngine.clear_cache()

    def test_landing_page_creation(self):
        page = LandingPage(self.root, app=None)
        page.pack(fill="both", expand=True)
        self.root.update_idletasks()

        # 1. Markaziy AI Orb mavjudligi va holati
        self.assertTrue(hasattr(page, "orb"))
        self.assertIsInstance(page.orb, MikasaOrb)
        self.assertEqual(page.orb.get_state(), "idle")

        # 2. Salomlashuv va foydalanuvchi ismi
        self.assertTrue(hasattr(page, "greeting_label"))
        self.assertIn("Salom", page.greeting_label.cget("text"))
        self.assertTrue(hasattr(page, "sub_greeting"))
        self.assertEqual(page.sub_greeting.cget("text"), "Qanday yordam beray?")

        # 3. Haqiqiy holat indikatori (Online/Offline)
        self.assertTrue(hasattr(page, "status_text"))
        self.assertIn(page.status_text.cget("text"), ["Online", "Offline"])

        # 4. Primary Voice Action ("Tinglashni boshlash")
        self.assertTrue(hasattr(page, "primary_voice_btn"))
        self.assertIn("Tinglashni boshlash", page.primary_voice_btn.cget("text"))

        # 5. Qo'shimcha amallar: Tozalash va Chat
        self.assertTrue(hasattr(page, "clear_btn"))
        self.assertEqual(page.clear_btn.cget("text"), "Tozalash")
        self.assertTrue(hasattr(page, "chat_btn"))
        self.assertIn("Chat", page.chat_btn.cget("text"))

        # 6. 3 ta taklif kartochkasi (Quick actions)
        self.assertTrue(hasattr(page, "card_ask"))
        self.assertTrue(hasattr(page, "card_command"))
        self.assertTrue(hasattr(page, "card_summary"))
        self.assertIsInstance(page.card_ask, QuickActionCard)
        self.assertIsInstance(page.card_command, QuickActionCard)
        self.assertIsInstance(page.card_summary, QuickActionCard)

        # 7. Ixcham kompozitor (Composer)
        self.assertTrue(hasattr(page, "input_entry"))
        self.assertEqual(page.input_entry.cget("placeholder_text"), "Nima yordam kerak?")
        self.assertTrue(hasattr(page, "attach_btn"))
        self.assertTrue(hasattr(page, "action_btn"))

        # Tozalash
        page.destroy()

    def test_composer_typing_and_clearing(self):
        page = LandingPage(self.root, app=None)
        page.pack()
        self.root.update_idletasks()

        # Bo'sh holatda action_btn mic bo'ladi
        self.assertEqual(page._action_mode, "mic")

        # Matn kiritilganda action_btn send rejimiga o'tadi
        page._input_var.set("Salom Mikasa")
        self.assertEqual(page._action_mode, "send")

        # Tozalash tugmasi bosilganda
        page._on_clear_composer()
        self.assertEqual(page._input_var.get(), "")
        self.assertEqual(page._action_mode, "mic")

        page.destroy()

    def test_landing_lifecycle(self):
        page = LandingPage(self.root, app=None)
        page.pack()
        self.root.update_idletasks()

        # on_show va on_hide chaqiruvlari xatosiz ishlashi
        page.on_show()
        self.assertTrue(page.orb._is_active)

        page.on_hide()
        self.assertFalse(page.orb._is_active)

        # destroy xatosiz yakunlanishi
        page.destroy()


class TestStartupLandingFlow(unittest.TestCase):
    """MikasaApp startap va landing oqimi integratsiya testi"""

    def setUp(self):
        VectorIconEngine.clear_cache()

    def tearDown(self):
        VectorIconEngine.clear_cache()

    def test_startup_default_page_is_home(self):
        # Splash siz yaratish
        app = MikasaApp(connect_backend=False, show_splash=False)
        app.update()

        # 1. Startapda joriy sahifa home/landing bo'lishi kerak, voice EMAS
        self.assertEqual(app._current_page, "home")
        self.assertNotEqual(app._current_page, "voice")

        # 2. Sidebar navigatsiyasida "home" faol, "voice" esa nofaol
        self.assertIn("home", app._nav_items)
        self.assertIn("voice", app._nav_items)
        self.assertTrue(app._nav_items["home"]._active)
        self.assertFalse(app._nav_items["voice"]._active)

        # 3. Sahifa instansi LandingPage bo'lishi kerak
        home_page = app._pages.get("home")
        self.assertIsInstance(home_page, LandingPage)

        app._on_closing()

    def test_landing_primary_voice_navigation(self):
        app = MikasaApp(connect_backend=False, show_splash=False)
        app.update()

        home_page = app._pages.get("home")
        self.assertIsNotNone(home_page)

        # "Tinglashni boshlash" tugmasi bosilganda voice sahifasiga o'tadi
        home_page._on_primary_voice()
        app.update()

        self.assertEqual(app._current_page, "voice")
        self.assertFalse(app._nav_items["home"]._active)
        self.assertTrue(app._nav_items["voice"]._active)

        app._on_closing()

    def test_landing_chat_navigation(self):
        app = MikasaApp(connect_backend=False, show_splash=False)
        app.update()

        home_page = app._pages.get("home")
        self.assertIsNotNone(home_page)

        # "Chat" tugmasi bosilganda chat sahifasiga o'tadi
        home_page._on_open_chat()
        app.update()

        self.assertEqual(app._current_page, "chat")
        self.assertFalse(app._nav_items["home"]._active)
        self.assertTrue(app._nav_items["chat"]._active)

        app._on_closing()

    def test_landing_composer_submits_to_chat(self):
        app = MikasaApp(connect_backend=False, show_splash=False)
        app.update()

        home_page = app._pages.get("home")
        self.assertIsNotNone(home_page)

        # Kompozitorga matn yozib Enter bosilganda
        home_page._input_var.set("Menga ob-havoni aytib ber")
        home_page._on_submit_composer()
        app.update()

        # Chat sahifasiga o'tgan bo'lishi kerak
        self.assertEqual(app._current_page, "chat")
        chat_page = app._pages.get("chat")
        self.assertIsNotNone(chat_page)

        # Chat sahifasiga oxirgi user xabari qo'shilgan bo'lishi kerak
        self.assertEqual(chat_page._last_user_text, "Menga ob-havoni aytib ber")

        app._on_closing()


if __name__ == "__main__":
    unittest.main()
