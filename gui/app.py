# ========== app.py ==========
# Mikasa AI — Asosiy Application Shell
# Sidebar navigatsiya + Main content area + Status bar

import customtkinter as ctk
import os
import datetime
import psutil
import threading
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import NavItem, StatusBadge
from gui.backend import BackendBridge

# Versiyani bitta joydan olish
try:
    from main import VERSION
except ImportError:
    VERSION = "3.1.0"


class MikasaApp(ctk.CTk):
    """Mikasa AI asosiy dastur oynasi"""
    
    def __init__(self, connect_backend=False):
        super().__init__()
        
        self._current_page = None
        self._pages = {}
        
        # Backend bridge — GUI va main.py orasida ko'prik
        self.bridge = BackendBridge(self)
        self._nav_items = {}
        
        # Oyna sozlamalari
        self.title(f"MIKASA AI v{VERSION}")
        self.geometry("1280x800")
        self.minsize(1000, 600)
        self.configure(fg_color=Colors.BG_DARK)
        
        # CustomTkinter tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # UI qurish
        self._build_titlebar()
        self._build_layout()
        self._build_sidebar()
        self._build_statusbar()
        
        # Sahifalarni yaratish
        self._init_pages()
        
        # Dashboard dan boshlash
        self.navigate_to("dashboard")
        
        # Soat va tizim ma'lumotlarini yangilash
        self._update_clock()
        self._update_system_stats()
        
        # Backend ni ishga tushirish
        if connect_backend:
            self.bridge.init_backend()
        
        # Yopish event
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    # ========== LAYOUT ==========
    
    def _build_titlebar(self):
        """Dastur sarlavha paneli"""
        self.titlebar = ctk.CTkFrame(
            self, fg_color=Colors.BG_DARKEST,
            height=44, corner_radius=0
        )
        self.titlebar.pack(fill="x", side="top")
        self.titlebar.pack_propagate(False)
        
        # Logo va nom
        self.logo_label = ctk.CTkLabel(
            self.titlebar,
            text="  🔷  MIKASA AI",
            font=(Fonts.FAMILY, 14, "bold"),
            text_color=Colors.PRIMARY,
            anchor="w"
        )
        self.logo_label.pack(side="left", padx=12)
        
        # Versiya
        self.version_label = ctk.CTkLabel(
            self.titlebar,
            text=f"v{VERSION}",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
            anchor="w"
        )
        self.version_label.pack(side="left", padx=(0, 16))
        
        # Status badge
        self.status_badge = StatusBadge(
            self.titlebar, status="online", text="Tayyor"
        )
        self.status_badge.pack(side="left", padx=8)
        
        # O'ng tomon — soat
        self.clock_label = ctk.CTkLabel(
            self.titlebar,
            text="--:--",
            font=(Fonts.FAMILY, 12),
            text_color=Colors.TEXT_SECONDARY
        )
        self.clock_label.pack(side="right", padx=16)
    
    def _build_layout(self):
        """Asosiy layout — sidebar + content"""
        self.main_container = ctk.CTkFrame(
            self, fg_color="transparent"
        )
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar konteyneri
        self.sidebar_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=Colors.SIDEBAR_BG,
            width=Sizing.SIDEBAR_WIDTH_EXPANDED,
            corner_radius=0
        )
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        # Main content area
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=Colors.BG_DARK,
            corner_radius=0
        )
        self.content_frame.pack(side="left", fill="both", expand=True)
    
    def _build_sidebar(self):
        """Sidebar navigatsiya"""
        # Nav elementlar konfiguratsiya
        nav_config = [
            ("dashboard",  Icons.DASHBOARD, "Dashboard"),
            ("voice",      Icons.VOICE,     "Ovozli dialog"),
            ("chat",       Icons.CHAT,      "AI Suhbat"),
            ("commands",   Icons.COMMANDS,  "Buyruqlar"),
            ("memory",     Icons.MEMORY,    "Xotira"),
            ("scheduler",  Icons.SCHEDULER, "Rejalashtiruvchi"),
            ("plugins",    Icons.PLUGINS,   "Plaginlar"),
        ]
        
        # Navigatsiya paneli
        self.nav_frame = ctk.CTkFrame(
            self.sidebar_frame, fg_color="transparent"
        )
        self.nav_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Nav elementlarni yaratish
        for page_id, icon, label in nav_config:
            nav_item = NavItem(
                self.nav_frame, 
                icon=icon, 
                label=label,
                command=lambda pid=page_id: self.navigate_to(pid)
            )
            nav_item.pack(fill="x", pady=2)
            self._nav_items[page_id] = nav_item
        
        # Ajratgich
        separator = ctk.CTkFrame(
            self.nav_frame, fg_color=Colors.BORDER,
            height=1
        )
        separator.pack(fill="x", padx=12, pady=8)
        
        # Sozlamalar (pastda)
        settings_item = NavItem(
            self.nav_frame,
            icon=Icons.SETTINGS,
            label="Sozlamalar",
            command=lambda: self.navigate_to("settings")
        )
        settings_item.pack(fill="x", pady=2, side="bottom")
        self._nav_items["settings"] = settings_item
    
    def _build_statusbar(self):
        """Pastki status bar"""
        self.statusbar = ctk.CTkFrame(
            self, fg_color=Colors.STATUSBAR_BG,
            height=Sizing.STATUSBAR_HEIGHT,
            corner_radius=0
        )
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        
        # CPU
        self.cpu_label = ctk.CTkLabel(
            self.statusbar,
            text="CPU: --%",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_MUTED
        )
        self.cpu_label.pack(side="left", padx=16)
        
        # Ajratgich
        ctk.CTkLabel(
            self.statusbar, text="│",
            font=Fonts.STATUS, text_color=Colors.BORDER
        ).pack(side="left")
        
        # RAM
        self.ram_label = ctk.CTkLabel(
            self.statusbar,
            text="RAM: --%",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_MUTED
        )
        self.ram_label.pack(side="left", padx=16)
        
        # Ajratgich
        ctk.CTkLabel(
            self.statusbar, text="│",
            font=Fonts.STATUS, text_color=Colors.BORDER
        ).pack(side="left")
        
        # API status
        self.api_label = ctk.CTkLabel(
            self.statusbar,
            text="API: Tayyor",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_MUTED
        )
        self.api_label.pack(side="left", padx=16)
        
        # O'ng tomon — TTS engine
        self.tts_label = ctk.CTkLabel(
            self.statusbar,
            text="TTS: Silero",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_MUTED
        )
        self.tts_label.pack(side="right", padx=16)
    
    # ========== SAHIFALAR ==========
    
    def _init_pages(self):
        """Barcha sahifalarni yaratish"""
        from gui.pages.dashboard import DashboardPage
        from gui.pages.voice import VoicePage
        from gui.pages.chat import ChatPage
        from gui.pages.commands import CommandsPage
        from gui.pages.memory import MemoryPage
        from gui.pages.scheduler import SchedulerPage
        from gui.pages.plugins import PluginsPage
        from gui.pages.settings import SettingsPage
        
        page_classes = {
            "dashboard": DashboardPage,
            "voice":     VoicePage,
            "chat":      ChatPage,
            "commands":  CommandsPage,
            "memory":    MemoryPage,
            "scheduler": SchedulerPage,
            "plugins":   PluginsPage,
            "settings":  SettingsPage,
        }
        
        for page_id, page_class in page_classes.items():
            page = page_class(self.content_frame, app=self)
            self._pages[page_id] = page
    
    def navigate_to(self, page_id):
        """Sahifaga o'tish"""
        if page_id == self._current_page:
            return
        
        # Avvalgi sahifani yashirish
        if self._current_page and self._current_page in self._pages:
            self._pages[self._current_page].pack_forget()
        
        # Yangi sahifani ko'rsatish
        if page_id in self._pages:
            self._pages[page_id].pack(fill="both", expand=True)
            
            # on_show callback — sahifa ko'rsatilganda
            if hasattr(self._pages[page_id], 'on_show'):
                self._pages[page_id].on_show()
        
        # Nav aktivligini yangilash
        for nav_id, nav_item in self._nav_items.items():
            nav_item.set_active(nav_id == page_id)
        
        self._current_page = page_id
    
    # ========== YANGILANISHLAR ==========
    
    def _update_clock(self):
        """Soatni har soniyada yangilash"""
        now = datetime.datetime.now()
        self.clock_label.configure(text=now.strftime("%H:%M:%S"))
        self.after(1000, self._update_clock)
    
    def _update_system_stats(self):
        """Tizim ma'lumotlarini har 3 soniyada yangilash"""
        try:
            cpu = psutil.cpu_percent(interval=0)
            ram = psutil.virtual_memory().percent
            self.cpu_label.configure(text=f"CPU: {cpu:.0f}%")
            self.ram_label.configure(text=f"RAM: {ram:.0f}%")
            
            # Rang o'zgartirish
            cpu_color = Colors.SUCCESS if cpu < 60 else (
                Colors.WARNING if cpu < 85 else Colors.DANGER
            )
            ram_color = Colors.SUCCESS if ram < 70 else (
                Colors.WARNING if ram < 90 else Colors.DANGER
            )
            self.cpu_label.configure(text_color=cpu_color)
            self.ram_label.configure(text_color=ram_color)
        except Exception:
            pass
        
        self.after(3000, self._update_system_stats)
    
    def set_status(self, status, text=None):
        """Global holatni o'zgartirish"""
        self.status_badge.set_status(status, text)
    
    # ========== YOPISH ==========
    
    def _on_closing(self):
        """Dasturni yopish — resurslarni tozalash"""
        try:
            # 1. Tinglashni to'xtatish
            self.bridge.stop_listening()
            
            # 2. AgentMemory saqlash
            if self.bridge._agent_memory:
                self.bridge._agent_memory.save_all()
            
            # 3. Scheduler to'xtatish
            if self.bridge._agent_scheduler:
                self.bridge._agent_scheduler.stop()
            
            # 4. pygame tozalash
            try:
                import pygame
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
            except Exception:
                pass
            
            # 5. Temp TTS fayllarni tozalash
            import glob
            import tempfile
            for pattern in ["silero_tts_*.wav", "edge_tts_*.mp3"]:
                for f in glob.glob(os.path.join(tempfile.gettempdir(), pattern)):
                    try:
                        os.remove(f)
                    except Exception:
                        pass
            
        except Exception as e:
            import logging
            logging.error(f"Yopish xatolik: {e}")
        
        self.destroy()
