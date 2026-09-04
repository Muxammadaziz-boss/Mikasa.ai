# ========== memory.py ==========
# Memory Hub sahifasi — xotira boshqaruvi

import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, GlowButton, SecondaryButton, SearchBar, StatWidget


class MemoryPage(ctk.CTkFrame):
    """AI xotira markaziy — profil, bilimlar, tarix"""
    
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()
    
    def _build_ui(self):
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))
        
        ctk.CTkLabel(
            header, text="🧠  Xotira markazi",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left")
        
        # Eksport tugma
        SecondaryButton(
            header, text="Eksport", icon="📤"
        ).pack(side="right")
        
        # ===== STATS =====
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 12))
        
        stats_data = [
            ("0", "Kontekst", "💭", Colors.PRIMARY),
            ("0", "Suhbatlar", "💬", Colors.SECONDARY),
            ("0", "Bilimlar", "📚", Colors.SUCCESS),
            ("✅", "Profil", "👤", Colors.INFO),
        ]
        
        for i, (val, label, icon, color) in enumerate(stats_data):
            w = StatWidget(stats_frame, value=val, label=label, icon=icon, color=color)
            w.grid(row=0, column=i, padx=5, pady=4, sticky="ew")
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        # ===== TABVIEW =====
        self.tabs = ctk.CTkTabview(
            self, fg_color=Colors.BG_SURFACE,
            segmented_button_fg_color=Colors.BG_INPUT,
            segmented_button_selected_color=Colors.PRIMARY_DARK,
            segmented_button_selected_hover_color=Colors.PRIMARY,
            segmented_button_unselected_color=Colors.BG_INPUT,
            segmented_button_unselected_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        
        # 3 tab
        tab1 = self.tabs.add("👤 Profil")
        tab2 = self.tabs.add("📚 Bilimlar")
        tab3 = self.tabs.add("💬 Suhbat tarixi")
        
        self._build_profile_tab(tab1)
        self._build_knowledge_tab(tab2)
        self._build_history_tab(tab3)
    
    def _build_profile_tab(self, parent):
        """Foydalanuvchi profili"""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        fields = [
            ("Ism", "Muxammadaziz"),
            ("Ovoz turi", "Erkak"),
            ("Til", "O'zbek"),
            ("Yaratilgan", "2026-yil"),
        ]
        
        for label, value in fields:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            
            ctk.CTkLabel(
                row, text=label,
                font=Fonts.SMALL_BOLD,
                text_color=Colors.TEXT_SECONDARY,
                width=120, anchor="w"
            ).pack(side="left")
            
            entry = ctk.CTkEntry(
                row, font=Fonts.BODY,
                fg_color=Colors.BG_INPUT,
                border_width=1,
                border_color=Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY,
                height=36
            )
            entry.insert(0, value)
            entry.pack(side="left", fill="x", expand=True)
        
        # Saqlash tugma
        GlowButton(
            scroll, text="Saqlash", icon="💾"
        ).pack(pady=16)
    
    def _build_knowledge_tab(self, parent):
        """Bilimlar bazasi"""
        # Qidiruv
        search = SearchBar(parent, placeholder="Bilimlardan qidirish...")
        search.pack(fill="x", padx=16, pady=(12, 8))
        
        # Bilimlar ro'yxati
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        # Yangi bilim qo'shish
        add_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        add_frame.pack(fill="x", padx=16, pady=(8, 16))
        
        self.new_key = ctk.CTkEntry(
            add_frame, placeholder_text="Kalit",
            font=Fonts.SMALL, fg_color=Colors.BG_INPUT,
            border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY, height=34, width=150
        )
        self.new_key.pack(side="left", padx=(0, 4))
        
        self.new_value = ctk.CTkEntry(
            add_frame, placeholder_text="Qiymat",
            font=Fonts.SMALL, fg_color=Colors.BG_INPUT,
            border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY, height=34
        )
        self.new_value.pack(side="left", fill="x", expand=True, padx=4)
        
        GlowButton(
            add_frame, text="Qo'shish", icon="➕"
        ).pack(side="right", padx=(4, 0))
        
        # Bo'sh holat
        ctk.CTkLabel(
            scroll, text="Bilimlar bazasi bo'sh\nAI suhbatda avtomatik to'ldiradi",
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED
        ).pack(pady=30)
    
    def _build_history_tab(self, parent):
        """Suhbat tarixi"""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        # Bo'sh holat
        ctk.CTkLabel(
            scroll, text="Suhbat tarixi bo'sh\nAI bilan gaplashganda avtomatik to'ladi",
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED
        ).pack(pady=30)
    
    def on_show(self):
        """Sahifa ko'rsatilganda"""
        pass
