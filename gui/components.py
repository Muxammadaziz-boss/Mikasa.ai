# ========== components.py ==========
# Mikasa AI — Professional UI Components Library
# 80% minimal solid surfaces / 20% glass/accent surfaces
# Unified Button System, Card Architecture, Vector Icons, and AppleSiriOrb

import math
import tkinter as tk
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing
from gui.icons import VectorIconEngine, get_vector_icon


# ==========================================
# 1. CARD ARCHITECTURE (80% Solid / 20% Glass)
# ==========================================

class Card(ctk.CTkFrame):
    """
    Mikasa AI 80% Solid Surface Card.
    Toza, shovqinsiz va yuqori kontrastli minimal karta konteyneri.
    """

    def __init__(
        self,
        master,
        title="",
        subtitle="",
        padding=None,
        accent_color=None,
        action_widget=None,
        **kwargs,
    ):
        padding = Sizing.CARD_PADDING if padding is None else padding
        accent_color = accent_color or Colors.PRIMARY

        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_DARK

        super().__init__(
            master,
            fg_color=kwargs.pop("fg_color", Colors.BG_CARD),
            corner_radius=kwargs.pop("corner_radius", Sizing.CARD_RADIUS),
            border_width=kwargs.pop("border_width", 1),
            border_color=kwargs.pop("border_color", Colors.BORDER),
            **kwargs,
        )

        self._padding = padding
        self._accent_color = accent_color

        if title or subtitle:
            self.header = ctk.CTkFrame(self, fg_color="transparent")
            self.header.pack(fill="x", padx=padding, pady=(padding, 6))

            title_row = ctk.CTkFrame(self.header, fg_color="transparent")
            title_row.pack(fill="x")

            if title:
                ctk.CTkLabel(
                    title_row,
                    text="●",
                    font=(Fonts.FAMILY, 8),
                    text_color=accent_color,
                    width=12,
                ).pack(side="left")

                self.title_label = ctk.CTkLabel(
                    title_row,
                    text=title,
                    font=Fonts.HEADING_3,
                    text_color=Colors.TEXT_PRIMARY,
                    anchor="w",
                )
                self.title_label.pack(side="left", fill="x", expand=True)

            if action_widget:
                action_widget(title_row)

            if subtitle:
                self.subtitle_label = ctk.CTkLabel(
                    self.header,
                    text=subtitle,
                    font=Fonts.SMALL,
                    text_color=Colors.TEXT_MUTED,
                    anchor="w",
                    justify="left",
                    wraplength=850,
                )
                self.subtitle_label.pack(fill="x", pady=(2, 0))

            # Hairline 1px divider
            ctk.CTkFrame(
                self,
                fg_color=Colors.BORDER,
                height=1,
            ).pack(fill="x", padx=padding, pady=(4, padding))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=padding, pady=(0, padding))


class GlassCard(Card):
    """
    Mikasa AI 20% Glass Surface Card.
    Faqat suzuvchi panellar, hero elementlar va muhim holat kartalari uchun.
    """

    def __init__(self, master, title="", subtitle="", padding=None, accent_color=None, **kwargs):
        kwargs.setdefault("fg_color", Colors.GLASS_BG)
        kwargs.setdefault("border_color", Colors.GLASS_BORDER)
        super().__init__(
            master,
            title=title,
            subtitle=subtitle,
            padding=padding,
            accent_color=accent_color,
            **kwargs,
        )


class ElevatedCard(Card):
    """Qatlamli yoki hover bo'ladigan sirtlar uchun karta"""

    def __init__(self, master, title="", subtitle="", padding=None, accent_color=None, **kwargs):
        kwargs.setdefault("fg_color", Colors.BG_PANEL)
        kwargs.setdefault("border_color", Colors.BORDER)
        super().__init__(
            master,
            title=title,
            subtitle=subtitle,
            padding=padding,
            accent_color=accent_color,
            **kwargs,
        )


class PageHero(GlassCard):
    """Sahifa bosh sarlavhasi — zamonaviy minimal banner"""

    def __init__(
        self,
        master,
        title="",
        subtitle="",
        icon="✦",
        accent_color=None,
        chips=None,
        **kwargs,
    ):
        super().__init__(
            master,
            title="",
            subtitle="",
            accent_color=accent_color,
            padding=Sizing.SPACING_16,
            **kwargs,
        )

        accent = accent_color or Colors.PRIMARY

        header_row = ctk.CTkFrame(self.content, fg_color="transparent")
        header_row.pack(fill="x")

        icon_frame = ctk.CTkFrame(
            header_row,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.BORDER,
            corner_radius=12,
            width=42,
            height=42,
            bg_color=Colors.GLASS_BG,
        )
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)

        # Check for vector icon or symbol
        v_img = get_vector_icon(icon, size=20, color_dark=accent, color_light=accent)
        if v_img:
            ctk.CTkLabel(icon_frame, image=v_img, text="").pack(expand=True)
        else:
            ctk.CTkLabel(
                icon_frame,
                text=icon,
                font=(Fonts.FAMILY, 16),
                text_color=accent,
            ).pack(expand=True)

        text_block = ctk.CTkFrame(header_row, fg_color="transparent")
        text_block.pack(side="left", padx=12, fill="x", expand=True)

        self.title_label = ctk.CTkLabel(
            text_block,
            text=title,
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.title_label.pack(fill="x")

        if subtitle:
            self.subtitle_label = ctk.CTkLabel(
                text_block,
                text=subtitle,
                font=Fonts.SMALL,
                text_color=Colors.TEXT_MUTED,
                anchor="w",
                justify="left",
                wraplength=750,
            )
            self.subtitle_label.pack(fill="x", pady=(2, 0))

        self.actions = ctk.CTkFrame(header_row, fg_color="transparent")
        self.actions.pack(side="right", padx=(8, 0))

        if chips:
            chip_row = ctk.CTkFrame(self.content, fg_color="transparent")
            chip_row.pack(fill="x", pady=(10, 0))

            for text, chip_icon, fg, tc in chips:
                self.add_chip(chip_row, text, chip_icon, fg, tc)

    def add_chip(self, parent, text, icon="•", fg=None, text_color=None):
        chip = ctk.CTkFrame(
            parent,
            fg_color=fg or Colors.BG_CARD,
            corner_radius=Sizing.RADIUS_PILL,
            border_width=1,
            border_color=Colors.BORDER,
            bg_color=Colors.GLASS_BG,
        )
        chip.pack(side="left", padx=(0, 8))

        inner = ctk.CTkFrame(chip, fg_color="transparent")
        inner.pack(padx=10, pady=3)

        ctk.CTkLabel(
            inner,
            text=f"{icon}  {text}",
            font=Fonts.TINY,
            text_color=text_color or Colors.TEXT_SECONDARY,
        ).pack()
        return chip


# ==========================================
# 2. UNIFIED BUTTON SYSTEM
# ==========================================

class Button(ctk.CTkButton):
    """
    Mikasa AI Unified Button Component.
    Variants: 'primary', 'secondary', 'ghost', 'danger', 'glass'
    Heights: Default (42px), Compact (36px)
    Corners: Semantic (12px) or Pill (999)
    """

    def __init__(
        self,
        master,
        text="",
        variant="primary",
        icon=None,
        icon_size=16,
        command=None,
        height=None,
        width=None,
        corner_radius=None,
        tooltip=None,
        **kwargs,
    ):
        # Extract unsupported CTkButton kwargs safely
        self._hover_border = kwargs.pop("border_hover_color", None)
        self._normal_border = kwargs.get("border_color", None)

        height = height or Sizing.BUTTON_HEIGHT
        corner_radius = corner_radius if corner_radius is not None else Sizing.BUTTON_RADIUS

        colors = self._resolve_variant_colors(variant)
        fg_color = kwargs.pop("fg_color", colors["fg_color"])
        hover_color = kwargs.pop("hover_color", colors["hover_color"])
        border_color = kwargs.pop("border_color", colors["border_color"])
        border_width = kwargs.pop("border_width", colors["border_width"])
        text_color = kwargs.pop("text_color", colors["text_color"])

        if self._normal_border is None:
            self._normal_border = border_color
        if self._hover_border is None:
            self._hover_border = colors.get("border_hover_color", border_color)

        image = kwargs.pop("image", None)
        final_text = text
        if icon and not image:
            if isinstance(icon, str):
                v_img = get_vector_icon(
                    icon,
                    size=icon_size,
                    color_dark=text_color if text_color != "transparent" else "#FFFFFF",
                    color_light=text_color if text_color != "transparent" else "#0F172A",
                )
                if v_img:
                    image = v_img
                else:
                    final_text = f"{icon}  {text}" if text else icon

        btn_kwargs = {}
        if width is not None:
            btn_kwargs["width"] = width

        super().__init__(
            master,
            text=final_text,
            image=image,
            command=command,
            height=height,
            corner_radius=corner_radius,
            fg_color=fg_color,
            hover_color=hover_color,
            border_color=border_color,
            border_width=border_width,
            text_color=text_color,
            font=kwargs.pop("font", Fonts.BODY_BOLD),
            cursor="hand2",
            **btn_kwargs,
            **kwargs,
        )

        self._variant = variant
        self._tooltip_text = tooltip

    @staticmethod
    def _resolve_variant_colors(variant: str) -> dict:
        if variant == "primary":
            return {
                "fg_color": Colors.PRIMARY,
                "hover_color": Colors.PRIMARY_HOVER,
                "border_color": Colors.PRIMARY,
                "border_width": 0,
                "text_color": "#FFFFFF",
                "border_hover_color": Colors.PRIMARY_HOVER,
            }
        elif variant == "secondary":
            return {
                "fg_color": Colors.BG_CARD,
                "hover_color": Colors.BG_HOVER,
                "border_color": Colors.BORDER,
                "border_width": 1,
                "text_color": Colors.TEXT_PRIMARY,
                "border_hover_color": Colors.BORDER_HOVER,
            }
        elif variant == "ghost":
            return {
                "fg_color": "transparent",
                "hover_color": Colors.BG_HOVER,
                "border_color": Colors.BORDER,
                "border_width": 0,
                "text_color": Colors.TEXT_PRIMARY,
                "border_hover_color": Colors.BORDER_HOVER,
            }
        elif variant == "danger":
            return {
                "fg_color": Colors.DANGER,
                "hover_color": "#D73228",
                "border_color": Colors.DANGER,
                "border_width": 0,
                "text_color": "#FFFFFF",
                "border_hover_color": "#D73228",
            }
        elif variant == "glass":
            return {
                "fg_color": Colors.GLASS_BG,
                "hover_color": Colors.GLASS_BG_HOVER,
                "border_color": Colors.GLASS_BORDER,
                "border_width": 1,
                "text_color": "#FFFFFF",
                "border_hover_color": Colors.GLASS_BORDER_HOVER,
            }
        return {
            "fg_color": Colors.PRIMARY,
            "hover_color": Colors.PRIMARY_HOVER,
            "border_color": Colors.PRIMARY,
            "border_width": 0,
            "text_color": "#FFFFFF",
            "border_hover_color": Colors.PRIMARY_HOVER,
        }


    def configure(self, require_redraw=False, **kwargs):
        if "border_color" in kwargs:
            self._normal_border = kwargs["border_color"]
        if "border_hover_color" in kwargs:
            self._hover_border = kwargs.pop("border_hover_color")
        if "icon" in kwargs:
            icon = kwargs.pop("icon")
            v_img = get_vector_icon(icon, size=16, color_dark="#FFFFFF", color_light="#0F172A") if isinstance(icon, str) else None
            if v_img:
                kwargs["image"] = v_img
            else:
                if "text" in kwargs:
                    kwargs["text"] = f"{icon}  {kwargs['text']}" if kwargs["text"] else icon
                else:
                    kwargs["text"] = icon
        if "variant" in kwargs:
            kwargs.pop("variant")
        super().configure(require_redraw=require_redraw, **kwargs)


class GlassButton(Button):
    """
    Apple Frosted Glass Button with dynamic border hover highlight.
    """

    def __init__(self, master, text="", icon="", **kwargs):
        kwargs.setdefault("variant", "glass")
        super().__init__(master, text=text, icon=icon, **kwargs)

        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        try:
            if self._hover_border:
                ctk.CTkButton.configure(self, border_color=self._hover_border)
        except Exception:
            pass

    def _on_leave(self, event=None):
        try:
            if self._normal_border:
                ctk.CTkButton.configure(self, border_color=self._normal_border)
        except Exception:
            pass

    def configure(self, require_redraw=False, **kwargs):
        super().configure(require_redraw=require_redraw, **kwargs)


class GlowButton(Button):
    """Primary action glow button with subtle border"""

    def __init__(self, master, text="", icon="", **kwargs):
        kwargs.setdefault("variant", "primary")
        kwargs.setdefault("fg_color", Colors.GLASS_HERO_BG)
        kwargs.setdefault("hover_color", Colors.GLASS_HERO_HOVER)
        kwargs.setdefault("border_color", Colors.GLASS_HERO_BORDER)
        kwargs.setdefault("border_width", 1)
        super().__init__(master, text=text, icon=icon, **kwargs)


class SecondaryButton(GlassButton):
    """Secondary button subclassing GlassButton for backward compatibility"""

    def __init__(self, master, text="", icon="", **kwargs):
        kwargs.setdefault("fg_color", Colors.GLASS_BG)
        kwargs.setdefault("hover_color", Colors.GLASS_BG_HOVER)
        kwargs.setdefault("border_color", Colors.GLASS_BORDER)
        kwargs.setdefault("border_hover_color", Colors.GLASS_BORDER_HOVER)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("text_color", Colors.TEXT_PRIMARY)
        super().__init__(master, text=text, icon=icon, **kwargs)


class IconButton(GlassButton):
    """Icon-only button"""

    def __init__(self, master, icon="", size=36, **kwargs):
        super().__init__(master, text="", icon=icon, width=size, height=size, corner_radius=12, **kwargs)


class CircleIconButton(GlassButton):
    """
    Doiraviy ikonka tugmasi (📎, 🎙️, ➤, ✕).
    CustomTkinter scaled_minsize ustunlarini 0 ga tushirib,
    1:1 aniq doira geometriyasini kafolatlaydi.
    """

    def __init__(self, master, icon="", size=38, tooltip="", **kwargs):
        radius = size // 2
        super().__init__(
            master,
            text="",
            icon=icon,
            icon_size=max(14, size - 18),
            width=size,
            height=size,
            corner_radius=radius,
            tooltip=tooltip,
            **kwargs,
        )
        self.grid_columnconfigure(0, minsize=0)
        self.grid_columnconfigure(4, minsize=0)

    def configure(self, require_redraw=False, **kwargs):
        super().configure(require_redraw=require_redraw, **kwargs)
        self.grid_columnconfigure(0, minsize=0)
        self.grid_columnconfigure(4, minsize=0)


# ==========================================
# 3. APPLE SIRI ORB (Multi-layer Aura)
# ==========================================

class AppleSiriOrb(ctk.CTkFrame):
    """
    Apple Siri / Apple Intelligence animatsion glowing orb.
    States: 'idle', 'listening', 'thinking', 'speaking', 'error', 'offline'
    Optimized 35 FPS rendering, safe cancellation on destroy.
    """

    def __init__(self, master, size=210, **kwargs):
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_DARK

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
        self._state = "idle"
        self._tick = 0
        self._anim_job = None
        self._is_active = True

        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=Colors.BG_DARK,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self._draw_orb()
        self._animate()

    def set_state(self, state: str):
        """Orb holatini o'zgartirish: 'idle', 'listening', 'thinking', 'speaking', 'error', 'offline'"""
        self._state = state.lower()
        self._draw_orb()

    def _draw_orb(self):
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
            self.canvas.create_oval(cx - 40, cy - 40, cx + 40, cy + 40, fill="#0A84FF", outline="")
            return

        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

        def draw_glow_blob(base_img, bx, by, radius, color_rgb, max_alpha=200):
            blob_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            d = ImageDraw.Draw(blob_img)
            step = 3
            for r in range(int(radius), 0, -step):
                frac = r / radius
                alpha = int(max_alpha * (1.0 - frac * frac))
                d.ellipse([bx - r, by - r, bx + r, by + r], fill=(*color_rgb, alpha))
            return Image.alpha_composite(base_img, blob_img)

        st = self._state

        if st == "listening":
            breath = math.sin(t * 0.18) * 8
            img = draw_glow_blob(img, cx, cy, 96 + breath, (10, 132, 255), 180)
            bx1 = cx + math.sin(t * 0.22) * 16
            by1 = cy + math.cos(t * 0.22) * 12
            img = draw_glow_blob(img, bx1, by1, 82, (0, 245, 255), 190)
            bx2 = cx - math.sin(t * 0.19) * 14
            by2 = cy - math.cos(t * 0.19) * 16
            img = draw_glow_blob(img, bx2, by2, 76, (255, 45, 120), 170)
            bx3 = cx + math.cos(t * 0.26) * 12
            by3 = cy - math.sin(t * 0.26) * 10
            img = draw_glow_blob(img, bx3, by3, 70, (175, 82, 222), 160)
            img = draw_glow_blob(img, cx, cy, 44, (200, 245, 255), 230)
            img = draw_glow_blob(img, cx, cy, 24, (255, 255, 255), 255)
            img = img.filter(ImageFilter.GaussianBlur(radius=4))

            draw = ImageDraw.Draw(img)
            bar_count = 7
            bar_w = 4
            bar_gap = 3
            total_w = bar_count * bar_w + (bar_count - 1) * bar_gap
            sx = cx - total_w // 2
            for i in range(bar_count):
                phase = i * 0.8 + t * 0.4
                h = int(10 + abs(math.sin(phase)) * 22 + abs(math.cos(phase * 0.7)) * 12)
                x = sx + i * (bar_w + bar_gap)
                draw.rounded_rectangle([x, cy - h // 2, x + bar_w, cy + h // 2], radius=2, fill=(255, 255, 255, 240))

        elif st == "thinking":
            breath = math.sin(t * 0.14) * 6
            img = draw_glow_blob(img, cx, cy, 90 + breath, (94, 92, 230), 180)
            bx1 = cx + math.sin(t * 0.2) * 14
            by1 = cy + math.cos(t * 0.2) * 14
            img = draw_glow_blob(img, bx1, by1, 75, (175, 82, 222), 190)
            bx2 = cx - math.sin(t * 0.2) * 12
            by2 = cy - math.cos(t * 0.2) * 12
            img = draw_glow_blob(img, bx2, by2, 68, (10, 132, 255), 170)
            img = draw_glow_blob(img, cx, cy, 38, (230, 215, 255), 230)
            img = draw_glow_blob(img, cx, cy, 20, (255, 255, 255), 255)
            img = img.filter(ImageFilter.GaussianBlur(radius=4))

        elif st == "speaking":
            breath = math.sin(t * 0.2) * 7
            img = draw_glow_blob(img, cx, cy, 95 + breath, (80, 20, 160), 180)
            bx1 = cx + math.sin(t * 0.24) * 14
            by1 = cy + math.cos(t * 0.24) * 10
            img = draw_glow_blob(img, bx1, by1, 80, (220, 40, 180), 190)
            bx2 = cx - math.sin(t * 0.2) * 12
            by2 = cy - math.cos(t * 0.2) * 12
            img = draw_glow_blob(img, bx2, by2, 72, (160, 60, 240), 170)
            img = draw_glow_blob(img, cx, cy, 42, (240, 210, 255), 230)
            img = draw_glow_blob(img, cx, cy, 22, (255, 255, 255), 255)
            img = img.filter(ImageFilter.GaussianBlur(radius=4))

        elif st == "error":
            breath = math.sin(t * 0.25) * 5
            img = draw_glow_blob(img, cx, cy, 88 + breath, (255, 69, 58), 180)
            img = draw_glow_blob(img, cx, cy, 64, (255, 159, 10), 190)
            img = draw_glow_blob(img, cx, cy, 32, (255, 220, 220), 230)
            img = img.filter(ImageFilter.GaussianBlur(radius=4))

        elif st == "offline":
            img = draw_glow_blob(img, cx, cy, 60, (50, 50, 70), 120)
            img = draw_glow_blob(img, cx, cy, 28, (80, 80, 105), 160)
            img = img.filter(ImageFilter.GaussianBlur(radius=4))

        else:
            breath = math.sin(t * 0.1) * 6
            img = draw_glow_blob(img, cx, cy, 92 + breath, (10, 132, 255), 180)
            bx1 = cx + math.sin(t * 0.12) * 8
            by1 = cy + math.cos(t * 0.12) * 6
            img = draw_glow_blob(img, bx1, by1, 76 + breath * 0.8, (0, 210, 255), 190)
            img = draw_glow_blob(img, cx, cy, 60 + breath * 0.5, (30, 100, 240), 200)
            img = draw_glow_blob(img, cx, cy, 38, (180, 240, 255), 230)
            img = draw_glow_blob(img, cx, cy, 20, (255, 255, 255), 255)
            img = img.filter(ImageFilter.GaussianBlur(radius=4))

        try:
            self._photo = ImageTk.PhotoImage(img, master=self.canvas)
            self.canvas.create_image(cx, cy, image=self._photo)
        except Exception:
            return

        if st in ("idle", "offline"):
            self.canvas.create_text(cx, cy, text="✦", font=("Segoe UI", 16, "bold"), fill="#0A2540")
        elif st == "speaking":
            self.canvas.create_text(cx, cy, text="✦", font=("Segoe UI", 16, "bold"), fill="#2E0854")

    def _animate(self):
        if not self._is_active:
            return
        self._tick += 1
        try:
            if self.winfo_exists():
                self._draw_orb()
                delay = 40 if self._state in ("listening", "speaking", "thinking") else (150 if self._state == "offline" else 65)
                self._anim_job = self.after(delay, self._animate)
        except Exception:
            pass

    def stop(self):
        self._is_active = False
        if self._anim_job:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

    def destroy(self):
        self.stop()
        super().destroy()


# ==========================================
# 4. CHAT COMPONENTS (MessageBubble, AgentStep)
# ==========================================

class MessageBubble(ctk.CTkFrame):
    """
    Apple macOS / Linear style Chat Message Bubble.
    Clean distinction between User and Assistant.
    """

    def __init__(self, master, text="", role="user", timestamp="", **kwargs):
        is_user = role == "user"

        if is_user:
            bg_color = Colors.PRIMARY
            border_width = 0
            border_color = Colors.PRIMARY
            text_color = "#FFFFFF"
            time_color = "#CBE4FF"
        else:
            bg_color = Colors.BG_CARD
            border_width = 1
            border_color = Colors.BORDER
            text_color = Colors.TEXT_PRIMARY
            time_color = Colors.TEXT_MUTED

        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_SURFACE

        super().__init__(
            master,
            fg_color=bg_color,
            corner_radius=16,
            border_width=border_width,
            border_color=border_color,
            **kwargs,
        )

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=14, pady=10)

        # Assistant header with title, copy, and timestamp
        if not is_user:
            meta_row = ctk.CTkFrame(container, fg_color="transparent")
            meta_row.pack(fill="x", pady=(0, 4))

            ctk.CTkLabel(
                meta_row,
                text="✦ Mikasa",
                font=Fonts.SMALL_BOLD,
                text_color=Colors.PRIMARY,
                anchor="w",
            ).pack(side="left")

            if timestamp:
                ctk.CTkLabel(
                    meta_row,
                    text=timestamp,
                    font=Fonts.TINY,
                    text_color=time_color,
                    anchor="e",
                ).pack(side="right", padx=(6, 0))

            # Copy button
            c_img = get_vector_icon("copy", size=13, color_dark=Colors.TEXT_MUTED, color_light=Colors.TEXT_MUTED)
            copy_btn = ctk.CTkButton(
                meta_row,
                text="" if c_img else "❐",
                image=c_img,
                width=18,
                height=18,
                fg_color="transparent",
                hover_color=Colors.BG_HOVER,
                command=lambda t=text: self._copy_to_clipboard(t),
            )
            copy_btn.pack(side="right")
        elif timestamp:
            meta_row = ctk.CTkFrame(container, fg_color="transparent")
            meta_row.pack(fill="x", pady=(0, 2))
            ctk.CTkLabel(
                meta_row,
                text=timestamp,
                font=Fonts.TINY,
                text_color=time_color,
                anchor="e",
            ).pack(side="right")

        self.text_label = ctk.CTkLabel(
            container,
            text=text,
            font=Fonts.BODY,
            text_color=text_color,
            wraplength=520,
            justify="left",
            anchor="w",
        )
        self.text_label.pack(fill="x")

    def _copy_to_clipboard(self, text: str):
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            try:
                self.clipboard_clear()
                self.clipboard_append(text)
            except Exception:
                pass


class TypingBubble(ctk.CTkFrame):
    """Animatsiyali 3-nuqta yozish indikatori"""

    def __init__(self, master, prefix="✦ Mikasa o'ylamoqda", **kwargs):
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_SURFACE

        prefix_text = kwargs.pop("prefix", prefix)
        self._prefix = prefix_text

        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
            **kwargs,
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=14, pady=10)

        self.text_label = ctk.CTkLabel(
            inner,
            text=prefix_text,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.PRIMARY,
        )
        self.text_label.pack(side="left", padx=(0, 8))

        self.dots_label = ctk.CTkLabel(
            inner,
            text="● ○ ○",
            font=(Fonts.FAMILY, 10),
            text_color=Colors.PRIMARY,
        )
        self.dots_label.pack(side="left")

        self._phase = 0
        self._anim_job = None
        self._is_running = True
        self._animate()

    def _animate(self):
        if not self._is_running:
            return
        patterns = ["● ○ ○", "○ ● ○", "○ ○ ●"]
        self._phase = (self._phase + 1) % len(patterns)
        try:
            if self.winfo_exists():
                self.dots_label.configure(text=patterns[self._phase])
                self._anim_job = self.after(350, self._animate)
        except Exception:
            pass

    def set_prefix(self, prefix: str):
        self._prefix = prefix
        self.text_label.configure(text=prefix)

    def stop(self):
        self._is_running = False
        if self._anim_job:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

    def destroy(self):
        self.stop()
        super().destroy()


class AgentStepIndicator(ctk.CTkFrame):
    """
    ReAct Agent qadamlari vizualizatori.
    ✓ Bajarildi (muted) | ◌ Faol (electric blue/violet) | ○ Kutilmoqda | ✕ Xato
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._steps = []

    def add_step(self, step_type: str, title: str, description: str = ""):
        step_row = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=10, border_width=1, border_color=Colors.BORDER)
        step_row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(step_row, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=6)

        badge_colors = {
            "completed": (Colors.SUCCESS_SOFT, Colors.SUCCESS, "✓"),
            "thought": (Colors.PRIMARY_SOFT, Colors.PRIMARY, "✦"),
            "tool": (Colors.INFO_SOFT, Colors.INFO, "⚡"),
            "error": (Colors.DANGER_SOFT, Colors.DANGER, "✕"),
            "pending": (Colors.BG_INPUT, Colors.TEXT_MUTED, "○"),
        }
        bg, tc, sym = badge_colors.get(step_type, (Colors.BG_INPUT, Colors.TEXT_MUTED, "•"))

        icon_frame = ctk.CTkFrame(inner, fg_color=bg, corner_radius=10, width=20, height=20)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=sym, font=(Fonts.FAMILY, 10, "bold"), text_color=tc).pack(expand=True)

        text_block = ctk.CTkFrame(inner, fg_color="transparent")
        text_block.pack(side="left", padx=8, fill="x", expand=True)

        ctk.CTkLabel(text_block, text=title, font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x")
        if description:
            ctk.CTkLabel(text_block, text=description, font=Fonts.TINY, text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")

        self._steps.append(step_row)

    def clear(self):
        for s in self._steps:
            try:
                s.destroy()
            except Exception:
                pass
        self._steps.clear()


# ==========================================
# 5. SIDEBAR NAVIGATION ITEM
# ==========================================

class NavItem(ctk.CTkFrame):
    """Mikasa Command Center Sidebar Nav Item"""

    def __init__(
        self,
        master,
        icon="dashboard",
        label="",
        active=False,
        command=None,
        compact=False,
        **kwargs,
    ):
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.SIDEBAR_BG

        super().__init__(
            master,
            fg_color=Colors.SIDEBAR_ACTIVE if active else "transparent",
            corner_radius=10 if active else 0,
            border_width=1 if active else 0,
            border_color="#33334A" if active else Colors.SIDEBAR_BG,
            height=44,
            cursor="hand2",
            **kwargs,
        )
        self.pack_propagate(False)

        self._command = command
        self._active = active
        self._compact = compact
        self._icon_name = icon

        # 3px Electric blue active indicator on the left
        self.indicator = ctk.CTkFrame(
            self,
            fg_color=Colors.SIDEBAR_INDICATOR if active else "transparent",
            width=3,
            corner_radius=2,
        )
        self.indicator.pack(side="left", fill="y", padx=(4, 6), pady=8)

        self.icon_label = ctk.CTkLabel(self, text="", width=24)
        self.icon_label.pack(side="left", padx=(2, 6))
        self._update_icon()

        self.text_label = ctk.CTkLabel(
            self,
            text=label,
            font=Fonts.NAV_LABEL,
            text_color=Colors.TEXT_PRIMARY if active else Colors.TEXT_SECONDARY,
            anchor="w",
        )
        if not compact:
            self.text_label.pack(side="left", fill="x", expand=True, padx=(0, 8))

        for widget in [self, self.icon_label, self.text_label, self.indicator]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

        self.set_compact(compact)

    def _update_icon(self):
        c_dark = Colors.PRIMARY if self._active else Colors.TEXT_SECONDARY
        c_light = Colors.PRIMARY if self._active else Colors.TEXT_SECONDARY
        v_img = get_vector_icon(self._icon_name, size=18, color_dark=c_dark, color_light=c_light)
        if v_img:
            self.icon_label.configure(image=v_img, text="")
        else:
            self.icon_label.configure(image=None, text=self._icon_name, text_color=c_dark, font=Fonts.NAV_ICON)

    def _on_click(self, event=None):
        if self._command:
            self._command()

    def _on_enter(self, event=None):
        if not self._active:
            self.configure(fg_color=Colors.SIDEBAR_HOVER, corner_radius=10, border_width=1, border_color="#262638")
            self.text_label.configure(text_color=Colors.TEXT_PRIMARY)

    def _on_leave(self, event=None):
        if not self._active:
            self.configure(fg_color="transparent", corner_radius=0, border_width=0)
            self.text_label.configure(text_color=Colors.TEXT_SECONDARY)

    def set_active(self, active: bool):
        self._active = active
        self.configure(
            fg_color=Colors.SIDEBAR_ACTIVE if active else "transparent",
            corner_radius=10 if active else 0,
            border_width=1 if active else 0,
            border_color="#33334A" if active else Colors.SIDEBAR_BG,
        )
        self.indicator.configure(fg_color=Colors.SIDEBAR_INDICATOR if active else "transparent")
        self.text_label.configure(text_color=Colors.TEXT_PRIMARY if active else Colors.TEXT_SECONDARY)
        self._update_icon()

    def set_compact(self, compact: bool):
        self._compact = compact
        self.configure(height=38 if compact else 44)
        if compact:
            self.text_label.pack_forget()
            self.indicator.pack_configure(padx=(1, 2))
        else:
            if not self.text_label.winfo_manager():
                self.text_label.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.indicator.pack_configure(padx=(2, 6))


# ==========================================
# 6. BADGES, CHIPS & EMPTY STATES
# ==========================================

class StatusBadge(ctk.CTkFrame):
    """Holat ko'rsatgich — dot + text (Apple capsule badge)"""

    def __init__(self, master, status="online", text="", **kwargs):
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_DARKEST
        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizing.RADIUS_PILL,
            border_width=1,
            border_color=Colors.BORDER,
            **kwargs,
        )

        color = self._status_color(status)
        self.dot = ctk.CTkLabel(
            self,
            text="●",
            font=(Fonts.FAMILY, 10),
            text_color=color,
            width=14,
        )
        self.dot.pack(side="left", padx=(10, 4), pady=4)

        display_text = text or status.capitalize()
        self.label = ctk.CTkLabel(
            self,
            text=display_text,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.label.pack(side="left", padx=(0, 10), pady=4)
        self._status = status

    def set_status(self, status, text=None):
        self._status = status
        color = self._status_color(status)
        self.dot.configure(text_color=color)
        self.label.configure(text=text or status.capitalize())

    def _status_color(self, status):
        return {
            "online": Colors.SUCCESS,
            "offline": Colors.DANGER,
            "busy": Colors.WARNING,
            "idle": Colors.TEXT_MUTED,
            "listening": Colors.PRIMARY,
            "speaking": Colors.SECONDARY,
            "info": Colors.INFO,
        }.get(status, Colors.TEXT_MUTED)


class InfoChip(ctk.CTkFrame):
    """Ixcham axborot nishoni (Chip)"""

    def __init__(self, master, text="", icon="", fg_color=None, text_color=None, **kwargs):
        super().__init__(
            master,
            fg_color=fg_color or Colors.BG_CARD,
            corner_radius=Sizing.RADIUS_PILL,
            border_width=1,
            border_color=Colors.BORDER,
            **kwargs,
        )
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=10, pady=4)

        if icon:
            v_img = get_vector_icon(icon, size=13, color_dark=text_color or Colors.TEXT_SECONDARY, color_light=text_color or Colors.TEXT_SECONDARY)
            if v_img:
                ctk.CTkLabel(inner, image=v_img, text="").pack(side="left", padx=(0, 4))
            else:
                ctk.CTkLabel(inner, text=icon, font=(Fonts.FAMILY, 11), text_color=text_color or Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 4))

        self.label = ctk.CTkLabel(
            inner,
            text=text,
            font=Fonts.TINY,
            text_color=text_color or Colors.TEXT_SECONDARY,
        )
        self.label.pack(side="left")

    def configure_text(self, text):
        self.label.configure(text=text)

    def set_text(self, text):
        self.label.configure(text=text)


class EmptyState(ctk.CTkFrame):
    """Bo'sh holat — toza vektorli empty state"""

    def __init__(self, master, icon="sparkles", title="", description="", action_label=None, action_cmd=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        curr = master
        effective_bg = Colors.BG_CARD
        while curr:
            c = getattr(curr, "_fg_color", None) or getattr(curr, "fg_color", None)
            if c and c != "transparent":
                effective_bg = c
                break
            curr = getattr(curr, "master", None)

        icon_frame = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_PANEL,
            bg_color=effective_bg,
            border_width=1,
            border_color=Colors.BORDER,
            corner_radius=28,
            width=56,
            height=56,
        )
        icon_frame.pack(pady=(16, 8))
        icon_frame.pack_propagate(False)

        v_img = get_vector_icon(icon, size=24, color_dark=Colors.PRIMARY, color_light=Colors.PRIMARY)
        if v_img:
            ctk.CTkLabel(icon_frame, image=v_img, text="").pack(expand=True)
        else:
            ctk.CTkLabel(icon_frame, text=icon, font=(Fonts.FAMILY, 20), text_color=Colors.PRIMARY).pack(expand=True)

        ctk.CTkLabel(self, text=title, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(pady=(4, 0))

        ctk.CTkLabel(
            self,
            text=description,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            justify="center",
            wraplength=450,
        ).pack(pady=(4, 10))

        if action_label and action_cmd:
            Button(self, text=action_label, variant="secondary", height=34, command=action_cmd).pack(pady=(0, 10))


class SearchBar(ctk.CTkFrame):
    """Qidiruv maydoni"""

    def __init__(self, master, placeholder="Qidirish...", **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_INPUT,
            corner_radius=Sizing.RADIUS_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            height=40,
            **kwargs,
        )
        self.pack_propagate(False)

        s_img = get_vector_icon("search", size=16, color_dark=Colors.TEXT_MUTED, color_light=Colors.TEXT_MUTED)
        if s_img:
            ctk.CTkLabel(self, image=s_img, text="").pack(side="left", padx=(12, 6))
        else:
            ctk.CTkLabel(self, text="⌕", font=(Fonts.FAMILY, 14), text_color=Colors.TEXT_MUTED).pack(side="left", padx=(12, 6))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 12))


class StatWidget(Card):
    """Statistika vidjeti"""

    def __init__(self, master, value="0", label="", icon="", color=None, **kwargs):
        color = color or Colors.PRIMARY
        super().__init__(master, padding=Sizing.SPACING_12, **kwargs)

        top = ctk.CTkFrame(self.content, fg_color="transparent")
        top.pack(fill="x")

        v_img = get_vector_icon(icon, size=18, color_dark=color, color_light=color)
        if v_img:
            ctk.CTkLabel(top, image=v_img, text="").pack(side="left")
        elif icon:
            ctk.CTkLabel(top, text=icon, font=(Fonts.FAMILY, 16), text_color=color).pack(side="left")

        ctk.CTkLabel(top, text=label, font=Fonts.SMALL, text_color=Colors.TEXT_MUTED).pack(side="left", padx=(6, 0))

        self.value_label = ctk.CTkLabel(
            self.content,
            text=str(value),
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.value_label.pack(fill="x", pady=(4, 0))

    def update_value(self, value):
        self.value_label.configure(text=str(value))

    def set_value(self, value):
        self.update_value(value)


class ProgressRing(ctk.CTkFrame):
    """Dumaloq progress indikatori"""

    def __init__(self, master, size=64, line_width=5, color=None, **kwargs):
        super().__init__(master, fg_color="transparent", width=size, height=size, **kwargs)
        self.pack_propagate(False)
        self._size = size
        self._width = line_width
        self._color = color or Colors.PRIMARY
        self._progress = 0

        self.canvas = tk.Canvas(self, width=size, height=size, bg=Colors.BG_CARD, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self._draw()

    def set_progress(self, val: float):
        self._progress = max(0.0, min(1.0, val))
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        s = self._size
        w = self._width
        pad = w + 2
        extent = int(self._progress * 360)
        self.canvas.create_oval(pad, pad, s - pad, s - pad, outline=Colors.BORDER, width=w)
        if extent > 0:
            self.canvas.create_arc(pad, pad, s - pad, s - pad, start=90, extent=-extent, outline=self._color, width=w, style="arc")


class ToastNotification(ctk.CTkFrame):
    """
    Silliq paydo bo'luvchi va avtomatik yo'qoluvchi Toast bildirishnoma.
    Types: 'info', 'success', 'warning', 'error'
    """

    def __init__(
        self,
        master,
        message: str,
        title: str = "Mikasa AI",
        duration: int = 4000,
        toast_type: str = "info",
        action_label: str = None,
        action_command = None,
        **kwargs,
    ):
        type_colors = {
            "info": Colors.INFO,
            "success": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "error": Colors.DANGER,
        }
        accent = type_colors.get(toast_type, Colors.PRIMARY)

        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=accent,
            **kwargs,
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        v_img = get_vector_icon(toast_type if toast_type in ("info", "warning", "check", "close") else "sparkles", size=14, color_dark=accent, color_light=accent)
        if v_img:
            ctk.CTkLabel(header, image=v_img, text="").pack(side="left")
        else:
            ctk.CTkLabel(header, text="✦", font=(Fonts.FAMILY, 12), text_color=accent).pack(side="left")

        ctk.CTkLabel(header, text=title, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=6)

        c_img = get_vector_icon("close", size=12, color_dark=Colors.TEXT_MUTED, color_light=Colors.TEXT_MUTED)
        ctk.CTkButton(
            header,
            text="" if c_img else "✕",
            image=c_img,
            width=18,
            height=18,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            command=self.dismiss,
        ).pack(side="right")

        ctk.CTkLabel(
            inner,
            text=message,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY,
            wraplength=280,
            justify="left",
        ).pack(fill="x")

        if action_label and action_command:
            Button(
                inner,
                text=action_label,
                variant="secondary",
                height=28,
                command=lambda: [action_command(), self.dismiss()],
            ).pack(anchor="e", pady=(6, 0))

        self.place(relx=0.98, rely=0.96, anchor="se")
        self.after(duration, self.dismiss)

    def dismiss(self):
        try:
            self.destroy()
        except Exception:
            pass


def show_toast(root_widget, message: str, title: str = "Mikasa AI", duration: int = 4000, toast_type: str = "info"):
    """Xavfsiz Toast chiqarish funksiyasi"""
    try:
        root_widget.after(0, lambda: ToastNotification(root_widget, message, title=title, duration=duration, toast_type=toast_type))
    except Exception:
        pass
