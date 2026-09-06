# ========== test_v6_chat_ux.py ==========
# Mikasa AI v6.0.0 — Chat UX Critical Fix & Activity Collapsing Testlari

import unittest
import customtkinter as ctk

from gui.theme import Colors, Fonts
from gui.pages.chat import ChatPage, AgentActivityGroup


class TestV6ChatUXCriticalFix(unittest.TestCase):
    """Chat UX tanqidiy tuzatishlar tekshiruvi"""

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

    def test_thought_is_never_rendered_as_message_bubble(self):
        page = ChatPage(self.root)

        # 1. Thought yuborilganda xabarlar ro'yxatiga qo'shilmasligi va kartochka chizilmasligi kerak
        initial_child_count = len(page.chat_scroll.winfo_children())
        page.add_agent_step(1, "thought", "Ichki maxfiy reja va mulohazalar...")

        # _messages bo'sh qolishi shart
        self.assertEqual(len(page._messages), 0)

        # Chat scroll ichida thought matni bo'lgan hech qanday label bo'lmasligi kerak
        for widget in page.chat_scroll.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                self.assertNotIn("Ichki maxfiy reja", widget.cget("text"))

        page.destroy()

    def test_action_renders_compact_inline_activity_group(self):
        page = ChatPage(self.root)

        # 1. Action kelganda AgentActivityGroup yaratilishi kerak
        page.add_agent_step("Asbob", "action", "'app_check': Chrome topildi")

        self.assertIsNotNone(page._active_activity_group)
        self.assertIsInstance(page._active_activity_group, AgentActivityGroup)

        # 2. Faoliyat ichida tool nomi va 'ishlatilmoqda' yoki 'bajarildi' ko'rinishi
        self.assertEqual(len(page._active_activity_group._actions), 1)
        self.assertEqual(page._active_activity_group._actions[0]["tool"], "app_check")

        # 3. Ikkinchi tool qo'shilganda yangi ulkan kartochka emas, mavjud guruhga ixcham qo'shilishi
        page.add_agent_step("Asbob", "action", "'system_info': CPU 12%")
        self.assertEqual(len(page._active_activity_group._actions), 2)
        self.assertEqual(page._active_activity_group._actions[1]["tool"], "system_info")

        # 4. Final step kelganda 'Yakun: Final' kartochkasi chizilmasdan guruh yakunlanishi kerak
        page.add_agent_step("Yakun", "final", "Tayyor")
        self.assertTrue(page._active_activity_group is None or page._active_activity_group._is_finished)

        # Final xabar oddiy assistant add_message orqali keladi
        page.add_message("Mana natija", "assistant")
        self.assertEqual(len(page._messages), 1)
        self.assertEqual(page._messages[0]["text"], "Mana natija")

        page.destroy()

    def test_activity_group_batafsil_toggle(self):
        page = ChatPage(self.root)
        page.add_agent_step("Asbob", "action", "'app_check': Chrome muvaffaqiyatli ishlayapti")

        group = page._active_activity_group
        self.assertIsNotNone(group.toggle_btn)
        self.assertEqual(group.toggle_btn.cget("text"), "Batafsil")
        self.assertTrue(group._is_collapsed)

        # Ochish
        group._toggle_details()
        self.assertFalse(group._is_collapsed)
        self.assertEqual(group.toggle_btn.cget("text"), "Yopish")

        # Yopish
        group._toggle_details()
        self.assertTrue(group._is_collapsed)
        self.assertEqual(group.toggle_btn.cget("text"), "Batafsil")

        page.destroy()

    def test_centered_conversation_column_resize(self):
        page = ChatPage(self.root)

        # 1600px kenglik: target column width 960px, padx = (1600 - 960) // 2 = 320px
        page.winfo_width = lambda: 1600
        page._update_layout_geometry()

        col_info = page.conversation_column.pack_info()
        expected_padx = (1600 - 960) // 2
        self.assertEqual(int(col_info.get("padx", 0)), expected_padx)

        comp_info = page.composer_wrapper.pack_info()
        self.assertEqual(int(comp_info.get("padx", 0)), expected_padx)

        # 750px kenglik: target column width 720px, padx = max(16, (750 - 720) // 2) = 16
        page.winfo_width = lambda: 750
        page._update_layout_geometry()

        col_info_small = page.conversation_column.pack_info()
        self.assertEqual(int(col_info_small.get("padx", 0)), 16)

        page.destroy()

    def test_layout_geometry_and_full_width_viewport(self):
        page = ChatPage(self.root)

        # chat_scroll tashqi containeri (_parent_frame) to'liq enli va bo'sh joyni to'liq egallashi kerak
        scroll_info = page.chat_scroll._parent_frame.pack_info()
        self.assertEqual(scroll_info.get("fill"), "both")
        self.assertEqual(scroll_info.get("expand"), "1" if isinstance(scroll_info.get("expand"), str) else 1)

        # target ustun kengliklari tekshiruvi (viewport kengliklari bo'yicha):
        # 1920x1080 oynada (viewport ~1680px) -> 960px
        self.assertEqual(page._get_target_column_width(1680), 960)
        # 1440x900 oynada (viewport ~1200px) -> 900px
        self.assertEqual(page._get_target_column_width(1200), 900)
        # 1280x800 oynada (viewport ~1040px) -> 820px
        self.assertEqual(page._get_target_column_width(1040), 820)
        # 1024x700 oynada (viewport ~780px) -> 720px
        self.assertEqual(page._get_target_column_width(780), 720)

        # Bo'sh holatda skrollbar yashirilgan bo'lishi kerak
        self.assertFalse(bool(page.chat_scroll._scrollbar.grid_info()))

        page.destroy()

    def test_composer_focus_ring(self):
        page = ChatPage(self.root)

        # FocusIn bo'lganda PRIMARY (Electric Blue) hoshiya bo'lishi kerak
        page._on_input_focus_in()
        self.assertEqual(page.input_frame.cget("border_color"), Colors.PRIMARY)

        # FocusOut bo'lganda BORDER ga qaytishi kerak
        page._on_input_focus_out()
        self.assertEqual(page.input_frame.cget("border_color"), Colors.BORDER)

        page.destroy()


if __name__ == "__main__":
    unittest.main()
