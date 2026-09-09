# ========== app.py ==========
# Mikasa AI — Asosiy Application Shell
# Sidebar navigatsiya + Main content area + Status bar

import customtkinter as ctk
from customtkinter.windows.widgets.core_rendering import DrawEngine

# Windows Tkinter font to'rtburchak/qavs qoldiqlarisiz toza geometriya
DrawEngine.preferred_drawing_method = "circle_shapes"

import os
import logging
import datetime
import psutil
import threading

logger = logging.getLogger(__name__)
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import NavItem, LoadingSkeleton, AccountRow, UserAvatar
from gui.backend import BackendBridge

# Versiyani bitta joydan olish
try:
    from main import VERSION
except ImportError:
    VERSION = "7.0.0"


class MikasaApp(ctk.CTk):
    """Mikasa AI asosiy dastur oynasi"""

    def __init__(self, connect_backend=False, show_splash=True):
        super().__init__()

        self._current_page = None
        self._pages = {}
        self._nav_state = "IDLE"
        self._nav_generation = 0
        self._lazy_nav_job = None
        self._clock_job = None
        self._stats_job = None
        self._page_loading_skeleton = None
        self._pending_page_states = {}
        self._compact_mode = False
        self._ui_theme = "dark"
        self._color_theme = "blue"
        self._connect_backend = connect_backend
        self._show_splash = show_splash
        self.splash = None
        self._is_rebuilding_shell = False
        self._status_state = {"status": "online", "text": "Tayyor"}
        self._window_sizes = {"standard": "1280x800", "compact": "960x700"}

        # Backend bridge — GUI va main.py orasida ko'prik
        self.bridge = BackendBridge(self)
        self._nav_items = {}

        self._load_ui_preferences()
        self._apply_ui_preferences(initial=True)

        # Oyna sozlamalari
        self.title("MIKASA AI")
        self.configure(fg_color=Colors.BG_DARK)
        self._apply_window_mode()

        # Global hotkeys: Ctrl+K orqali qidiruv
        self.bind("<Control-k>", lambda e: self._on_global_search())
        self.bind("<Control-K>", lambda e: self._on_global_search())

        # UI qurish (Asosiy shell)
        self._build_shell()

        # Custom window chrome va configure listener
        self._setup_custom_window_chrome()
        self.bind("<Configure>", self._on_window_configure, add="+")

        # Splash Screen ni ishga tushirish (Mikasa 7.0 birinchi vizual kadri)
        if show_splash:
            from gui.splash import MikasaSplashScreen

            self.splash = MikasaSplashScreen(self, on_retry=self._on_splash_retry)
            self.splash.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
            self.splash.lift()

        # Backend ni ishga tushirish
        if connect_backend:
            self.bridge.init_backend()

        # Yopish event
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ========== SPLASH SCREEN & STARTUP LIFECYCLE ==========

    def on_init_progress(self, text: str, progress: float = None):
        """Backend yuklanish jarayonida splash statusini yangilash (Thread-safe)"""
        if hasattr(self, "splash") and self.splash and self.splash.winfo_exists():
            self.splash.set_status(text, progress)

    def on_backend_ready(self):
        """Backend to'liq tayyor bo'lganda splash dan asosiy oynaga silliq o'tish"""
        self._transition_from_splash()

    def on_backend_error(self, error_msg: str):
        """Backend da jiddiy xato yuz berganda splash xatolik holatini ko'rsatish"""
        if hasattr(self, "splash") and self.splash and self.splash.winfo_exists():
            self.splash.set_error(error_msg)

    def _on_splash_retry(self):
        """Foydalanuvchi Qayta urinish tugmasini bosganda"""
        if self._connect_backend:
            self.bridge.init_backend()
        else:
            self.after(250, self._transition_from_splash)

    def _transition_from_splash(self):
        """Splash ekrandan asosiy dastur interfeysiga silliq o'tish"""
        if hasattr(self, "splash") and self.splash and self.splash.winfo_exists():
            def _cleanup():
                self.splash = None
                try:
                    self.update_idletasks()
                except Exception:
                    pass

            self.splash.fade_out_and_destroy(on_complete=_cleanup)


    def _windows_set_titlebar_color(self, color_mode: str):
        """CustomTkinter _windows_set_titlebar_color xavfsiz versiyasi:
        rebuild_shell paytida o'chirilgan widgetlarga focus_set chaqirib TclError bermasligi uchun.
        """
        try:
            super()._windows_set_titlebar_color(color_mode)
        except Exception:
            pass
        finally:
            self.focused_widget_before_widthdraw = None
            self._setup_custom_window_chrome()

    def _setup_custom_window_chrome(self):
        """
        Standart Windows sarlavha panelini (WS_CAPTION) va no-client oq/kulrang hoshiyasini
        butunlay olib tashlash (Zero-pixel unwanted top frame).

        Root cause tahlili:
        WS_THICKFRAME bo'lgan oynada DefWindowProc standart holatda 7-8px non-client frame
        ajratadi va DWM bu sohani oq/kulrang chiziq qilib chizadi.
        WM_NCCALCSIZE xabarini ushlab 0 qaytarish orqali client area to'liq oynani (y=0 dan boshlab)
        qamrab oladi va oq chiziq butunlay yo'qoladi.
        WM_NCHITTEST orqali esa oynaning 4 ta chekkasi va burchaklaridan native resizing ta'minlanadi.
        """
        if os.name != "nt":
            return

        try:
            import ctypes
            from ctypes import wintypes, c_int, c_void_p, WINFUNCTYPE, Structure, byref

            user32 = ctypes.windll.user32
            user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, c_int]
            user32.GetWindowLongPtrW.restype = c_void_p
            user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, c_int, c_void_p]
            user32.SetWindowLongPtrW.restype = c_void_p
            user32.CallWindowProcW.argtypes = [c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
            user32.CallWindowProcW.restype = c_void_p

            hwnd = user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id()
            self._parent_hwnd = hwnd

            GWL_STYLE = -16
            GWLP_WNDPROC = -4
            WS_CAPTION = 0x00C00000
            WS_THICKFRAME = 0x00040000
            WS_MINIMIZEBOX = 0x00020000
            WS_MAXIMIZEBOX = 0x00010000
            WS_SYSMENU = 0x00080000

            SWP_FRAMECHANGED = 0x0020
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004

            WM_NCCALCSIZE = 0x0083
            WM_NCHITTEST = 0x0084

            class MONITORINFO(Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            class NCCALCSIZE_PARAMS(Structure):
                _fields_ = [("rgrc", wintypes.RECT * 3), ("lppos", c_void_p)]

            # 1. Windows frame style ni to'g'irlash
            style = user32.GetWindowLongW(hwnd, GWL_STYLE)
            new_style = (style & ~WS_CAPTION) | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU
            user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
            user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
            )

            # 2. DWM Dark Mode va ranglar
            dark_val = c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(dark_val), 4)

            # DWMWA_BORDER_COLOR (34) va DWMWA_CAPTION_COLOR (35) ni Colors.BG_DARKEST ga moslash
            # #08080C -> BGR 0x000C0808
            border_color = c_int(0x000C0808)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(border_color), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(border_color), 4)

            # DWMWA_WINDOW_CORNER_PREFERENCE (33): 2 = ROUND (Windows 11 silliq burchaklar)
            corner_pref = c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, byref(corner_pref), 4)

            # 3. WndProc hook (WM_NCCALCSIZE va WM_NCHITTEST)
            if not getattr(self, "_wndproc_installed", False):
                old_wndproc = user32.GetWindowLongPtrW(hwnd, GWLP_WNDPROC)
                self._old_wndproc = old_wndproc

                WNDPROC_T = WINFUNCTYPE(c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

                def custom_wndproc(h, msg, wp, lp):
                    if msg == WM_NCCALCSIZE and wp:
                        if user32.IsZoomed(h):
                            hmon = user32.MonitorFromWindow(h, 2)
                            mi = MONITORINFO()
                            mi.cbSize = ctypes.sizeof(MONITORINFO)
                            if user32.GetMonitorInfoW(hmon, byref(mi)):
                                params = ctypes.cast(lp, ctypes.POINTER(NCCALCSIZE_PARAMS)).contents
                                params.rgrc[0].left = mi.rcWork.left
                                params.rgrc[0].top = mi.rcWork.top
                                params.rgrc[0].right = mi.rcWork.right
                                params.rgrc[0].bottom = mi.rcWork.bottom
                            return 0
                        return 0
                    elif msg == WM_NCHITTEST:
                        if not user32.IsZoomed(h):
                            x = lp & 0xFFFF
                            if x > 0x7FFF:
                                x -= 0x10000
                            y = (lp >> 16) & 0xFFFF
                            if y > 0x7FFF:
                                y -= 0x10000
                            rect = wintypes.RECT()
                            user32.GetWindowRect(h, byref(rect))
                            border = 6

                            # O'ng tomondagi boshqaruv tugmalari sohasi (Minimize, Maximize, Close)
                            if y <= rect.top + 36 and x >= rect.right - 140:
                                return 1  # HTCLIENT

                            top = y < rect.top + border
                            bottom = y >= rect.bottom - border
                            left = x < rect.left + border
                            right = x >= rect.right - border

                            if top and left:
                                return 13  # HTTOPLEFT
                            if top and right:
                                return 14  # HTTOPRIGHT
                            if bottom and left:
                                return 16  # HTBOTTOMLEFT
                            if bottom and right:
                                return 17  # HTBOTTOMRIGHT
                            if top:
                                return 12  # HTTOP
                            if bottom:
                                return 15  # HTBOTTOM
                            if left:
                                return 10  # HTLEFT
                            if right:
                                return 11  # HTRIGHT

                    return user32.CallWindowProcW(self._old_wndproc, h, msg, wp, lp)

                self._wndproc_ref = WNDPROC_T(custom_wndproc)
                user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, ctypes.cast(self._wndproc_ref, c_void_p))
                self._wndproc_installed = True

            user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
            )
        except Exception as e:
            logger.debug(f"Custom window chrome initialization warning: {e}")

    def _start_window_drag(self, event):
        """Oynani surishni boshlash (Pure Tkinter main-thread xavfsiz mexanizm)"""
        if self.state() == "zoomed":
            max_w = self.winfo_width()
            click_ratio = max(0.0, min(1.0, event.x / max_w)) if max_w > 0 else 0.5
            self._toggle_maximize()
            self.update_idletasks()
            new_w = self.winfo_width()
            self._drag_start_x = int(new_w * click_ratio)
            self._drag_start_y = event.y
            new_x = event.x_root - self._drag_start_x
            new_y = event.y_root - self._drag_start_y
            self.geometry(f"+{new_x}+{max(0, new_y)}")
            return

        self._drag_start_x = event.x_root - self.winfo_x()
        self._drag_start_y = event.y_root - self.winfo_y()

    def _on_window_drag(self, event):
        """Oynani koordinatalar bo'yicha surish (GIL yoki modal loop xatolarisiz)"""
        if getattr(self, "_drag_start_x", None) is not None and getattr(self, "_drag_start_y", None) is not None:
            new_x = event.x_root - self._drag_start_x
            new_y = event.y_root - self._drag_start_y
            self.geometry(f"+{new_x}+{max(0, new_y)}")

    def _end_window_drag(self, event=None):
        """Oynani surish yakunlanganda koordinata holatini tozalash"""
        self._drag_start_x = None
        self._drag_start_y = None

    def _toggle_maximize(self):
        """Oynani kattalashtirish yoki avvalgi o'lchamga qaytarish (Maximize ↔ Restore)"""
        if self.state() == "zoomed":
            self.state("normal")
            if hasattr(self, "window_controls") and self.window_controls:
                self.window_controls.sync_maximized_state(False)
        else:
            self.state("zoomed")
            if hasattr(self, "window_controls") and self.window_controls:
                self.window_controls.sync_maximized_state(True)

    def _on_window_configure(self, event=None):
        """Oyna o'lchami yoki holati o'zgarganda window_controls ni yangilash"""
        if event and event.widget == self:
            is_max = self.state() == "zoomed"
            if hasattr(self, "window_controls") and self.window_controls:
                if self.window_controls._is_maximized != is_max:
                    self.window_controls.sync_maximized_state(is_max)

    def report_callback_exception(self, exc, val, tb):
        """Rebuild yoki sahifa almashtirish paytidagi o'chirilgan widgetlar focus TclError larini xavfsiz bartaraf etish"""
        if issubclass(exc, Exception) and "bad window path name" in str(val):
            logger.debug(f"Ignored benign Tkinter TclError on destroyed widget: {val}")
            return
        super().report_callback_exception(exc, val, tb)

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

    def _build_shell(self, page_id="voice", page_states=None):
        self._build_titlebar()
        self._build_statusbar()
        self._build_layout()
        self._build_sidebar()
        if page_states:
            self._pending_page_states = dict(page_states)
        self._init_pages(initial_page=page_id)
        if page_states:
            self._restore_page_states(page_states)
        self.navigate_to(page_id, sync=True)
        self._restore_runtime_state()

    def _rebuild_shell(self):
        current_page = self._current_page or "voice"
        page_states = self._capture_page_states()
        self._current_page = None
        self._is_rebuilding_shell = True

        if self._lazy_nav_job:
            try:
                self.after_cancel(self._lazy_nav_job)
            except Exception:
                pass
            self._lazy_nav_job = None

        if self._page_loading_skeleton:
            try:
                self._page_loading_skeleton.destroy()
            except Exception:
                pass
            self._page_loading_skeleton = None

        # O'chiriladigan widgetlarga focus tushib qolmasligi uchun
        self.focused_widget_before_widthdraw = None
        try:
            self.focus_set()
        except Exception:
            pass

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
        if not getattr(self, "tts_label", None):
            return
        try:
            from config import get_config

            engine = get_config("audio.tts_engine", "silero")
            label = "Edge TTS" if engine == "edge_tts" else "Silero"
        except Exception:
            label = "Silero"

        self.tts_label.configure(text=f"TTS: {label}")

    def _build_titlebar(self):
        """Dastur sarlavha paneli — Custom Premium Window Chrome"""
        from gui.components import WindowControls

        self.titlebar = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_DARKEST,
            height=36,
            corner_radius=0,
        )
        self.titlebar.pack(fill="x", side="top")
        self.titlebar.pack_propagate(False)

        # 1. Chap tomon: Logo va nom (vector sparkles bilan)
        from gui.icons import get_vector_icon
        logo_icon = get_vector_icon("sparkles", size=15, color_dark=Colors.PRIMARY, color_light=Colors.PRIMARY)

        self.logo_label = ctk.CTkLabel(
            self.titlebar,
            text="  MIKASA" if self._compact_mode else "  MIKASA AI",
            image=logo_icon,
            compound="left",
            font=(Fonts.FAMILY, 13, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.logo_label.pack(side="left", padx=(14, 6))

        # 2. O'ng tomon: Desktop Native Window Controls (Minimize, Maximize/Restore, Close)
        self.window_controls = WindowControls(self.titlebar, app=self, height=36, btn_width=44)
        self.window_controls.pack(side="right", fill="y")
        try:
            self.window_controls.sync_maximized_state(self.state() == "zoomed")
        except Exception:
            pass

        # 3. Sarlavhadan ushlab oynani surish (Dragging) va Double-Click Maximize
        for widget in (self.titlebar, self.logo_label):
            widget.bind("<ButtonPress-1>", self._start_window_drag)
            widget.bind("<B1-Motion>", self._on_window_drag)
            widget.bind("<ButtonRelease-1>", self._end_window_drag)
            widget.bind("<Double-Button-1>", lambda e: self._toggle_maximize())

        # 7. 1px hairline border below titlebar
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
        """Sidebar navigatsiya — Command Center hierarchy"""
        # 1. Pastki boshqaruv maydoni (Foydalanuvchi Hisobi / Sozlamalar)
        self.sidebar_bottom = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_bottom.pack(side="bottom", fill="x", padx=8, pady=(0, 8))

        # Ajratgich
        separator = ctk.CTkFrame(self.sidebar_bottom, fg_color=Colors.BORDER, height=1)
        separator.pack(fill="x", padx=4, pady=(6, 6))

        # Foydalanuvchi hisobi (AccountRow — Sozlamalar va Profil yagona kirish nuqtasi)
        user_name = self._get_user_name()
        self.account_row = AccountRow(
            self.sidebar_bottom,
            name=user_name,
            compact=self._compact_mode,
            command=lambda: self.navigate_to("settings"),
        )
        self.account_row.pack(fill="x", pady=(0, 2))

        # 2. Asosiy navigatsiya paneli (Yuqori qism)
        self.nav_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.nav_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Nav elementlar bo'limlari
        nav_sections = [
            (
                "MIKASA",
                [
                    ("voice", Icons.VOICE, "Ovozli muloqot"),
                    ("chat", Icons.CHAT, "AI Suhbat"),
                    ("commands", Icons.COMMANDS, "Buyruqlar"),
                    ("memory", Icons.MEMORY, "Xotira"),
                ],
            ),
            (
                "AGENT",
                [
                    ("scheduler", Icons.SCHEDULER, "Rejalashtiruvchi"),
                    ("plugins", Icons.PLUGINS, "Plaginlar"),
                ],
            ),
        ]

        for sec_idx, (section_title, items) in enumerate(nav_sections):
            if not self._compact_mode and section_title:
                sec_header = ctk.CTkLabel(
                    self.nav_frame,
                    text=section_title,
                    font=(Fonts.FAMILY, 9, "bold"),
                    text_color=Colors.TEXT_MUTED,
                    anchor="w",
                )
                sec_header.pack(fill="x", padx=12, pady=(10 if sec_idx > 0 else 4, 4))

            for page_id, icon, label in items:
                nav_item = NavItem(
                    self.nav_frame,
                    icon=icon,
                    label=label,
                    compact=self._compact_mode,
                    command=lambda pid=page_id: self.navigate_to(pid),
                )
                nav_item.pack(fill="x", pady=2)
                self._nav_items[page_id] = nav_item

    def _build_statusbar(self):
        """Persistent AI Control Bar — AI holati va tezkor boshqaruv"""
        from gui.icons import get_vector_icon
        from gui.components import GlassButton
        
        # 1px hairline border above
        self.statusbar_divider = ctk.CTkFrame(
            self,
            fg_color=Colors.BORDER,
            height=1,
            corner_radius=0,
        )
        self.statusbar_divider.pack(fill="x", side="bottom")
        
        # Control bar
        self.statusbar = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_DARKEST,
            height=34,
            corner_radius=0,
        )
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        
        # Left: AI status indicator
        status_left = ctk.CTkFrame(self.statusbar, fg_color="transparent")
        status_left.pack(side="left", padx=14)
        
        self._ai_dot = ctk.CTkLabel(
            status_left,
            text="",
            image=get_vector_icon("circle", size=7, color=Colors.SUCCESS),
        )
        self._ai_dot.pack(side="left", padx=(0, 6))
        
        self._ai_status_label = ctk.CTkLabel(
            status_left,
            text="Mikasa kutmoqda",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        )
        self._ai_status_label.pack(side="left")
        
        # Right: Voice <-> Chat switch button
        self._mode_switch_btn = ctk.CTkButton(
            self.statusbar,
            text="Chat",
            image=get_vector_icon("chat", size=14, color=Colors.TEXT_MUTED),
            compound="left",
            font=Fonts.TINY,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            height=26,
            width=80,
            corner_radius=Sizing.SMALL,
            command=self._toggle_voice_chat,
        )
        self._mode_switch_btn.pack(side="right", padx=10)
        
        # Center-right: Mic toggle button  
        self._bar_mic_btn = ctk.CTkButton(
            self.statusbar,
            text="",
            image=get_vector_icon("mic", size=16, color=Colors.TEXT_MUTED),
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            width=30,
            height=26,
            corner_radius=Sizing.SMALL,
            command=self._bar_toggle_mic,
        )
        self._bar_mic_btn.pack(side="right", padx=4)
        
        # Backward compatibility stubs
        self.cpu_label = None
        self.ram_label = None
        self.api_label = None
        self.tts_label = None

    def _toggle_voice_chat(self):
        """Voice va Chat orasida tezkor almashtirish"""
        if self._current_page == "voice":
            self.navigate_to("chat")
        else:
            self.navigate_to("voice")

    def _bar_toggle_mic(self):
        """Control bar mikrofon toggle — Voice sahifasiga o'tib tinglashni boshlash/to'xtatish"""
        if self._current_page != "voice":
            self.navigate_to("voice")
        voice_page = self._pages.get("voice")
        if voice_page and hasattr(voice_page, "_toggle_listening"):
            self.after(100, voice_page._toggle_listening)

    def update_ai_control_bar(self, status_text=None, is_listening=False):
        """AI Control Bar holatini yangilash"""
        from gui.icons import get_vector_icon
        if not hasattr(self, '_ai_status_label'):
            return
        try:
            if status_text and self._ai_status_label.winfo_exists():
                self._ai_status_label.configure(text=status_text)
            
            if is_listening:
                self._ai_dot.configure(
                    image=get_vector_icon("circle", size=7, color=Colors.PRIMARY)
                )
                self._bar_mic_btn.configure(
                    image=get_vector_icon("mic", size=16, color=Colors.PRIMARY)
                )
            else:
                self._ai_dot.configure(
                    image=get_vector_icon("circle", size=7, color=Colors.SUCCESS)
                )
                self._bar_mic_btn.configure(
                    image=get_vector_icon("mic", size=16, color=Colors.TEXT_MUTED)
                )
        except Exception:
            pass

    # ========== SAHIFALAR & LAZY NAVIGATSIYA ==========

    def _get_page_class(self, page_id):
        page_registry = {
            "dashboard": ("gui.pages.dashboard", "DashboardPage"),
            "voice": ("gui.pages.voice", "VoicePage"),
            "chat": ("gui.pages.chat", "ChatPage"),
            "commands": ("gui.pages.commands", "CommandsPage"),
            "memory": ("gui.pages.memory", "MemoryPage"),
            "scheduler": ("gui.pages.scheduler", "SchedulerPage"),
            "plugins": ("gui.pages.plugins", "PluginsPage"),
            "settings": ("gui.pages.settings", "SettingsPage"),
        }
        return page_registry.get(page_id)

    def _init_pages(self, initial_page="voice"):
        """Dastlabki sahifani yuklash (Lazy loading — qolgan sahifalar talab bo'lganda yaratiladi)"""
        self._get_or_create_page(initial_page)

    def _get_or_create_page(self, page_id):
        """Sahifani keshdan olish yoki birinchi marta yaratish (Lazy loading)"""
        if page_id in self._pages:
            return self._pages[page_id]

        entry = self._get_page_class(page_id)
        if not entry:
            logger.warning(f"Noma'lum sahifa identifikatori: {page_id}")
            return None

        module_name, class_name = entry
        try:
            import importlib
            module = importlib.import_module(module_name)
            page_class = getattr(module, class_name)
            page = page_class(self.content_frame, app=self)
            self._pages[page_id] = page

            # Agar saqlangan holat bo'lsa tiklash
            if page_id in self._pending_page_states:
                state = self._pending_page_states.pop(page_id)
                if hasattr(page, "import_ui_state"):
                    try:
                        page.import_ui_state(state)
                    except Exception as err:
                        logger.error(f"UI holatini tiklashda xatolik ({page_id}): {err}")

            return page
        except Exception as e:
            logger.error(f"Sahifani yaratishda xatolik ({page_id}): {e}", exc_info=True)
            return None

    def _on_global_search(self):
        """Ctrl + K orqali Command Palette (Spotlight) ochish"""
        try:
            from gui.components import CommandPaletteOverlay
            if hasattr(self, "_palette") and self._palette and self._palette.winfo_exists():
                self._palette.lift()
                self._palette.focus_set()
                return
            self._palette = CommandPaletteOverlay(self)
        except Exception:
            self.navigate_to("commands")
            def _focus():
                page = self._pages.get("commands")
                if page and hasattr(page, "focus_search"):
                    page.focus_search()
            self.after(50, _focus)

    def navigate_to(self, page_id, sync=False):
        """
        Sahifaga o'tish (State Machine + Generation Token + Lazy Load + Zero-Freeze)
        IDLE -> LOADING -> READY / ERROR
        """
        self._nav_generation += 1
        req_generation = self._nav_generation

        if page_id == self._current_page and self._nav_state == "READY":
            return

        # 1. Oldingi sahifaning on_hide() lifecycle chaqiruvi
        if self._current_page and self._current_page in self._pages:
            old_page = self._pages[self._current_page]
            if hasattr(old_page, "on_hide"):
                try:
                    old_page.on_hide()
                except Exception as e:
                    logger.error(f"on_hide da xatolik ({self._current_page}): {e}")

        # 2. Tezkor vizual aks-sado (<10ms): sidebar nav va hisob paneli
        for nav_id, nav_item in self._nav_items.items():
            nav_item.set_active(nav_id == page_id)

        if hasattr(self, "account_row") and self.account_row:
            self.account_row.set_active(page_id == "settings")

        # 3. Bekor qilinmagan oldingi lazy nav jobini to'xtatish
        if self._lazy_nav_job:
            try:
                self.after_cancel(self._lazy_nav_job)
            except Exception:
                pass
            self._lazy_nav_job = None

        # 4. Oldingi sahifani yashirish
        if self._current_page and self._current_page in self._pages:
            try:
                self._pages[self._current_page].pack_forget()
            except Exception:
                pass

        # 5. Keshda mavjud bo'lsa — darhol ko'rsatish
        if page_id in self._pages:
            if self._page_loading_skeleton:
                self._page_loading_skeleton.pack_forget()

            page = self._pages[page_id]
            page.pack(fill="both", expand=True)

            if hasattr(page, "on_show"):
                try:
                    page.on_show()
                except Exception as e:
                    logger.error(f"on_show da xatolik ({page_id}): {e}")

            self._current_page = page_id
            self._nav_state = "READY"
            
            # Update AI Control Bar mode button
            if hasattr(self, '_mode_switch_btn'):
                try:
                    from gui.icons import get_vector_icon
                    if page_id == "voice":
                        self._mode_switch_btn.configure(
                            text="Chat",
                            image=get_vector_icon("chat", size=14, color=Colors.TEXT_MUTED),
                        )
                    elif page_id == "chat":
                        self._mode_switch_btn.configure(
                            text="Voice", 
                            image=get_vector_icon("mic", size=14, color=Colors.TEXT_MUTED),
                        )
                except Exception:
                    pass
                    
            return

        # 6. Keshda yo'q bo'lsa — Loading Skeleton ko'rsatish
        self._nav_state = "LOADING"
        if not self._page_loading_skeleton:
            self._page_loading_skeleton = LoadingSkeleton(
                self.content_frame,
                title=f"{self._page_title(page_id)} yuklanmoqda...",
                rows=4,
            )
        else:
            self._page_loading_skeleton.set_title(f"{self._page_title(page_id)} yuklanmoqda...")

        self._page_loading_skeleton.pack(fill="both", expand=True)

        if sync:
            self._finish_lazy_navigation(page_id, req_generation)
        else:
            # UI chizib olishi uchun 16ms kechiktirish
            self._lazy_nav_job = self.after(
                16,
                lambda pid=page_id, gen=req_generation: self._finish_lazy_navigation(pid, gen)
            )

    def _finish_lazy_navigation(self, page_id, generation=None):
        """Lazy yuklashni yakunlash va sahifani chiqarish (Stale generation rejection)"""
        self._lazy_nav_job = None
        # Agar navigatsiya avlodi mos kelmasa (stale async callback) — bekor qilish
        if generation is not None and generation != self._nav_generation:
            logger.debug(f"Stale navigation callback rejected: target={page_id}, gen={generation}, current={self._nav_generation}")
            return

        try:
            page = self._get_or_create_page(page_id)

            if self._page_loading_skeleton:
                self._page_loading_skeleton.pack_forget()

            if generation is not None and generation != self._nav_generation:
                return

            if page:
                page.pack(fill="both", expand=True)
                if hasattr(page, "on_show"):
                    try:
                        page.on_show()
                    except Exception as e:
                        logger.error(f"on_show da xatolik ({page_id}): {e}")

                self._current_page = page_id
                self._nav_state = "READY"
                
                # Update AI Control Bar mode button
                if hasattr(self, '_mode_switch_btn'):
                    try:
                        from gui.icons import get_vector_icon
                        if page_id == "voice":
                            self._mode_switch_btn.configure(
                                text="Chat",
                                image=get_vector_icon("chat", size=14, color=Colors.TEXT_MUTED),
                            )
                        elif page_id == "chat":
                            self._mode_switch_btn.configure(
                                text="Voice", 
                                image=get_vector_icon("mic", size=14, color=Colors.TEXT_MUTED),
                            )
                    except Exception:
                        pass
            else:
                self._nav_state = "ERROR"
        except Exception as e:
            self._nav_state = "ERROR"
            if self._page_loading_skeleton:
                self._page_loading_skeleton.pack_forget()
            logger.error(f"Lazy navigatsiyada xatolik ({page_id}): {e}", exc_info=True)

    # ========== YANGILANISHLAR ==========

    def _update_clock(self):
        """Soat endi yo'q"""
        pass

    def _update_system_stats(self):
        """Tizim ma'lumotlari endi yo'q"""
        pass

    def set_status(self, status, text=None):
        """Global holatni o'zgartirish"""
        self._status_state = {"status": status, "text": text or status.capitalize()}
        display_text = self._status_state["text"]
        is_listening = status == "listening"
        self.update_ai_control_bar(f"Mikasa: {display_text}", is_listening)

    def _get_user_name(self):
        try:
            from config import get_config

            return get_config("user.name", "Muxammadaziz")
        except Exception:
            return "Muxammadaziz"

    def update_account_display(self):
        """Foydalanuvchi ismi o'zgarganda hisob satrini yangilash"""
        name = self._get_user_name()
        if hasattr(self, "account_row") and self.account_row and self.account_row.winfo_exists():
            self.account_row.update_user_name(name)

    def _page_title(self, page_id):
        titles = {
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
            for timer_attr in ["_lazy_nav_job", "_stats_job"]:
                job = getattr(self, timer_attr, None)
                if job:
                    try:
                        self.after_cancel(job)
                    except Exception:
                        pass
                    setattr(self, timer_attr, None)

            self._remember_window_geometry()
            try:
                from config import set_config

                set_config("gui.window_size", self._window_sizes["standard"])
                set_config("gui.compact_window_size", self._window_sizes["compact"])
            except Exception:
                pass

            # 1. Proactive Watcher to'xtatish (fon oqimi xavfsiz to'xtashi uchun)
            try:
                from core.proactive_watcher import stop_proactive_watcher

                stop_proactive_watcher()
            except Exception:
                pass

            # 2. Backend bridge to'xtatish va tozalash
            if hasattr(self, "bridge") and self.bridge:
                try:
                    self.bridge.stop()
                except Exception:
                    pass

            # 3. AgentMemory saqlash
            if hasattr(self, "bridge") and self.bridge and getattr(self.bridge, "_agent_memory", None):
                try:
                    self.bridge._agent_memory.save_all()
                except Exception:
                    pass

            # 4. Scheduler to'xtatish
            if hasattr(self, "bridge") and self.bridge and getattr(self.bridge, "_agent_scheduler", None):
                try:
                    self.bridge._agent_scheduler.stop()
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

            # 6. Windows wndproc tiklash
            if getattr(self, "_old_wndproc", None) and getattr(self, "_parent_hwnd", None):
                try:
                    import ctypes
                    GWLP_WNDPROC = -4
                    ctypes.windll.user32.SetWindowLongPtrW(self._parent_hwnd, GWLP_WNDPROC, self._old_wndproc)
                except Exception:
                    pass
                self._old_wndproc = None
                self._wndproc_ref = None

        except Exception as e:
            import logging

            logging.error(f"Yopish xatolik: {e}")

        self.destroy()
