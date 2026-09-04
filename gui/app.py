# ========== app.py ==========
# Mikasa AI — Asosiy Application Shell
# Sidebar navigatsiya + Main content area + Status bar

import customtkinter as ctk
from customtkinter.windows.widgets.core_rendering import DrawEngine

# Windows Tkinter font to'rtburchak/qavs qoldiqlarisiz toza geometriya
DrawEngine.preferred_drawing_method = "circle_shapes"

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
    VERSION = "6.0.0"


class MikasaApp(ctk.CTk):
    """Mikasa AI asosiy dastur oynasi"""

    def __init__(self, connect_backend=False):
        super().__init__()

        self._current_page = None
        self._pages = {}
        self._compact_mode = False
        self._ui_theme = "dark"
        self._color_theme = "blue"
        self._connect_backend = connect_backend
        self._is_rebuilding_shell = False
        self._status_state = {"status": "online", "text": "Tayyor"}
        self._window_sizes = {"standard": "1280x800", "compact": "960x700"}

        # Backend bridge — GUI va main.py orasida ko'prik
        self.bridge = BackendBridge(self)
        self._nav_items = {}

        self._load_ui_preferences()
        self._apply_ui_preferences(initial=True)

        # Oyna sozlamalari
        self.title(f"MIKASA AI v{VERSION}")
        self.configure(fg_color=Colors.BG_DARK)
        self._apply_window_mode()

        # UI qurish
        self._build_shell()

        # Soat va tizim ma'lumotlarini yangilash
        self._update_clock()
        self._update_system_stats()

        # Backend ni ishga tushirish
        if connect_backend:
            self.bridge.init_backend()

        # Yopish event
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ========== LAYOUT ==========

    def _load_ui_preferences(self):
        try:
            from config import get_config

            self._ui_theme = str(get_config("gui.theme", "dark") or "dark").lower()
            self._compact_mode = bool(get_config("gui.compact_mode", False))
            self._color_theme = str(
                get_config("gui.color", get_config("gui.color_scheme", "blue"))
                or "blue"
            )
            self._window_sizes["standard"] = str(
                get_config("gui.window_size", self._window_sizes["standard"])
                or self._window_sizes["standard"]
            )
            self._window_sizes["compact"] = str(
                get_config("gui.compact_window_size", self._window_sizes["compact"])
                or self._window_sizes["compact"]
            )
        except Exception:
            self._ui_theme = "dark"
            self._compact_mode = False
            self._color_theme = "blue"

    def _appearance_mode_value(self):
        theme = self._ui_theme.lower()
        if theme == "light":
            return "Light"
        if theme == "system":
            return "System"
        return "Dark"

    def _apply_ui_preferences(self, initial=False):
        ctk.set_appearance_mode(self._appearance_mode_value())
        try:
            ctk.set_default_color_theme(self._color_theme)
        except Exception:
            ctk.set_default_color_theme("blue")
            self._color_theme = "blue"

        Colors.apply_theme(self._ui_theme)
        Fonts.apply_density(self._compact_mode)
        Sizing.apply_density(self._compact_mode)

        if not initial:
            self._rebuild_shell()

    def apply_ui_preferences(self, theme=None, compact_mode=None, color_theme=None):
        self._remember_window_geometry()
        if theme is not None:
            self._ui_theme = str(theme).lower()
        if compact_mode is not None:
            self._compact_mode = bool(compact_mode)
        if color_theme is not None:
            self._color_theme = str(color_theme)
        self._apply_ui_preferences(initial=False)

    def _apply_window_mode(self):
        target_size = self._window_sizes[
            "compact" if self._compact_mode else "standard"
        ]
        if self._compact_mode:
            self.geometry(target_size)
            self.minsize(820, 560)
        else:
            self.geometry(target_size)
            self.minsize(1000, 600)

    def _build_shell(self, page_id="dashboard", page_states=None):
        self._build_titlebar()
        self._build_statusbar()
        self._build_layout()
        self._build_sidebar()
        self._init_pages()
        if page_states:
            self._restore_page_states(page_states)
        self.navigate_to(page_id)
        self._restore_runtime_state()

    def _rebuild_shell(self):
        current_page = self._current_page or "dashboard"
        page_states = self._capture_page_states()
        self._current_page = None
        self._is_rebuilding_shell = True

        for page in self._pages.values():
            try:
                page.destroy()
            except Exception:
                pass

        self._pages = {}
        self._nav_items = {}

        for attr in [
            "titlebar",
            "titlebar_divider",
            "sidebar_divider",
            "main_container",
            "statusbar_divider",
            "statusbar",
        ]:
            widget = getattr(self, attr, None)
            if widget is not None:
                try:
                    widget.destroy()
                except Exception:
                    pass

        try:
            self.configure(fg_color=Colors.BG_DARK)
            self._apply_window_mode()
            self._build_shell(current_page, page_states=page_states)
        finally:
            self._is_rebuilding_shell = False

        self._restore_page_focus()

    def _capture_page_states(self):
        states = {}
        for page_id, page in self._pages.items():
            if hasattr(page, "export_ui_state"):
                try:
                    state = page.export_ui_state()
                    if state is not None:
                        states[page_id] = state
                except Exception:
                    pass
        return states

    def _restore_page_states(self, states):
        for page_id, state in states.items():
            page = self._pages.get(page_id)
            if page and hasattr(page, "import_ui_state"):
                try:
                    page.import_ui_state(state)
                except Exception:
                    pass

    def _restore_runtime_state(self):
        self.set_status(self._status_state["status"], self._status_state["text"])
        self._sync_tts_label()

        try:
            if self.bridge:
                self.bridge._refresh_dashboard_activity()
        except Exception:
            pass

    def _restore_page_focus(self):
        return

    def _remember_window_geometry(self):
        try:
            if not self.winfo_exists() or self.state() != "normal":
                return
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            if width < 300 or height < 200:
                return
            geometry = f"{width}x{height}+{self.winfo_x()}+{self.winfo_y()}"
            if geometry and "x" in geometry:
                key = "compact" if self._compact_mode else "standard"
                self._window_sizes[key] = geometry
        except Exception:
            pass

    def _sync_tts_label(self):
        if not hasattr(self, "tts_label"):
            return
        try:
            from config import get_config

            engine = get_config("audio.tts_engine", "silero")
            label = "Edge TTS" if engine == "edge_tts" else "Silero"
        except Exception:
            label = "Silero"

        self.tts_label.configure(text=f"TTS: {label}")

    def _build_titlebar(self):
        """Dastur sarlavha paneli — Apple Dark minimal"""
        self.titlebar = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_DARKEST,
            height=40 if self._compact_mode else 44,
            corner_radius=0,
        )
        self.titlebar.pack(fill="x", side="top")
        self.titlebar.pack_propagate(False)

        # Logo va nom
        self.logo_label = ctk.CTkLabel(
            self.titlebar,
            text="  MIKASA" if self._compact_mode else "  MIKASA AI",
            font=(Fonts.FAMILY, 13, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.logo_label.pack(side="left", padx=(14, 6))

        # Versiya pill badge
        if not self._compact_mode:
            self.version_badge = ctk.CTkFrame(
                self.titlebar,
                fg_color=Colors.BG_CARD,
                corner_radius=6,
                border_width=1,
                border_color=Colors.BORDER,
                bg_color=Colors.BG_DARKEST,
            )
            self.version_badge.pack(side="left", padx=(0, 10))
            self.version_label = ctk.CTkLabel(
                self.version_badge,
                text=f"v{VERSION}",
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
            )
            self.version_label.pack(padx=6, pady=1)

        # Status badge
        self.status_badge = StatusBadge(
            self.titlebar,
            status=self._status_state["status"],
            text=self._status_state["text"],
            bg_color=Colors.BG_DARKEST,
        )
        self.status_badge.pack(side="left", padx=6)

        self.page_label = ctk.CTkLabel(
            self.titlebar,
            text="Dashboard",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.page_label.pack(side="left", padx=8 if self._compact_mode else 10)

        self.user_label = ctk.CTkLabel(
            self.titlebar,
            text=f"{self._get_user_name()}",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_MUTED,
        )
        if not self._compact_mode:
            self.user_label.pack(side="left", padx=8)

        # O'ng tomon — soat
        self.clock_label = ctk.CTkLabel(
            self.titlebar,
            text="--:--",
            font=(Fonts.FAMILY, 12),
            text_color=Colors.TEXT_MUTED,
        )
        self.clock_label.pack(side="right", padx=16)

        # 1px hairline border below titlebar
        self.titlebar_divider = ctk.CTkFrame(
            self,
            fg_color=Colors.BORDER,
            height=1,
            corner_radius=0,
        )
        self.titlebar_divider.pack(fill="x", side="top")

    def _build_layout(self):
        """Asosiy layout — sidebar + content"""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # Sidebar konteyneri
        self.sidebar_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=Colors.SIDEBAR_BG,
            width=Sizing.SIDEBAR_WIDTH_EXPANDED,
            corner_radius=0,
        )
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # 1px vertical hairline divider
        self.sidebar_divider = ctk.CTkFrame(
            self.main_container,
            fg_color=Colors.BORDER,
            width=1,
            corner_radius=0,
        )
        self.sidebar_divider.pack(side="left", fill="y")

        # Main content area
        self.content_frame = ctk.CTkFrame(
            self.main_container, fg_color=Colors.BG_DARK, corner_radius=0
        )
        self.content_frame.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        """Sidebar navigatsiya"""
        # Nav elementlar konfiguratsiya
        nav_config = [
            ("dashboard", Icons.DASHBOARD, "Dashboard"),
            ("voice", Icons.VOICE, "Ovozli dialog"),
            ("chat", Icons.CHAT, "AI Suhbat"),
            ("commands", Icons.COMMANDS, "Buyruqlar"),
            ("memory", Icons.MEMORY, "Xotira"),
            ("scheduler", Icons.SCHEDULER, "Rejalashtiruvchi"),
            ("plugins", Icons.PLUGINS, "Plaginlar"),
        ]

        # Navigatsiya paneli
        self.nav_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.nav_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Nav elementlarni yaratish
        for page_id, icon, label in nav_config:
            nav_item = NavItem(
                self.nav_frame,
                icon=icon,
                label=label,
                compact=self._compact_mode,
                command=lambda pid=page_id: self.navigate_to(pid),
            )
            nav_item.pack(fill="x", pady=2)
            self._nav_items[page_id] = nav_item

        # Ajratgich
        separator = ctk.CTkFrame(self.nav_frame, fg_color=Colors.BORDER, height=1)
        separator.pack(fill="x", padx=12, pady=8)

        # Sozlamalar (pastda)
        settings_item = NavItem(
            self.nav_frame,
            icon=Icons.SETTINGS,
            label="Sozlamalar",
            compact=self._compact_mode,
            command=lambda: self.navigate_to("settings"),
        )
        settings_item.pack(fill="x", pady=2, side="bottom")
        self._nav_items["settings"] = settings_item

    def _build_statusbar(self):
        """Pastki status bar — Apple hairline border + muted stats"""
        # 1px hairline border above statusbar
        self.statusbar_divider = ctk.CTkFrame(
            self,
            fg_color=Colors.BORDER,
            height=1,
            corner_radius=0,
        )
        self.statusbar_divider.pack(fill="x", side="bottom")

        self.statusbar = ctk.CTkFrame(
            self,
            fg_color=Colors.STATUSBAR_BG,
            height=Sizing.STATUSBAR_HEIGHT,
            corner_radius=0,
        )
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)

        # CPU
        self.cpu_label = ctk.CTkLabel(
            self.statusbar,
            text="CPU: --%",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_MUTED,
        )
        self.cpu_label.pack(side="left", padx=16)

        if not self._compact_mode:
            ctk.CTkLabel(
                self.statusbar, text="│", font=Fonts.STATUS, text_color=Colors.BORDER
            ).pack(side="left")

        self.ram_label = ctk.CTkLabel(
            self.statusbar,
            text="RAM: --%",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_MUTED,
        )
        self.ram_label.pack(side="left", padx=12 if self._compact_mode else 16)

        if not self._compact_mode:
            ctk.CTkLabel(
                self.statusbar, text="│", font=Fonts.STATUS, text_color=Colors.BORDER
            ).pack(side="left")

            self.api_label = ctk.CTkLabel(
                self.statusbar,
                text=f"API: {self._status_state['text']}",
                font=Fonts.STATUS,
                text_color=Colors.TEXT_MUTED,
            )
            self.api_label.pack(side="left", padx=16)
        else:
            self.api_label = None

        # O'ng tomon — TTS engine
        self.tts_label = ctk.CTkLabel(
            self.statusbar,
            text="TTS: Silero",
            font=Fonts.STATUS,
            text_color=Colors.TEXT_MUTED,
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
            "voice": VoicePage,
            "chat": ChatPage,
            "commands": CommandsPage,
            "memory": MemoryPage,
            "scheduler": SchedulerPage,
            "plugins": PluginsPage,
            "settings": SettingsPage,
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
            if hasattr(self._pages[page_id], "on_show"):
                self._pages[page_id].on_show()

        # Nav aktivligini yangilash
        for nav_id, nav_item in self._nav_items.items():
            nav_item.set_active(nav_id == page_id)

        self._current_page = page_id
        self.page_label.configure(text=self._page_title(page_id))
        self.user_label.configure(text=f"User: {self._get_user_name()}")

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
            cpu_color = (
                Colors.SUCCESS
                if cpu < 60
                else (Colors.WARNING if cpu < 85 else Colors.DANGER)
            )
            ram_color = (
                Colors.SUCCESS
                if ram < 70
                else (Colors.WARNING if ram < 90 else Colors.DANGER)
            )
            self.cpu_label.configure(text_color=cpu_color)
            self.ram_label.configure(text_color=ram_color)
            if self.api_label is not None:
                self.api_label.configure(text_color=Colors.TEXT_MUTED)
        except Exception:
            pass

        self.after(3000, self._update_system_stats)

    def set_status(self, status, text=None):
        """Global holatni o'zgartirish"""
        self._status_state = {"status": status, "text": text or status.capitalize()}
        if hasattr(self, "status_badge") and self.status_badge.winfo_exists():
            self.status_badge.set_status(status, text)
        display_text = self._status_state["text"]
        api_label = getattr(self, "api_label", None)
        if api_label is not None and api_label.winfo_exists():
            api_label.configure(text=f"API: {display_text}")

    def _get_user_name(self):
        try:
            from config import get_config

            return get_config("user.name", "Foydalanuvchi")
        except Exception:
            return "Foydalanuvchi"

    def _page_title(self, page_id):
        titles = {
            "dashboard": "Dashboard",
            "voice": "Ovozli dialog",
            "chat": "AI suhbat",
            "commands": "Buyruqlar",
            "memory": "Xotira",
            "scheduler": "Rejalashtiruvchi",
            "plugins": "Plaginlar",
            "settings": "Sozlamalar",
        }
        return titles.get(page_id, "Mikasa AI")

    # ========== YOPISH ==========

    def _on_closing(self):
        """Dasturni yopish — resurslarni tozalash"""
        try:
            self._remember_window_geometry()
            try:
                from config import set_config

                set_config("gui.window_size", self._window_sizes["standard"])
                set_config("gui.compact_window_size", self._window_sizes["compact"])
            except Exception:
                pass

            # 1. Tinglashni to'xtatish
            self.bridge.stop_listening()

            # 2. AgentMemory saqlash
            if self.bridge._agent_memory:
                self.bridge._agent_memory.save_all()

            # 3. Scheduler to'xtatish
            if self.bridge._agent_scheduler:
                self.bridge._agent_scheduler.stop()

            # 4. Proactive Watcher to'xtatish
            try:
                from core.proactive_watcher import stop_proactive_watcher

                stop_proactive_watcher()
            except Exception:
                pass

            # 5. pygame tozalash
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
