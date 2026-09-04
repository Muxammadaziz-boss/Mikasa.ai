# ========== chat.py ==========
# AI Chat sahifasi — suhbat interfeysi + ReAct agent panel

import os
import datetime
from tkinter import filedialog
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, GlowButton, MessageBubble, TypingBubble


class ChatPage(ctk.CTkFrame):
    """AI bilan matnli suhbat sahifasi"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._messages = []
        # Duplikat xabardan himoya — oxirgi yuborilgan user xabar
        self._last_user_text = None
        # Animatsion yozish indikatori holati
        self._typing_bubble = None
        self._typing_row = None
        self._agent_step_count = 0
        # Biriktirilgan fayl va Telegram uslubidagi dinamik tugma holati
        self._attached_file = None
        self._action_mode = "mic"
        self._build_ui()

    def _on_mode_change(self, value):
        """Rejim o'zgarganda input placeholder'ni moslashtirish"""
        if hasattr(self, "input_entry"):
            if "Chat" in value:
                self.input_entry.configure(
                    placeholder_text="AI ga xabar yozing (tezkor javob)..."
                )
            elif "Agent" in value:
                self.input_entry.configure(
                    placeholder_text="Murakkab vazifa yoki buyruq bering..."
                )
            elif "Vision" in value:
                self.input_entry.configure(
                    placeholder_text="Ekran tahlili uchun so'rov kiriting..."
                )

    def _build_ui(self):
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header,
            text="💬  AI Suhbat",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        # Suhbatni tozalash
        ctk.CTkButton(
            header,
            text="🗑️ Tozalash",
            font=Fonts.SMALL,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            width=100,
            height=30,
            command=self._clear_chat,
        ).pack(side="right")

        # Mode selector
        self.mode_selector = ctk.CTkSegmentedButton(
            header,
            values=["💬 Chat", "🤖 Agent", "👁️ Vision"],
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            selected_color=Colors.PRIMARY_DARK,
            selected_hover_color=Colors.PRIMARY,
            unselected_color=Colors.BG_INPUT,
            unselected_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            command=self._on_mode_change,
        )
        self.mode_selector.set("💬 Chat")
        self.mode_selector.pack(side="right", padx=10)

        # ===== ASOSIY KONTENT — 2 COLUMN =====
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # --- CHAP: CHAT AREA ---
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._build_chat_area(left)
        self._build_input_bar(left)

        # --- O'NG: AGENT PANEL ---
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        self._build_agent_panel(right)
        self._build_context_panel(right)

    def _build_chat_area(self, parent):
        """Xabarlar maydoni"""
        self.chat_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color=Colors.BG_SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.chat_scroll.pack(fill="both", expand=True, pady=(0, 8))

        # Boshlang'ich xabar
        self._add_welcome_message()

    def _add_welcome_message(self):
        """Xush kelibsiz xabari"""
        welcome_card = GlassCard(self.chat_scroll, title="✨  Suhbatni boshlash")
        welcome_card.pack(fill="x", padx=8, pady=12)

        welcome_frame = ctk.CTkFrame(welcome_card.content, fg_color="transparent")
        welcome_frame.pack(fill="x")

        ctk.CTkLabel(welcome_frame, text="🤖", font=(Fonts.FAMILY, 40)).pack()

        ctk.CTkLabel(
            welcome_frame,
            text="Salom! Men Mikasa AI yordamchiman.",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY,
        ).pack(pady=(8, 4))

        ctk.CTkLabel(
            welcome_frame,
            text="Savolingizni yozing yoki ovozli buyruq bering",
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
        ).pack()

        info_row = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        info_row.pack(pady=(10, 0))

        for text, color in [
            ("⚡ Tez javob", Colors.BG_PANEL),
            ("🎙️ Ovozli rejim", Colors.BG_PANEL),
            ("🤖 Agent panel", Colors.BG_PANEL),
        ]:
            chip = ctk.CTkFrame(
                info_row,
                fg_color=color,
                corner_radius=999,
                border_width=1,
                border_color=Colors.BORDER,
                bg_color=Colors.BG_CARD,
            )
            chip.pack(side="left", padx=4)
            ctk.CTkLabel(
                chip,
                text=text,
                font=Fonts.TINY,
                text_color=Colors.TEXT_SECONDARY,
            ).pack(padx=10, pady=4)

        # Tezkor savollar
        suggestions_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        suggestions_frame.pack(pady=(16, 0))

        suggestions = [
            "Havo qanday?",
            "Dollar kursi necha?",
            "Musiqa qo'y",
            "Soat necha?",
        ]

        for suggestion in suggestions:
            btn = ctk.CTkButton(
                suggestions_frame,
                text=suggestion,
                font=Fonts.SMALL,
                fg_color=Colors.BG_CARD,
                hover_color=Colors.BG_HOVER,
                text_color=Colors.TEXT_SECONDARY,
                border_width=1,
                border_color=Colors.BORDER,
                corner_radius=20,
                height=32,
                bg_color=Colors.BG_CARD,
                command=lambda s=suggestion: self._send_suggestion(s),
            )
            btn.pack(side="left", padx=4)

    def _build_input_bar(self, parent):
        """Matn kiritish paneli — Telegram / Apple uslubidagi minimalist dizayn"""
        # Biriktirilgan fayl preview paneli (fayl tanlanganda input_frame ustida chiqadi)
        self.attachment_bar = ctk.CTkFrame(
            parent,
            fg_color=Colors.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            height=34,
        )
        self.attachment_label = ctk.CTkLabel(
            self.attachment_bar,
            text="",
            font=Fonts.SMALL,
            text_color=Colors.PRIMARY,
            anchor="w",
        )
        self.attachment_label.pack(side="left", padx=12, fill="x", expand=True)

        ctk.CTkButton(
            self.attachment_bar,
            text="✕",
            font=Fonts.TINY,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            width=26,
            height=26,
            corner_radius=13,
            command=self._remove_attached_file,
        ).pack(side="right", padx=6)

        # Asosiy input kapsulasi
        self.input_frame = ctk.CTkFrame(
            parent,
            fg_color=Colors.BG_CARD,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
            height=54,
        )
        self.input_frame.pack(fill="x", pady=(0, 8))
        self.input_frame.pack_propagate(False)

        # Chap tomonda skripka (📎) tugmasi — fayl/hujjat/rasm biriktirish
        self.attach_btn = ctk.CTkButton(
            self.input_frame,
            text="📎",
            font=(Fonts.FAMILY, 16),
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            width=38,
            height=38,
            corner_radius=19,
            command=self._on_attach_file,
        )
        self.attach_btn.pack(side="left", padx=(8, 0))

        # Matn kiritish maydoni (StringVar orqali dinamik kuzatuv)
        self._input_var = ctk.StringVar()
        self._input_var.trace_add("write", lambda *args: self._update_action_button())

        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            textvariable=self._input_var,
            placeholder_text="Mikasa ga xabar yozing...",
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            height=46,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.input_entry.bind("<Return>", self._on_enter_pressed)

        # O'ng tomondagi Telegram uslubidagi dinamik tugma (🎙️ <-> ➤)
        # Matn bo'sh bo'lsa mikrofon, biron belgi yozilsa yuborish belgisiga aylanadi
        self.action_btn = ctk.CTkButton(
            self.input_frame,
            text="🎙️",
            font=(Fonts.FAMILY, 15),
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            width=38,
            height=38,
            corner_radius=19,
            command=self._on_action_button_click,
        )
        self.action_btn.pack(side="right", padx=8)

        # Mavjud kodlar bilan moslik uchun alias
        self.send_btn = self.action_btn

    def _build_agent_panel(self, parent):
        """Agent thinking paneli — jarayon qadamlari"""
        self.agent_card = GlassCard(parent, title="🤖 Agent jarayoni")
        self.agent_card.pack(fill="x", pady=(0, 8))

        self.agent_steps = ctk.CTkFrame(self.agent_card.content, fg_color="transparent")
        self.agent_steps.pack(fill="x")

        # Boshlang'ich holat
        self.agent_placeholder = ctk.CTkLabel(
            self.agent_steps,
            text="✦ Agent kutish rejimida",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        )
        self.agent_placeholder.pack(pady=12)

    def _build_context_panel(self, parent):
        """Kontekst paneli — faol sessiya va xotira holati"""
        context_card = GlassCard(parent, title="🧠 Kontekst")
        context_card.pack(fill="both", expand=True, pady=(8, 0))

        self.session_summary = ctk.CTkLabel(
            context_card.content,
            text="💬 Sessiya: tayyor",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        )
        self.session_summary.pack(fill="x", pady=(0, 4))

        # Suhbatlar soni
        self.context_count = ctk.CTkLabel(
            context_card.content,
            text="📊 Suhbatlar: 0 ta",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.context_count.pack(fill="x", pady=2)

        # Xotira holati
        self.memory_status = ctk.CTkLabel(
            context_card.content,
            text="💾 Xotira: Faol (SQLite)",
            font=Fonts.SMALL,
            text_color=Colors.SUCCESS,
            anchor="w",
        )
        self.memory_status.pack(fill="x", pady=2)

        # Model
        self.model_label = ctk.CTkLabel(
            context_card.content,
            text="⚡ Model: Gemini 2.5 Flash",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        )
        self.model_label.pack(fill="x", pady=2)

    # ========== FUNKSIYALAR ==========

    def _update_action_button(self):
        """Telegram uslubida: matn bo'sh bo'lsa 🎙️ (Mikrofon), matn yozilsa yoki fayl bo'lsa ➤ (Yuborish)"""
        has_text = bool(self._input_var.get().strip())
        has_attachment = bool(self._attached_file)

        if has_text or has_attachment:
            if self._action_mode != "send":
                self._action_mode = "send"
                self.action_btn.configure(
                    text="➤",
                    font=(Fonts.FAMILY, 15, "bold"),
                    fg_color=Colors.PRIMARY,
                    hover_color=Colors.PRIMARY_HOVER,
                    text_color="#FFFFFF",
                )
        else:
            if self._action_mode != "mic":
                self._action_mode = "mic"
                self.action_btn.configure(
                    text="🎙️",
                    font=(Fonts.FAMILY, 15),
                    fg_color="transparent",
                    hover_color=Colors.BG_HOVER,
                    text_color=Colors.TEXT_MUTED,
                )

    def _on_action_button_click(self):
        """O'ngdagi tugma bosilganda: matn bo'lsa yuboradi, bo'sh bo'lsa ovozli tinglaydi"""
        if self._action_mode == "send":
            self._on_send()
        else:
            self._on_mic_click()

    def _on_enter_pressed(self, event=None):
        """Enter bosilganda xabar yuborish"""
        if self._input_var.get().strip() or self._attached_file:
            self._on_send()

    def _on_mic_click(self):
        """Mikrofon bosilganda ovozli tinglashni boshlash yoki to'xtatish"""
        if self.app and hasattr(self.app, "bridge"):
            bridge = self.app.bridge
            if getattr(bridge, "is_listening", False):
                bridge.stop_listening()
            else:
                bridge.start_listening()
        else:
            if self.app and hasattr(self.app, "navigate_to"):
                self.app.navigate_to("voice")

    def _on_attach_file(self):
        """Fayl biriktirish (skripka belgisi bosilganda)"""
        file_path = filedialog.askopenfilename(
            title="Fayl yoki rasm biriktirish",
            filetypes=[
                (
                    "Barcha qo'llab-quvvatlanadigan fayllar",
                    "*.png;*.jpg;*.jpeg;*.webp;*.pdf;*.txt;*.docx;*.csv;*.py;*.json;*.md",
                ),
                ("Rasmlar", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
                ("Hujjatlar", "*.pdf;*.txt;*.docx;*.csv;*.json;*.md"),
                ("Barcha fayllar", "*.*"),
            ],
        )
        if not file_path:
            return

        self._attached_file = file_path
        self._show_attachment_preview(file_path)
        self._update_action_button()

    def _show_attachment_preview(self, file_path):
        """Biriktirilgan fayl nishonini ko'rsatish"""
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        icon = "🖼️" if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp") else "📄"

        try:
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        except Exception:
            size_str = ""

        disp_text = f"{icon} {filename}" + (f" ({size_str})" if size_str else "")
        self.attachment_label.configure(text=disp_text)
        self.attachment_bar.pack(fill="x", pady=(0, 4), before=self.input_frame)

    def _remove_attached_file(self):
        """Biriktirilgan faylni olib tashlash"""
        self._attached_file = None
        if hasattr(self, "attachment_bar") and self.attachment_bar.winfo_ismapped():
            self.attachment_bar.pack_forget()
        self._update_action_button()

    def _on_send(self, event=None):
        """Xabar yuborish (matn + biriktirilgan fayl)"""
        text = self._input_var.get().strip()
        attached = self._attached_file

        if not text and not attached:
            return

        # Matn va biriktirilgan faylni tozalash
        self._input_var.set("")
        self._attached_file = None
        if hasattr(self, "attachment_bar") and self.attachment_bar.winfo_ismapped():
            self.attachment_bar.pack_forget()

        self._update_action_button()

        # Chatda ko'rinadigan xabar matni
        display_text = text
        if attached:
            fname = os.path.basename(attached)
            display_text = f"📎 [{fname}]\n{text}" if text else f"📎 [{fname}]"

        # Backend ga uzatiladigan buyruq matni
        command_text = text
        if attached:
            command_text = f"[Fayl: {attached}] {text}".strip()

        # Duplikat himoya
        self._last_user_text = display_text

        self.add_message(display_text, "user")
        self.show_typing("yozyapti")

        # Backend ga buyruq yuborish
        if self.app and hasattr(self.app, "bridge"):
            self.app.bridge.send_text_command(command_text)

    def _send_suggestion(self, text):
        """Tezkor taklif yuborish"""
        self._input_var.set(text)
        self._on_send()

    def _clear_chat(self):
        """Suhbatni tozalash"""
        self.hide_typing()
        self._remove_attached_file()
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
        self._messages.clear()
        self._last_user_text = None
        self._add_welcome_message()
        self.context_count.configure(text="📊 Suhbatlar: 0 ta")
        self.session_summary.configure(text="💬 Sessiya: 0 xabar")
        self.clear_agent_steps()

    def show_typing(self, prefix="yozyapti"):
        """Animatsion 'yozyapti . . .' indikatorini ko'rsatish"""
        if self._typing_bubble:
            self._typing_bubble.set_prefix(prefix)
            self._scroll_to_bottom()
            return

        # Birinchi xabar bo'lsa welcome tozalash
        if len(self._messages) == 0:
            for widget in self.chat_scroll.winfo_children():
                widget.destroy()

        self._typing_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        self._typing_row.pack(fill="x", padx=8, pady=3)

        self._typing_bubble = TypingBubble(self._typing_row, prefix=prefix)
        self._typing_bubble.pack(side="left", padx=(4, 80))

        self.after(50, self._scroll_to_bottom)

    def hide_typing(self):
        """Animatsion indikatorni to'xtatish va o'chirish"""
        if self._typing_bubble:
            try:
                self._typing_bubble.stop()
            except Exception:
                pass
            self._typing_bubble = None

        if hasattr(self, "_typing_row") and self._typing_row:
            try:
                self._typing_row.destroy()
            except Exception:
                pass
            self._typing_row = None

    def add_message(self, text, role="user", timestamp=None, track_duplicate=True):
        """Yangi xabar qo'shish — to'g'ri joylashuv bilan"""
        timestamp = timestamp or datetime.datetime.now().strftime("%H:%M")

        # Duplikat user xabar tekshirish
        # (backend callback dan kelgan user xabar — biz allaqachon ko'rsatganmiz)
        if track_duplicate and role == "user" and text == self._last_user_text:
            for msg in self._messages:
                if msg["text"] == text and msg["role"] == "user":
                    return  # Duplikat — o'tkazib yuborish

        # Assistant javob kelganda typing indikatorini avtomatik yopish
        if role == "assistant":
            self.hide_typing()

        # Welcome xabarni tozalash (birinchi xabar)
        if len(self._messages) == 0:
            for widget in self.chat_scroll.winfo_children():
                widget.destroy()

        self._messages.append({"text": text, "role": role, "time": timestamp})
        self._render_message_widget(text, role, timestamp)

        # Kontekst yangilash
        self.context_count.configure(text=f"📊 Suhbatlar: {len(self._messages)} ta")
        self.session_summary.configure(text=f"💬 Sessiya: {len(self._messages)} xabar")

    def _render_message_widget(self, text, role, timestamp):
        is_user = role == "user"

        msg_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        msg_row.pack(fill="x", padx=8, pady=4)

        bubble_frame = MessageBubble(
            msg_row,
            text=text,
            role=role,
            timestamp=timestamp,
        )

        if is_user:
            bubble_frame.pack(side="right", padx=(80, 4))
        else:
            bubble_frame.pack(side="left", padx=(4, 80))

        self.after(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """Chat ni eng pastga scroll qilish"""
        try:
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def clear_agent_steps(self):
        """Agent qadamlari panelini tozalash"""
        for w in self.agent_steps.winfo_children():
            w.destroy()
        self.agent_placeholder = ctk.CTkLabel(
            self.agent_steps,
            text="✦ Agent kutish rejimida",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        )
        self.agent_placeholder.pack(pady=12)
        self._agent_step_count = 0

    def add_agent_step(self, step_num, step_type, data):
        """Agent qadamini o'ng paneldagi kartada ko'rsatish"""
        if hasattr(self, "agent_placeholder") and self.agent_placeholder.winfo_exists():
            self.agent_placeholder.destroy()

        # Agar birinchi qadam bo'lsa yoki yangi vazifa, eskilarni tozalash
        if step_num == 1 or self._agent_step_count == 0:
            for w in self.agent_steps.winfo_children():
                w.destroy()

        self._agent_step_count += 1

        # O'ng panel juda uzun bo'lib ketmasligi uchun maks 5 ta qadam saqlash
        children = self.agent_steps.winfo_children()
        if len(children) >= 5:
            children[0].destroy()

        type_icons = {
            "thought": "💭",
            "action": "⚡",
            "observation": "👁️",
            "final": "✅",
            "error": "❌",
        }

        icon = type_icons.get(step_type, "●")
        color = {
            "thought": Colors.PRIMARY,
            "action": Colors.WARNING,
            "observation": Colors.INFO,
            "final": Colors.SUCCESS,
            "error": Colors.DANGER,
        }.get(step_type, Colors.TEXT_MUTED)

        step_card = ctk.CTkFrame(
            self.agent_steps,
            fg_color=Colors.BG_PANEL,
            corner_radius=10,
            border_width=1,
            border_color=Colors.BORDER,
        )
        step_card.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(step_card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=6)

        title = f"{icon} Qadam {step_num}" if isinstance(step_num, int) else f"{icon} {step_num}"
        ctk.CTkLabel(
            inner,
            text=f"{title}: {step_type.capitalize()}",
            font=Fonts.SMALL_BOLD,
            text_color=color,
            anchor="w",
        ).pack(fill="x")

        if data:
            data_text = str(data).strip()
            ctk.CTkLabel(
                inner,
                text=data_text[:120],
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
                anchor="w",
                wraplength=220,
                justify="left",
            ).pack(fill="x", pady=(2, 0))

        if step_type == "final":
            self._agent_step_count = 0

    def on_show(self):
        """Sahifa ko'rsatilganda"""
        self._refresh_context_stats()
        self.model_label.configure(text=f"Model: {self._get_model_name()}")

    def focus_primary_input(self):
        try:
            self.input_entry.focus_set()
        except Exception:
            pass

    def export_ui_state(self):
        return {
            "messages": list(self._messages),
            "last_user_text": self._last_user_text,
            "input_text": self.input_entry.get(),
            "mode": self.mode_selector.get(),
        }

    def import_ui_state(self, state):
        state = state or {}
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()

        self._messages = []
        replay_messages = state.get("messages", [])
        self._last_user_text = None

        if replay_messages:
            for message in replay_messages:
                self.add_message(
                    message.get("text", ""),
                    message.get("role", "user"),
                    timestamp=message.get("time", ""),
                    track_duplicate=False,
                )
        else:
            self._add_welcome_message()

        self._last_user_text = state.get("last_user_text")
        self.mode_selector.set(state.get("mode", "💬 Chat"))
        self._on_mode_change(self.mode_selector.get())
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, state.get("input_text", ""))

    def _get_model_name(self):
        try:
            from config import get_config

            model = get_config("ai.model", "gemini")
            return "Gemini" if model == "gemini" else "OpenRouter"
        except Exception:
            return "Gemini"

    def _refresh_context_stats(self):
        if self.app and hasattr(self.app, "bridge"):
            try:
                stats = self.app.bridge.get_memory_stats()
                conversations = stats.get("suhbatlar_soni", 0)
                knowledge = stats.get("bilimlar_soni", 0)
                self.context_count.configure(text=f"Suhbatlar: {conversations}")
                self.memory_status.configure(
                    text=f"Xotira: {knowledge} bilim",
                    text_color=Colors.SUCCESS if knowledge else Colors.TEXT_MUTED,
                )
                self.session_summary.configure(
                    text=f"Sessiya: {len(self._messages)} xabar, {knowledge} bilim"
                )
                return
            except Exception:
                pass

        self.session_summary.configure(text=f"Sessiya: {len(self._messages)} xabar")
