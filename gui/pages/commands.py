# ========== commands.py ==========
# Command Center sahifasi — tool'lar va buyruqlarni boshqarish
# Yuqori unumdorlik: Normalized Search Index, Card Cache & Result Diffing,
# Virtualized Windowing (100–1000 tools), Time-Budgeted Rendering

import time
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing
from gui.icons import get_vector_icon
from gui.components import Card, EmptyState, GlassButton, InfoChip, PageHero, SearchBar, Button


CAT_COLORS = {
    "internet": Colors.INFO,
    "utility": Colors.SUCCESS,
    "system": Colors.DANGER,
    "media": Colors.SECONDARY,
    "info": Colors.WARNING,
    "productivity": Colors.PRIMARY,
    "memory": Colors.SECONDARY,
    "interaction": Colors.INFO,
    "coding": Colors.PRIMARY,
    "general": Colors.TEXT_MUTED,
}

CAT_ICONS = {
    "internet": "search",
    "utility": "settings",
    "system": "commands",
    "media": "play",
    "info": "info",
    "productivity": "scheduler",
    "memory": "memory",
    "interaction": "chat",
    "coding": "commands",
    "general": "sparkles",
}


class CommandsPage(ctk.CTkFrame):
    """Buyruqlar va tool'lar markazi — yuqori unumdorlikdagi katalog"""

    BATCH_SIZE = 8
    WINDOW_SIZE = 24
    MAX_BATCH_TIME_MS = 12.0

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._all_tools: list[dict] = []
        self._tools_dataset_version: int = 1
        self._active_category: str = "all"
        self._sort_mode: str = "name"
        self._view_mode: str = "grid"  # "grid" yoki "list"

        self._search_timer = None
        self._batch_job = None
        self._search_cache: dict = {}
        self._category_chips: dict[str, ctk.CTkButton] = {}
        self._tools_loaded: bool = False

        # Card Widget Cache & Result Diffing
        self._tool_cards: dict[str, ctk.CTkFrame] = {}
        self._rendered_tool_names: list[str] = []
        self._current_filtered_tools: list[dict] = []
        self._active_window_limit: int = self.WINDOW_SIZE

        self._empty_state_widget = None
        self._load_more_frame = None

        self._build_ui()
        self._init_data()

    @property
    def search_entry(self):
        return getattr(self.search, "entry", None)

    @property
    def _selected_category(self):
        return self._active_category

    @property
    def _batch_render_job(self):
        return self._batch_job

    @property
    def _search_debounce_job(self):
        return self._search_timer

    def _build_ui(self):
        # 1. Sahifa bosh sarlavhasi (PageHero)
        self.hero = PageHero(
            self,
            title="Tool katalogi",
            subtitle="29 ta tool • 8 ta kategoriya | Kerakli tool'ni qidiring yoki kategoriyalarga ko'ra ko'ring.",
            icon="commands",
            accent_color=Colors.WARNING,
            chips=[
                ("Chat bilan ulanadi", "chat", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
                ("Kategoriya filtri", "search", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
            ],
        )
        self.hero.pack(fill="x", padx=20, pady=(16, 12))

        self.tool_count_chip = InfoChip(
            self.hero.actions,
            text="0 ta tool",
            icon="commands",
            fg_color=Colors.WARNING_SOFT,
            text_color=Colors.WARNING,
        )
        self.tool_count_chip.pack(anchor="e")

        # 2. Qidiruv paneli — Ctrl + K nishoni bilan
        self.search = SearchBar(
            self,
            placeholder="Tool, buyruq yoki kategoriya qidiring...",
            shortcut="Ctrl + K",
        )
        self.search.pack(fill="x", padx=20, pady=(0, 10))
        self.search.entry.bind("<KeyRelease>", self._on_search_keyrelease)
        self.search.entry.bind("<Return>", lambda e: self._execute_search(immediate=True))

        # 3. Kategoriya filtri chiplari konteyneri
        self.filter_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=44,
            orientation="horizontal",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.filter_scroll.pack(fill="x", padx=20, pady=(0, 10))

        # 4. Natijalar paneli va boshqaruv qatori (Card)
        self.controls_card = Card(
            self,
            surface="card",
            padding=Sizing.SPACING_8,
        )
        self.controls_card.pack(fill="x", padx=20, pady=(0, 10))

        ctrl_inner = ctk.CTkFrame(self.controls_card.content, fg_color="transparent")
        ctrl_inner.pack(fill="x")

        # Chap tomonda natijalar sarlavhasi
        left_meta = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        left_meta.pack(side="left", fill="x", expand=True)

        self.results_label = ctk.CTkLabel(
            left_meta,
            text="Barcha tool'lar",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.results_label.pack(side="left")

        self.result_meta = ctk.CTkLabel(
            left_meta,
            text="",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.result_meta.pack(side="left", padx=(10, 0))

        # O'ng tomonda saralash va view mode
        right_controls = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        right_controls.pack(side="right")

        self.sort_menu = ctk.CTkOptionMenu(
            right_controls,
            values=["Nomi bo'yicha", "Kategoriya bo'yicha"],
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            button_color=Colors.BG_PANEL,
            button_hover_color=Colors.BG_HOVER,
            dropdown_fg_color=Colors.BG_CARD,
            dropdown_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            height=30,
            width=130,
            command=self._on_sort_change,
        )
        self.sort_menu.set("Nomi bo'yicha")
        self.sort_menu.pack(side="left", padx=(0, 8))

        self.view_btn = Button(
            right_controls,
            text="",
            icon="dashboard",
            variant="secondary",
            width=32,
            height=30,
            corner_radius=Sizing.RADIUS_BUTTON,
            command=self._toggle_view_mode,
        )
        self.view_btn.pack(side="left")

        # 5. Asosiy natijalar ScrollableFrame
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.grid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)

        # 6. Bo'sh holat placeholder (EmptyState)
        self._empty_state_widget = EmptyState(
            self.grid_frame,
            icon="search",
            title="Mos tool topilmadi",
            description="Qidiruvni qisqartirib ko'ring yoki boshqa kategoriya filtrini tanlang.",
        )

        # 7. "Ko'proq yuklash" paneli (Katta ro'yxatlar uchun)
        self._load_more_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._load_more_btn = GlassButton(
            self._load_more_frame,
            text="Yana ko'proq yuklash",
            icon="refresh",
            font=Fonts.SMALL_BOLD,
            height=34,
            corner_radius=Sizing.PILL,
            command=self._load_more_items,
        )
        self._load_more_btn.pack(pady=12)

    # ========================================================
    # DATA & NORMALIZED SEARCH INDEX
    # ========================================================

    def _get_tools(self):
        """ToolRegistry dan tool ro'yxatini tezkor olish"""
        tools = []
        try:
            from core.agent_tools import get_registry

            registry = get_registry()
            if hasattr(registry, "_tools"):
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
                            "icon": CAT_ICONS.get(category, "commands"),
                            "color": CAT_COLORS.get(category, Colors.TEXT_MUTED),
                        }
                    )
        except Exception:
            pass
        return tools

    def _init_data(self):
        """Dastlabki ma'lumotlarni xotiraga yuklash va indekslash"""
        if not self._tools_loaded:
            self._load_and_index_tools()
            self._tools_loaded = True
            count = len(self._all_tools)
            self.tool_count_chip.set_text(f"{count} ta tool")
            self._build_category_filters()
            self._execute_search(immediate=True)

    def _load_and_index_tools(self, tools=None):
        """Normalized qidiruv indeksini bir marta yaratish (Har bir harfda qayta hisoblamaslik uchun)"""
        raw_tools = tools if tools is not None else self._get_tools()
        self._all_tools = []
        for t in raw_tools:
            item = dict(t)
            # Normalized search text (kichik harflar bilan birlashgan qidiruv maydoni)
            item["_search_text"] = f"{item['name'].lower()} {item['category'].lower()} {item['description'].lower()}"
            self._all_tools.append(item)

        self._tools_dataset_version += 1
        self._search_cache.clear()
        self._prune_card_cache()

    def _prune_card_cache(self):
        """Olib tashlangan yoki eskirgan kartalarni xotiradan xavfsiz tozalash"""
        valid_names = {t["name"] for t in self._all_tools}
        for name in list(self._tool_cards.keys()):
            if name not in valid_names:
                card = self._tool_cards.pop(name, None)
                if card:
                    try:
                        card.destroy()
                    except Exception:
                        pass

    def _build_category_filters(self):
        """Kategoriya chiplarini (Barchasi, System, Utility, ...) qurish"""
        for widget in self.filter_scroll.winfo_children():
            widget.destroy()
        self._category_chips.clear()

        counts = {"all": len(self._all_tools)}
        for tool in self._all_tools:
            cat = tool["category"]
            counts[cat] = counts.get(cat, 0) + 1

        # Barchasi chipi
        self._create_category_chip("all", f"Barchasi ({counts['all']})")

        # Kategoriya chiplari (eng ko'p tool bo'lganlari bo'yicha)
        other_cats = [c for c in counts.keys() if c != "all"]
        other_cats.sort(key=lambda c: (-counts[c], c))

        for cat in other_cats:
            self._create_category_chip(cat, f"{cat.title()} ({counts[cat]})")

    def _create_category_chip(self, category_key: str, label_text: str):
        is_active = self._active_category == category_key
        fg = Colors.PRIMARY if is_active else Colors.BG_CARD
        tc = "#FFFFFF" if is_active else Colors.TEXT_SECONDARY
        bc = Colors.PRIMARY if is_active else Colors.BORDER

        chip = ctk.CTkButton(
            self.filter_scroll,
            text=label_text,
            font=Fonts.SMALL_BOLD if is_active else Fonts.SMALL,
            fg_color=fg,
            hover_color=Colors.PRIMARY_HOVER if is_active else Colors.BG_HOVER,
            text_color=tc,
            border_width=1,
            border_color=bc,
            corner_radius=Sizing.PILL,
            height=30,
            command=lambda k=category_key: self._on_category_click(k),
        )
        chip.pack(side="left", padx=(0, 6), pady=4)
        self._category_chips[category_key] = chip

    def _on_category_click(self, category_key: str):
        if self._active_category == category_key:
            return
        self._active_category = category_key

        # Chip ko'rinishlarini yangilash
        for key, chip in self._category_chips.items():
            if not chip.winfo_exists():
                continue
            is_active = key == category_key
            chip.configure(
                fg_color=Colors.PRIMARY if is_active else Colors.BG_CARD,
                hover_color=Colors.PRIMARY_HOVER if is_active else Colors.BG_HOVER,
                text_color="#FFFFFF" if is_active else Colors.TEXT_SECONDARY,
                border_color=Colors.PRIMARY if is_active else Colors.BORDER,
                font=Fonts.SMALL_BOLD if is_active else Fonts.SMALL,
            )

        self._active_window_limit = self.WINDOW_SIZE
        self._execute_search(immediate=True)

    # ========================================================
    # DEBOUNCED SEARCH & DATA PIPELINE
    # ========================================================

    def _on_search_keyrelease(self, event=None):
        if event and event.keysym in (
            "Up", "Down", "Left", "Right",
            "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R",
        ):
            return

        if self._search_timer:
            try:
                self.after_cancel(self._search_timer)
            except Exception:
                pass
            self._search_timer = None

        query = self.search.entry.get().strip()
        if not query:
            # So'z tozalanganda zudlik bilan tiklash
            self._active_window_limit = self.WINDOW_SIZE
            self._execute_search(immediate=True)
        else:
            # 280ms debounced search
            self._search_timer = self.after(280, lambda: self._execute_search(immediate=False))

    def _on_search(self, event=None):
        """Backward compatibility helper for tests and external callers"""
        self._execute_search(immediate=True)

    def _filter_and_sort_tools(self, query: str, category: str, sort_mode: str) -> list[dict]:
        """Sof ma'lumotlar bosqichi (UI ga daxlsiz, o'ta tezkor)"""
        cache_key = (query, category, sort_mode, self._tools_dataset_version)
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        results = self._all_tools

        # 1. Kategoriya filtri
        if category != "all":
            results = [t for t in results if t["category"] == category]

        # 2. Normalized qidiruv
        if query:
            q = query.lower()
            results = [t for t in results if q in t["_search_text"]]

        # 3. Saralash
        if sort_mode == "category":
            results = sorted(results, key=lambda t: (t["category"], t["name"]))
        else:
            results = sorted(results, key=lambda t: t["name"])

        # Keshga saqlash (maksimum 100 ta yozuv)
        if len(self._search_cache) > 100:
            self._search_cache.clear()
        self._search_cache[cache_key] = results
        return results

    def _execute_search(self, immediate=False):
        self._search_timer = None
        query = self.search.entry.get().strip().lower() if hasattr(self, "search") and self.search.entry else ""

        # Ma'lumotlarni filtrlash
        filtered = self._filter_and_sort_tools(query, self._active_category, self._sort_mode)
        self._current_filtered_tools = filtered

        # Sarlavha va natijalar metani yangilash
        if query:
            self.results_label.configure(text=f"Qidiruv: {query}")
        elif self._active_category != "all":
            self.results_label.configure(text=f"Kategoriya: {self._active_category.title()}")
        else:
            self.results_label.configure(text="Barcha tool'lar")

        self.result_meta.configure(text=f"{len(filtered)} ta natija")

        # UI diffing va render
        self._build_tools_grid(filtered, immediate=immediate)

    def _on_sort_change(self, choice):
        self._sort_mode = "category" if "Kategoriya" in choice else "name"
        self._active_window_limit = self.WINDOW_SIZE
        self._execute_search(immediate=True)

    def _toggle_view_mode(self):
        self._view_mode = "list" if self._view_mode == "grid" else "grid"
        self.view_btn.configure(icon="chat" if self._view_mode == "list" else "dashboard")
        # View mode o'zgarganda barcha kartalar yangi layoutga joylashtiriladi
        self._rendered_tool_names.clear()
        self._execute_search(immediate=True)

    def _load_more_items(self):
        """Katta kataloglarda keyingi oynani yuklash"""
        self._active_window_limit += self.WINDOW_SIZE
        self._build_tools_grid(self._current_filtered_tools)

    # ========================================================
    # CARD CACHE, RESULT DIFFING & TIME-BUDGET RENDERING
    # ========================================================

    def _cancel_batch_render(self):
        if self._batch_job:
            try:
                self.after_cancel(self._batch_job)
            except Exception:
                pass
            self._batch_job = None

    def _build_tools_grid(self, tools=None, immediate: bool = False):
        """
        Natijalarni diffing va Card Cache orqali ekranga chiqarish.
        Mavjud kartalar destroy() qilinmaydi, to'g'ridan-to'g'ri qayta ishlatiladi!
        """
        self._cancel_batch_render()

        if tools is None:
            tools = self._all_tools

        # 1. Bo'sh holat tekshiruvi
        if not tools:
            # Barcha ochiq kartalarni yashirish
            for name in self._rendered_tool_names:
                card = self._tool_cards.get(name)
                if card and card.winfo_exists():
                    card.grid_remove() if self._view_mode == "grid" else card.pack_forget()
            self._rendered_tool_names.clear()

            if self._load_more_frame and self._load_more_frame.winfo_exists():
                self._load_more_frame.pack_forget()

            if self._empty_state_widget and self._empty_state_widget.winfo_exists():
                self._empty_state_widget.pack(fill="x", pady=20)
            return
        else:
            if self._empty_state_widget and self._empty_state_widget.winfo_exists():
                self._empty_state_widget.pack_forget()

        # 2. Windowing / Virtualizatsiya (Ko'rinuvchi qism)
        visible_tools = tools[:self._active_window_limit]
        target_names = [t["name"] for t in visible_tools]

        # 3. No-Op tekshiruvi: Agar ko'rinayotgan ro'yxat aynan bir xil bo'lsa — hech narsa o'zgarmaydi (0ms)
        if target_names == self._rendered_tool_names:
            self._update_load_more_visibility(len(tools), len(visible_tools))
            return

        # 4. Ustunlar konfiguratsiyasi
        columns = 1 if self._view_mode == "list" else 3
        for i in range(columns):
            self.grid_frame.columnconfigure(i, weight=1)

        # 5. Diffing: Ko'rinishdan chiqqan kartalarni yashirish (grid_remove / pack_forget)
        target_name_set = set(target_names)
        for name in list(self._rendered_tool_names):
            if name not in target_name_set:
                card = self._tool_cards.get(name)
                if card and card.winfo_exists():
                    card.grid_remove() if self._view_mode == "grid" else card.pack_forget()

        # 6. Partiyalab render qilish (Time-budgeted yoki immediate)
        self._rendered_tool_names = list(target_names)
        self._render_chunk_time_budget(visible_tools, 0, columns, len(tools), synchronous=immediate)

    def _render_chunk_time_budget(self, tools: list[dict], start_idx: int, columns: int, total_tools_count: int, synchronous: bool = False):
        """Vaqt byudjetiga ega (max 12ms) bosqichma-bosqich chizish"""
        if not self.winfo_exists():
            return

        t_start = time.perf_counter()
        idx = start_idx
        n = len(tools)

        while idx < n:
            tool = tools[idx]
            name = tool["name"]

            # Kartani keshdan olish yoki bir marta yaratish
            if name in self._tool_cards and self._tool_cards[name].winfo_exists():
                card = self._tool_cards[name]
            else:
                card = self._create_tool_card(tool)
                self._tool_cards[name] = card

            # Geometriyaga joylashtirish
            if columns == 1:
                card.pack(fill="x", padx=6, pady=4)
            else:
                row, col = divmod(idx, columns)
                card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            idx += 1

            # Agar sinxron bo'lmasa, 12 ms dan oshib ketgan bo'lsa, qolganini keyingi freymga uzatish (Zero UI freeze)
            if not synchronous and (time.perf_counter() - t_start) * 1000.0 >= self.MAX_BATCH_TIME_MS:
                break

        if idx < n:
            self._batch_job = self.after(
                16,
                lambda: self._render_chunk_time_budget(tools, idx, columns, total_tools_count, synchronous=synchronous),
            )
        else:
            self._batch_job = None
            self._update_load_more_visibility(total_tools_count, len(tools))

    def _update_load_more_visibility(self, total_count: int, visible_count: int):
        """Katta ro'yxatlarda 'Ko'proq ko'rsatish' tugmasi boshqaruvi"""
        if not self._load_more_frame or not self._load_more_frame.winfo_exists():
            return

        if total_count > visible_count:
            remaining = total_count - visible_count
            self._load_more_btn.configure(text=f"Yana {remaining} ta tool'ni ko'rsatish...")
            self._load_more_frame.pack(fill="x", pady=16)
        else:
            self._load_more_frame.pack_forget()

    # ========================================================
    # CARD COMPONENT (100% Retained Visuals & Styling)
    # ========================================================

    def _create_tool_card(self, tool: dict) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self.grid_frame,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizing.CARD,
            border_width=1,
            border_color=Colors.BORDER,
            cursor="hand2",
        )

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        # Yuqori qism: Ikonka + Nom + Kategoriya
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        icon_box = ctk.CTkFrame(
            top,
            fg_color=Colors.BG_SOFT,
            corner_radius=Sizing.SMALL,
            width=38,
            height=38,
        )
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)

        v_img = get_vector_icon(tool["icon"], size=18, color_dark=tool["color"], color_light=tool["color"], fallback="commands")
        if v_img:
            ctk.CTkLabel(icon_box, image=v_img, text="").pack(expand=True)

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
            icon=tool["icon"],
            fg_color=Colors.BG_PANEL,
            text_color=tool["color"],
        ).pack(anchor="w", pady=(4, 0))

        # O'rta qism: Tavsif
        desc_lbl = ctk.CTkLabel(
            inner,
            text=tool["description"],
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            justify="left",
            wraplength=260 if self._view_mode == "grid" else 680,
            anchor="w",
        )
        desc_lbl.pack(fill="x", pady=(10, 10))

        # Pastki qism: Status + Harakat tugmasi
        footer = ctk.CTkFrame(inner, fg_color="transparent")
        footer.pack(fill="x")

        ctk.CTkLabel(
            footer,
            text="Chatga tayyor",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
        ).pack(side="left")

        act_btn = GlassButton(
            footer,
            text="Foydalanish",
            icon="send",
            font=Fonts.SMALL,
            height=28,
            width=92,
            corner_radius=Sizing.PILL,
            command=lambda t=tool["name"]: self._on_tool_click(t),
        )
        act_btn.pack(side="right")

        # Hover & Click bog'lash (faqat asosiy qatlamlarga)
        def on_enter(event=None):
            if card.winfo_exists():
                card.configure(border_color=tool["color"])

        def on_leave(event=None):
            if card.winfo_exists():
                card.configure(border_color=Colors.BORDER)

        def on_card_click(event=None):
            self._on_tool_click(tool["name"])

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", on_card_click)
        inner.bind("<Button-1>", on_card_click)
        desc_lbl.bind("<Button-1>", on_card_click)

        return card

    def _on_tool_click(self, tool_name: str):
        if self.app:
            self.app.navigate_to("chat")
            chat_page = self.app._pages.get("chat")
            if chat_page:
                if hasattr(chat_page, "input_entry"):
                    chat_page.input_entry.delete(0, "end")
                    chat_page.input_entry.insert(0, f"{tool_name} tool ni ishlatib ko'rsat")
                if hasattr(self.app, "_schedule_page_focus"):
                    self.app._schedule_page_focus("chat")
                elif hasattr(chat_page, "focus_primary_input"):
                    chat_page.focus_primary_input()

    # ========================================================
    # LIFECYCLE: ON_SHOW, ON_HIDE, DESTROY
    # ========================================================

    def on_show(self):
        """Navigatsiya orqali sahifa ochilganda chaqiriladi"""
        if not self._tools_loaded:
            self._init_data()
        else:
            # Qidiruv inputiga fokus berish
            try:
                if hasattr(self, "search") and self.search.entry:
                    self.search.entry.focus_set()
            except Exception:
                pass

    def on_hide(self):
        """Sahifadan chiqilganda barcha kutilayotgan timer va batch joblarni to'xtatish"""
        self._cancel_batch_render()
        if self._search_timer:
            try:
                self.after_cancel(self._search_timer)
            except Exception:
                pass
            self._search_timer = None

    def focus_search(self):
        """Ctrl + K orqali qidiruvga fokus berish"""
        try:
            if hasattr(self, "search") and self.search.entry:
                self.search.entry.focus_set()
                self.search.entry.select_range(0, "end")
        except Exception:
            pass

    def destroy(self):
        self.on_hide()
        self._tool_cards.clear()
        self._rendered_tool_names.clear()
        self._search_cache.clear()
        super().destroy()
