# ========== plugins.py ==========
# Plugin Manager sahifasi

import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, GlowButton, SecondaryButton


class PluginsPage(ctk.CTkFrame):
    """Plugin boshqaruvi sahifasi"""
    
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()
    
    def _build_ui(self):
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))
        
        ctk.CTkLabel(
            header, text="🔌  Plaginlar",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left")
        
        GlowButton(
            header, text="Yangi plugin", icon="➕"
        ).pack(side="right")
        
        # ===== KONTENT =====
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        
        # ===== PLUGIN TURLARI =====
        self._build_plugin_info()
        self._build_installed_plugins()
        self._build_templates()
    
    def _build_plugin_info(self):
        """Plugin tizimi haqida ma'lumot"""
        info_card = GlassCard(self.scroll, title="ℹ️  Plugin tizimi")
        info_card.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(
            info_card.content,
            text="Mikasa AI plugin tizimi JSON yoki Python format qo'llab-quvvatlaydi.\n"
                 "Plugin'lar plugins/ papkasiga joylanadi va avtomatik yuklanadi.",
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w", justify="left",
            wraplength=600
        ).pack(fill="x")
        
        # Qo'llab-quvvatlanadigan turlar
        types_frame = ctk.CTkFrame(info_card.content, fg_color="transparent")
        types_frame.pack(fill="x", pady=(10, 0))
        
        for icon, label, desc in [
            ("📄", "JSON Plugin", "URL ochish, CMD buyruq"),
            ("🐍", "Python Plugin", "To'liq Python modul"),
        ]:
            item = ctk.CTkFrame(
                types_frame, fg_color=Colors.BG_INPUT,
                corner_radius=8
            )
            item.pack(side="left", fill="x", expand=True, padx=4)
            
            inner = ctk.CTkFrame(item, fg_color="transparent")
            inner.pack(padx=12, pady=8)
            
            ctk.CTkLabel(
                inner, text=f"{icon} {label}",
                font=Fonts.BODY_BOLD,
                text_color=Colors.TEXT_PRIMARY, anchor="w"
            ).pack(fill="x")
            
            ctk.CTkLabel(
                inner, text=desc,
                font=Fonts.SMALL,
                text_color=Colors.TEXT_MUTED, anchor="w"
            ).pack(fill="x")
    
    def _build_installed_plugins(self):
        """O'rnatilgan pluginlar"""
        installed_card = GlassCard(self.scroll, title="📦  O'rnatilgan pluginlar")
        installed_card.pack(fill="x", pady=(0, 12))
        
        # Hozircha namuna plugin
        plugins = [
            ("GitHub", "github.json", "JSON", True,
             "GitHub profil sahifasini ochish"),
        ]
        
        for name, file, ptype, enabled, desc in plugins:
            row = ctk.CTkFrame(
                installed_card.content,
                fg_color=Colors.BG_INPUT,
                corner_radius=8, border_width=1,
                border_color=Colors.BORDER
            )
            row.pack(fill="x", pady=3)
            
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)
            
            # Chap: ma'lumot
            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                info, text=f"🔌 {name}",
                font=Fonts.BODY_BOLD,
                text_color=Colors.TEXT_PRIMARY, anchor="w"
            ).pack(fill="x")
            
            ctk.CTkLabel(
                info, text=f"{desc}  •  {ptype}  •  {file}",
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED, anchor="w"
            ).pack(fill="x")
            
            # O'ng: toggle
            switch = ctk.CTkSwitch(
                inner, text="",
                progress_color=Colors.PRIMARY,
                button_color=Colors.TEXT_PRIMARY,
                fg_color=Colors.BG_DARK
            )
            if enabled:
                switch.select()
            switch.pack(side="right")
        
        if not plugins:
            ctk.CTkLabel(
                installed_card.content,
                text="Plugin topilmadi",
                font=Fonts.BODY,
                text_color=Colors.TEXT_MUTED
            ).pack(pady=20)
    
    def _build_templates(self):
        """Plugin shablonlari"""
        templates_card = GlassCard(self.scroll, title="📋  Shablonlar")
        templates_card.pack(fill="x", pady=(0, 12))
        
        templates = [
            ("🌐", "Web Opener", "Har qanday saytni voice command bilan ochish"),
            ("🖥️", "System Command", "Windows buyruqlarini bajarish"),
            ("📡", "API Caller", "Tashqi API ga so'rov yuborish"),
        ]
        
        for icon, name, desc in templates:
            row = ctk.CTkFrame(
                templates_card.content,
                fg_color=Colors.BG_INPUT,
                corner_radius=8
            )
            row.pack(fill="x", pady=3)
            
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)
            
            ctk.CTkLabel(
                inner, text=f"{icon} {name}",
                font=Fonts.BODY_BOLD,
                text_color=Colors.TEXT_PRIMARY, anchor="w"
            ).pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                inner, text=desc,
                font=Fonts.SMALL,
                text_color=Colors.TEXT_MUTED
            ).pack(side="left", padx=8)
            
            SecondaryButton(
                inner, text="Yaratish", icon="✨"
            ).pack(side="right")
    
    def on_show(self):
        """Sahifa ko'rsatilganda"""
        pass
