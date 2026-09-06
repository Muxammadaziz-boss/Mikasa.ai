# ========== test_v6_window_chrome.py ==========
# Mikasa AI — Custom Premium Window Chrome & WindowControls Tests

import unittest
import customtkinter as ctk
from gui.icons import get_vector_icon, VectorIconEngine
from gui.components import WindowControls
from gui.app import MikasaApp


class TestV6WindowChrome(unittest.TestCase):
    def setUp(self):
        VectorIconEngine.clear_cache()
        self.root = ctk.CTk()
        self.root.geometry("600x400")

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        VectorIconEngine.clear_cache()

    def test_window_control_vector_icons(self):
        """Barcha oyna boshqaruv vektor ikonkalari mavjudligi va chizilishi"""
        for icon_name in ("minimize", "maximize", "restore", "close"):
            img = get_vector_icon(icon_name, size=14)
            self.assertIsNotNone(img, f"Ikonka topilmadi: {icon_name}")
            self.assertIsInstance(img, ctk.CTkImage)

        # Semantik aliaslar tekshiruvi
        for alias, target in [
            ("win_min", "minimize"),
            ("win_max", "maximize"),
            ("win_restore", "restore"),
            ("win_close", "close"),
        ]:
            resolved = VectorIconEngine.resolve_icon_name(alias)
            self.assertEqual(resolved, target)

    def test_window_controls_component(self):
        """WindowControls komponenti, tugmalari va o'lchamlari"""
        wc = WindowControls(self.root, height=36, btn_width=44)
        wc.pack()
        self.root.update()

        self.assertTrue(hasattr(wc, "min_btn"))
        self.assertTrue(hasattr(wc, "max_btn"))
        self.assertTrue(hasattr(wc, "close_btn"))

        # O'lchamlar va radius
        self.assertEqual(wc.min_btn.cget("width"), 44)
        self.assertEqual(wc.max_btn.cget("width"), 44)
        self.assertEqual(wc.close_btn.cget("width"), 44)
        self.assertEqual(wc.min_btn.cget("corner_radius"), 0)
        self.assertEqual(wc.close_btn.cget("hover_color"), "#DC2626")

        # Maximize/Restore holat sinxronizatsiyasi
        wc.sync_maximized_state(True)
        self.assertTrue(wc._is_maximized)
        self.assertEqual(wc.max_tooltip.text, "Tiklash")

        wc.sync_maximized_state(False)
        self.assertFalse(wc._is_maximized)
        self.assertEqual(wc.max_tooltip.text, "Kattalashtirish")

        wc.destroy()

    def test_mikasa_app_custom_chrome_integration(self):
        """MikasaApp bilan Custom Window Chrome integratsiyasi"""
        try:
            self.root.destroy()
        except Exception:
            pass
        VectorIconEngine.clear_cache()

        app = MikasaApp(connect_backend=False)
        app.update()

        # 1. Title "MIKASA AI" (build versiyasiz)
        self.assertEqual(app.title(), "MIKASA AI")

        # 2. Window controls mavjudligi
        self.assertTrue(hasattr(app, "window_controls"))
        self.assertIsInstance(app.window_controls, WindowControls)

        # 3. Maximize toggle va state sync
        app._toggle_maximize()
        app.update()
        self.assertEqual(app.state(), "zoomed")
        self.assertTrue(app.window_controls._is_maximized)

        app._toggle_maximize()
        app.update()
        self.assertEqual(app.state(), "normal")
        self.assertFalse(app.window_controls._is_maximized)

        # 4. Drag va double-click handlerlari mavjudligi va xatoliksiz ishlashi
        class MockEvent:
            x_root = 100
            y_root = 100

        # Drag start chaqiruvi
        app._start_window_drag(MockEvent())

        # 5. Toza yopish
        app._on_closing()


if __name__ == "__main__":
    unittest.main()
