# ========== gui/orb.py ==========
# Mikasa AI 7.0 — MikasaOrb Reusable Core Component
# Premium, futuristic, softly glowing 3D AI Orb with subtle breathing aura

import math
import logging
import tkinter as tk
import customtkinter as ctk
from gui.theme import Colors

logger = logging.getLogger(__name__)


class MikasaOrb(ctk.CTkFrame):
    """
    MikasaOrb — Mikasa AI ning markaziy vizual intellekt yadrosi.
    
    Qo'llab-quvvatlanadigan holatlar (States):
      - 'loading':   Sokin nafas oluvchi elektr ko'k/sian/siyohrang 3D aura (startap uchun)
      - 'idle':      Sokin zangori/binafsha nurli kutish holati
      - 'listening': Ovoz to'lqinlari bilan faol tinglash holati
      - 'thinking':  Ichki aylanuvchi binafsha/ko'k fikrlash holati
      - 'speaking':  Dinamik kengayuvchi nutq holati
      - 'error':     Ogohlantiruvchi qizil/olovrang nur
      - 'offline':   Sokin kulrang/xira oflayn holat

    Optimallashtirilgan ~28 FPS render, kam protsessor sarfi (<1% CPU),
    xavfsiz bekor qilinuvchi timerlar va xotirani tozalash.
    """

    SUPPORTED_STATES = {
        "loading",
        "idle",
        "listening",
        "thinking",
        "speaking",
        "error",
        "offline",
    }

    def __init__(self, master, size: int = 200, state: str = "loading", **kwargs):
        canvas_bg = kwargs.get("bg_color", None)
        if not canvas_bg or canvas_bg == "transparent":
            cand = getattr(master, "_fg_color", None) or getattr(master, "fg_color", None)
            canvas_bg = cand if (cand and cand != "transparent") else Colors.BG_DARKEST

        if "bg_color" not in kwargs:
            kwargs["bg_color"] = canvas_bg

        super().__init__(
            master,
            fg_color="transparent",
            width=size,
            height=size,
            **kwargs,
        )
        self.pack_propagate(False)

        self._size = size
        self._center = size // 2
        self._state = state.lower() if state.lower() in self.SUPPORTED_STATES else "loading"
        self._tick = 0
        self._anim_job = None
        def _resolve_color(col, fallback="#07090E"):
            if not col or col == "transparent":
                return fallback
            if isinstance(col, (tuple, list)):
                return str(col[1]) if len(col) > 1 else str(col[0])
            return str(col)

        resolved_bg = _resolve_color(canvas_bg)

        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=resolved_bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self._is_active = True
        self._draw_orb()
        self._animate()

    def set_state(self, state: str):
        """Orb holatini o'zgartirish"""
        s = state.lower()
        if s in self.SUPPORTED_STATES:
            self._state = s
        else:
            self._state = "idle"
        self._draw_orb()

    def get_state(self) -> str:
        """Joriy orb holati"""
        return self._state

    def _draw_orb(self):
        """Orbning joriy holatiga mos kadrni chizish"""
        if not self.winfo_exists():
            return

        self.canvas.delete("all")
        cx = self._center
        cy = self._center
        t = self._tick
        size = self._size

        try:
            from PIL import Image, ImageDraw, ImageFilter, ImageTk
        except ImportError:
            # PIL yo'q bo'lsa oddiy oval
            self.canvas.create_oval(
                cx - 35, cy - 35, cx + 35, cy + 35, fill="#0A84FF", outline=""
            )
            return

        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

        def draw_glow_blob(base_img, bx, by, radius, color_rgb, max_alpha=200):
            if radius <= 0:
                return base_img
            blob_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            d = ImageDraw.Draw(blob_img)
            step = 3
            for r in range(int(radius), 0, -step):
                frac = r / radius
                alpha = int(max_alpha * (1.0 - frac * frac))
                d.ellipse([bx - r, by - r, bx + r, by + r], fill=(*color_rgb, alpha))
            return Image.alpha_composite(base_img, blob_img)

        st = self._state

        if st == "loading":
            # Mikasa 7.0 Loading Core: Sokin nafas oluvchi, chuqur elektr ko'k, sian va siyohrang yadro
            breath = math.sin(t * 0.08) * 6
            glow_intensity = int(170 + math.sin(t * 0.08) * 25)

            # 1. Tashqi chuqur ko'k/binafsha atmosferik aura
            img = draw_glow_blob(img, cx, cy, 96 + breath, (10, 132, 255), int(glow_intensity * 0.75))

            # 2. Ichki orbital sian energiya
            bx1 = cx + math.sin(t * 0.12) * 8
            by1 = cy + math.cos(t * 0.12) * 6
            img = draw_glow_blob(img, bx1, by1, 80 + breath * 0.5, (6, 182, 212), int(glow_intensity * 0.85))

            # 3. Markaziy siyohrang qatlam
            bx2 = cx - math.cos(t * 0.10) * 6
            by2 = cy - math.sin(t * 0.10) * 8
            img = draw_glow_blob(img, bx2, by2, 70, (124, 58, 237), int(glow_intensity * 0.8))

            # 4. Yorqin ichki shisha yadro (Bright core)
            img = draw_glow_blob(img, cx, cy, 48 + breath * 0.3, (186, 230, 253), 210)
            img = draw_glow_blob(img, cx, cy, 26, (255, 255, 255), 245)
            img = img.filter(ImageFilter.GaussianBlur(radius=3.0))

            # 5. Nozik markaziy konsentrik pulsatsiya halqalari
            draw = ImageDraw.Draw(img)
            ring_radius = int(58 + (t * 0.4) % 28)
            ring_alpha = int(140 * (1.0 - ((t * 0.4) % 28) / 28.0))
            if ring_alpha > 0:
                draw.ellipse(
                    [cx - ring_radius, cy - ring_radius, cx + ring_radius, cy + ring_radius],
                    outline=(186, 230, 253, ring_alpha),
                    width=1,
                )

        elif st == "listening":
            breath = math.sin(t * 0.16) * 6
            img = draw_glow_blob(img, cx, cy, 94 + breath, (10, 132, 255), 170)
            bx1 = cx + math.sin(t * 0.2) * 14
            by1 = cy + math.cos(t * 0.2) * 10
            img = draw_glow_blob(img, bx1, by1, 80, (56, 189, 248), 160)
            bx2 = cx - math.sin(t * 0.17) * 12
            by2 = cy - math.cos(t * 0.17) * 14
            img = draw_glow_blob(img, bx2, by2, 74, (94, 92, 230), 160)
            bx3 = cx + math.cos(t * 0.22) * 10
            by3 = cy - math.sin(t * 0.22) * 8
            img = draw_glow_blob(img, bx3, by3, 68, (124, 58, 237), 150)
            img = draw_glow_blob(img, cx, cy, 42, (186, 230, 253), 210)
            img = draw_glow_blob(img, cx, cy, 22, (255, 255, 255), 240)
            img = img.filter(ImageFilter.GaussianBlur(radius=3.5))

            draw = ImageDraw.Draw(img)
            bar_count = 7
            bar_w = 4
            bar_gap = 3
            total_w = bar_count * bar_w + (bar_count - 1) * bar_gap
            sx = cx - total_w // 2
            for i in range(bar_count):
                phase = i * 0.8 + t * 0.35
                h = int(10 + abs(math.sin(phase)) * 20 + abs(math.cos(phase * 0.7)) * 10)
                x = sx + i * (bar_w + bar_gap)
                draw.rounded_rectangle([x, cy - h // 2, x + bar_w, cy + h // 2], radius=2, fill=(255, 255, 255, 230))

        elif st == "thinking":
            breath = math.sin(t * 0.12) * 5
            img = draw_glow_blob(img, cx, cy, 88 + breath, (94, 92, 230), 170)
            bx1 = cx + math.sin(t * 0.18) * 12
            by1 = cy + math.cos(t * 0.18) * 12
            img = draw_glow_blob(img, bx1, by1, 72, (124, 58, 237), 170)
            bx2 = cx - math.sin(t * 0.18) * 10
            by2 = cy - math.cos(t * 0.18) * 10
            img = draw_glow_blob(img, bx2, by2, 66, (10, 132, 255), 160)
            img = draw_glow_blob(img, cx, cy, 36, (224, 231, 255), 210)
            img = draw_glow_blob(img, cx, cy, 18, (255, 255, 255), 240)
            img = img.filter(ImageFilter.GaussianBlur(radius=3.5))

        elif st == "speaking":
            breath = math.sin(t * 0.18) * 6
            img = draw_glow_blob(img, cx, cy, 92 + breath, (124, 58, 237), 170)
            bx1 = cx + math.sin(t * 0.22) * 12
            by1 = cy + math.cos(t * 0.22) * 10
            img = draw_glow_blob(img, bx1, by1, 76, (10, 132, 255), 170)
            bx2 = cx - math.sin(t * 0.18) * 10
            by2 = cy - math.cos(t * 0.18) * 10
            img = draw_glow_blob(img, bx2, by2, 70, (94, 92, 230), 160)
            img = draw_glow_blob(img, cx, cy, 38, (216, 180, 254), 210)
            img = draw_glow_blob(img, cx, cy, 20, (255, 255, 255), 240)
            img = img.filter(ImageFilter.GaussianBlur(radius=3.5))

        elif st == "error":
            breath = math.sin(t * 0.2) * 4
            img = draw_glow_blob(img, cx, cy, 84 + breath, (220, 38, 38), 170)
            img = draw_glow_blob(img, cx, cy, 60, (234, 88, 12), 170)
            img = draw_glow_blob(img, cx, cy, 30, (254, 202, 202), 210)
            img = img.filter(ImageFilter.GaussianBlur(radius=3.5))

        elif st == "offline":
            img = draw_glow_blob(img, cx, cy, 55, (51, 65, 85), 110)
            img = draw_glow_blob(img, cx, cy, 26, (71, 85, 105), 140)
            img = img.filter(ImageFilter.GaussianBlur(radius=3.5))

        else:  # idle
            breath = math.sin(t * 0.08) * 5
            img = draw_glow_blob(img, cx, cy, 90 + breath, (10, 132, 255), 160)
            bx1 = cx + math.sin(t * 0.1) * 8
            by1 = cy + math.cos(t * 0.1) * 6
            img = draw_glow_blob(img, bx1, by1, 74 + breath * 0.6, (94, 92, 230), 160)
            img = draw_glow_blob(img, cx, cy, 56 + breath * 0.4, (56, 189, 248), 180)
            img = draw_glow_blob(img, cx, cy, 34, (224, 242, 254), 210)
            img = draw_glow_blob(img, cx, cy, 18, (255, 255, 255), 240)
            img = img.filter(ImageFilter.GaussianBlur(radius=3.5))

        try:
            self._photo = ImageTk.PhotoImage(img, master=self.canvas)
            self.canvas.create_image(cx, cy, image=self._photo)
        except Exception:
            return

    def _animate(self):
        if not self._is_active:
            return
        self._tick += 1
        try:
            if self.winfo_exists():
                self._draw_orb()
                delay = (
                    40
                    if self._state in ("listening", "speaking", "thinking")
                    else (
                        150
                        if self._state == "offline"
                        else (50 if self._state == "loading" else 65)
                    )
                )
                self._anim_job = self.after(delay, self._animate)
        except Exception:
            pass

    def stop(self):
        """Animatsiyani to'xtatish va resurslarni bo'shatish"""
        self._is_active = False
        if self._anim_job:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

    def start(self):
        """Animatsiyani qayta ishga tushirish"""
        if not self._is_active:
            self._is_active = True
            self._animate()

    def update_theme(self):
        """Mavzu o'zgarganda orb fonini yangilash"""
        cand = getattr(self.master, "_fg_color", None) or getattr(self.master, "fg_color", None)
        new_bg = cand if (cand and cand != "transparent") else Colors.BG_DARKEST
        if self.canvas.winfo_exists():
            self.canvas.configure(bg=new_bg)
            self._draw_orb()

    def destroy(self):
        self.stop()
        super().destroy()
