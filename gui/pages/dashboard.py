# ========== dashboard.py ==========
# Dashboard sahifasi — AI holati, widget'lar, tezkor buyruqlar

import customtkinter as ctk
import datetime
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, StatWidget, GlowButton, StatusBadge


class DashboardPage(ctk.CTkFrame):
    """Bosh sahifa — markaziy boshqaruv paneli"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._stat_widgets = {}
        self._build_ui()

    def _build_ui(self):
        # ===== SCROLLABLE FRAME =====
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # ===== GREETING BANNER =====
        self._build_greeting()

        # ===== AI STATUS ORB =====
        self._build_ai_orb()

        # ===== QUICK ACTIONS =====
        self._build_quick_actions()

        # ===== STATS GRID =====
        self._build_stats()

        # ===== RECENT ACTIVITY =====
        self._build_activity()

    def _build_greeting(self):
        """Salomlashuv banneri"""
        greeting, emoji = self._get_greeting()
        name = self._get_user_name()

        self.greeting_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.greeting_frame.pack(fill="x", pady=(0, 16))

        # Katta salomlashuv
        self.greeting_label = ctk.CTkLabel(
            self.greeting_frame,
            text=f"{emoji} {greeting}, {name}!",
            font=Fonts.HEADING_1,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.greeting_label.pack(fill="x")

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.greeting_frame,
            text="Mikasa AI sizga xizmat qilishga tayyor 🤖",
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(2, 0))

    def _build_ai_orb(self):
        """AI Status Orb — markaziy holat ko'rsatgich"""
        self.orb_card = GlassCard(self.scroll)
        self.orb_card.pack(fill="x", pady=(0, 16))

        # Orb konteyner
        orb_container = ctk.CTkFrame(self.orb_card.content, fg_color="transparent")
        orb_container.pack(pady=20)

        # AI Orb (katta emoji)
        self.orb_label = ctk.CTkLabel(
            orb_container, text="🔵", font=(Fonts.FAMILY, 64), text_color=Colors.PRIMARY
        )
        self.orb_label.pack()

        # Holat matni
        self.orb_status = ctk.CTkLabel(
            orb_container,
            text="● Tayyor va kutmoqda",
            font=Fonts.BODY_BOLD,
            text_color=Colors.SUCCESS,
        )
        self.orb_status.pack(pady=(8, 0))

        # AI engine info — dinamik tool soni
        try:
            from core.agent_tools import get_registry

            tool_count = get_registry().count
        except Exception:
            tool_count = 20
        self.engine_label = ctk.CTkLabel(
            orb_container,
            text=f"Engine: Gemini + Silero TTS  |  Tools: {tool_count} ta  |  Xotira: Faol",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        )
        self.engine_label.pack(pady=(4, 0))

    def _build_quick_actions(self):
        """Tezkor harakatlar tugmalari"""
        actions_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(0, 16))

        # Sarlavha
        ctk.CTkLabel(
            actions_frame,
            text="⚡  Tezkor harakatlar",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        # Tugmalar grid
        btn_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        actions = [
            (
                "🎤",
                "Tinglash",
                Colors.PRIMARY_DARK,
                lambda: self.app.navigate_to("voice") if self.app else None,
            ),
            (
                "💬",
                "AI Suhbat",
                Colors.SECONDARY_DARK,
                lambda: self.app.navigate_to("chat") if self.app else None,
            ),
            (
                "🌤️",
                "Ob-havo",
                Colors.SUCCESS,
                lambda: self._quick_command("Toshkentda havo qanday?"),
            ),
            (
                "🎵",
                "Musiqa",
                Colors.SECONDARY,
                lambda: self._quick_command("musiqa qo'y"),
            ),
            (
                "💱",
                "Valyuta",
                Colors.WARNING,
                lambda: self._quick_command("bugungi dollar kursi"),
            ),
            (
                "📸",
                "Ekran tahlil",
                Colors.INFO,
                lambda: self._quick_command("ekranda nima bor"),
            ),
        ]

        for i, (icon, text, color, cmd) in enumerate(actions):
            btn = ctk.CTkButton(
                btn_frame,
                text=f" {icon}  {text}",
                font=Fonts.BODY_BOLD,
                fg_color=color,
                hover_color=Colors.BG_HOVER,
                text_color=Colors.TEXT_PRIMARY,
                corner_radius=10,
                height=50,
                command=cmd,
            )
            btn.grid(row=0, column=i, padx=4, pady=4, sticky="ew")

        # Ustunlarni teng qilish
        for i in range(len(actions)):
            btn_frame.columnconfigure(i, weight=1)

    def _build_stats(self):
        """Statistika widgetlari"""
        # Sarlavha
        ctk.CTkLabel(
            self.scroll,
            text="📊  Tizim statistikasi",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        stats_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 16))

        stats = self._get_stats()

        for i, (value, label, icon, color) in enumerate(stats):
            widget = StatWidget(
                stats_frame, value=value, label=label, icon=icon, color=color
            )
            widget.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            self._stat_widgets[label] = widget

        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

    def _build_activity(self):
        """Oxirgi faoliyat ro'yxati — backend bridge tomonidan yangilanadi"""
        activity_card = GlassCard(self.scroll, title="📋  Oxirgi faoliyat")
        activity_card.pack(fill="x", pady=(0, 16))

        # Backend bridge shu frame ga yozadi
        self._activity_list = ctk.CTkFrame(
            activity_card.content, fg_color="transparent"
        )
        self._activity_list.pack(fill="x")

        # Boshlang'ich xabar
        now = datetime.datetime.now().strftime("%H:%M:%S")

        row = ctk.CTkFrame(self._activity_list, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(
            row, text="●", font=(Fonts.FAMILY, 8), text_color=Colors.SUCCESS, width=14
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            row,
            text="🟢 Dastur ishga tushdi",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(row, text=now, font=Fonts.TINY, text_color=Colors.TEXT_MUTED).pack(
            side="right"
        )

    def _quick_command(self, text):
        """Dashboard quick action — buyruqni backend ga yuborish"""
        if self.app and hasattr(self.app, "bridge"):
            self.app.bridge.send_text_command(text)

    def on_show(self):
        """Sahifa ko'rsatilganda chaqiriladi"""
        greeting, emoji = self._get_greeting()
        self.greeting_label.configure(
            text=f"{emoji} {greeting}, {self._get_user_name()}!"
        )

        for value, label, icon, color in self._get_stats():
            widget = self._stat_widgets.get(label)
            if widget:
                widget.set_value(value)
                if hasattr(widget, "icon_label"):
                    widget.icon_label.configure(text_color=color)

        if self.app and hasattr(self.app, "bridge"):
            stats = self.app.bridge.get_memory_stats()
            self.orb_status.configure(
                text=f"● Tayyor va kutmoqda | Suhbatlar: {stats.get('suhbatlar_soni', 0)}"
            )

    def _get_user_name(self):
        try:
            from config import get_config

            return get_config("user.name", "Foydalanuvchi")
        except Exception:
            return "Foydalanuvchi"

    def _get_greeting(self):
        hour = datetime.datetime.now().hour
        if hour < 6:
            return "Xayrli tun", "🌙"
        if hour < 12:
            return "Xayrli tong", "☀️"
        if hour < 18:
            return "Xayrli kun", "🌤️"
        return "Xayrli kech", "🌆"

    def _get_stats(self):
        tool_count = 20
        conversation_count = 110
        knowledge_count = 3
        task_count = 0

        if self.app and hasattr(self.app, "bridge"):
            try:
                bridge = self.app.bridge
                if bridge._agent_memory:
                    memory_stats = bridge.get_memory_stats()
                    conversation_count = memory_stats.get(
                        "suhbatlar_soni", conversation_count
                    )
                    knowledge_count = memory_stats.get("bilimlar_soni", knowledge_count)
                from core.agent_tools import get_registry

                tool_count = get_registry().count
                tasks = bridge.get_scheduler_tasks()
                task_count = len(tasks) if tasks else 0
            except Exception:
                pass

        return [
            (str(tool_count), "Agent Tools", "🛠️", Colors.PRIMARY),
            (str(conversation_count), "Suhbatlar", "💬", Colors.SECONDARY),
            (str(knowledge_count), "Bilimlar", "🧠", Colors.SUCCESS),
            (str(task_count), "Rejalar", "⏰", Colors.WARNING),
        ]
