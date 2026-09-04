# ========== chat.py ==========
# AI Chat sahifasi — suhbat interfeysi + ReAct agent panel

import customtkinter as ctk
import datetime
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, GlowButton


class ChatPage(ctk.CTkFrame):
    """AI bilan matnli suhbat sahifasi"""
    
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._messages = []
        # Duplikat xabardan himoya — oxirgi yuborilgan user xabar
        self._last_user_text = None
        self._build_ui()
    
    def _build_ui(self):
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        
        ctk.CTkLabel(
            header, text="💬  AI Suhbat",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left")
        
        # Suhbatni tozalash
        ctk.CTkButton(
            header, text="🗑️ Tozalash",
            font=Fonts.SMALL,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            width=100, height=30,
            command=self._clear_chat
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
            text_color=Colors.TEXT_PRIMARY
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
            scrollbar_button_hover_color=Colors.BG_HOVER
        )
        self.chat_scroll.pack(fill="both", expand=True, pady=(0, 8))
        
        # Boshlang'ich xabar
        self._add_welcome_message()
    
    def _add_welcome_message(self):
        """Xush kelibsiz xabari"""
        welcome_frame = ctk.CTkFrame(
            self.chat_scroll, fg_color="transparent"
        )
        welcome_frame.pack(fill="x", padx=16, pady=20)
        
        ctk.CTkLabel(
            welcome_frame, text="🤖",
            font=(Fonts.FAMILY, 36)
        ).pack()
        
        ctk.CTkLabel(
            welcome_frame,
            text="Salom! Men Mikasa AI yordamchiman.",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(8, 4))
        
        ctk.CTkLabel(
            welcome_frame,
            text="Savolingizni yozing yoki ovozli buyruq bering",
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY
        ).pack()
        
        # Tezkor savollar
        suggestions_frame = ctk.CTkFrame(
            welcome_frame, fg_color="transparent"
        )
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
                command=lambda s=suggestion: self._send_suggestion(s)
            )
            btn.pack(side="left", padx=4)
    
    def _build_input_bar(self, parent):
        """Matn kiritish paneli"""
        input_frame = ctk.CTkFrame(
            parent, fg_color=Colors.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            height=52
        )
        input_frame.pack(fill="x", pady=(0, 8))
        input_frame.pack_propagate(False)
        
        # Mikrofon tugma
        ctk.CTkButton(
            input_frame, text="🎙️",
            font=(Fonts.FAMILY, 16),
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            width=40, height=40,
            corner_radius=20,
            command=lambda: self.app.navigate_to("voice") if self.app else None
        ).pack(side="left", padx=(4, 0))
        
        # Matn input
        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Xabar yozing...",
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            height=44
        )
        self.input_entry.pack(
            side="left", fill="x", expand=True, padx=8
        )
        self.input_entry.bind("<Return>", self._on_send)
        
        # Send tugma
        self.send_btn = ctk.CTkButton(
            input_frame, text="➤",
            font=(Fonts.FAMILY, 18),
            fg_color=Colors.PRIMARY_DARK,
            hover_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            width=40, height=40,
            corner_radius=20,
            command=self._on_send
        )
        self.send_btn.pack(side="right", padx=4)
    
    def _build_agent_panel(self, parent):
        """Agent thinking paneli"""
        self.agent_card = GlassCard(parent, title="🤖 Agent jarayoni")
        self.agent_card.pack(fill="x", pady=(0, 8))
        
        self.agent_steps = ctk.CTkFrame(
            self.agent_card.content, fg_color="transparent"
        )
        self.agent_steps.pack(fill="x")
        
        # Boshlang'ich holat
        ctk.CTkLabel(
            self.agent_steps,
            text="Agent hali ishlamagan",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED
        ).pack(pady=8)
    
    def _build_context_panel(self, parent):
        """Kontekst paneli"""
        context_card = GlassCard(parent, title="🧠 Kontekst")
        context_card.pack(fill="both", expand=True, pady=(8, 0))
        
        # Suhbatlar soni
        self.context_count = ctk.CTkLabel(
            context_card.content,
            text="Suhbatlar: 0",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w"
        )
        self.context_count.pack(fill="x", pady=2)
        
        # Xotira holati
        self.memory_status = ctk.CTkLabel(
            context_card.content,
            text="Xotira: Faol",
            font=Fonts.SMALL,
            text_color=Colors.SUCCESS,
            anchor="w"
        )
        self.memory_status.pack(fill="x", pady=2)
        
        # Model
        self.model_label = ctk.CTkLabel(
            context_card.content,
            text="Model: Gemini",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w"
        )
        self.model_label.pack(fill="x", pady=2)
    
    # ========== FUNKSIYALAR ==========
    
    def _on_send(self, event=None):
        """Xabar yuborish"""
        text = self.input_entry.get().strip()
        if not text:
            return
        
        self.input_entry.delete(0, "end")
        
        # Duplikat himoya — shu matn callback dan qaytmasligini belgilash
        self._last_user_text = text
        
        self.add_message(text, "user")
        
        # Backend ga buyruq yuborish
        if self.app and hasattr(self.app, 'bridge'):
            self.app.bridge.send_text_command(text)
    
    def _send_suggestion(self, text):
        """Tezkor taklif yuborish"""
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, text)
        self._on_send()
    
    def _clear_chat(self):
        """Suhbatni tozalash"""
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
        self._messages.clear()
        self._last_user_text = None
        self._add_welcome_message()
    
    def add_message(self, text, role="user"):
        """Yangi xabar qo'shish — to'g'ri joylashuv bilan"""
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Duplikat user xabar tekshirish
        # (backend callback dan kelgan user xabar — biz allaqachon ko'rsatganmiz)
        if role == "user" and text == self._last_user_text:
            # Birinchi marta — o'zimiz yuborgan, ruxsat
            # Ikkinchi marta — callback dan, blok
            for msg in self._messages:
                if msg["text"] == text and msg["role"] == "user":
                    return  # Duplikat — o'tkazib yuborish
        
        # Welcome xabarni tozalash (birinchi xabar)
        if len(self._messages) == 0:
            for widget in self.chat_scroll.winfo_children():
                widget.destroy()
        
        self._messages.append({"text": text, "role": role, "time": timestamp})
        
        is_user = (role == "user")
        
        # === XABAR KONTEYNERI ===
        # fill="x" bilan to'liq kenglik oladi — ichida anchor orqali joylashtiramiz
        msg_row = ctk.CTkFrame(
            self.chat_scroll, fg_color="transparent"
        )
        msg_row.pack(fill="x", padx=8, pady=3)
        
        # === BUBBLE ===
        bubble_frame = ctk.CTkFrame(
            msg_row,
            fg_color=Colors.BG_INPUT if is_user else Colors.BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER if is_user else Colors.PRIMARY_DARK
        )
        
        if is_user:
            # O'ng tomonga joylash
            bubble_frame.pack(side="right", padx=(80, 4))
        else:
            # Chap tomonga joylash
            bubble_frame.pack(side="left", padx=(4, 80))
        
        # Xabar matni
        text_label = ctk.CTkLabel(
            bubble_frame, text=text,
            font=Fonts.BODY,
            text_color=Colors.TEXT_PRIMARY,
            wraplength=420,
            justify="left",
            anchor="w"
        )
        text_label.pack(fill="x", padx=14, pady=(10, 4))
        
        # Vaqt va rol belgisi
        role_text = f"Siz • {timestamp}" if is_user else f"AI • {timestamp}"
        time_label = ctk.CTkLabel(
            bubble_frame, text=role_text,
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
            anchor="e" if is_user else "w"
        )
        time_label.pack(fill="x", padx=14, pady=(0, 8))
        
        # Auto-scroll — pastga tushirish
        self.after(50, self._scroll_to_bottom)
        
        # Kontekst yangilash
        self.context_count.configure(text=f"Suhbatlar: {len(self._messages)}")
    
    def _scroll_to_bottom(self):
        """Chat ni eng pastga scroll qilish"""
        try:
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
    
    def add_agent_step(self, step_num, step_type, data):
        """Agent qadamini ko'rsatish"""
        # Eski placeholder'ni tozalash
        for widget in self.agent_steps.winfo_children():
            widget.destroy()
        
        type_icons = {
            "thought": "💭",
            "action": "⚡",
            "observation": "👁️",
            "final": "✅",
            "error": "❌"
        }
        
        icon = type_icons.get(step_type, "●")
        color = {
            "thought": Colors.PRIMARY,
            "action": Colors.WARNING,
            "observation": Colors.INFO,
            "final": Colors.SUCCESS,
            "error": Colors.DANGER
        }.get(step_type, Colors.TEXT_MUTED)
        
        step_frame = ctk.CTkFrame(
            self.agent_steps, fg_color="transparent"
        )
        step_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            step_frame,
            text=f"{icon} Qadam {step_num}: {step_type.capitalize()}",
            font=Fonts.SMALL_BOLD,
            text_color=color, anchor="w"
        ).pack(fill="x")
        
        if isinstance(data, str):
            ctk.CTkLabel(
                step_frame,
                text=data[:100],
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
                anchor="w", wraplength=250
            ).pack(fill="x")
    
    def on_show(self):
        """Sahifa ko'rsatilganda"""
        self.input_entry.focus_set()
