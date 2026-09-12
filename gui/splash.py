# ========== gui/splash.py ==========
# Mikasa AI 7.0 — Premium Futuristic Desktop Splash Screen
# Ultra-clean, dark, calm, intelligent startup interface

import math
import logging
import tkinter as tk
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing
from gui.orb import MikasaOrb

logger = logging.getLogger(__name__)


class MikasaLoadingBar(ctk.CTkFrame):
    """
    Mikasa 7.0 Sokin Progress Indikatori (180x2px).
    Soxta foizlarsiz, sokin elektr-ko'k / sian nurli skaner-indikator.
    """

    def __init__(self, master, width: int = 200, height: int = 2, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            width=width,
            height=height + 2,
            **kwargs,
        )
        self.pack_propagate(False)
        self._bar_width = width
        self._bar_height = height
        self._progress = None  # None bo'lsa indeterminate (sokin tebranish)
        self._tick = 0
        self._anim_job = None
        self._active = True

        def _resolve_color(col, fallback="#07090E"):
            if not col or col == "transparent":
                return fallback
            if isinstance(col, (tuple, list)):
                return str(col[1]) if len(col) > 1 else str(col[0])
            return str(col)

        canvas_bg = _resolve_color(Colors.BG_DARKEST)

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height + 2,
            bg=canvas_bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self._draw_track()
        self._animate()

    def set_progress(self, val: float = None):
        """0.0 dan 1.0 gacha aniq qiymat, yoki None (indeterminate)"""
        self._progress = val
        self._draw_track()

    def _draw_track(self):
        if not self.winfo_exists():
            return
        self.canvas.delete("all")
        w = self._bar_width
        h = self._bar_height
        cy = (h + 2) // 2

        # 1. Tinch fon chizig'i (Muted dark track)
        self.canvas.create_line(
            0, cy, w, cy, fill="#131B2E", width=h, capstyle="round"
        )

        # 2. Faol yorug'lik indikatori
        if self._progress is not None:
            # Deterministic progress
            fill_w = max(4, int(w * min(1.0, max(0.0, self._progress))))
            self.canvas.create_line(
                0, cy, fill_w, cy, fill="#0A84FF", width=h, capstyle="round"
            )
            # Uchi nurlanishi
            if fill_w < w:
                self.canvas.create_oval(
                    fill_w - 2, cy - 2, fill_w + 2, cy + 2, fill="#38BDF8", outline=""
                )
        else:
            # Indeterminate smooth calm scanner
            t = self._tick
            seg_len = 54
            travel = w - seg_len
            # Sokin kosinus harakati
            pos = int((1.0 - math.cos(t * 0.07)) * 0.5 * travel)

            # Asosiy nur
            self.canvas.create_line(
                pos, cy, pos + seg_len, cy, fill="#0A84FF", width=h, capstyle="round"
            )
            # Ichki yorqin yadro (Cyan gleam)
            core_len = 24
            core_pos = pos + (seg_len - core_len) // 2
            self.canvas.create_line(
                core_pos, cy, core_pos + core_len, cy, fill="#38BDF8", width=h, capstyle="round"
            )

    def _animate(self):
        if not self._active:
            return
        self._tick += 1
        try:
            if self.winfo_exists():
                if self._progress is None:
                    self._draw_track()
                self._anim_job = self.after(35, self._animate)
        except Exception:
            pass

    def stop(self):
        self._active = False
        if self._anim_job:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

    def destroy(self):
        self.stop()
        super().destroy()


class MikasaSplashScreen(ctk.CTkFrame):
    """
    Mikasa AI 7.0 Splash Screen.
    To'liq oynani qamrab oluvchi, yuqori darajadagi minimal, sokin va intellektual startap qatlami.
    """

    def __init__(self, master_app, on_retry=None, **kwargs):
        super().__init__(
            master_app,
            fg_color=Colors.BG_DARKEST,
            corner_radius=0,
            **kwargs,
        )
        self.app = master_app
        self.on_retry = on_retry
        self._is_dismissed = False

        # 1. Yuqori oyna boshqaruv paneli (Minimal Chrome: drag zone + WindowControls)
        self._build_top_controls()

        # 2. Markaziy intellekt va brending maydoni
        self._build_center_content()

    def _build_top_controls(self):
        """Oynani surish va standart WindowControls (Minimize, Maximize, Close)"""
        from gui.components import WindowControls

        self.top_bar = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=36,
            corner_radius=0,
        )
        self.top_bar.pack(side="top", fill="x")
        self.top_bar.pack_propagate(False)

        # Oynani surish uchun bo'sh joy (Drag zone)
        self.drag_area = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.drag_area.pack(side="left", fill="both", expand=True)

        # Barcha top bar elementlarida oynani surish
        for widget in (self.top_bar, self.drag_area):
            if hasattr(self.app, "_start_window_drag"):
                widget.bind("<ButtonPress-1>", self.app._start_window_drag)
            if hasattr(self.app, "_on_window_drag"):
                widget.bind("<B1-Motion>", self.app._on_window_drag)
            if hasattr(self.app, "_end_window_drag"):
                widget.bind("<ButtonRelease-1>", self.app._end_window_drag)
            if hasattr(self.app, "_toggle_maximize"):
                widget.bind("<Double-Button-1>", lambda e: self.app._toggle_maximize())

        # O'ng tomonda WindowControls
        self.window_controls = WindowControls(
            self.top_bar, app=self.app, height=36, btn_width=44
        )
        self.window_controls.pack(side="right", fill="y")
        try:
            if hasattr(self.app, "state") and callable(getattr(self.app, "state", None)):
                self.window_controls.sync_maximized_state(self.app.state() == "zoomed")
        except Exception:
            pass

    def _build_center_content(self):
        """Markaziy AI Orb, Tipografiya va Yuklanish Indikatori"""
        # Markazlashtiruvchi tashqi konteyner (Vertikal va gorizontal markaz)
        self.center_container = ctk.CTkFrame(self, fg_color="transparent")
        self.center_container.pack(expand=True, fill="both")

        # Ichki vertikal blok
        self.inner_box = ctk.CTkFrame(self.center_container, fg_color="transparent")
        self.inner_box.place(relx=0.5, rely=0.48, anchor="center")

        # 1. Mikasa AI Orb (Markaziy dominant intellekt yadrosi)
        self.orb = MikasaOrb(
            self.inner_box,
            size=210,
            state="loading",
            bg_color=Colors.BG_DARKEST,
        )
        self.orb.pack(pady=(0, 24))

        # 2. MIKASA AI Brending
        self.brand_title = ctk.CTkLabel(
            self.inner_box,
            text="MIKASA AI",
            font=(Fonts.FAMILY, 30, "bold"),
            text_color=Colors.TEXT_PRIMARY,
        )
        self.brand_title.pack(pady=(0, 6))

        # 3. Taglavha
        self.subtitle = ctk.CTkLabel(
            self.inner_box,
            text="Sizning shaxsiy AI yordamchingiz",
            font=(Fonts.FAMILY, 14),
            text_color=Colors.TEXT_MUTED,
        )
        self.subtitle.pack(pady=(0, 28))

        # 4. Sokin Progress Indikatori (180px x 2px)
        self.progress_bar = MikasaLoadingBar(
            self.inner_box,
            width=190,
            height=2,
        )
        self.progress_bar.pack(pady=(0, 14))

        # 5. Holat matni
        self.status_label = ctk.CTkLabel(
            self.inner_box,
            text="Mikasa tayyorlanmoqda...",
            font=(Fonts.FAMILY, 12),
            text_color=Colors.TEXT_MUTED,
        )
        self.status_label.pack()

        # 6. Xatolik konteyneri (standart holatda yashirin)
        self.error_frame = ctk.CTkFrame(self.inner_box, fg_color="transparent")

        self.error_title = ctk.CTkLabel(
            self.error_frame,
            text="MIKASA ishga tushmadi",
            font=(Fonts.FAMILY, 15, "bold"),
            text_color=Colors.DANGER,
        )
        self.error_title.pack(pady=(12, 4))

        self.error_detail = ctk.CTkLabel(
            self.error_frame,
            text="",
            font=(Fonts.FAMILY, 12),
            text_color=Colors.TEXT_MUTED,
            wraplength=400,
        )
        self.error_detail.pack(pady=(0, 12))

        from gui.components import GlassButton
        self.retry_btn = GlassButton(
            self.error_frame,
            text="Qayta urinish",
            width=130,
            height=32,
            command=self._on_retry_clicked,
        )
        self.retry_btn.pack()

    def set_status(self, text: str, progress: float = None):
        """Yuklanish holati matni va progress qiymatini yangilash (Thread-safe)"""
        if self._is_dismissed or not self.winfo_exists():
            return
        if self.status_label.winfo_exists():
            self.status_label.configure(text=text)
        if self.progress_bar.winfo_exists() and progress is not None:
            self.progress_bar.set_progress(progress)

    def set_error(self, error_message: str):
        """Xatolik holatini ko'rsatish"""
        if self._is_dismissed or not self.winfo_exists():
            return
        self.orb.set_state("error")
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.pack_forget()

        self.error_detail.configure(text=str(error_message))
        self.error_frame.pack(pady=(8, 0))

    def _on_retry_clicked(self):
        """Qayta urinish bosilganda"""
        self.error_frame.pack_forget()
        self.progress_bar.pack(pady=(0, 14))
        self.status_label.pack()
        self.orb.set_state("loading")
        self.progress_bar.start()
        self.set_status("Qayta ishga tushirilmoqda...", None)
        if callable(self.on_retry):
            self.on_retry()

    def fade_out_and_destroy(self, on_complete=None):
        """
        Splash ekranni silliq so'ndirish (150-200ms) va xotiradan to'liq tozalash.
        Barcha timerlar bekor qilinadi, xotira tozalanadi.
        """
        if self._is_dismissed:
            return
        self._is_dismissed = True

        # Animatsiyalarni zudlik bilan to'xtatish (CPU = 0%)
        self.orb.stop()
        self.progress_bar.stop()

        steps = 4
        delay = 40  # 4 * 40 = 160ms silliq o'tish

        def _step(step_idx):
            if not self.winfo_exists():
                if callable(on_complete):
                    on_complete()
                return

            if step_idx >= steps:
                try:
                    self.place_forget()
                    self.destroy()
                except Exception:
                    pass
                if callable(on_complete):
                    on_complete()
            else:
                self.after(delay, lambda: _step(step_idx + 1))

        _step(0)
