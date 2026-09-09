# ========== commands.py ==========
# Command Center sahifasi — tool'lar va buyruqlarni boshqarish
# Raycast-level discovery + Linear-level discipline + Yandex Music polish
# Yuqori unumdorlik: Normalized Search Index, Card Cache & Result Diffing,
# Virtualized Windowing, Dynamic Responsive Grid, Keyboard Navigation

import time
import tkinter as tk
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing
from gui.icons import get_vector_icon
from gui.components import Card, EmptyState, GlassButton, InfoChip, SearchBar, Button, attach_tooltip


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
    "knowledge": Colors.SECONDARY,
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
    "knowledge": "memory",
    "general": "sparkles",
}


class CommandsPage(ctk.CTkFrame):
    """Buyruqlar va tool'lar markazi — tezkor capability browser"""

    BATCH_SIZE = 8
    WINDOW_SIZE = 32
    MAX_BATCH_TIME_MS = 12.0

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._all_tools: list[dict] = []
        self._tools_dataset_version: int = 1
        self._active_category: str = "all"
        self._sort_mode: str = "name"
        self._view_mode: str = "grid"  # "grid" yoki "list"
        self._current_columns: int = 3
        self._selected_index: int = -1

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
        # 1. Ixcham header (Title, Badge, Sort & View mode)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 8))

        # Chap tomonda Ikonka + Sarlavha + Toollar soni badge
        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.pack(side="left", fill="y")

        icon = get_vector_icon("commands", size=22, color=Colors.PRIMARY)
        if icon:
            ctk.CTkLabel(header_left, text="", image=icon).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            header_left,
            text="Buyruqlar",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        self.tool_count_chip = InfoChip(header_left, text="0 ta tool", icon="commands")
        self.tool_count_chip.pack(side="left", padx=12)

        # O'ng tomonda Saralash va Ko'rinish rejimi (Grid / List)
        header_right = ctk.CTkFrame(header, fg_color="transparent")
        header_right.pack(side="right")

        self.sort_menu = ctk.CTkOptionMenu(
            header_right,
            values=["Nomi bo'yicha", "Kategoriya bo'yicha"],
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            button_color=Colors.BG_PANEL,
            button_hover_color=Colors.BG_HOVER,
            dropdown_fg_color=Colors.BG_CARD,
            dropdown_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            height=30,
            width=134,
            corner_radius=Sizing.RADIUS_BUTTON,
            command=self._on_sort_change,
        )
        self.sort_menu.set("Nomi bo'yicha")
        self.sort_menu.pack(side="left", padx=(0, 8))

        self.view_btn = Button(
            header_right,
            text="",
            icon="dashboard",
            variant="secondary",
            width=32,
            height=30,
            corner_radius=Sizing.RADIUS_BUTTON,
            command=self._toggle_view_mode,
        )
        self.view_btn.pack(side="left")

        # 2. Raycast-style Qidiruv paneli (44px)
        self.search = SearchBar(
            self,
            placeholder="Buyruq yoki amalni qidiring... (masalan: tizim, ob-havo, fayl)",
            shortcut="Ctrl + K",
            height=44,
        )
        self.search.pack(fill="x", padx=24, pady=(0, 8))
        self.search.entry.bind("<KeyRelease>", self._on_search_keyrelease)
        self.search.entry.bind("<Return>", self._on_search_return)
        self.search.entry.bind("<Down>", self._on_search_down)
        self.search.entry.bind("<Escape>", self._on_search_escape)

        # Qidiruv maydoni interaktiv fokus effekti
        def on_search_focus_in(event=None):
            if hasattr(self.search, "configure"):
                self.search.configure(border_color=Colors.PRIMARY, border_width=1.5)

        def on_search_focus_out(event=None):
            if hasattr(self.search, "configure"):
                self.search.configure(border_color=Colors.BORDER, border_width=1)

        self.search.entry.bind("<FocusIn>", on_search_focus_in)
        self.search.entry.bind("<FocusOut>", on_search_focus_out)

        # Qidiruvni tozalash tugmasi
        self._search_clear_btn = ctk.CTkButton(
            self.search,
            text="✕",
            font=Fonts.SMALL,
            width=22,
            height=22,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            corner_radius=11,
            command=self._clear_search,
        )

        # 3. Kategoriya filtri chiplari konteyneri
        self.filter_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=34,
            orientation="horizontal",
            scrollbar_button_color=Colors.BG_DARK,
            scrollbar_button_hover_color=Colors.BG_DARK,
        )
        self.filter_scroll.pack(fill="x", padx=24, pady=(0, 6))

        # 4. Ixcham Natijalar va boshqaruv kartasi (Solid Card - 80/20 surface hierarchy)
        self.controls_card = Card(
            self,
            surface="card",
            padding=Sizing.SPACING_8,
        )
        self.controls_card.pack(fill="x", padx=24, pady=(0, 8))

        ctrl_inner = ctk.CTkFrame(self.controls_card.content, fg_color="transparent")
        ctrl_inner.pack(fill="x")

        self.results_label = ctk.CTkLabel(
            ctrl_inner,
            text="Barcha tool'lar",
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.results_label.pack(side="left")

        self.result_meta = ctk.CTkLabel(
            ctrl_inner,
            text="",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.result_meta.pack(side="left", padx=(8, 0))

        # Klaviatura ko'rsatmalari (o'ng tomonda)
        self.hints_lbl = ctk.CTkLabel(
            ctrl_inner,
            text="↑↓ Navigatsiya   ↵ Tanlash   Esc Tozalash",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
            anchor="e",
        )
        self.hints_lbl.pack(side="right")

        self.meta_frame = ctrl_inner

        # 5. Asosiy ScrollableFrame
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.scroll.bind("<Configure>", self._on_scroll_configure)

        self.grid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)

        # Klaviatura navigatsiyasi hodisalarini bog'lash
        self.bind("<Down>", self._on_key_down)
        self.bind("<Up>", self._on_key_up)
        self.bind("<Left>", self._on_key_left)
        self.bind("<Right>", self._on_key_right)
        self.bind("<Return>", self._on_key_return)
        self.bind("<Escape>", self._on_key_escape)

        # 6. Bo'sh holat placeholder (EmptyState)
        self._empty_state_widget = EmptyState(
            self.grid_frame,
            icon="search",
            title="Mos tool topilmadi",
            description="Qidiruv so'zini o'zgartiring yoki boshqa kategoriya filtrini tanlang.",
        )

        # 7. "Ko'proq yuklash" paneli (Katta ro'yxatlar uchun)
        self._load_more_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._load_more_btn = GlassButton(
            self._load_more_frame,
            text="Yana ko'proq yuklash",
            icon="refresh",
            font=Fonts.SMALL_BOLD,
            height=32,
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
                            "description": description[:160],
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

        self._create_category_chip("all", f"Barchasi ({counts['all']})")

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
            height=28,
            command=lambda k=category_key: self._on_category_click(k),
        )
        chip.pack(side="left", padx=(0, 6), pady=2)
        self._category_chips[category_key] = chip

    def _on_category_click(self, category_key: str):
        if self._active_category == category_key:
            return
        self._active_category = category_key

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

        self._selected_index = -1
        self._active_window_limit = self.WINDOW_SIZE
        self._execute_search(immediate=True)

    # ========================================================
    # DEBOUNCED SEARCH & DATA PIPELINE
    # ========================================================

    def _on_search_keyrelease(self, event=None):
        if event and event.keysym in (
            "Up", "Down", "Left", "Right",
            "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R", "Return", "Escape",
        ):
            return

        if self._search_timer:
            try:
                self.after_cancel(self._search_timer)
            except Exception:
                pass
            self._search_timer = None

        query = self.search.entry.get().strip() if hasattr(self, "search") and self.search.entry else ""

        # Clear tugmasini ko'rsatish/yashirish
        if hasattr(self, "_search_clear_btn"):
            if query:
                if not self._search_clear_btn.winfo_ismapped():
                    if hasattr(self.search, "shortcut_badge") and self.search.shortcut_badge:
                        self._search_clear_btn.pack(side="right", before=self.search.shortcut_badge, padx=(0, 6))
                    else:
                        self._search_clear_btn.pack(side="right", padx=(0, 8))
            else:
                if self._search_clear_btn.winfo_ismapped():
                    self._search_clear_btn.pack_forget()

        if not query:
            self._selected_index = -1
            self._active_window_limit = self.WINDOW_SIZE
            self._execute_search(immediate=True)
        else:
            self._search_timer = self.after(280, lambda: self._execute_search(immediate=False))

    def _clear_search(self):
        if hasattr(self, "search") and self.search.entry:
            self.search.entry.delete(0, "end")
        if hasattr(self, "_search_clear_btn") and self._search_clear_btn.winfo_ismapped():
            self._search_clear_btn.pack_forget()
        self._selected_index = -1
        self._active_window_limit = self.WINDOW_SIZE
        self._execute_search(immediate=True)
        if hasattr(self, "search") and self.search.entry:
            self.search.entry.focus_set()

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

        if len(self._search_cache) > 100:
            self._search_cache.clear()
        self._search_cache[cache_key] = results
        return results

    def _execute_search(self, immediate=False):
        self._search_timer = None
        query = self.search.entry.get().strip().lower() if hasattr(self, "search") and self.search.entry else ""

        # Clear tugmasini sinxronlash
        if hasattr(self, "_search_clear_btn"):
            if query:
                if not self._search_clear_btn.winfo_ismapped():
                    if hasattr(self.search, "shortcut_badge") and self.search.shortcut_badge:
                        self._search_clear_btn.pack(side="right", before=self.search.shortcut_badge, padx=(0, 6))
                    else:
                        self._search_clear_btn.pack(side="right", padx=(0, 8))
            else:
                if self._search_clear_btn.winfo_ismapped():
                    self._search_clear_btn.pack_forget()

        filtered = self._filter_and_sort_tools(query, self._active_category, self._sort_mode)
        self._current_filtered_tools = filtered

        if query:
            self.results_label.configure(text=f'Qidiruv: "{query}"')
        elif self._active_category != "all":
            self.results_label.configure(text=f"Kategoriya: {self._active_category.title()}")
        else:
            self.results_label.configure(text="Barcha tool'lar")

        self.result_meta.configure(text=f"{len(filtered)} ta natija")
        self._selected_index = -1

        self._build_tools_grid(filtered, immediate=immediate)

    def _on_sort_change(self, choice):
        self._sort_mode = "category" if "Kategoriya" in choice else "name"
        self._active_window_limit = self.WINDOW_SIZE
        self._execute_search(immediate=True)

    def _toggle_view_mode(self):
        self._cancel_batch_render()
        self._view_mode = "list" if self._view_mode == "grid" else "grid"
        self.view_btn.configure(icon="chat" if self._view_mode == "list" else "dashboard")
        for card in list(self._tool_cards.values()):
            if card and card.winfo_exists():
                card.grid_forget()
                card.pack_forget()
                try:
                    card.destroy()
                except Exception:
                    pass
        self._tool_cards.clear()
        self._rendered_tool_names.clear()
        self._selected_index = -1
        self._execute_search(immediate=True)

    def _load_more_items(self):
        """Katta kataloglarda keyingi oynani yuklash"""
        self._active_window_limit += self.WINDOW_SIZE
        self._build_tools_grid(self._current_filtered_tools)

    # ========================================================
    # RESPONSIVE GRID & VIRTUALIZED RENDERING
    # ========================================================

    def _get_column_count(self) -> int:
        if self._view_mode == "list":
            return 1
        width = self.scroll.winfo_width() if self.scroll.winfo_exists() else 0
        if width <= 1:
            width = self.winfo_width() if self.winfo_exists() else 1440
        if width >= 1280:
            return 4
        elif width >= 860:
            return 3
        else:
            return 2

    def _on_scroll_configure(self, event=None):
        cols = self._get_column_count()
        if cols != self._current_columns:
            self._current_columns = cols
            self._regrid_visible_cards(cols)

    def _regrid_visible_cards(self, cols: int):
        for i in range(max(cols, 4)):
            self.grid_frame.columnconfigure(i, weight=1 if i < cols else 0)

        for idx, name in enumerate(self._rendered_tool_names):
            card = self._tool_cards.get(name)
            if card and card.winfo_exists():
                if cols == 1:
                    card.grid_forget()
                    card.pack(fill="x", padx=6, pady=3)
                else:
                    card.pack_forget()
                    row, col = divmod(idx, cols)
                    card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

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
            for card in self._tool_cards.values():
                if card and card.winfo_exists():
                    card.grid_forget()
                    card.pack_forget()
            self._rendered_tool_names.clear()

            if self._load_more_frame and self._load_more_frame.winfo_exists():
                self._load_more_frame.pack_forget()

            if self._empty_state_widget and self._empty_state_widget.winfo_exists():
                self._empty_state_widget.pack(fill="x", pady=20)
            return
        else:
            if self._empty_state_widget and self._empty_state_widget.winfo_exists():
                self._empty_state_widget.pack_forget()

        # 2. Windowing / Virtualizatsiya
        visible_tools = tools[:self._active_window_limit]
        target_names = [t["name"] for t in visible_tools]

        # 3. No-Op tekshiruvi
        if target_names == self._rendered_tool_names:
            self._update_load_more_visibility(len(tools), len(visible_tools))
            return

        # 4. Ustunlar konfiguratsiyasi
        columns = self._get_column_count()
        self._current_columns = columns
        for i in range(max(columns, 4)):
            self.grid_frame.columnconfigure(i, weight=1 if i < columns else 0)

        # 5. Diffing: Ko'rinishdan chiqqan kartalarni to'liq yashirish
        target_name_set = set(target_names)
        for name, card in self._tool_cards.items():
            if name not in target_name_set and card and card.winfo_exists():
                card.grid_forget()
                card.pack_forget()

        # 6. Partiyalab render qilish
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

            if name in self._tool_cards and self._tool_cards[name].winfo_exists():
                card = self._tool_cards[name]
            else:
                card = self._create_tool_card(tool)
                self._tool_cards[name] = card

            if columns == 1:
                card.grid_forget()
                card.pack(fill="x", padx=6, pady=3)
            else:
                card.pack_forget()
                row, col = divmod(idx, columns)
                card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            idx += 1

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
        if not self._load_more_frame or not self._load_more_frame.winfo_exists():
            return

        if total_count > visible_count:
            remaining = total_count - visible_count
            self._load_more_btn.configure(text=f"Yana {remaining} ta tool'ni ko'rsatish...")
            self._load_more_frame.pack(fill="x", pady=16)
        else:
            self._load_more_frame.pack_forget()

    # ========================================================
    # COMPACT CAPABILITY ITEM (Grid & List modes)
    # ========================================================

    def _create_tool_card(self, tool: dict) -> ctk.CTkFrame:
        if self._view_mode == "list":
            return self._create_list_item(tool)
        return self._create_grid_card(tool)

    def _create_grid_card(self, tool: dict) -> ctk.CTkFrame:
        """Ixcham, skanerlash oson Raycast uslubidagi Capability Item"""
        card = ctk.CTkFrame(
            self.grid_frame,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizing.RADIUS_CARD,
            border_width=1,
            border_color=Colors.BORDER,
            height=108,
            cursor="hand2",
        )
        card.pack_propagate(False)
        card.grid_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # 1. Yuqori qator: Ikonka + Nom + Harakat ko'rsatkichi (→)
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(side="top", fill="x")

        icon_box = ctk.CTkFrame(
            top,
            fg_color=Colors.BG_SOFT,
            corner_radius=6,
            width=28,
            height=28,
        )
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)

        v_img = get_vector_icon(
            tool["icon"],
            size=16,
            color_dark=tool["color"],
            color_light=tool["color"],
            fallback="commands",
        )
        icon_lbl = None
        if v_img:
            icon_lbl = ctk.CTkLabel(icon_box, image=v_img, text="")
            icon_lbl.pack(expand=True)

        name_lbl = ctk.CTkLabel(
            top,
            text=tool["name"],
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        name_lbl.pack(side="left", fill="x", expand=True, padx=(8, 0))

        arrow_lbl = ctk.CTkLabel(
            top,
            text="→",
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_MUTED,
        )
        arrow_lbl.pack(side="right")

        # 2. Pastki qator: Semantik kategoriya nuqtasi + Harakat ko'rsatmasi (Pastki qirraga qat'iy mahkamlangan)
        footer = ctk.CTkFrame(inner, fg_color="transparent")
        footer.pack(side="bottom", fill="x")

        cat_wrap = ctk.CTkFrame(footer, fg_color="transparent")
        cat_wrap.pack(side="left")

        dot_lbl = ctk.CTkLabel(
            cat_wrap,
            text="●",
            font=("Segoe UI", 9),
            text_color=tool["color"],
        )
        dot_lbl.pack(side="left")

        cat_lbl = ctk.CTkLabel(
            cat_wrap,
            text=f" {tool['category'].title()}",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
        )
        cat_lbl.pack(side="left")

        hint_lbl = ctk.CTkLabel(
            footer,
            text="↵ Ishlatish",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
        )
        hint_lbl.pack(side="right")

        # 3. O'rta qism: Qisqa tavsif (1-2 qator, markaziy bo'shliqni to'ldiradi)
        raw_desc = tool["description"]
        clean_desc = (raw_desc[:85] + "...") if len(raw_desc) > 88 else raw_desc

        desc_lbl = ctk.CTkLabel(
            inner,
            text=clean_desc,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            justify="left",
            wraplength=280,
            anchor="nw",
        )
        desc_lbl.pack(side="top", fill="both", expand=True, pady=(4, 2))

        # To'liq ma'lumot tooltip
        full_text = f"{tool['name']} ({tool['category']})\n\n{tool['description']}"
        attach_tooltip(card, full_text)

        # Hover & Click boshqaruvi
        def on_enter(event=None):
            if card.winfo_exists() and not getattr(card, "_is_selected", False):
                card.configure(border_color=tool["color"], fg_color=Colors.BG_HOVER)
                arrow_lbl.configure(text_color=Colors.PRIMARY)
                hint_lbl.configure(text_color=Colors.TEXT_PRIMARY)

        def on_leave(event=None):
            if card.winfo_exists() and not getattr(card, "_is_selected", False):
                card.configure(border_color=Colors.BORDER, fg_color=Colors.BG_CARD)
                arrow_lbl.configure(text_color=Colors.TEXT_MUTED)
                hint_lbl.configure(text_color=Colors.TEXT_MUTED)

        def on_click(event=None):
            self._on_tool_click(tool["name"])

        def on_context_menu(event):
            self._show_context_menu(event, tool)

        all_widgets = [card, inner, top, icon_box, name_lbl, arrow_lbl, desc_lbl, footer, cat_wrap, dot_lbl, cat_lbl, hint_lbl]
        if icon_lbl:
            all_widgets.append(icon_lbl)

        for w in all_widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
            w.bind("<Button-3>", on_context_menu)

        card._arrow_lbl = arrow_lbl
        card._hint_lbl = hint_lbl
        card._tool_data = tool
        card._is_selected = False

        return card

    def _create_list_item(self, tool: dict) -> ctk.CTkFrame:
        """Ixcham ro'yxat ko'rinishidagi Capability Item (48px)"""
        card = ctk.CTkFrame(
            self.grid_frame,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizing.RADIUS_CARD,
            border_width=1,
            border_color=Colors.BORDER,
            height=48,
            cursor="hand2",
        )
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=6)

        left_box = ctk.CTkFrame(inner, fg_color="transparent")
        left_box.pack(side="left")

        icon_box = ctk.CTkFrame(
            left_box,
            fg_color=Colors.BG_SOFT,
            corner_radius=6,
            width=26,
            height=26,
        )
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)

        v_img = get_vector_icon(
            tool["icon"],
            size=14,
            color_dark=tool["color"],
            color_light=tool["color"],
            fallback="commands",
        )
        icon_lbl = None
        if v_img:
            icon_lbl = ctk.CTkLabel(icon_box, image=v_img, text="")
            icon_lbl.pack(expand=True)

        name_lbl = ctk.CTkLabel(
            left_box,
            text=tool["name"],
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
            width=140,
        )
        name_lbl.pack(side="left", padx=(8, 0))

        cat_lbl = ctk.CTkLabel(
            left_box,
            text=f"● {tool['category'].title()}",
            font=Fonts.TINY,
            text_color=tool["color"],
            anchor="w",
        )
        cat_lbl.pack(side="left", padx=(6, 12))

        desc_lbl = ctk.CTkLabel(
            inner,
            text=tool["description"],
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        desc_lbl.pack(side="left", fill="x", expand=True)

        arrow_lbl = ctk.CTkLabel(
            inner,
            text="↵ Ishlatish",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
        )
        arrow_lbl.pack(side="right", padx=(8, 4))

        attach_tooltip(card, f"{tool['name']} ({tool['category']})\n\n{tool['description']}")

        def on_enter(event=None):
            if card.winfo_exists() and not getattr(card, "_is_selected", False):
                card.configure(border_color=tool["color"], fg_color=Colors.BG_HOVER)
                arrow_lbl.configure(text_color=Colors.PRIMARY)

        def on_leave(event=None):
            if card.winfo_exists() and not getattr(card, "_is_selected", False):
                card.configure(border_color=Colors.BORDER, fg_color=Colors.BG_CARD)
                arrow_lbl.configure(text_color=Colors.TEXT_MUTED)

        def on_click(event=None):
            self._on_tool_click(tool["name"])

        def on_context_menu(event):
            self._show_context_menu(event, tool)

        all_widgets = [card, inner, left_box, icon_box, name_lbl, cat_lbl, desc_lbl, arrow_lbl]
        if icon_lbl:
            all_widgets.append(icon_lbl)

        for w in all_widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
            w.bind("<Button-3>", on_context_menu)

        card._arrow_lbl = arrow_lbl
        card._tool_data = tool
        card._is_selected = False

        return card

    def _show_context_menu(self, event, tool: dict):
        """O'ng tugma bosilganda tezkor amallar menyusi"""
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=Colors.BG_PANEL,
            fg=Colors.TEXT_PRIMARY,
            activebackground=Colors.PRIMARY,
            activeforeground="#FFFFFF",
            font=(Fonts.FAMILY, 9),
            bd=1,
            relief="solid",
        )
        menu.add_command(
            label=f"💬 Chatda ishlatish ({tool['name']})",
            command=lambda: self._on_tool_click(tool["name"]),
        )
        menu.add_command(
            label="📋 Nomini nusxalash",
            command=lambda: self._copy_tool_name(tool["name"]),
        )
        menu.add_separator()
        menu.add_command(
            label=f"ℹ️ Kategoriya: {tool['category'].title()}",
            state="disabled",
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_tool_name(self, name: str):
        try:
            self.clipboard_clear()
            self.clipboard_append(name)
            if self.app and hasattr(self.app, "show_toast"):
                self.app.show_toast(f"'{name}' nusxalandi", icon="check")
        except Exception:
            pass

    # ========================================================
    # KEYBOARD NAVIGATION (Raycast style)
    # ========================================================

    def _select_card_by_index(self, index: int):
        visible = self._rendered_tool_names
        if not visible:
            return

        if 0 <= self._selected_index < len(visible):
            old_name = visible[self._selected_index]
            old_card = self._tool_cards.get(old_name)
            if old_card and old_card.winfo_exists():
                old_card._is_selected = False
                old_card.configure(border_color=Colors.BORDER, border_width=1, fg_color=Colors.BG_CARD)
                if hasattr(old_card, "_arrow_lbl"):
                    old_card._arrow_lbl.configure(text_color=Colors.TEXT_MUTED)

        index = max(0, min(index, len(visible) - 1))
        self._selected_index = index

        new_name = visible[index]
        new_card = self._tool_cards.get(new_name)
        if new_card and new_card.winfo_exists():
            new_card._is_selected = True
            new_card.configure(border_color=Colors.PRIMARY, border_width=2, fg_color=Colors.BG_HOVER)
            if hasattr(new_card, "_arrow_lbl"):
                new_card._arrow_lbl.configure(text_color=Colors.PRIMARY)
            self._ensure_card_visible(new_card)

    def _ensure_card_visible(self, card):
        try:
            scroll_canvas = getattr(self.scroll, "_parent_canvas", None)
            if scroll_canvas:
                card_y = card.winfo_y()
                card_h = card.winfo_height()
                canvas_h = scroll_canvas.winfo_height()
                canvas_scroll_y = scroll_canvas.canvasy(0)
                grid_h = max(1, self.grid_frame.winfo_height())
                if card_y < canvas_scroll_y:
                    scroll_canvas.yview_moveto(max(0.0, card_y / grid_h))
                elif card_y + card_h > canvas_scroll_y + canvas_h:
                    scroll_canvas.yview_moveto(max(0.0, (card_y + card_h - canvas_h + 16) / grid_h))
        except Exception:
            pass

    def _clear_selection(self):
        visible = self._rendered_tool_names
        if 0 <= self._selected_index < len(visible):
            old_name = visible[self._selected_index]
            old_card = self._tool_cards.get(old_name)
            if old_card and old_card.winfo_exists():
                old_card._is_selected = False
                old_card.configure(border_color=Colors.BORDER, border_width=1, fg_color=Colors.BG_CARD)
        self._selected_index = -1

    def _on_search_down(self, event=None):
        if self._rendered_tool_names:
            self._select_card_by_index(0)
            self.focus_set()
            return "break"

    def _on_search_return(self, event=None):
        if self._selected_index >= 0 and self._selected_index < len(self._rendered_tool_names):
            name = self._rendered_tool_names[self._selected_index]
            self._on_tool_click(name)
        elif self._rendered_tool_names:
            self._on_tool_click(self._rendered_tool_names[0])
        else:
            self._execute_search(immediate=True)
        return "break"

    def _on_search_escape(self, event=None):
        query = self.search.entry.get().strip() if self.search and self.search.entry else ""
        if query:
            self._clear_search()
        else:
            self.focus_set()
        return "break"

    def _on_key_down(self, event=None):
        cols = self._get_column_count()
        if self._selected_index < 0:
            self._select_card_by_index(0)
        else:
            self._select_card_by_index(self._selected_index + cols)
        return "break"

    def _on_key_up(self, event=None):
        cols = self._get_column_count()
        if self._selected_index - cols < 0:
            self._clear_selection()
            if hasattr(self, "search") and self.search.entry:
                self.search.entry.focus_set()
        else:
            self._select_card_by_index(self._selected_index - cols)
        return "break"

    def _on_key_right(self, event=None):
        if self._selected_index < 0:
            self._select_card_by_index(0)
        else:
            self._select_card_by_index(self._selected_index + 1)
        return "break"

    def _on_key_left(self, event=None):
        if self._selected_index <= 0:
            self._clear_selection()
            if hasattr(self, "search") and self.search.entry:
                self.search.entry.focus_set()
        else:
            self._select_card_by_index(self._selected_index - 1)
        return "break"

    def _on_key_return(self, event=None):
        if 0 <= self._selected_index < len(self._rendered_tool_names):
            name = self._rendered_tool_names[self._selected_index]
            self._on_tool_click(name)
            return "break"

    def _on_key_escape(self, event=None):
        self._clear_selection()
        if hasattr(self, "search") and self.search.entry:
            self.search.entry.focus_set()
        return "break"

    # ========================================================
    # TOOL EXECUTION
    # ========================================================

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
