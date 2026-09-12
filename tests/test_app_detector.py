# ========== test_app_detector.py ==========
# Mikasa AI 7.x — WindowsAppDetector va Chuqur Inventarizatsiya Testlari

import unittest
from core.app_detector import WindowsAppDetector, AppInfo, get_app_detector
from core.command_dispatcher import CommandDispatcher, find_installed_app, get_system_specs_summary
from core.agent_tools import get_registry


class TestWindowsAppDetector(unittest.TestCase):
    """WindowsAppDetector testlari"""

    def setUp(self):
        self.detector = WindowsAppDetector(cache_ttl=5.0)

    def test_singleton(self):
        """get_app_detector() singleton nusxa qaytaradi"""
        d1 = get_app_detector()
        d2 = get_app_detector()
        self.assertIs(d1, d2)
        self.assertIsInstance(d1, WindowsAppDetector)

    def test_app_info_to_dict(self):
        """AppInfo obyekti to'g'ri dict ga aylanadi"""
        info = AppInfo(
            found=True,
            running=True,
            name="Test App",
            canonical_name="testapp",
            family="test",
            exe_path="C:\\test.exe",
            pid=1234
        )
        d = info.to_dict()
        self.assertTrue(d["found"])
        self.assertTrue(d["running"])
        self.assertEqual(d["name"], "Test App")
        self.assertEqual(d["canonical_name"], "testapp")
        self.assertEqual(d["family"], "test")
        self.assertEqual(d["exe_path"], "C:\\test.exe")
        self.assertEqual(d["pid"], 1234)

    def test_uzbek_response_formatting(self):
        """O'zbekcha javoblar rostgo'y va aniq tuziladi"""
        # Telegram client (AyuGram)
        info_ayu = AppInfo(
            found=True,
            running=True,
            name="AyuGram Desktop (Telegram mijozi)",
            canonical_name="ayugram",
            family="telegram"
        )
        resp_tg = info_ayu.format_uzbek_response("telegram")
        self.assertIn("AyuGram Desktop", resp_tg)
        self.assertIn("Telegram mijozi", resp_tg)
        self.assertIn("ishlab turibdi", resp_tg)

        # Topilmagan ilova
        info_none = AppInfo(found=False, name="RandomNonexistentApp")
        resp_none = info_none.format_uzbek_response("RandomNonexistentApp")
        self.assertIn("topilmadi", resp_none)
        self.assertIn("o'rnatilmagan", resp_none)

    def test_realtime_system_specs(self):
        """Haqiqiy apparat parametrlari xatoliksiz va to'liq shakllanadi"""
        specs = self.detector.get_realtime_system_specs()
        self.assertIsInstance(specs, str)
        self.assertIn("Operatsion tizim:", specs)
        self.assertIn("Protsessor (CPU):", specs)
        self.assertIn("Videokarta (GPU):", specs)
        self.assertIn("Tezkor xotira (RAM):", specs)
        self.assertIn("Disklar:", specs)

    def test_realtime_inventory_summary(self):
        """Inventarizatsiya xulosasi ro'yxat qaytaradi va duplikatlardan holi"""
        summary = self.detector.get_realtime_inventory_summary()
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)
        lines = [line.strip() for line in summary.split("\n") if line.strip()]
        self.assertEqual(len(lines), len(set(lines)), "Inventarda duplikat bo'lmasligi kerak")

    def test_telegram_ayugram_detection(self):
        """Telegram yoki AyuGram aniqlanganda kamida bittasi topilgan bo'lishi kerak"""
        info_tg = self.detector.detect_app("telegram")
        self.assertTrue(info_tg.found)
        self.assertTrue(len(info_tg.exe_path) > 0 or info_tg.running)

        info_ayu = self.detector.detect_app("ayugram")
        self.assertTrue(info_ayu.found)

    def test_command_dispatcher_integration(self):
        """CommandDispatcher bilan integratsiya to'g'ri ishlaydi"""
        cd = CommandDispatcher()

        # 1. Telegram so'rovi
        handled, resp = cd.dispatch_local("menda telegram bormi?")
        self.assertTrue(handled)
        self.assertTrue("AyuGram" in resp or "Telegram" in resp)

        # 2. Mavjud bo'lmagan ilova
        handled_fake, resp_fake = cd.dispatch_local("menda photoshop bormi?")
        if handled_fake:
            self.assertIn("topilmadi", resp_fake)

        # 3. Kompyuter parametrlari
        handled_pc, resp_pc = cd.dispatch_local("kompyuterim parametrlari")
        self.assertTrue(handled_pc)
        self.assertIn("Kompyuteringiz parametrlari:", resp_pc)
        self.assertIn("Protsessor (CPU):", resp_pc)

    def test_agent_tools_app_check(self):
        """ToolRegistry dagi app_check to'liq integratsiyalangan"""
        reg = get_registry()
        res = reg.call("app_check", app_name="telegram")
        self.assertTrue(res.get("success"))
        result = res.get("result", {})
        self.assertTrue(result.get("found"))
        self.assertEqual(result.get("family"), "telegram")


if __name__ == "__main__":
    unittest.main()
