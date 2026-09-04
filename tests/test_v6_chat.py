# ========== test_v6_chat.py ==========
# Mikasa AI v6.0.0 — Chat UI va Backend Routing testlari

import unittest
from unittest.mock import MagicMock
import customtkinter as ctk

from gui.theme import Colors, Fonts
from gui.components import MessageBubble, TypingBubble
from gui.pages.chat import ChatPage
from gui.backend import BackendBridge


class TestV6ChatUI(unittest.TestCase):
    """Chat UI komponentlari va sahifasi testlari"""

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

    def test_message_bubble_user_styling(self):
        bubble = MessageBubble(self.root, text="Salom", role="user", timestamp="20:00")
        self.assertEqual(bubble.cget("fg_color"), Colors.PRIMARY)
        self.assertEqual(bubble.cget("border_width"), 0)
        self.assertEqual(bubble.text_label.cget("text"), "Salom")
        self.assertEqual(bubble.text_label.cget("text_color"), "#FFFFFF")
        bubble.destroy()

    def test_message_bubble_assistant_styling(self):
        bubble = MessageBubble(
            self.root,
            text="Assalomu alaykum!",
            role="assistant",
            timestamp="20:01",
        )
        self.assertEqual(bubble.cget("fg_color"), Colors.BG_CARD)
        self.assertEqual(bubble.cget("border_width"), 1)
        self.assertEqual(bubble.cget("border_color"), Colors.BORDER)
        self.assertEqual(bubble.text_label.cget("text"), "Assalomu alaykum!")
        bubble.destroy()

    def test_typing_bubble_animation_lifecycle(self):
        tb = TypingBubble(self.root, prefix="yozyapti")
        self.assertTrue(tb._is_running)
        self.assertIn("yozyapti", tb.text_label.cget("text"))

        # Animatsiya qadami
        tb._animate()
        self.assertIn("yozyapti", tb.text_label.cget("text"))

        # Prefix o'zgartirish
        tb.set_prefix("Agent o'ylamoqda")
        self.assertEqual(tb._prefix, "Agent o'ylamoqda")

        # To'xtatish va yo'q qilish
        tb.stop()
        self.assertFalse(tb._is_running)
        tb.destroy()

    def test_chat_page_typing_and_messages(self):
        page = ChatPage(self.root)

        # Xabar yuborish
        page.add_message("Salom Mikasa", "user", "20:05")
        self.assertEqual(len(page._messages), 1)

        # Typing ko'rsatish
        page.show_typing("yozyapti")
        self.assertIsNotNone(page._typing_bubble)
        self.assertIsNotNone(page._typing_row)

        # Assistant javob kelganda typing avtomatik yashirilishi kerak
        page.add_message("Salom! Qanday yordam bera olaman?", "assistant", "20:06")
        self.assertIsNone(page._typing_bubble)
        self.assertEqual(len(page._messages), 2)

        # Agent qadamlari qo'shish
        page.add_agent_step(1, "thought", "Reja tuzilmoqda")
        page.add_agent_step("Asbob", "action", "Google qidiruv")
        page.add_agent_step("Yakun", "final", "Tayyor")

        # Tozalash
        page._clear_chat()
        self.assertEqual(len(page._messages), 0)
        self.assertIsNone(page._typing_bubble)

        page.destroy()

    def test_telegram_style_dynamic_button_and_attachment(self):
        page = ChatPage(self.root)

        # 1. Chapdagi skripka tugmasi mavjudligi
        self.assertEqual(page.attach_btn.cget("text"), "📎")

        # 2. Boshlang'ich holat: matn yo'q -> mikrofon icon (🎙️)
        self.assertEqual(page.action_btn.cget("text"), "🎙️")
        self.assertEqual(page._action_mode, "mic")

        # 3. Matn yozilganda -> avtomatik yuborish (➤) tugmasiga aylanadi
        page._input_var.set("Salom Mikasa")
        self.assertEqual(page.action_btn.cget("text"), "➤")
        self.assertEqual(page._action_mode, "send")
        self.assertEqual(page.action_btn.cget("fg_color"), Colors.PRIMARY)

        # 4. Matn o'chirilganda -> avtomatik mikrofon (🎙️) ga qaytadi
        page._input_var.set("")
        self.assertEqual(page.action_btn.cget("text"), "🎙️")
        self.assertEqual(page._action_mode, "mic")

        # 5. Fayl biriktirilganda -> tugma ➤ ga aylanadi
        page._attached_file = "test_document.pdf"
        page._update_action_button()
        self.assertEqual(page.action_btn.cget("text"), "➤")
        self.assertEqual(page._action_mode, "send")

        # 6. Fayl olib tashlanganda -> tugma yana 🎙️ ga qaytadi
        page._remove_attached_file()
        self.assertEqual(page.action_btn.cget("text"), "🎙️")
        self.assertEqual(page._action_mode, "mic")

        page.destroy()


class TestV6BackendRouting(unittest.TestCase):
    """BackendBridge xabarlarni filtrlash va to'g'ri yo'naltirish testlari"""

    def setUp(self):
        self.mock_app = MagicMock()
        self.mock_app.winfo_exists.return_value = True
        self.mock_chat = MagicMock()
        self.mock_voice = MagicMock()
        self.mock_app._pages = {"chat": self.mock_chat, "voice": self.mock_voice}

        self.bridge = BackendBridge(self.mock_app)

    def _execute_queued_callbacks(self):
        """UI queue dagi barcha vazifalarni sinxron bajarish"""
        while not self.bridge._ui_queue.empty():
            cb = self.bridge._ui_queue.get_nowait()
            cb()

    def test_filter_status_and_debug_messages(self):
        # Ichki loglar va test eslatmalari
        self.bridge._gui_callback("🎙️ Tinglash boshlandi")
        self.bridge._gui_callback("💡 Eslatma: test_key = test_value")
        self.bridge._gui_callback("🎯 Buyruq: vaqt")
        self._execute_queued_callbacks()

        # Chat sahifasiga xabar qo'shilmasligi kerak
        self.mock_chat.add_message.assert_not_called()

    def test_route_agent_thinking_to_typing_and_panel(self):
        self.bridge._gui_callback("🤖 Agent o'ylamoqda...")
        self._execute_queued_callbacks()

        # Asosiy chatga pufakcha qo'shilmasdan, show_typing va agent_step chaqirilishi kerak
        self.mock_chat.add_message.assert_not_called()
        self.mock_chat.show_typing.assert_called_with("yozyapti")
        self.mock_chat.add_agent_step.assert_called_with(
            1, "thought", "Vazifa tahlil qilinmoqda..."
        )

    def test_route_agent_step_and_tool(self):
        self.bridge._gui_callback("🧠 Qadam 2: Tizim parametrlarini tekshirish")
        self.bridge._gui_callback("🔧 Tool 'system_info': CPU 12%")
        self._execute_queued_callbacks()

        self.mock_chat.add_message.assert_not_called()
        self.mock_chat.add_agent_step.assert_any_call(
            2, "thought", "Tizim parametrlarini tekshirish"
        )
        self.mock_chat.add_agent_step.assert_any_call(
            "Asbob", "action", "'system_info': CPU 12%"
        )

    def test_strip_prefixes_and_show_final_response(self):
        self.bridge._gui_callback("🤖 Agent: Bugun ob-havo ochiq, 24 daraja iliq.")
        self._execute_queued_callbacks()

        # hide_typing chaqirilgan va tozalangan matn chatga uzatilgan
        self.mock_chat.hide_typing.assert_called()
        self.mock_chat.add_message.assert_called_with(
            "Bugun ob-havo ochiq, 24 daraja iliq.", "assistant"
        )
        self.mock_chat.add_agent_step.assert_called_with(
            "Yakun", "final", "Javob berildi"
        )


class TestV6MediaAndMusicPlayback(unittest.TestCase):
    """Musiqa qidirish va ijro etish intentlari testi"""

    def test_youtube_music_intent_priority(self):
        from main import buyruqni_aniqla

        cases = [
            ("youtubdan rose funk qo'shig'ini qo'yib ber", "music_search"),
            ("youtube dan sevara nazarkhan qo'shig'ini qo'y", "music_search"),
            ("rose funk musiqasini qo'y", "music_search"),
            ("yutubdan sherik qo'shig'ini eshitaylik", "music_search"),
            ("yutubdan rose funk qo'y", "music_search"),
            ("spotifydan lola qo'shig'ini qo'y", "music_search"),
            ("yandex music dan rayhon ijro et", "music_search"),
            ("bitta rose funk trekini qo'yib ber", "music_search"),
            ("musiqa qo'y", "music_search"),
            ("qo'shiq eshitaylik", "music_search"),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(buyruqni_aniqla(text), expected)

    def test_open_youtube_not_conflicted(self):
        from main import buyruqni_aniqla

        open_yt_cases = [
            "youtube",
            "yutub",
            "youtubeni och",
            "yutubni och",
            "yutubga kir",
        ]
        for text in open_yt_cases:
            with self.subTest(text=text):
                self.assertEqual(buyruqni_aniqla(text), "open_youtube")

    def test_toza_musiqa_nomi_extraction(self):
        from main import toza_musiqa_nomi

        cases = [
            ("youtubdan rose funk qo'shig'ini qo'yib ber", "rose funk"),
            ("youtube dan sevara nazarkhan qo'shig'ini qo'y", "sevara nazarkhan"),
            ("rose funk musiqasini qo'y", "rose funk"),
            ("spotifydan lola qo'shig'ini qo'y", "lola"),
            ("yandex music dan rayhon ijro et", "rayhon"),
            ("bitta rose funk trekini qo'yib ber", "rose funk"),
            ("yutubdan rose funk qo'y", "rose funk"),
            ("musiqa qo'y", ""),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(toza_musiqa_nomi(text), expected)

    def test_media_controls(self):
        from main import buyruqni_aniqla

        self.assertEqual(buyruqni_aniqla("musiqani to'xtat"), "music_pause")
        self.assertEqual(buyruqni_aniqla("davom ettir"), "music_play")
        self.assertEqual(buyruqni_aniqla("musiqani qo'y"), "music_play")


if __name__ == "__main__":
    unittest.main()
