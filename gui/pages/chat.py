# ========== chat.py ==========
# AI Chat sahifasi — suhbat interfeysi

import os
import datetime
from tkinter import filedialog
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.icons import get_vector_icon
from gui.components import (
    CircleIconButton,
    GlassButton,
    MessageBubble,
    TypingBubble,
)

class ChatPage(ctk.CTkFrame):
    """AI bilan matnli suhbat sahifasi"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._messages = []
        self._last_user_text = None
        self._typing_bubble = None
        self._typing_row = None
        self._attached_file = None
        self._action_mode = "mic"
        self._build_ui()

    def _build_ui(self):
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")

        chat_icon_img = get_vector_icon("chat", size=22, color=Colors.PRIMARY, fallback="chat")
        if chat_icon_img:
            ctk.CTkLabel(title_frame, text="", image=chat_icon_img).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_frame,
            text="AI Suhbat",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        # Suhbatni tozalash
        GlassButton(
            header,
            text="Tozalash",
            icon="trash",
            font=Fonts.SMALL,
            width=105,
            height=32,
            corner_radius=999,
            command=self._clear_chat,
        ).pack(side="right")

        # ===== ASOSIY KONTENT — SINGLE COLUMN =====
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20)
        
        self._build_chat_area(content)
        self._build_input_bar(content)

    def _build_chat_area(self, parent):
        self.chat_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.chat_scroll.pack(fill="both", expand=True, pady=(0, 6))

        self._add_welcome_message()

    def _add_welcome_message(self):
        welcome_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        welcome_frame.pack(fill="x", pady=(60, 20))

        ai_icon = get_vector_icon("sparkles", size=40, color=Colors.PRIMARY)
        if ai_icon:
            ctk.CTkLabel(welcome_frame, text="", image=ai_icon).pack(pady=(4, 2))

        ctk.CTkLabel(
            welcome_frame,
            text="Mikasa AI bilan suhbat",
            font=Fonts.HEADING_1,
            text_color=Colors.TEXT_PRIMARY,
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            welcome_frame,
            text="Savolingizni yozing yoki ovozli buyruq bering",
            font=Fonts.BODY,
            text_color=Colors.TEXT_MUTED,
        ).pack()

        suggestions_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        suggestions_frame.pack(pady=(20, 0))

        suggestions = [
            ("search", "Havo qanday?"),
            ("sparkles", "Dollar kursi necha?"),
            ("play", "Musiqa qo'y"),
        ]

        for icon_name, suggestion in suggestions:
            btn = GlassButton(
                suggestions_frame,
                text=suggestion,
                icon=icon_name,
                font=Fonts.SMALL,
                corner_radius=Sizing.PILL,
                height=34,
                command=lambda s=suggestion: self._send_suggestion(s),
            )
            btn.pack(side="left", padx=4)

    def _build_input_bar(self, parent):
        self.attachment_bar = ctk.CTkFrame(
            parent,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizing.RADIUS_BUTTON,
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

        CircleIconButton(
            self.attachment_bar,
            icon="close",
            size=26,
            font=Fonts.TINY,
            command=self._remove_attached_file,
        ).pack(side="right", padx=6)

        self.input_frame = ctk.CTkFrame(
            parent,
            fg_color=Colors.BG_INPUT,
            corner_radius=27,
            border_width=1,
            border_color=Colors.BORDER,
            height=54,
        )
        self.input_frame.pack(fill="x", pady=(0, 8))
        self.input_frame.pack_propagate(False)

        self.attach_btn = CircleIconButton(
            self.input_frame,
            icon="attach",
            size=38,
            fg_color=Colors.GLASS_BG,
            hover_color=Colors.GLASS_BG_HOVER,
            border_color=Colors.GLASS_BORDER,
            border_hover_color=Colors.GLASS_BORDER_HOVER,
            border_width=1,
            bg_color=Colors.BG_INPUT,
            text_color="#FFFFFF",
            command=self._on_attach_file,
        )
        self.attach_btn.pack(side="left", padx=(8, 4), pady=8)

        self.action_btn = CircleIconButton(
            self.input_frame,
            icon="mic",
            size=38,
            fg_color=Colors.GLASS_BG,
            hover_color=Colors.GLASS_BG_HOVER,
            border_color=Colors.GLASS_BORDER,
            border_hover_color=Colors.GLASS_BORDER_HOVER,
            border_width=1,
            bg_color=Colors.BG_INPUT,
            text_color=Colors.PRIMARY,
            command=self._on_action_button_click,
        )
        self.action_btn.pack(side="right", padx=(4, 8), pady=8)

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
            height=38,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=4, pady=8)
        self.input_entry.bind("<Return>", self._on_enter_pressed)
        
        self.send_btn = self.action_btn

    def _update_action_button(self):
        has_text = bool(self._input_var.get().strip())
        has_attachment = bool(self._attached_file)

        if has_text or has_attachment:
            if self._action_mode != "send":
                self._action_mode = "send"
                self.action_btn.configure(
                    icon="send",
                    fg_color=Colors.GLASS_HERO_BG,
                    hover_color=Colors.GLASS_HERO_HOVER,
                    border_color=Colors.GLASS_HERO_BORDER,
                    border_width=1,
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
                    border_width=1,
                    text_color=Colors.PRIMARY,
                )

    def _on_action_button_click(self):
        if self._action_mode == "send":
            self._on_send()
        else:
            self._on_mic_click()

    def _on_enter_pressed(self, event=None):
        if self._input_var.get().strip() or self._attached_file:
            self._on_send()

    def _on_mic_click(self):
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
        self.attach_btn.configure(
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            border_width=0,
            text_color="#FFFFFF",
        )
        self._update_action_button()

    def _show_attachment_preview(self, file_path):
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        icon_name = "image" if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp") else "file"

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

        disp_text = f"  {filename}" + (f" ({size_str})" if size_str else "")
        v_img = get_vector_icon(icon_name, size=14, color_dark=Colors.PRIMARY, color_light=Colors.PRIMARY, fallback="file")
        if v_img:
            self.attachment_label.configure(image=v_img, compound="left", text=disp_text)
        else:
            self.attachment_label.configure(image=None, text=disp_text)
        self.attachment_bar.pack(fill="x", pady=(0, 4), before=self.input_frame)

    def _remove_attached_file(self):
        self._attached_file = None
        if hasattr(self, "attachment_bar") and self.attachment_bar.winfo_ismapped():
            self.attachment_bar.pack_forget()
        if hasattr(self, "attachment_label"):
            self.attachment_label.configure(image=None, text="")
        self.attach_btn.configure(
            fg_color=Colors.GLASS_BG,
            hover_color=Colors.GLASS_BG_HOVER,
            border_width=1,
            border_color=Colors.GLASS_BORDER,
            text_color="#FFFFFF",
        )
        self._update_action_button()

    def _on_send(self, event=None):
        text = self._input_var.get().strip()
        attached = self._attached_file

        if not text and not attached:
            return

        self._input_var.set("")
        self._attached_file = None
        if hasattr(self, "attachment_bar") and self.attachment_bar.winfo_ismapped():
            self.attachment_bar.pack_forget()

        self._update_action_button()

        display_text = text
        if attached:
            fname = os.path.basename(attached)
            display_text = f"[{fname}]\n{text}" if text else f"[{fname}]"

        command_text = text
        if attached:
            command_text = f"[Fayl: {attached}] {text}".strip()

        self._last_user_text = display_text

        self.add_message(display_text, "user")
        self.show_typing("yozyapti")

        if self.app and hasattr(self.app, "bridge"):
            self.app.bridge.send_text_command(command_text)

    def _send_suggestion(self, text):
        self._input_var.set(text)
        self._on_send()

    def _clear_chat(self):
        self.hide_typing()
        self._remove_attached_file()
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
        self._messages.clear()
        self._last_user_text = None
        self._add_welcome_message()

    def show_typing(self, prefix="yozyapti"):
        if self._typing_bubble:
            self._typing_bubble.set_prefix(prefix)
            self._scroll_to_bottom()
            return

        if len(self._messages) == 0:
            for widget in self.chat_scroll.winfo_children():
                widget.destroy()

        self._typing_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        self._typing_row.pack(fill="x", padx=8, pady=3)

        self._typing_bubble = TypingBubble(self._typing_row, prefix=prefix)
        self._typing_bubble.pack(side="left", padx=(4, 80))

        self.after(50, self._scroll_to_bottom)

    def hide_typing(self):
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
        timestamp = timestamp or datetime.datetime.now().strftime("%H:%M")

        if track_duplicate and role == "user" and text == self._last_user_text:
            for msg in self._messages:
                if msg["text"] == text and msg["role"] == "user":
                    return

        if role == "assistant":
            self.hide_typing()

        if len(self._messages) == 0:
            for widget in self.chat_scroll.winfo_children():
                widget.destroy()

        self._messages.append({"text": text, "role": role, "time": timestamp})
        self._render_message_widget(text, role, timestamp)

    def _render_message_widget(self, text, role, timestamp):
        is_user = role == "user"

        msg_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        msg_row.pack(fill="x", padx=12, pady=3)

        bubble_frame = MessageBubble(
            msg_row,
            text=text,
            role=role,
            timestamp=timestamp,
        )

        if is_user:
            bubble_frame.pack(side="right", padx=(80, 8))
        else:
            bubble_frame.pack(side="left", padx=(8, 60))

        self.after(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        try:
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def add_agent_step(self, step_num, step_type, data):
        before_kw = {}
        if hasattr(self, "_typing_row") and self._typing_row and self._typing_row.winfo_exists():
            before_kw = {"before": self._typing_row}
            
        type_icons = {
            "thought": "chat",
            "action": "commands",
            "observation": "search",
            "final": "check",
            "error": "close",
        }

        icon_name = type_icons.get(step_type, "circle")
        color = {
            "thought": Colors.PRIMARY,
            "action": Colors.WARNING,
            "observation": Colors.INFO,
            "final": Colors.SUCCESS,
            "error": Colors.DANGER,
        }.get(step_type, Colors.TEXT_MUTED)
        
        step_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        step_row.pack(fill="x", padx=12, pady=2, **before_kw)
        
        step_content = ctk.CTkFrame(
            step_row,
            fg_color=Colors.BG_PANEL,
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER,
        )
        step_content.pack(side="left", padx=(4, 80))
        
        title_row = ctk.CTkFrame(step_content, fg_color="transparent")
        title_row.pack(fill="x", padx=8, pady=(4, 2))
        
        step_icon_img = get_vector_icon(icon_name, size=12, color=color, fallback="circle")
        if step_icon_img:
            ctk.CTkLabel(title_row, text="", image=step_icon_img).pack(side="left", padx=(0, 4))
            
        title = f"Qadam {step_num}" if isinstance(step_num, int) else f"{step_num}"
        ctk.CTkLabel(
            title_row,
            text=f"{title}: {step_type.capitalize()}",
            font=Fonts.SMALL_BOLD,
            text_color=color,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        if data:
            data_text = str(data).strip()
            ctk.CTkLabel(
                step_content,
                text=data_text[:120],
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
                anchor="w",
                wraplength=220,
                justify="left",
            ).pack(fill="x", padx=8, pady=(0, 4))
            
        self.after(50, self._scroll_to_bottom)

    def on_show(self):
        pass

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
        
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, state.get("input_text", ""))
