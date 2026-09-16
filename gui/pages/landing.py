# ========== gui/pages/landing.py ==========
# Mikasa AI 7.0 — Landing / AI Home Sahifasi
# Assistentning markaziy kirish nuqtasi: Orb + Salomlashuv + Voice/Chat CTA + Kompozitor

import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing
from gui.icons import get_vector_icon
from gui.orb import MikasaOrb
from gui.components import CircleIconButton


class QuickActionCard(ctk.CTkFrame):
    """
    Ixcham AI taklif kartochkasi (Suggestion card — dashboard kartasi EMAS).
    """

    def __init__(self, master, icon: str, title: str, subtitle: str, command=None, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            width=140,
            height=66,
            cursor="hand2",
            **kwargs,
        )
        self.pack_propagate(False)
        self._command = command

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # Yuqori qator: Ikonka + Sarlavha
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        icon_img = get_vector_icon(icon, size=15, color_dark=Colors.PRIMARY, color_light=Colors.PRIMARY)
        if icon_img:
            self.icon_lbl = ctk.CTkLabel(top_row, text="", image=icon_img)
            self.icon_lbl.pack(side="left", padx=(0, 6))

        title_lbl = ctk.CTkLabel(
            top_row,
            text=title,
            font=(Fonts.FAMILY, 12, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        # Pastki qator: Qisqacha tavsif
        sub_lbl = ctk.CTkLabel(
            inner,
            text=subtitle,
            font=(Fonts.FAMILY, 10),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        sub_lbl.pack(fill="x", pady=(3, 0))

        # Click va hover bog'lash
        for w in (self, inner, top_row, title_lbl, sub_lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
        if hasattr(self, "icon_lbl"):
            self.icon_lbl.bind("<Button-1>", self._on_click)
            self.icon_lbl.bind("<Enter>", self._on_enter)
            self.icon_lbl.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        self.configure(
            fg_color=Colors.BG_HOVER,
            border_color=Colors.PRIMARY_GLOW,
        )

    def _on_leave(self, event=None):
        self.configure(
            fg_color=Colors.BG_CARD,
            border_color=Colors.BORDER_SUBTLE,
        )

    def _on_click(self, event=None):
        if self._command:
            self._command()


class LandingPage(ctk.CTkFrame):
    """
    Mikasa AI 7.0 Landing / AI Home Page.
    
    Arxitektura:
      - Dashboard emas: telemetriya, grafiklar va statistika yo'q.
      - Markazlashgan AI Orb (MikasaOrb).
      - Foydalanuvchining haqiqiy ismi bilan salomlashuv.
      - Real backend holati (Online/Offline).
      - Primary Action: "Tinglashni boshlash" (Voice).
      - Secondary Actions: "Tozalash" va "Chat".
      - 3 ta ixcham taklif kartochkasi (So'rash, Buyruq, Xulosa).
      - Ixcham kompozitor (Enter -> ChatPage ga prompt uzatish).
    """

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color=Colors.BG_DARK, corner_radius=0, **kwargs)
        self.app = app
        self._attached_file = None
        self._action_mode = "mic"
        self._is_composer_focused = False

        self._build_ui()
        self.bind("<Configure>", self._on_configure)

    def _build_ui(self):
        # Asosiy vertikal markazlashuvchi konteyner
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        self.center_column = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.center_column.pack(expand=True, padx=20, pady=10)

        # 1. Tepada nafis ✦ AI aksenti
        self.top_sparkle = ctk.CTkLabel(
            self.center_column,
            text="",
            image=get_vector_icon("sparkles", size=14, color=Colors.PRIMARY_GLOW),
        )
        self.top_sparkle.pack(pady=(0, 4))

        # 2. Markaziy Mikasa AI Orb (150x150)
        self.orb_size = 150
        self.orb = MikasaOrb(
            self.center_column,
            size=self.orb_size,
            state="idle",
            bg_color=Colors.BG_DARK,
        )
        self.orb.pack(pady=(0, 10))

        # 3. Salomlashuv va foydalanuvchi ismi
        user_name = self._get_user_name()
        self.greeting_label = ctk.CTkLabel(
            self.center_column,
            text=f"Salom, {user_name}",
            font=(Fonts.FAMILY, 24, "bold"),
            text_color=Colors.TEXT_PRIMARY,
        )
        self.greeting_label.pack(pady=(0, 2))

        self.sub_greeting = ctk.CTkLabel(
            self.center_column,
            text="Qanday yordam beray?",
            font=(Fonts.FAMILY, 14),
            text_color=Colors.TEXT_SECONDARY,
        )
        self.sub_greeting.pack(pady=(0, 8))

        # 4. Haqiqiy holat indikatori (● Online / ● Offline)
        self.status_badge = ctk.CTkFrame(
            self.center_column,
            fg_color=Colors.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            height=24,
        )
        self.status_badge.pack(pady=(0, 14))

        status_inner = ctk.CTkFrame(self.status_badge, fg_color="transparent")
        status_inner.pack(padx=10, pady=3)

        self.status_dot = ctk.CTkLabel(status_inner, text="")
        self.status_dot.pack(side="left", padx=(0, 6))

        self.status_text = ctk.CTkLabel(
            status_inner,
            text="Online",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
        )
        self.status_text.pack(side="left")
        self._update_online_status()

        # 5. Asosiy harakat: "Tinglashni boshlash" (Primary Voice CTA)
        mic_icon = get_vector_icon("mic", size=18, color="#FFFFFF")
        self.primary_voice_btn = ctk.CTkButton(
            self.center_column,
            text="  Tinglashni boshlash",
            image=mic_icon,
            compound="left",
            font=(Fonts.FAMILY, 13, "bold"),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=42,
            width=320,
            corner_radius=21,
            command=self._on_primary_voice,
        )
        self.primary_voice_btn.pack(pady=(0, 8))

        # 6. Qo'shimcha amallar: [ Tozalash ]  [ Chat ]
        self.action_row = ctk.CTkFrame(self.center_column, fg_color="transparent")
        self.action_row.pack(pady=(0, 14))

        self.clear_btn = ctk.CTkButton(
            self.action_row,
            text="Tozalash",
            font=Fonts.SMALL,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_MUTED,
            height=30,
            width=100,
            corner_radius=15,
            command=self._on_clear_composer,
        )
        self.clear_btn.pack(side="left", padx=5)

        chat_icon = get_vector_icon("chat", size=13, color=Colors.PRIMARY)
        self.chat_btn = ctk.CTkButton(
            self.action_row,
            text="  Chat",
            image=chat_icon,
            compound="left",
            font=Fonts.SMALL,
            fg_color=Colors.GLASS_BG,
            hover_color=Colors.GLASS_BG_HOVER,
            border_width=1,
            border_color=Colors.GLASS_BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=30,
            width=100,
            corner_radius=15,
            command=self._on_open_chat,
        )
        self.chat_btn.pack(side="left", padx=5)

        # 7. 3 ta ixcham taklif kartochkasi (Quick actions)
        self.cards_row = ctk.CTkFrame(self.center_column, fg_color="transparent")
        self.cards_row.pack(pady=(0, 14))

        self.card_ask = QuickActionCard(
            self.cards_row,
            icon="sparkles",
            title="So‘rash",
            subtitle="Savol berish",
            command=self._on_card_ask,
        )
        self.card_ask.pack(side="left", padx=6)

        self.card_command = QuickActionCard(
            self.cards_row,
            icon="commands",
            title="Buyruq",
            subtitle="Tizim amallari",
            command=self._on_card_command,
        )
        self.card_command.pack(side="left", padx=6)

        self.card_summary = QuickActionCard(
            self.cards_row,
            icon="circle_outline",
            title="Xulosa",
            subtitle="Matn tahlili",
            command=self._on_card_summary,
        )
        self.card_summary.pack(side="left", padx=6)

        # 8. Ixcham AI Kompozitor (Composer)
        self._build_composer()

    def _build_composer(self):
        """Pastki ixcham kiritish paneli"""
        self.composer_container = ctk.CTkFrame(self.center_column, fg_color="transparent")
        self.composer_container.pack(fill="x", pady=(0, 5))

        # Fayl biriktirilganda ko'rinuvchi kichik indikator
        self.attachment_bar = ctk.CTkFrame(self.composer_container, fg_color="transparent", height=22)
        self.attachment_lbl = ctk.CTkLabel(
            self.attachment_bar,
            text="",
            font=Fonts.TINY,
            text_color=Colors.PRIMARY,
        )
        self.attachment_lbl.pack(side="left", padx=8)

        self.composer_frame = ctk.CTkFrame(
            self.composer_container,
            fg_color=Colors.BG_INPUT,
            corner_radius=23,
            border_width=1,
            border_color=Colors.BORDER,
            height=46,
            width=460,
        )
        self.composer_frame.pack()
        self.composer_frame.pack_propagate(False)

        # Hover & focus border effektlari
        self.composer_frame.bind("<Enter>", lambda e: self._on_composer_hover(True))
        self.composer_frame.bind("<Leave>", lambda e: self._on_composer_hover(False))

        # Attach tugmasi
        self.attach_btn = CircleIconButton(
            self.composer_frame,
            icon="attach",
            size=32,
            fg_color=Colors.GLASS_BG,
            hover_color=Colors.GLASS_BG_HOVER,
            border_color=Colors.GLASS_BORDER,
            border_width=1,
            bg_color=Colors.BG_INPUT,
            text_color="#FFFFFF",
            command=self._on_attach_file,
        )
        self.attach_btn.pack(side="left", padx=(7, 4), pady=7)

        # Matn entry
        self._input_var = ctk.StringVar()
        self._input_var.trace_add("write", lambda *args: self._update_composer_action())

        self.input_entry = ctk.CTkEntry(
            self.composer_frame,
            textvariable=self._input_var,
            placeholder_text="Nima yordam kerak?",
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            height=34,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=4, pady=6)
        self.input_entry.bind("<Return>", self._on_submit_composer)
        self.input_entry.bind("<FocusIn>", lambda e: self._set_composer_focus(True))
        self.input_entry.bind("<FocusOut>", lambda e: self._set_composer_focus(False))

        # Action tugmasi (Mic <-> Send)
        self.action_btn = CircleIconButton(
            self.composer_frame,
            icon="mic",
            size=32,
            fg_color=Colors.GLASS_BG,
            hover_color=Colors.GLASS_BG_HOVER,
            border_color=Colors.GLASS_BORDER,
            border_width=1,
            bg_color=Colors.BG_INPUT,
            text_color=Colors.PRIMARY,
            command=self._on_composer_action,
        )
        self.action_btn.pack(side="right", padx=(4, 7), pady=7)

    def _on_composer_hover(self, is_hover: bool):
        if not self._is_composer_focused:
            self.composer_frame.configure(
                border_color=Colors.BORDER_HOVER if is_hover else Colors.BORDER
            )

    def _set_composer_focus(self, focused: bool):
        self._is_composer_focused = focused
        self.composer_frame.configure(
            border_color=Colors.PRIMARY if focused else Colors.BORDER
        )

    def _update_composer_action(self):
        has_text = bool(self._input_var.get().strip())
        has_file = bool(self._attached_file)

        if has_text or has_file:
            if self._action_mode != "send":
                self._action_mode = "send"
                self.action_btn.configure(
                    icon="send",
                    fg_color=Colors.GLASS_HERO_BG,
                    hover_color=Colors.GLASS_HERO_HOVER,
                    border_color=Colors.GLASS_HERO_BORDER,
                    text_color="#FFFFFF",
                )
        else:
            if self._action_mode != "mic":
                self._action_mode = "mic"
                self.action_btn.configure(
                    icon="mic",
                    fg_color=Colors.GLASS_BG,
                    hover_color=Colors.GLASS_BG_HOVER,
                    border_color=Colors.GLASS_BORDER,
                    text_color=Colors.PRIMARY,
                )

    def _on_attach_file(self):
        path = filedialog.askopenfilename(
            title="Fayl biriktirish",
            filetypes=[("Barcha fayllar", "*.*")],
        )
        if not path:
            return
        self._attached_file = path
        fname = os.path.basename(path)
        self.attachment_lbl.configure(text=f"📎 {fname}")
        self.attachment_bar.pack(fill="x", pady=(0, 2), before=self.composer_frame)
        self.attach_btn.configure(fg_color=Colors.PRIMARY)
        self._update_composer_action()

    def _on_clear_composer(self):
        """Kompozitordagi matn va faylni tozalash"""
        self._input_var.set("")
        self._attached_file = None
        if hasattr(self, "attachment_bar") and self.attachment_bar.winfo_ismapped():
            self.attachment_bar.pack_forget()
        self.attach_btn.configure(fg_color=Colors.GLASS_BG)
        self._update_composer_action()

    def _on_composer_action(self):
        if self._action_mode == "send":
            self._on_submit_composer()
        else:
            self._on_primary_voice()

    def _on_submit_composer(self, event=None):
        """Kiritilgan matnni mavjud ChatPage ga yo'naltirish"""
        text = self._input_var.get().strip()
        file_path = self._attached_file

        if not text and not file_path:
            return

        # Kompozitorni tozalash
        self._on_clear_composer()

        # Chat sahifasiga o'tish va matnni yuborish
        if self.app and hasattr(self.app, "navigate_to"):
            self.app.navigate_to("chat")
            chat_page = self.app._get_or_create_page("chat")
            if chat_page and hasattr(chat_page, "send_prompt"):
                chat_page.send_prompt(text, auto_send=True, attached_file=file_path)

    # ========== NAVIGATION BUTTON ACTIONS ==========

    def _on_primary_voice(self):
        """Voice sahifasiga o'tish"""
        if self.app and hasattr(self.app, "navigate_to"):
            self.app.navigate_to("voice")

    def _on_open_chat(self):
        """Chat sahifasiga o'tish"""
        if self.app and hasattr(self.app, "navigate_to"):
            self.app.navigate_to("chat")
            chat_page = self.app._get_or_create_page("chat")
            if chat_page and hasattr(chat_page, "focus_input"):
                chat_page.focus_input()

    def _on_card_ask(self):
        """So'rash kartasi bosilganda"""
        self._on_open_chat()

    def _on_card_command(self):
        """Buyruq kartasi bosilganda"""
        if self.app and hasattr(self.app, "navigate_to"):
            self.app.navigate_to("commands")

    def _on_card_summary(self):
        """Xulosa kartasi bosilganda"""
        if self.app and hasattr(self.app, "navigate_to"):
            self.app.navigate_to("chat")
            chat_page = self.app._get_or_create_page("chat")
            if chat_page and hasattr(chat_page, "send_prompt"):
                chat_page.send_prompt("Quyidagi matnni qisqacha xulosa qilib ber: ", auto_send=False)

    # ========== HELPER METHODS & LIFECYCLE ==========

    def _get_user_name(self) -> str:
        if self.app and hasattr(self.app, "_get_user_name"):
            return self.app._get_user_name()
        return "Muxammadaziz"

    def _is_online(self) -> bool:
        """Haqiqiy backend holatini tekshirish"""
        if self.app:
            status = getattr(self.app, "_status_state", {}).get("status", "")
            if status == "offline":
                return False
            bridge = getattr(self.app, "bridge", None)
            if bridge:
                return getattr(bridge, "is_ready", True)
            return True
        return True

    def _update_online_status(self):
        """Online/Offline indikatorini yangilash"""
        is_on = self._is_online()
        dot_color = Colors.SUCCESS if is_on else Colors.DANGER
        status_lbl = "Online" if is_on else "Offline"

        dot_img = get_vector_icon("circle", size=6, color=dot_color)
        if dot_img:
            self.status_dot.configure(image=dot_img)
        self.status_text.configure(text=status_lbl)

    def _on_configure(self, event=None):
        """Oyna o'lchami o'zgarganda oraliqlarni optimal saqlash"""
        if not event or event.widget != self:
            return
        h = event.height
        if h < 720:
            # Ixcham oyna (1024x700 yoki kichikroq)
            self.status_badge.pack_configure(pady=(0, 8))
            self.primary_voice_btn.pack_configure(pady=(0, 6))
            self.action_row.pack_configure(pady=(0, 8))
            self.cards_row.pack_configure(pady=(0, 8))
        else:
            self.status_badge.pack_configure(pady=(0, 14))
            self.primary_voice_btn.pack_configure(pady=(0, 8))
            self.action_row.pack_configure(pady=(0, 14))
            self.cards_row.pack_configure(pady=(0, 14))

    def on_show(self):
        """Sahifa ko'rsatilganda chaqiriladi"""
        # 1. Foydalanuvchi ismini yangilash
        user_name = self._get_user_name()
        self.greeting_label.configure(text=f"Salom, {user_name}")

        # 2. Haqiqiy holatni yangilash
        self._update_online_status()

        # 3. Orb animatsiyasini ishga tushirish
        if hasattr(self, "orb") and self.orb:
            self.orb.start()

    def on_hide(self):
        """Sahifa yashirilganda chaqiriladi — resurslarni tejash"""
        if hasattr(self, "orb") and self.orb:
            self.orb.stop()

    def destroy(self):
        """Sahifa butunlay yo'q qilinganda"""
        if hasattr(self, "orb") and self.orb:
            try:
                self.orb.destroy()
            except Exception:
                pass
        super().destroy()
