# ========== test_v6_user_account.py ==========
# Mikasa AI v6.0.0 — User Account Area & Chat Avatar Testlari

import unittest
import customtkinter as ctk
from gui.theme import Colors, Fonts
from gui.components import UserAvatar, AssistantAvatar, AccountRow, MessageBubble
from gui.pages.chat import ChatPage


class TestUserAccountAndChatAvatar(unittest.TestCase):
    """Foydalanuvchi hisob maydoni va Chat avatari testlari"""

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

    def test_user_avatar_initials_extraction(self):
        self.assertEqual(UserAvatar._extract_initials("Muxammadaziz"), "MA")
        self.assertEqual(UserAvatar._extract_initials("Sardor Rahimov"), "SR")
        self.assertEqual(UserAvatar._extract_initials("A"), "A")
        self.assertEqual(UserAvatar._extract_initials(""), "U")
        self.assertEqual(UserAvatar._extract_initials(None), "U")

    def test_user_avatar_rendering(self):
        avatar = UserAvatar(self.root, name="Muxammadaziz", size=36)
        self.assertEqual(avatar.cget("width"), 36)
        self.assertEqual(avatar.cget("height"), 36)
        self.assertEqual(avatar.cget("corner_radius"), 18)
        self.assertIsNotNone(avatar.avatar_image)
        self.assertIsNotNone(avatar.avatar_label)
        avatar.destroy()

    def test_assistant_avatar_rendering(self):
        avatar = AssistantAvatar(self.root, size=28)
        self.assertEqual(avatar.cget("width"), 28)
        self.assertEqual(avatar.cget("height"), 28)
        self.assertEqual(avatar.cget("corner_radius"), 14)
        self.assertEqual(avatar.cget("border_color"), Colors.PRIMARY)
        self.assertIsNotNone(avatar.icon_img)
        self.assertIsNotNone(avatar.icon_label)
        avatar.destroy()

    def test_account_row_structure_and_click(self):
        clicked = []
        row = AccountRow(
            self.root,
            name="Muxammadaziz",
            compact=False,
            command=lambda: clicked.append(True),
        )
        self.assertEqual(row._name, "Muxammadaziz")
        self.assertEqual(row.name_label.cget("text"), "Muxammadaziz")
        self.assertEqual(row.sub_label.cget("text"), "Hisob")
        self.assertIsNotNone(row.avatar)
        self.assertIsNotNone(row.chevron_label)

        # Klik hodisasi
        row._on_click()
        self.assertEqual(len(clicked), 1)

        # Ismni yangilash
        row.update_user_name("Azizbek")
        self.assertEqual(row._name, "Azizbek")
        self.assertEqual(row.name_label.cget("text"), "Azizbek")

        row.destroy()

    def test_account_row_compact_mode(self):
        row = AccountRow(self.root, name="Muxammadaziz", compact=False)
        self.assertTrue(bool(row.text_frame.winfo_manager()))
        self.assertTrue(bool(row.chevron_label.winfo_manager()))

        # Compact rejimga o'tish
        row.set_compact(True)
        self.assertFalse(bool(row.text_frame.winfo_manager()))
        self.assertFalse(bool(row.chevron_label.winfo_manager()))

        # Qayta to'liq rejimga o'tish
        row.set_compact(False)
        self.assertTrue(bool(row.text_frame.winfo_manager()))
        self.assertTrue(bool(row.chevron_label.winfo_manager()))

        row.destroy()

    def test_chat_page_avatars_and_grouping(self):
        page = ChatPage(self.root)

        # 1. User xabari (boshlang'ich - avatar bilan)
        page.add_message("Dollar kursi necha?", "user", "10:00")
        self.assertEqual(len(page._messages), 1)

        # 2. Assistant xabari (avatar bilan)
        page.add_message("12,850 so'm", "assistant", "10:01")
        self.assertEqual(len(page._messages), 2)

        # 3. Ketma-ket user xabarlari (birinchisida avatar, ikkinchisida bo'shliq/spacer)
        page.add_message("Ob-havo qanday?", "user", "10:02")
        page.add_message("Toshkentda", "user", "10:02")
        self.assertEqual(len(page._messages), 4)

        # Tekshiruv: conversation_column ichida UserAvatar va AssistantAvatar mavjud
        children = page.conversation_column.winfo_children()
        user_avatars = []
        assistant_avatars = []

        def collect_avatars(w):
            if isinstance(w, UserAvatar):
                user_avatars.append(w)
            elif isinstance(w, AssistantAvatar):
                assistant_avatars.append(w)
            for ch in w.winfo_children():
                collect_avatars(ch)

        for c in children:
            collect_avatars(c)

        # 1-user, 1-assistant, 1-user (ketma-ket ikkinchisida avatar takrorlanmaydi)
        # Jami 2 ta UserAvatar va 1 ta AssistantAvatar bo'lishi kerak
        self.assertEqual(len(user_avatars), 2)
        self.assertEqual(len(assistant_avatars), 1)

        page.destroy()


if __name__ == "__main__":
    unittest.main()
