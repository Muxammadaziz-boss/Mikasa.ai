# ========== dashboard.py ==========
# Mikasa AI v6.0.0 — Apple Dark Minimal Dashboard
# Toza, zamonaviy va nafis interfeys

import customtkinter as ctk
import datetime
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassButton, GlassCard, GlowButton, StatWidget, StatusBadge


class DashboardPage(ctk.CTkFrame):
    """Bosh sahifa — Apple uslubidagi minimalist boshqaruv paneli"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color=Colors.BG_DARK, **kwargs)
        self.app = app
        self._stat_widgets = {}
        self._build_ui()

    def _build_ui(self):
        # ===== SCROLLABLE FRAME =====
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=Colors.BG_DARK,
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.scroll.pack(fill="both", expand=True, padx=60, pady=20)

        # ===== GREETING BANNER =====
        self._build_greeting()

        # ===== AI STATUS HERO CARD (Apple Intelligence style) =====
        self._build_ai_hero()

        # ===== QUICK ACTIONS =====
        self._build_quick_actions()

        # ===== STATS GRID =====
        self._build_stats()

        # ===== RECENT ACTIVITY =====
        self._build_activity()

    def _build_greeting(self):
        """Salomlashuv sarlavhasi"""
        greeting, emoji = self._get_greeting()
        name = self._get_user_name()

        self.greeting_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.greeting_frame.pack(fill="x", pady=(0, 20))

        # Katta salomlashuv
        self.greeting_label = ctk.CTkLabel(
            self.greeting_frame,
            text=f"{emoji}  {greeting}, {name}!",
            font=(Fonts.FAMILY, 24, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.greeting_label.pack(fill="x")

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.greeting_frame,
            text="Mikasa AI shaxsiy assistenti barcha vazifalarga tayyor",
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(4, 0))

    def _build_ai_hero(self):
        """Apple Intelligence uslubidagi markaziy holat kartasi"""
        self.orb_card = GlassCard(self.scroll, padding=20)
        self.orb_card.pack(fill="x", pady=(0, 20))

        hero_inner = ctk.CTkFrame(self.orb_card.content, fg_color="transparent")
        hero_inner.pack(fill="x")

        # Yuqori qism: Holat + Emblem
        top_row = ctk.CTkFrame(hero_inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(4, 12))

        # Chap tomonda Siri/Intelligence uslubidagi nafis doira
        emblem_frame = ctk.CTkFrame(
            top_row,
            fg_color=Colors.PRIMARY_SOFT,
            corner_radius=24,
            width=48,
            height=48,
            bg_color=Colors.BG_CARD,
        )
        emblem_frame.pack(side="left")
        emblem_frame.pack_propagate(False)

        self.emblem_label = ctk.CTkLabel(
            emblem_frame,
            text="✦",
            font=(Fonts.FAMILY, 22),
            text_color=Colors.PRIMARY,
        )
        self.emblem_label.pack(expand=True)

        # Matn bloki
        text_block = ctk.CTkFrame(top_row, fg_color="transparent")
        text_block.pack(side="left", padx=16, fill="x", expand=True)

        status_row = ctk.CTkFrame(text_block, fg_color="transparent")
        status_row.pack(fill="x")

        # Yashil nuqta
        ctk.CTkLabel(
            status_row,
            text="●",
            font=(Fonts.FAMILY, 10),
            text_color=Colors.SUCCESS,
            width=14,
        ).pack(side="left")

        self.orb_status = ctk.CTkLabel(
            status_row,
            text="Mikasa AI tayyor va kutmoqda",
            font=(Fonts.FAMILY, 14, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.orb_status.pack(side="left", padx=4)

        self.desc_label = ctk.CTkLabel(
            text_block,
            text="Ovozli va matnli buyruqlarni qabul qilishga to'liq shay holatda",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.desc_label.pack(fill="x", pady=(2, 0))

        # Ajratuvchi chiziq
        ctk.CTkFrame(hero_inner, fg_color=Colors.BORDER, height=1).pack(fill="x", pady=12)

        # Pastki qism: 3 ta toza pill badge
        badges_row = ctk.CTkFrame(hero_inner, fg_color="transparent")
        badges_row.pack(fill="x")

        try:
            from core.agent_tools import get_registry
            tool_count = get_registry().count
        except Exception:
            tool_count = 29

        chips = [
            ("⚡", "Gemini 2.5 Flash"),
            ("🛠️", f"{tool_count} ta Vosita"),
            ("🧠", "Vektor Xotira Faol"),
            ("🎙️", "Tezkor VAD Oqim"),
        ]

        for icon, chip_text in chips:
            chip = ctk.CTkFrame(
                badges_row,
                fg_color=Colors.GLASS_BG,
                corner_radius=999,
                border_width=1,
                border_color=Colors.GLASS_BORDER,
                bg_color=Colors.BG_CARD,
            )
            chip.pack(side="left", padx=(0, 10))

            inner_chip = ctk.CTkFrame(chip, fg_color="transparent")
            inner_chip.pack(padx=14, pady=6)

            ctk.CTkLabel(
                inner_chip,
                text=f"{icon}  {chip_text}",
                font=Fonts.SMALL_BOLD,
                text_color="#E2E2EC",
            ).pack()

    def _build_quick_actions(self):
        """Tezkor harakatlar tugmalari — Apple Capsule uslubida"""
        actions_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(0, 20))

        # Sarlavha
        ctk.CTkLabel(
            actions_frame,
            text="Tezkor harakatlar",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        # Tugmalar konteyneri
        btn_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        actions = [
            (
                "🎙️",
                "Tinglash",
                True,  # Primary Hero Action
                lambda: self.app.navigate_to("voice") if self.app else None,
            ),
            (
                "💬",
                "AI Suhbat",
                False,
                lambda: self.app.navigate_to("chat") if self.app else None,
            ),
            (
                "🌤️",
                "Ob-havo",
                False,
                lambda: self._quick_command("Toshkentda havo qanday?"),
            ),
            (
                "🎵",
                "Musiqa",
                False,
                lambda: self._quick_command("musiqa qo'y"),
            ),
            (
                "💱",
                "Valyuta",
                False,
                lambda: self._quick_command("bugungi dollar kursi"),
            ),
            (
                "👁️",
                "Ekran tahlil",
                False,
                lambda: self._quick_command("ekranda nima bor"),
            ),
        ]

        for i, (icon, text, is_hero, cmd) in enumerate(actions):
            if is_hero:
                # Apple Hero Glow Button — Full Pill Capsule (zero boxiness!)
                btn = GlowButton(
                    btn_frame,
                    text=text,
                    icon=icon,
                    width=200,
                    height=48,
                    corner_radius=999,
                    command=cmd,
                )
                btn.grid(row=0, column=i, padx=6, pady=4)
            else:
                # Apple Dark Glass Capsule Button — Full Pill Capsule (zero boxiness!)
                btn = GlassButton(
                    btn_frame,
                    text=text,
                    icon=icon,
                    width=140,
                    height=48,
                    corner_radius=999,
                    command=cmd,
                )
                btn.grid(row=0, column=i, padx=4, pady=4)

    def _build_stats(self):
        """Statistika kartalari — Apple minimal widgetlari"""
        # Sarlavha
        ctk.CTkLabel(
            self.scroll,
            text="Tizim statistikasi",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        stats_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))

        stats = self._get_stats()

        for i, (value, label, icon, color) in enumerate(stats):
            widget = StatWidget(
                stats_frame, value=value, label=label, icon=icon, color=color
            )
            widget.grid(row=0, column=i, padx=8, pady=4, sticky="ew")
            self._stat_widgets[label] = widget

        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

    def _build_activity(self):
        """Oxirgi faoliyat ro'yxati — Apple uslubidagi toza timeline"""
        activity_card = GlassCard(self.scroll, title="Oxirgi faoliyat")
        activity_card.pack(fill="x", pady=(0, 20))

        self._activity_list = ctk.CTkFrame(
            activity_card.content, fg_color="transparent"
        )
        self._activity_list.pack(fill="x")

        now = datetime.datetime.now().strftime("%H:%M:%S")

        row = ctk.CTkFrame(
            self._activity_list,
            fg_color=Colors.GLASS_BG,
            corner_radius=10,
            border_width=1,
            border_color=Colors.GLASS_BORDER,
        )
        row.pack(fill="x", pady=2)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=7)

        ctk.CTkLabel(
            inner, text="✨", font=(Fonts.FAMILY, 11), text_color=Colors.SUCCESS, width=16
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            inner,
            text="Mikasa AI v6.0.0 muvaffaqiyatli ishga tushdi",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            inner, text=now, font=Fonts.TINY, text_color=Colors.TEXT_MUTED
        ).pack(side="right")

    def _quick_command(self, text):
        """Dashboard quick action — buyruqni backend ga yuborish"""
        if self.app and hasattr(self.app, "bridge"):
            self.app.bridge.send_text_command(text)

    def on_show(self):
        """Sahifa ko'rsatilganda yangilanish"""
        greeting, emoji = self._get_greeting()
        self.greeting_label.configure(
            text=f"{emoji}  {greeting}, {self._get_user_name()}!"
        )

        for value, label, icon, color in self._get_stats():
            widget = self._stat_widgets.get(label)
            if widget:
                widget.set_value(value)

        if self.app and hasattr(self.app, "bridge"):
            stats = self.app.bridge.get_memory_stats()
            count = stats.get("suhbatlar_soni", 0)
            self.orb_status.configure(
                text=f"Mikasa AI tayyor  |  {count} ta suhbat saqlangan"
            )

    def _get_user_name(self):
        try:
            from config import get_config
            return get_config("user.name", "Muxammadaziz")
        except Exception:
            return "Muxammadaziz"

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
        tool_count = 29
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
