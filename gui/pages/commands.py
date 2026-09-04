# ========== commands.py ==========
# Command Center sahifasi — tool'lar va buyruqlarni boshqarish

import customtkinter as ctk
from gui.theme import Colors, Fonts
from gui.components import EmptyState, GlassCard, InfoChip, PageHero, SearchBar


class CommandsPage(ctk.CTkFrame):
    """Buyruqlar va tool'lar markazi"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._all_tools = []
        self._build_ui()

    def _build_ui(self):
        self.hero = PageHero(
            self,
            title="Tool katalogi",
            subtitle="Mikasa ichidagi barcha agent tool'larni qidiring, ko'ring va bir klik bilan chatga yuboring.",
            icon="⚡",
            accent_color=Colors.WARNING,
            chips=[
                ("Chat bilan ulanadi", "💬", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
                (
                    "Kategoriya bo'yicha qidiruv",
                    "🔎",
                    Colors.BG_PANEL,
                    Colors.TEXT_SECONDARY,
                ),
            ],
        )
        self.hero.pack(fill="x", padx=20, pady=(16, 12))

        self.tool_count_chip = InfoChip(
            self.hero.actions,
            text="0 ta tool",
            icon="🧰",
            fg_color=Colors.WARNING_SOFT,
            text_color=Colors.WARNING,
        )
        self.tool_count_chip.pack(anchor="e")

        self.search = SearchBar(
            self, placeholder="Tool, kategoriya yoki tavsif qidiring..."
        )
        self.search.pack(fill="x", padx=20, pady=(0, 12))
        self.search.entry.bind("<KeyRelease>", self._on_search)

        self.summary_card = GlassCard(
            self,
            title="Kategoriya ko'rinishi",
            subtitle="Qaysi yo'nalishdagi tool'lar ko'proq ekanini shu yerdan ko'rasiz.",
            accent_color=Colors.INFO,
        )
        self.summary_card.pack(fill="x", padx=20, pady=(0, 12))

        self.summary_row = ctk.CTkFrame(
            self.summary_card.content, fg_color="transparent"
        )
        self.summary_row.pack(fill="x")

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        results_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        results_row.pack(fill="x", pady=(0, 10))

        self.results_label = ctk.CTkLabel(
            results_row,
            text="Barcha tool'lar",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.results_label.pack(side="left")

        self.result_meta = ctk.CTkLabel(
            results_row,
            text="",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        )
        self.result_meta.pack(side="right")

        self.grid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_frame.pack(fill="x", pady=(0, 20))

    def _get_tools(self):
        """ToolRegistry dan tool ro'yxatini olish"""
        tools = []
        try:
            from core.agent_tools import get_registry

            registry = get_registry()
            if hasattr(registry, "_tools"):
                cat_colors = {
                    "internet": Colors.INFO,
                    "utility": Colors.SUCCESS,
                    "system": Colors.DANGER,
                    "media": Colors.SECONDARY,
                    "info": Colors.WARNING,
                    "productivity": Colors.PRIMARY,
                    "memory": Colors.SECONDARY,
                    "interaction": Colors.INFO,
                }
                cat_icons = {
                    "internet": "🌐",
                    "utility": "🔧",
                    "system": "💻",
                    "media": "🎵",
                    "info": "🌤️",
                    "productivity": "📌",
                    "memory": "📚",
                    "interaction": "💬",
                }

                for name, tool in registry._tools.items():
                    category = getattr(tool, "category", "utility")
                    description = (
                        getattr(tool, "description", "") or "Tavsif berilmagan"
                    )
                    tools.append(
                        {
                            "name": name,
                            "description": description[:120],
                            "category": category,
                            "icon": cat_icons.get(category, "⚡"),
                            "color": cat_colors.get(category, Colors.TEXT_MUTED),
                        }
                    )
        except Exception:
            pass
        return sorted(tools, key=lambda item: (item["category"], item["name"]))

    def _build_category_summary(self, tools):
        for widget in self.summary_row.winfo_children():
            widget.destroy()

        if not tools:
            EmptyState(
                self.summary_row,
                icon="🧩",
                title="Kategoriya yo'q",
                description="Tool yuklangach shu yerda kategoriyalar ko'rinadi.",
            ).pack(fill="x", pady=10)
            return

        counts = {}
        for tool in tools:
            counts[tool["category"]] = counts.get(tool["category"], 0) + 1

        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        for category, count in ordered:
            InfoChip(
                self.summary_row,
                text=f"{category.title()}: {count}",
                icon="🏷️",
                fg_color=Colors.BG_PANEL,
                text_color=Colors.TEXT_SECONDARY,
            ).pack(side="left", padx=(0, 8), pady=(0, 4))

    def _build_tools_grid(self, tools=None):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        if tools is None:
            tools = self._all_tools

        self._build_category_summary(tools)

        if not tools:
            EmptyState(
                self.grid_frame,
                icon="🔎",
                title="Mos tool topilmadi",
                description="Qidiruvni qisqartirib ko'ring yoki boshqa kategoriya nomini yozing.",
            ).pack(fill="x", pady=20)
            return

        columns = 3
        for i in range(columns):
            self.grid_frame.columnconfigure(i, weight=1)

        for i, tool in enumerate(tools):
            row, col = divmod(i, columns)
            card = self._create_tool_card(tool)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

    def _create_tool_card(self, tool):
        card = ctk.CTkFrame(
            self.grid_frame,
            fg_color=Colors.BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
            cursor="hand2",
        )

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=14)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        icon_box = ctk.CTkFrame(
            top,
            fg_color=Colors.BG_SOFT,
            corner_radius=10,
            width=40,
            height=40,
        )
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text=tool["icon"],
            font=(Fonts.FAMILY, 20),
            text_color=tool["color"],
        ).pack(expand=True)

        name_wrap = ctk.CTkFrame(top, fg_color="transparent")
        name_wrap.pack(side="left", fill="x", expand=True, padx=(10, 0))

        ctk.CTkLabel(
            name_wrap,
            text=tool["name"],
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        InfoChip(
            name_wrap,
            text=tool["category"],
            fg_color=Colors.BG_PANEL,
            text_color=tool["color"],
        ).pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(
            inner,
            text=tool["description"],
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            justify="left",
            wraplength=260,
            anchor="w",
        ).pack(fill="x", pady=(12, 12))

        footer = ctk.CTkFrame(inner, fg_color="transparent")
        footer.pack(fill="x")

        ctk.CTkLabel(
            footer,
            text="Chatga tayyor",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
        ).pack(side="left")

        ctk.CTkLabel(
            footer,
            text="Foydalanish →",
            font=Fonts.SMALL_BOLD,
            text_color=tool["color"],
        ).pack(side="right")

        def on_enter(event=None):
            card.configure(border_color=tool["color"])

        def on_leave(event=None):
            card.configure(border_color=Colors.BORDER)

        def on_click(event=None):
            self._on_tool_click(tool["name"])

        self._bind_click_recursive(card, on_click, on_enter, on_leave)
        return card

    def _bind_click_recursive(self, widget, on_click, on_enter, on_leave):
        widget.bind("<Button-1>", on_click)
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        for child in widget.winfo_children():
            self._bind_click_recursive(child, on_click, on_enter, on_leave)

    def _on_tool_click(self, tool_name):
        if self.app:
            self.app.navigate_to("chat")
            chat_page = self.app._pages.get("chat")
            if chat_page:
                chat_page.input_entry.delete(0, "end")
                chat_page.input_entry.insert(0, f"{tool_name} tool ni ishlatib ko'rsat")
                if hasattr(self.app, "_schedule_page_focus"):
                    self.app._schedule_page_focus("chat")
                elif hasattr(chat_page, "focus_primary_input"):
                    chat_page.focus_primary_input()

    def _on_search(self, event=None):
        query = self.search.entry.get().strip().lower()
        if not query:
            self.results_label.configure(text="Barcha tool'lar")
            self.result_meta.configure(text=f"{len(self._all_tools)} ta natija")
            self._build_tools_grid()
            return

        filtered = [
            tool
            for tool in self._all_tools
            if query in tool["name"].lower()
            or query in tool["description"].lower()
            or query in tool["category"].lower()
        ]
        self.results_label.configure(text=f"Qidiruv: {query}")
        self.result_meta.configure(text=f"{len(filtered)} ta natija")
        self._build_tools_grid(filtered)

    def on_show(self):
        self._all_tools = self._get_tools()
        count = len(self._all_tools)
        self.tool_count_chip.set_text(f"{count} ta tool")

        self.search.clear()
        self.results_label.configure(text="Barcha tool'lar")
        self.result_meta.configure(text=f"{count} ta natija")
        self._build_tools_grid()
