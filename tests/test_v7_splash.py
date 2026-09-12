# ========== tests/test_v7_splash.py ==========
# Mikasa AI 7.0 — Splash Screen & MikasaOrb Unit Tests

import unittest
import time
import customtkinter as ctk
from gui.icons import VectorIconEngine
from gui.orb import MikasaOrb
from gui.splash import MikasaSplashScreen, MikasaLoadingBar
from gui.app import MikasaApp


class TestV7MikasaOrb(unittest.TestCase):
    """MikasaOrb vizual yadrosi unit testlari"""

    def setUp(self):
        VectorIconEngine.clear_cache()
        self.root = ctk.CTk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        VectorIconEngine.clear_cache()

    def test_orb_initialization_and_states(self):
        """Orb to'g'ri yaratilishi va holatlari tekshiruvi"""
        orb = MikasaOrb(self.root, size=200, state="loading")
        self.root.update()

        self.assertEqual(orb.get_state(), "loading")
        self.assertTrue(orb.canvas.winfo_exists())
        self.assertEqual(orb._size, 200)

        # Holatlarni o'zgartirish
        for state in ["idle", "listening", "thinking", "speaking", "error", "offline", "loading"]:
            orb.set_state(state)
            self.assertEqual(orb.get_state(), state)
            self.root.update()

        # Noma'lum holat berilganda idle ga o'tishi
        orb.set_state("unknown_xyz")
        self.assertEqual(orb.get_state(), "idle")

        orb.stop()
        self.assertFalse(orb._is_active)
        self.assertIsNone(orb._anim_job)

        orb.destroy()

    def test_orb_backward_compatibility_alias(self):
        """AppleSiriOrb = MikasaOrb ekanligi va mavjud kod bilan ishlashi"""
        from gui.components import AppleSiriOrb
        self.assertIs(AppleSiriOrb, MikasaOrb)


class TestV7MikasaLoadingBar(unittest.TestCase):
    """MikasaLoadingBar progress indikatori testlari"""

    def setUp(self):
        VectorIconEngine.clear_cache()
        self.root = ctk.CTk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        VectorIconEngine.clear_cache()

    def test_loading_bar_progress_modes(self):
        bar = MikasaLoadingBar(self.root, width=200, height=2)
        self.root.update()

        self.assertIsNone(bar._progress)
        bar.set_progress(0.45)
        self.assertEqual(bar._progress, 0.45)
        self.root.update()

        bar.set_progress(None)
        self.assertIsNone(bar._progress)

        bar.stop()
        bar.destroy()


class TestV7SplashScreen(unittest.TestCase):
    """MikasaSplashScreen komponenti testlari"""

    def setUp(self):
        VectorIconEngine.clear_cache()
        self.root = ctk.CTk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        VectorIconEngine.clear_cache()

    def test_splash_screen_structure_and_hierarchy(self):
        """Splash ekranning to'liq vizual strukturasi va elementlari"""
        splash = MikasaSplashScreen(self.root)
        splash.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        self.root.update()

        # 1. Top controls (drag area va WindowControls)
        self.assertTrue(hasattr(splash, "top_bar"))
        self.assertTrue(hasattr(splash, "window_controls"))
        self.assertTrue(hasattr(splash, "drag_area"))

        # 2. Markaziy kontent
        self.assertTrue(hasattr(splash, "orb"))
        self.assertIsInstance(splash.orb, MikasaOrb)
        self.assertEqual(splash.orb.get_state(), "loading")

        self.assertTrue(hasattr(splash, "brand_title"))
        self.assertEqual(splash.brand_title.cget("text"), "MIKASA AI")

        self.assertTrue(hasattr(splash, "subtitle"))
        self.assertEqual(splash.subtitle.cget("text"), "Sizning shaxsiy AI yordamchingiz")

        self.assertTrue(hasattr(splash, "progress_bar"))
        self.assertTrue(hasattr(splash, "status_label"))

        # 3. Status matnini yangilash
        splash.set_status("AI tizimi tekshirilmoqda...", 0.4)
        self.assertEqual(splash.status_label.cget("text"), "AI tizimi tekshirilmoqda...")
        self.assertEqual(splash.progress_bar._progress, 0.4)

        # 4. Xatolik holati
        splash.set_error("Internet bilan aloqa yo'q")
        self.assertEqual(splash.orb.get_state(), "error")
        self.assertEqual(splash.error_frame.winfo_manager(), "pack")
        self.assertIn("Internet", splash.error_detail.cget("text"))

        splash.destroy()

    def test_splash_fade_out_and_destroy(self):
        """Splash ekranning silliq so'nishi va tozalanishi"""
        splash = MikasaSplashScreen(self.root)
        splash.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        self.root.update()

        completed = []
        splash.fade_out_and_destroy(on_complete=lambda: completed.append(True))

        for _ in range(15):
            self.root.update()
            time.sleep(0.03)

        self.assertTrue(completed[0])
        self.assertFalse(splash.winfo_exists())


class TestV7MikasaAppStartupIntegration(unittest.TestCase):
    """MikasaApp bilan Splash integratsiyasi testlari"""

    def setUp(self):
        VectorIconEngine.clear_cache()

    def tearDown(self):
        VectorIconEngine.clear_cache()

    def test_app_with_splash_startup(self):
        """App splash bilan ishga tushishi va keyin asosiy oynaga o'tishi"""
        app = MikasaApp(connect_backend=False, show_splash=True)
        app.withdraw()
        app.update()

        # Splash birinchi kadrda mavjud
        self.assertIsNotNone(app.splash)
        self.assertTrue(app.splash.winfo_exists())
        self.assertEqual(app.splash.brand_title.cget("text"), "MIKASA AI")

        # Asosiy shell ham tayyor bo'lib turadi
        self.assertTrue(hasattr(app, "titlebar"))
        self.assertTrue(hasattr(app, "sidebar_frame"))
        self.assertTrue(hasattr(app, "account_row"))

        # Backend progress xabari
        app.on_init_progress("Modullar yuklanmoqda...", 0.7)
        self.assertEqual(app.splash.status_label.cget("text"), "Modullar yuklanmoqda...")

        # Backend ready chaqirilganda
        app.on_backend_ready()

        # O'tish davrini kutish (event loop timerlarini aylantirish)
        for _ in range(15):
            app.update()
            time.sleep(0.03)

        # Splash xavfsiz tozalangan
        self.assertIsNone(app.splash)

        app._on_closing()

    def test_app_without_splash(self):
        """show_splash=False berilganda to'g'ridan-to'g'ri asosiy oyna ochilishi"""
        app = MikasaApp(connect_backend=False, show_splash=False)
        app.withdraw()
        app.update()

        self.assertIsNone(app.splash)
        self.assertTrue(hasattr(app, "titlebar"))
        self.assertTrue(hasattr(app, "account_row"))

        app._on_closing()


if __name__ == "__main__":
    unittest.main()
