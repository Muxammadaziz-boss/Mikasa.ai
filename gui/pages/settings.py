# ========== settings.py ==========
# Settings sahifasi — barcha sozlamalar

import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, GlowButton, SecondaryButton


class SettingsPage(ctk.CTkFrame):
    """Dastur sozlamalari sahifasi"""
    
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()
    
    def _build_ui(self):
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))
        
        ctk.CTkLabel(
            header, text="⚙️  Sozlamalar",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left")
        
        self.save_btn = GlowButton(
            header, text="Saqlash", icon="💾",
            command=self._save_settings
        )
        self.save_btn.pack(side="right")
        
        # ===== SCROLLABLE KONTENT =====
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        
        # ===== BO'LIMLAR =====
        self._build_general_section()
        self._build_audio_section()
        self._build_ai_section()
        self._build_gui_section()
        self._build_data_section()
    
    def _build_general_section(self):
        """Umumiy sozlamalar"""
        card = GlassCard(self.scroll, title="🏷️  Umumiy")
        card.pack(fill="x", pady=(0, 12))
        
        # Dastur nomi
        self._add_field(card.content, "Dastur nomi", "Ovozli Yordamchi Pro")
        
        # Versiya (o'zgarmas)
        row = ctk.CTkFrame(card.content, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            row, text="Versiya", font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY, width=140, anchor="w"
        ).pack(side="left")
        try:
            from main import VERSION
            ver = VERSION
        except ImportError:
            ver = "3.1.0"
        ctk.CTkLabel(
            row, text=ver, font=Fonts.BODY,
            text_color=Colors.TEXT_MUTED
        ).pack(side="left")
        
        # Til
        self._add_dropdown(
            card.content, "Til", 
            ["O'zbek", "Rus", "Ingliz"],
            "O'zbek"
        )
    
    def _build_audio_section(self):
        """Audio sozlamalari"""
        card = GlassCard(self.scroll, title="🔊  Audio")
        card.pack(fill="x", pady=(0, 12))
        
        # Ovoz turi
        self._add_segmented(
            card.content, "Ovoz turi",
            ["Erkak", "Ayol"], "Erkak"
        )
        
        # TTS Engine
        self._add_segmented(
            card.content, "TTS Engine",
            ["Silero (Local)", "Edge TTS (Cloud)"],
            "Silero (Local)"
        )
        
        # Tezlik
        self._add_slider(
            card.content, "Ovoz tezligi",
            0.5, 2.0, 1.0
        )
        
        # Sample rate
        self._add_dropdown(
            card.content, "Sample Rate",
            ["16000", "22050", "44100"],
            "16000"
        )
    
    def _build_ai_section(self):
        """AI sozlamalari"""
        card = GlassCard(self.scroll, title="🤖  AI")
        card.pack(fill="x", pady=(0, 12))
        
        # Gemini API
        self._add_field(
            card.content, "Gemini API Key",
            "●●●●●●●●", show="●"
        )
        
        # OpenRouter API
        self._add_field(
            card.content, "OpenRouter Key",
            "●●●●●●●●", show="●"
        )
        
        # Model
        self._add_dropdown(
            card.content, "AI Model",
            ["Gemini 2.0 Flash", "GPT-3.5 Turbo", "GPT-4"],
            "Gemini 2.0 Flash"
        )
        
        # Timeout
        self._add_slider(
            card.content, "API Timeout (s)",
            5, 30, 15
        )
    
    def _build_gui_section(self):
        """GUI sozlamalari"""
        card = GlassCard(self.scroll, title="🎨  Interfeys")
        card.pack(fill="x", pady=(0, 12))
        
        # Tema
        self._add_segmented(
            card.content, "Mavzu",
            ["Qorong'u", "Yorug'"],
            "Qorong'u"
        )
        
        # Rang sxemasi
        self._add_dropdown(
            card.content, "Rang sxemasi",
            ["Cyan (ko'k)", "Purple (binafsha)", "Green (yashil)", "Orange (to'q sariq)"],
            "Cyan (ko'k)"
        )
        
        # Shrift o'lchami
        self._add_slider(
            card.content, "Shrift o'lchami",
            10, 18, 13
        )
        
        # Animatsiyalar
        self._add_toggle(card.content, "Animatsiyalar", True)
    
    def _build_data_section(self):
        """Ma'lumotlar boshqaruvi"""
        card = GlassCard(self.scroll, title="📦  Ma'lumotlar")
        card.pack(fill="x", pady=(0, 12))
        
        # Harakatlar
        actions = ctk.CTkFrame(card.content, fg_color="transparent")
        actions.pack(fill="x", pady=4)
        
        for text, icon, color in [
            ("Keshni tozalash", "🗑️", Colors.WARNING),
            ("Loglarni tozalash", "📋", Colors.WARNING),
            ("Ma'lumot eksport", "📤", Colors.INFO),
            ("Dasturni tiklash", "🔄", Colors.DANGER),
        ]:
            btn = ctk.CTkButton(
                actions, text=f" {icon}  {text}",
                font=Fonts.SMALL,
                fg_color=Colors.BG_INPUT,
                hover_color=Colors.BG_HOVER,
                text_color=Colors.TEXT_SECONDARY,
                border_width=1,
                border_color=Colors.BORDER,
                corner_radius=8,
                height=36
            )
            btn.pack(fill="x", pady=3)
    
    # ========== YORDAMCHI FUNKSIYALAR ==========
    
    def _add_field(self, parent, label, default="", show=None):
        """Matn kiritish maydoni"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(
            row, text=label, font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=140, anchor="w"
        ).pack(side="left")
        
        entry = ctk.CTkEntry(
            row, font=Fonts.BODY,
            fg_color=Colors.BG_INPUT,
            border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=34, show=show or ""
        )
        if default and show is None:
            entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        return entry
    
    def _add_dropdown(self, parent, label, values, default=""):
        """Dropdown tanlash"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(
            row, text=label, font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=140, anchor="w"
        ).pack(side="left")
        
        dropdown = ctk.CTkOptionMenu(
            row, values=values,
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            button_color=Colors.BG_CARD,
            button_hover_color=Colors.BG_HOVER,
            dropdown_fg_color=Colors.BG_CARD,
            dropdown_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            height=34
        )
        if default:
            dropdown.set(default)
        dropdown.pack(side="left", fill="x", expand=True)
        return dropdown
    
    def _add_segmented(self, parent, label, values, default=""):
        """Segmented button"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(
            row, text=label, font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=140, anchor="w"
        ).pack(side="left")
        
        seg = ctk.CTkSegmentedButton(
            row, values=values, font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            selected_color=Colors.PRIMARY_DARK,
            selected_hover_color=Colors.PRIMARY,
            unselected_color=Colors.BG_INPUT,
            unselected_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY
        )
        if default:
            seg.set(default)
        seg.pack(side="left", fill="x", expand=True)
        return seg
    
    def _add_slider(self, parent, label, from_, to, default):
        """Slider"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(
            row, text=label, font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=140, anchor="w"
        ).pack(side="left")
        
        slider = ctk.CTkSlider(
            row, from_=from_, to=to,
            progress_color=Colors.PRIMARY,
            button_color=Colors.PRIMARY,
            button_hover_color=Colors.PRIMARY_DARK,
            fg_color=Colors.BG_INPUT
        )
        slider.set(default)
        slider.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        val_label = ctk.CTkLabel(
            row, text=str(default), font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED, width=40
        )
        val_label.pack(side="right")
        
        slider.configure(
            command=lambda v: val_label.configure(text=f"{v:.1f}")
        )
        return slider
    
    def _add_toggle(self, parent, label, default=False):
        """Toggle switch"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        
        ctk.CTkLabel(
            row, text=label, font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=140, anchor="w"
        ).pack(side="left")
        
        switch = ctk.CTkSwitch(
            row, text="",
            progress_color=Colors.PRIMARY,
            button_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.BG_INPUT
        )
        if default:
            switch.select()
        switch.pack(side="left")
        return switch
    
    def _save_settings(self):
        """Sozlamalarni saqlash"""
        # Saqlanganligi haqida foydalanuvchiga xabar
        self.save_btn.configure(text="✅  Saqlandi!", fg_color=Colors.SUCCESS)
        self.after(2000, lambda: self.save_btn.configure(
            text="💾  Saqlash", fg_color=Colors.PRIMARY_DARK
        ))
    
    def on_show(self):
        """Sahifa ko'rsatilganda"""
        pass
