# ========== commands.py ==========
# Command Center sahifasi — tool'lar va buyruqlarni boshqarish

import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, SearchBar, GlowButton


class CommandsPage(ctk.CTkFrame):
    """Buyruqlar va Tool'lar markazi"""
    
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()
    
    def _build_ui(self):
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))
        
        ctk.CTkLabel(
            header, text="⚡  Buyruqlar markazi",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left")
        
        # ===== QIDIRUV =====
        self.search = SearchBar(
            self, placeholder="Tool yoki buyruq qidiring..."
        )
        self.search.pack(fill="x", padx=20, pady=(0, 12))
        
        # ===== SCROLLABLE KONTENT =====
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        
        # ===== TOOL KARTALAR =====
        self._build_tools_grid()
        
        # ===== TARIX =====
        self._build_execution_history()
    
    def _build_tools_grid(self):
        """14 ta tool kartalar gridi"""
        # Sarlavha
        ctk.CTkLabel(
            self.scroll,
            text="🛠️  Agent Tools (14 ta)",
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 20))
        
        tools = [
            ("🔍", "Web Search", "Internet qidiruv", "internet", Colors.INFO),
            ("🔢", "Calculator", "Matematik hisob", "utility", Colors.SUCCESS),
            ("💻", "System Control", "Tizim boshqaruv", "system", Colors.DANGER),
            ("🎵", "Music Player", "Musiqa boshqaruv", "media", Colors.SECONDARY),
            ("🌤️", "Weather", "Ob-havo ma'lumot", "info", Colors.WARNING),
            ("📌", "Reminder", "Eslatmalar", "productivity", Colors.PRIMARY),
            ("📁", "File Manager", "Fayl boshqaruv", "utility", Colors.SUCCESS),
            ("📚", "Knowledge", "Bilimlar bazasi", "memory", Colors.SECONDARY),
            ("🕐", "DateTime", "Sana va vaqt", "info", Colors.TEXT_MUTED),
            ("⏰", "Scheduler", "Vazifa rejalashtirish", "productivity", Colors.PRIMARY),
            ("📄", "RAG Reader", "Fayl o'qish", "utility", Colors.INFO),
            ("💱", "Currency", "Valyuta kurslari", "info", Colors.WARNING),
            ("🌍", "Translator", "Tarjima", "utility", Colors.SUCCESS),
            ("👁️", "Screen Analyze", "Ekran tahlili", "system", Colors.DANGER),
        ]
        
        for i, (icon, name, desc, category, color) in enumerate(tools):
            row, col = divmod(i, 4)
            card = self._create_tool_card(grid, icon, name, desc, color)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        for i in range(4):
            grid.columnconfigure(i, weight=1)
    
    def _create_tool_card(self, parent, icon, name, desc, accent_color):
        """Tool karta yaratish"""
        card = ctk.CTkFrame(
            parent,
            fg_color=Colors.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=Colors.BORDER,
            cursor="hand2"
        )
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", padx=14, pady=12)
        
        # Icon + Nom
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        
        ctk.CTkLabel(
            top, text=icon,
            font=(Fonts.FAMILY, 20),
            text_color=accent_color
        ).pack(side="left")
        
        ctk.CTkLabel(
            top, text=f"  {name}",
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        ).pack(side="left", fill="x", expand=True)
        
        # Tavsif
        ctk.CTkLabel(
            inner, text=desc,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            anchor="w"
        ).pack(fill="x", pady=(6, 0))
        
        # Hover effect
        def on_enter(e):
            card.configure(border_color=accent_color)
        def on_leave(e):
            card.configure(border_color=Colors.BORDER)
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        
        return card
    
    def _build_execution_history(self):
        """Buyruq bajarilish tarixi"""
        history_card = GlassCard(
            self.scroll, title="📋  Bajarilish tarixi"
        )
        history_card.pack(fill="x", pady=(0, 16))
        
        # Bo'sh holat
        ctk.CTkLabel(
            history_card.content,
            text="Hali buyruq bajarilmagan\nTool tanlang yoki ovozli buyruq bering",
            font=Fonts.BODY,
            text_color=Colors.TEXT_MUTED
        ).pack(pady=20)
    
    def on_show(self):
        """Sahifa ko'rsatilganda"""
        self.search.entry.focus_set()
