# ========== chat.py ==========
# AI Chat sahifasi — Open conversation-first workspace

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


class AgentActivityGroup(ctk.CTkFrame):
    """
    Agent amallarini (tool call, status) ixcham va toza inline ko'rsatuvchi komponent.
    Foydalanuvchiga faqat toza amallar holati (masalan: '✓ app_check bajarildi') ko'rsatiladi.
    Ichki reasoning / thought matnlari bu yerda hech qachon ko'rsatilmaydi.
    Bir nechta amallar bo'lsa, 'Batafsil' tugmasi bilan ochiladigan ixcham guruhga birlashtiriladi.
    """

    def __init__(self, master, before_widget=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        if before_widget and before_widget.winfo_exists():
            self.pack(fill="x", padx=4, pady=(6, 8), before=before_widget)
        else:
            self.pack(fill="x", padx=4, pady=(6, 8))

        self._actions = []
        self._is_collapsed = True
        self._is_finished = False

        # Header identity row
        self.header_row = ctk.CTkFrame(self, fg_color="transparent")
        self.header_row.pack(fill="x", padx=2, pady=(0, 2))

        sparkle_img = get_vector_icon(
            "sparkles",
            size=13,
            color_dark=Colors.PRIMARY,
            color_light=Colors.PRIMARY,
            fallback="sparkles",
        )
        if sparkle_img:
            ctk.CTkLabel(self.header_row, image=sparkle_img, text="").pack(
                side="left", padx=(0, 6)
            )

        ctk.CTkLabel(
            self.header_row,
            text="Mikasa",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.PRIMARY,
            anchor="w",
        ).pack(side="left")

        self.summary_label = ctk.CTkLabel(
            self.header_row,
            text="• asbob ishlatilmoqda...",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.summary_label.pack(side="left", padx=(6, 0))

        # Compact container
        self.box = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
        )
        self.box.pack(fill="x", padx=2, pady=(2, 2))

        self.items_container = ctk.CTkFrame(self.box, fg_color="transparent")
        self.items_container.pack(fill="x", padx=10, pady=6)

        self.details_frame = ctk.CTkFrame(self.box, fg_color="transparent")

        self.bottom_bar = ctk.CTkFrame(self.box, fg_color="transparent", height=24)
        self.bottom_bar.pack(fill="x", padx=8, pady=(0, 4))
        self.bottom_bar.pack_propagate(False)

        self.toggle_btn = ctk.CTkButton(
            self.bottom_bar,
            text="Batafsil",
            font=Fonts.TINY,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.PRIMARY,
            height=20,
            width=64,
            corner_radius=6,
            command=self._toggle_details,
        )
        self.toggle_btn.pack(side="right")
        self.bottom_bar.pack_forget()

    def add_action(self, tool_name: str, detail: str = ""):
        for act in self._actions:
            if act["tool"] == tool_name and act["detail"] == detail:
                return
        self._actions.append({"tool": tool_name, "detail": detail})
        self._render_items()

    def finish(self):
        self._is_finished = True
        self._render_items()

    def _render_items(self):
        for child in self.items_container.winfo_children():
            child.destroy()
        for child in self.details_frame.winfo_children():
            child.destroy()

        check_icon = get_vector_icon(
            "check",
            size=12,
            color_dark=Colors.SUCCESS,
            color_light=Colors.SUCCESS,
            fallback="check",
        )
        pulse_icon = get_vector_icon(
            "circle",
            size=8,
            color_dark=Colors.PRIMARY,
            color_light=Colors.PRIMARY,
            fallback="circle",
        )

        count = len(self._actions)
        if count == 0:
            return

        if self._is_finished:
            self.summary_label.configure(
                text=f"• {count} ta amal bajarildi" if count > 1 else "• amal bajarildi"
            )
        else:
            self.summary_label.configure(text="• ishlamoqda...")

        for idx, act in enumerate(self._actions):
            row = ctk.CTkFrame(self.items_container, fg_color="transparent")
            row.pack(fill="x", pady=2)

            is_last = idx == count - 1
            icon = check_icon if (self._is_finished or not is_last) else pulse_icon

            if icon:
                ctk.CTkLabel(row, image=icon, text="").pack(side="left", padx=(0, 6))

            t_name = act["tool"]
            status_text = (
                f"{t_name} bajarildi"
                if (self._is_finished or not is_last)
                else f"{t_name} ishlatilmoqda..."
            )
            ctk.CTkLabel(
                row,
                text=status_text,
                font=Fonts.SMALL,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
            ).pack(side="left")

        # Batafsil tugmasi (agar tafsilotlar mavjud bo'lsa)
        has_details = any(bool(a.get("detail")) for a in self._actions)
        if has_details:
            for act in self._actions:
                if act.get("detail"):
                    ctk.CTkLabel(
                        self.details_frame,
                        text=f"• {act['tool']}: {act['detail'][:140]}",
                        font=Fonts.TINY,
                        text_color=Colors.TEXT_MUTED,
                        anchor="w",
                        justify="left",
                        wraplength=640,
                    ).pack(fill="x", padx=10, pady=2)

            if not self.bottom_bar.winfo_ismapped():
                self.bottom_bar.pack(fill="x", padx=8, pady=(0, 4))
        else:
            if self.bottom_bar.winfo_ismapped():
                self.bottom_bar.pack_forget()

    def _toggle_details(self):
        self._is_collapsed = not self._is_collapsed
        if self._is_collapsed:
            if self.details_frame.winfo_ismapped():
                self.details_frame.pack_forget()
            self.toggle_btn.configure(text="Batafsil")
        else:
            self.details_frame.pack(
                fill="x", padx=10, pady=(0, 6), before=self.bottom_bar
            )
            self.toggle_btn.configure(text="Yopish")


class ChatPage(ctk.CTkFrame):
    """AI bilan matnli suhbat sahifasi — Open conversation-first workspace"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._messages = []
        self._last_user_text = None
        self._welcome_frame = None
        self._typing_bubble = None
        self._typing_row = None
        self._attached_file = None
        self._action_mode = "mic"
        self._active_activity_group = None
        self._is_focused = False
        self._build_ui()

    def _build_ui(self):
        # ===== HEADER (Minimal) =====
        header = ctk.CTkFrame(self, fg_color="transparent", height=42)
        header.pack(fill="x", padx=24, pady=(12, 4))
        header.pack_propagate(False)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")

        chat_icon_img = get_vector_icon(
            "chat", size=18, color=Colors.PRIMARY, fallback="chat"
        )
        if chat_icon_img:
            ctk.CTkLabel(title_frame, text="", image=chat_icon_img).pack(
                side="left", padx=(0, 8)
            )

        ctk.CTkLabel(
            title_frame,
            text="AI Suhbat",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        # Suhbatni tozalash (subtle, minimal)
        self.clear_btn = ctk.CTkButton(
            header,
            text="Tozalash",
            font=Fonts.SMALL,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_MUTED,
            height=28,
            width=76,
            corner_radius=Sizing.RADIUS_BUTTON,
            command=self._clear_chat,
        )
        self.clear_btn.pack(side="right")

        # ===== OPEN WORKSPACE & CENTERED CONVERSATION COLUMN =====
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True)

        self.conversation_column = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.conversation_column.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        self.workspace.bind("<Configure>", self._on_workspace_resize)

        self._build_chat_area(self.conversation_column)
        self._build_input_bar(self.conversation_column)

    def _on_workspace_resize(self, event=None):
        try:
            if not self.workspace.winfo_exists():
                return
            w = self.workspace.winfo_width()
            if w < 100:
                return
            target_max = 780
            if w > target_max + 48:
                pad_x = (w - target_max) // 2
            else:
                pad_x = 16
            self.conversation_column.pack_configure(padx=pad_x)
        except Exception:
            pass

    def _build_chat_area(self, parent):
        self.chat_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.chat_scroll.pack(fill="both", expand=True, pady=(0, 8))

        self._add_welcome_message()

    def _add_welcome_message(self):
        self._welcome_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        self._welcome_frame.pack(fill="x", pady=(70, 20))

        ai_icon = get_vector_icon("sparkles", size=36, color=Colors.PRIMARY)
        if ai_icon:
            ctk.CTkLabel(self._welcome_frame, text="", image=ai_icon).pack(pady=(4, 6))

        ctk.CTkLabel(
            self._welcome_frame,
            text="Mikasa",
            font=Fonts.HEADING_1,
            text_color=Colors.TEXT_PRIMARY,
        ).pack(pady=(4, 2))

        ctk.CTkLabel(
            self._welcome_frame,
            text="Qanday yordam beray?",
            font=Fonts.BODY,
            text_color=Colors.TEXT_MUTED,
        ).pack(pady=(0, 16))

        suggestions_frame = ctk.CTkFrame(self._welcome_frame, fg_color="transparent")
        suggestions_frame.pack(pady=(6, 0))

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

    def _remove_welcome_message(self):
        if hasattr(self, "_welcome_frame") and self._welcome_frame:
            try:
                self._welcome_frame.destroy()
            except Exception:
                pass
            self._welcome_frame = None

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
            corner_radius=26,
            border_width=1,
            border_color=Colors.BORDER,
            height=52,
        )
        self.input_frame.pack(fill="x", pady=(0, 4))
        self.input_frame.pack_propagate(False)

        # Hover va focus holatlari
        self.input_frame.bind("<Enter>", self._on_input_frame_enter)
        self.input_frame.bind("<Leave>", self._on_input_frame_leave)

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
        self.attach_btn.pack(side="left", padx=(7, 4), pady=7)

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
        self.action_btn.pack(side="right", padx=(4, 7), pady=7)

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
        self.input_entry.pack(side="left", fill="x", expand=True, padx=4, pady=7)
        self.input_entry.bind("<Return>", self._on_enter_pressed)
        self.input_entry.bind("<FocusIn>", self._on_input_focus_in)
        self.input_entry.bind("<FocusOut>", self._on_input_focus_out)

        self.send_btn = self.action_btn

    def _on_input_focus_in(self, event=None):
        self._is_focused = True
        self.input_frame.configure(border_color=Colors.PRIMARY)

    def _on_input_focus_out(self, event=None):
        self._is_focused = False
        self.input_frame.configure(border_color=Colors.BORDER)

    def _on_input_frame_enter(self, event=None):
        if not self._is_focused:
            self.input_frame.configure(border_color=Colors.BORDER_HOVER)

    def _on_input_frame_leave(self, event=None):
        if not self._is_focused:
            self.input_frame.configure(border_color=Colors.BORDER)

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
        icon_name = (
            "image"
            if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp")
            else "file"
        )

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
        v_img = get_vector_icon(
            icon_name,
            size=14,
            color_dark=Colors.PRIMARY,
            color_light=Colors.PRIMARY,
            fallback="file",
        )
        if v_img:
            self.attachment_label.configure(
                image=v_img, compound="left", text=disp_text
            )
        else:
            self.attachment_label.configure(image=None, text=disp_text)
        self.attachment_bar.pack(
            fill="x", pady=(0, 4), before=self.input_frame
        )

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
        if self._active_activity_group and self._active_activity_group.winfo_exists():
            try:
                self._active_activity_group.destroy()
            except Exception:
                pass
        self._active_activity_group = None

        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
        self._messages.clear()
        self._last_user_text = None
        self._add_welcome_message()

    def show_typing(self, prefix="yozyapti"):
        if self._typing_bubble:
            self._typing_bubble.set_prefix(prefix)
            self._scroll_to_bottom(force=False)
            return

        self._remove_welcome_message()

        self._typing_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        self._typing_row.pack(fill="x", padx=4, pady=(4, 2))

        self._typing_bubble = TypingBubble(self._typing_row, prefix=prefix)
        self._typing_bubble.pack(side="left", padx=(4, 60))

        self.after(50, lambda: self._scroll_to_bottom(force=False))

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
            if (
                self._active_activity_group
                and self._active_activity_group.winfo_exists()
            ):
                self._active_activity_group.finish()
                self._active_activity_group = None

        self._remove_welcome_message()

        self._messages.append({"text": text, "role": role, "time": timestamp})
        self._render_message_widget(text, role, timestamp)

    def _render_message_widget(self, text, role, timestamp):
        is_user = role == "user"

        # Ritm: bir xil so'zlovchidan bo'lsa 3-4px, turli bo'lsa 14-16px
        pady = 3
        if len(self._messages) > 1:
            prev_role = self._messages[-2].get("role")
            if prev_role != role:
                pady = (14, 4)
            else:
                pady = (2, 3)

        msg_row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        msg_row.pack(fill="x", padx=4, pady=pady)

        bubble_frame = MessageBubble(
            msg_row,
            text=text,
            role=role,
            timestamp=timestamp,
        )

        if is_user:
            bubble_frame.pack(side="right", padx=(60, 4))
        else:
            bubble_frame.pack(side="left", padx=(4, 40))

        self.after(50, lambda: self._scroll_to_bottom(force=is_user))

    def _scroll_to_bottom(self, force=False):
        try:
            canvas = self.chat_scroll._parent_canvas
            if not force:
                yview = canvas.yview()
                if yview and len(yview) == 2:
                    bottom = yview[1]
                    if bottom < 0.88:
                        return
            canvas.yview_moveto(1.0)
        except Exception:
            pass

    def add_agent_step(self, step_num, step_type, data):
        """
        Agent amallarini (tool call, status) ko'rsatish.
        MUHIM:
        - Ichki reasoning / thought matnlari FOYDALANUVCHIGA KO'RSATILMAYDI (yashiriladi).
        - Tool chaqiruvlari ixcham inline status sifatida guruhlanadi.
        - 'Yakun: Final' kartasi ko'rsatilmaydi (yakuniy javob add_message orqali keladi).
        """
        if step_type == "thought":
            # Ichki reasoning / chain-of-thought foydalanuvchiga matn qilib ko'rsatilmaydi!
            # Faqat silliq yozish indikatoriga 'O'ylamoqda...' statusini beramiz
            self.show_typing("O'ylamoqda...")
            return

        elif step_type == "action":
            # Tool ishlatilishi
            self._remove_welcome_message()
            data_str = str(data).strip()
            if ":" in data_str:
                tool_name = data_str.split(":")[0].strip("'\" ")
                tool_detail = data_str.split(":", 1)[1].strip()
            else:
                tool_name = data_str
                tool_detail = ""

            if not tool_name or tool_name.lower() in ("action", "asbob"):
                tool_name = "Asbob"

            if (
                not self._active_activity_group
                or not self._active_activity_group.winfo_exists()
            ):
                before_w = (
                    self._typing_row
                    if (
                        hasattr(self, "_typing_row")
                        and self._typing_row
                        and self._typing_row.winfo_exists()
                    )
                    else None
                )
                self._active_activity_group = AgentActivityGroup(
                    self.chat_scroll, before_widget=before_w
                )

            self._active_activity_group.add_action(tool_name, tool_detail)
            self.show_typing(f"{tool_name} bajarilmoqda...")
            self.after(50, lambda: self._scroll_to_bottom(force=False))

        elif step_type == "final":
            # Yakuniy javob add_message orqali chiqadi, ortiqcha debug karta chizilmaydi
            if (
                self._active_activity_group
                and self._active_activity_group.winfo_exists()
            ):
                self._active_activity_group.finish()
                self._active_activity_group = None
            self.hide_typing()

        elif step_type == "error":
            self._remove_welcome_message()
            if (
                not self._active_activity_group
                or not self._active_activity_group.winfo_exists()
            ):
                before_w = (
                    self._typing_row
                    if (
                        hasattr(self, "_typing_row")
                        and self._typing_row
                        and self._typing_row.winfo_exists()
                    )
                    else None
                )
                self._active_activity_group = AgentActivityGroup(
                    self.chat_scroll, before_widget=before_w
                )
            self._active_activity_group.add_action("Xatolik", str(data))
            self.after(50, lambda: self._scroll_to_bottom(force=False))

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
