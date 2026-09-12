# ========== components.py ==========
# Mikasa AI — Professional UI Components Library
# 80% minimal solid surfaces / 20% glass/accent surfaces
# Unified Button System, Card Architecture, Vector Icons, and AppleSiriOrb

import math
import os
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing, Surfaces
from gui.icons import VectorIconEngine, get_vector_icon


# ==========================================
# 1. SEMANTIC SURFACE HIERARCHY (80% Solid / 20% Glass)
# ==========================================

class Surface(ctk.CTkFrame):
    """
    Mikasa AI Semantic Surface Base Frame.
    
    Barcha darajadagi konteyner va sirtlar uchun poydevor klass.
    Avtomatik ravishda Surfaces tokenlaridan rang, hoshiya va radiuslarni oladi.
    """
    DEFAULT_SURFACE = Surfaces.CARD

    def __init__(
        self,
        master,
        surface: str = None,
        fg_color=None,
        bg_color=None,
        border_color=None,
        border_width=None,
        corner_radius=None,
        tier=None,
        **kwargs,
    ):
        # Sirt darajasini aniqlash (Backward-compatible: 'surface' yoki 'tier')
        effective_surface = (surface or tier or self.DEFAULT_SURFACE or Surfaces.CARD).lower()
        self._surface_tier = effective_surface
        tokens = Surfaces.get_tokens(effective_surface)

        # Precedence 1: fg_color (explicit arg > kwargs.pop > semantic token default)
        if fg_color is None:
            fg_color = kwargs.pop("fg_color", None)
        self._user_fg_override = fg_color is not None
        resolved_fg = fg_color if self._user_fg_override else tokens.get("fg_color", Colors.BG_CARD)

        # Precedence 2: border_color
        if border_color is None:
            border_color = kwargs.pop("border_color", None)
        self._user_border_override = border_color is not None
        resolved_border_color = border_color if self._user_border_override else tokens.get("border_color", Colors.BORDER)

        # Precedence 3: border_width
        if border_width is None:
            border_width = kwargs.pop("border_width", None)
        self._user_border_width_override = border_width is not None
        resolved_border_width = border_width if self._user_border_width_override else tokens.get("border_width", 1)

        # Precedence 4: corner_radius
        if corner_radius is None:
            corner_radius = kwargs.pop("corner_radius", None)
        self._user_radius_override = corner_radius is not None
        resolved_radius = corner_radius if self._user_radius_override else tokens.get("corner_radius", Sizing.CARD)

        # Precedence 5: bg_color
        # Muhim: agar bg_color berilmagan bo'lsa, "transparent" beriladi.
        # CustomTkinter avtomatik ravishda master ning fg_color ini aniqlaydi va burchaklar
        # o'sha rangda tekis chiziladi (dark halo yoki mismatch bo'lmaydi).
        if bg_color is None:
            bg_color = kwargs.pop("bg_color", None)
        self._user_bg_override = bg_color is not None
        resolved_bg = bg_color if self._user_bg_override else "transparent"

        super().__init__(
            master=master,
            fg_color=resolved_fg,
            bg_color=resolved_bg,
            border_color=resolved_border_color,
            border_width=resolved_border_width,
            corner_radius=resolved_radius,
            **kwargs,
        )

    def update_theme(self):
        """Mavzu o'zgarganda sirt ranglarini qayta qo'llash"""
        tokens = Surfaces.get_tokens(self._surface_tier)
        if not self._user_fg_override:
            self.configure(fg_color=tokens.get("fg_color", Colors.BG_CARD))
        if not self._user_border_override:
            self.configure(border_color=tokens.get("border_color", Colors.BORDER))


class Card(Surface):
    """
    Mikasa AI 80% Solid Surface Card.
    
    Standard container for general UI: forms, lists, tables, data rows, and settings.
    Solid, distraction-free container with subtle hairline border (Colors.BORDER).
    """
    DEFAULT_SURFACE = Surfaces.CARD

    def __init__(
        self,
        master,
        title="",
        subtitle="",
        padding=None,
        accent_color=None,
        action_widget=None,
        surface=None,
        fg_color=None,
        bg_color=None,
        border_color=None,
        border_width=None,
        corner_radius=None,
        tier=None,
        **kwargs,
    ):
        padding = Sizing.CARD_PADDING if padding is None else padding
        accent_color = accent_color or Colors.PRIMARY
        effective_surface = surface or tier or self.DEFAULT_SURFACE

        super().__init__(
            master=master,
            surface=effective_surface,
            fg_color=fg_color,
            bg_color=bg_color,
            border_color=border_color,
            border_width=border_width,
            corner_radius=corner_radius,
            **kwargs,
        )

        self._padding = padding
        self._accent_color = accent_color
        self.title_label = None
        self.subtitle_label = None
        self.header_divider = None

        if title or subtitle:
            self.header = ctk.CTkFrame(self, fg_color="transparent")
            self.header.pack(fill="x", padx=padding, pady=(padding, 6))

            title_row = ctk.CTkFrame(self.header, fg_color="transparent")
            title_row.pack(fill="x")

            if title:
                dot_img = get_vector_icon("circle", size=7, color_dark=accent_color, color_light=accent_color, fallback="circle")
                if dot_img:
                    ctk.CTkLabel(title_row, image=dot_img, text="", width=12).pack(side="left")

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

            # Hairline 1px divider (subtle, non-intrusive)
            self.header_divider = ctk.CTkFrame(
                self,
                fg_color=Colors.BORDER_SUBTLE,
                height=1,
            )
            self.header_divider.pack(fill="x", padx=padding, pady=(4, padding))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=padding, pady=(0, padding))

    def update_theme(self):
        super().update_theme()
        if self.header_divider:
            self.header_divider.configure(fg_color=Colors.BORDER_SUBTLE)
        if self.title_label:
            self.title_label.configure(text_color=Colors.TEXT_PRIMARY)
        if self.subtitle_label:
            self.subtitle_label.configure(text_color=Colors.TEXT_MUTED)


class ElevatedCard(Card):
    """
    Mikasa AI Solid Elevated Surface Card.
    
    Qatlamli, balandroq sirtlar uchun: yon panellar, asbob kartalari,
    dropdown ro'yxatlar va ikkinchi darajali guruhlar.
    """
    DEFAULT_SURFACE = Surfaces.ELEVATED


class GlassCard(Card):
    """
    Mikasa AI 20% Glass-like Opaque Surface Card.
    
    NOTE ON ARCHITECTURE & RENDERING:
    CustomTkinter desktop widgets do not support real-time dynamic GPU backdrop blur
    or native window-level alpha compositing without crippling per-frame overhead.
    This component provides a "Glass-like opaque surface" — an engineered opaque tinted
    surface (Colors.GLASS_BG) framed by a crisp highlight border (Colors.GLASS_BORDER).
    It delivers the sleek visual tier of Apple/Linear glassmorphic design with ZERO fake-blur lag.
    
    STRICT 80/20 USAGE RULE:
    Reserved strictly for:
      - Hero banners and prominent headers
      - Floating control / status panels
      - Modals and prominent accent cards
    Do NOT use for ordinary buttons, lists, tables, or settings rows.
    """
    DEFAULT_SURFACE = Surfaces.GLASS


class HeroCard(Card):
    """
    Mikasa AI Hero Accent Surface Card.
    
    Prominent accent banner va yuqori darajadagi e'tibor panellari uchun sirt.
    Accent border (Colors.GLASS_HERO_BORDER / Colors.BORDER_HERO) bilan ajratiladi.
    """
    DEFAULT_SURFACE = Surfaces.HERO


class OverlayCard(Card):
    """
    Mikasa AI Overlay Surface Card.
    
    Modal dialoglar, qalqib chiquvchi oynalar va toast bildirishnomalar uchun sirt.
    """
    DEFAULT_SURFACE = Surfaces.OVERLAY


class PageHero(HeroCard):
    """Sahifa bosh sarlavhasi — zamonaviy minimal banner"""
    DEFAULT_SURFACE = Surfaces.HERO

    def __init__(
        self,
        master,
        title="",
        subtitle="",
        icon="sparkles",
        accent_color=None,
        chips=None,
        surface=None,
        **kwargs,
    ):
        accent = accent_color or Colors.PRIMARY
        tier = surface or self.DEFAULT_SURFACE
        
        # Border discipline: accent highlight border
        default_border = Colors.GLASS_HERO_BORDER if accent == Colors.PRIMARY else accent
        kwargs.setdefault("border_color", default_border)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", Sizing.LARGE)
        kwargs.setdefault("fg_color", Colors.GLASS_BG)

        super().__init__(
            master=master,
            title="",
            subtitle="",
            accent_color=accent_color,
            padding=Sizing.SPACING_16,
            surface=tier,
            **kwargs,
        )
        self._surface_tier = Surfaces.HERO

        header_row = ctk.CTkFrame(self.content, fg_color="transparent")
        header_row.pack(fill="x")

        self.icon_frame = ctk.CTkFrame(
            header_row,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.BORDER,
            corner_radius=Sizing.RADIUS_BUTTON,
            width=42,
            height=42,
        )
        self.icon_frame.pack(side="left")
        self.icon_frame.pack_propagate(False)

        # Pure vector icon rendering with automatic fallback
        v_img = get_vector_icon(icon, size=20, color_dark=accent, color_light=accent, fallback="sparkles")
        self.icon_label = ctk.CTkLabel(self.icon_frame, image=v_img, text="")
        self.icon_label.pack(expand=True)

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

    def add_chip(self, parent, text, icon="circle", fg=None, text_color=None):
        tc = text_color or Colors.TEXT_SECONDARY
        chip = ctk.CTkFrame(
            parent,
            fg_color=fg or Colors.BG_CARD,
            corner_radius=Sizing.PILL,
            border_width=1,
            border_color=Colors.BORDER,
        )
        chip.pack(side="left", padx=(0, 8))

        inner = ctk.CTkFrame(chip, fg_color="transparent")
        inner.pack(padx=10, pady=3)

        if icon:
            v_img = get_vector_icon(icon, size=12, color_dark=tc, color_light=tc, fallback="circle")
            if v_img:
                ctk.CTkLabel(inner, image=v_img, text="").pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            inner,
            text=text,
            font=Fonts.TINY,
            text_color=tc,
        ).pack(side="left")
        return chip

    def update_theme(self):
        super().update_theme()
        if hasattr(self, "icon_frame") and self.icon_frame:
            self.icon_frame.configure(fg_color=Colors.BG_CARD, border_color=Colors.BORDER)
        if hasattr(self, "title_label") and self.title_label:
            self.title_label.configure(text_color=Colors.TEXT_PRIMARY)
        if hasattr(self, "subtitle_label") and self.subtitle_label:
            self.subtitle_label.configure(text_color=Colors.TEXT_MUTED)



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
                    fallback="sparkles",
                )
                if v_img:
                    image = v_img


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

        from gui.icons import VectorIconEngine
        self._raw_icon = icon if isinstance(icon, str) else ""
        self._icon_name = VectorIconEngine.resolve_icon_name(icon, fallback="sparkles") if isinstance(icon, str) else ""
        self._icon_size = icon_size
        self._variant = variant
        self._tooltip_text = tooltip
        if tooltip:
            try:
                self.after(50, lambda: Tooltip(self, tooltip))
            except Exception:
                pass

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
                "text_color": Colors.GLASS_TEXT,
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
            from gui.icons import VectorIconEngine
            self._raw_icon = icon if isinstance(icon, str) else ""
            self._icon_name = VectorIconEngine.resolve_icon_name(icon, fallback="sparkles") if isinstance(icon, str) else ""
            v_img = (
                get_vector_icon(icon, size=getattr(self, "_icon_size", 16), color_dark="#FFFFFF", color_light="#0F172A", fallback="sparkles")
                if isinstance(icon, str)
                else None
            )
            if v_img:
                kwargs["image"] = v_img

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
        kwargs.setdefault("corner_radius", Sizing.RADIUS_BUTTON)
        super().__init__(master, text="", icon=icon, width=size, height=size, **kwargs)


class CircleIconButton(GlassButton):
    """
    Doiraviy ikonka tugmasi.
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
# 3. MIKASA AI ORB (Core Intelligence Visual Component)
# ==========================================
from gui.orb import MikasaOrb

# Orqaga muvofiqlik (backward compatibility) uchun alias
AppleSiriOrb = MikasaOrb



# ==========================================
# 4. CHAT COMPONENTS (MessageBubble, AgentStep)
# ==========================================

class MessageBubble(ctk.CTkFrame):
    """
    Apple macOS / Linear style Chat Message Bubble.
    Clean distinction between User and Assistant.
    """

    def __init__(self, master, text="", role="user", timestamp="", user_name="", **kwargs):
        is_user = role == "user"

        if is_user:
            bg_color = kwargs.pop("fg_color", Colors.PRIMARY)
            border_width = 0
            border_color = Colors.PRIMARY
            text_color = "#FFFFFF"
            time_color = "#A0C4FF"
            radius = 16
            inner_padx = 14
            inner_pady = 8
        else:
            bg_color = kwargs.pop("fg_color", Colors.BG_CARD)
            border_width = 1
            border_color = Colors.BORDER
            text_color = Colors.TEXT_PRIMARY
            time_color = Colors.TEXT_MUTED
            radius = 16
            inner_padx = 14
            inner_pady = 8

        if "bg_color" not in kwargs:
            kwargs["bg_color"] = "transparent"

        super().__init__(
            master,
            fg_color=bg_color,
            corner_radius=radius,
            border_width=border_width,
            border_color=border_color,
            **kwargs,
        )

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=inner_padx, pady=inner_pady)

        # Assistant header with title, copy, and timestamp
        if not is_user:
            meta_row = ctk.CTkFrame(container, fg_color="transparent")
            meta_row.pack(fill="x", pady=(0, 4))

            sparkle_img = get_vector_icon("sparkles", size=13, color_dark=Colors.PRIMARY, color_light=Colors.PRIMARY, fallback="sparkles")
            if sparkle_img:
                ctk.CTkLabel(meta_row, image=sparkle_img, text="").pack(side="left", padx=(0, 6))

            ctk.CTkLabel(
                meta_row,
                text="Mikasa",
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
            c_img = get_vector_icon("copy", size=13, color_dark=Colors.TEXT_MUTED, color_light=Colors.TEXT_MUTED, fallback="copy")
            copy_btn = ctk.CTkButton(
                meta_row,
                text="",
                image=c_img,
                width=18,
                height=18,
                fg_color="transparent",
                hover_color=Colors.BG_HOVER,
                command=lambda t=text: self._copy_to_clipboard(t),
            )
            copy_btn.pack(side="right")
        elif timestamp or user_name:
            meta_row = ctk.CTkFrame(container, fg_color="transparent")
            meta_row.pack(fill="x", pady=(0, 2))
            if user_name:
                ctk.CTkLabel(
                    meta_row,
                    text=user_name,
                    font=(Fonts.FAMILY, 10, "bold"),
                    text_color="#E0E7FF",
                    anchor="w",
                ).pack(side="left")
            if timestamp:
                ctk.CTkLabel(
                    meta_row,
                    text=timestamp,
                    font=Fonts.TINY,
                    text_color=time_color,
                    anchor="e",
                ).pack(side="right")

        wrap = kwargs.pop("wraplength", 720 if not is_user else 540)
        self.text_label = ctk.CTkLabel(
            container,
            text=text,
            font=Fonts.BODY,
            text_color=text_color,
            wraplength=wrap,
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

    def __init__(self, master, prefix="Mikasa o'ylamoqda", **kwargs):
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = "transparent"

        prefix_text = kwargs.pop("prefix", prefix)
        if prefix_text.startswith("✦ "):
            prefix_text = prefix_text[2:]
        self._prefix = prefix_text

        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            **kwargs,
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=4, pady=4)

        sparkle_img = get_vector_icon("sparkles", size=13, color_dark=Colors.PRIMARY, color_light=Colors.PRIMARY, fallback="sparkles")
        if sparkle_img:
            ctk.CTkLabel(inner, image=sparkle_img, text="").pack(side="left", padx=(0, 6))

        self.text_label = ctk.CTkLabel(
            inner,
            text=prefix_text,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.PRIMARY,
        )
        self.text_label.pack(side="left", padx=(0, 8))

        self.dots_label = ctk.CTkLabel(
            inner,
            text=".  ",
            font=Fonts.BODY_BOLD,
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
        patterns = [".  ", ".. ", "..."]
        self._phase = (self._phase + 1) % len(patterns)
        try:
            if self.winfo_exists():
                self.dots_label.configure(text=patterns[self._phase])
                self._anim_job = self.after(350, self._animate)
        except Exception:
            pass

    def set_prefix(self, prefix: str):
        if prefix.startswith("✦ "):
            prefix = prefix[2:]
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
    check Bajarildi | sparkles O'ylash | commands Asbob | close Xato | circle Kutilmoqda
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._steps = []

    def add_step(self, step_type: str, title: str, description: str = ""):
        step_row = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=Sizing.SMALL, border_width=1, border_color=Colors.BORDER)
        step_row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(step_row, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=6)

        badge_colors = {
            "completed": (Colors.SUCCESS_SOFT, Colors.SUCCESS, "check"),
            "thought": (Colors.PRIMARY_SOFT, Colors.PRIMARY, "sparkles"),
            "tool": (Colors.INFO_SOFT, Colors.INFO, "commands"),
            "error": (Colors.DANGER_SOFT, Colors.DANGER, "close"),
            "pending": (Colors.BG_INPUT, Colors.TEXT_MUTED, "circle"),
        }
        bg, tc, icon_name = badge_colors.get(step_type, (Colors.BG_INPUT, Colors.TEXT_MUTED, "circle"))

        icon_frame = ctk.CTkFrame(inner, fg_color=bg, corner_radius=Sizing.SMALL, width=20, height=20)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        v_img = get_vector_icon(icon_name, size=11, color_dark=tc, color_light=tc, fallback="circle")
        if v_img:
            ctk.CTkLabel(icon_frame, image=v_img, text="").pack(expand=True)


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
            corner_radius=Sizing.SMALL if active else 0,
            border_width=1 if active else 0,
            border_color=Colors.BORDER_HOVER if active else Colors.SIDEBAR_BG,
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
        v_img = get_vector_icon(self._icon_name, size=18, color_dark=c_dark, color_light=c_light, fallback="circle")
        self.icon_label.configure(image=v_img, text="")


    def _on_click(self, event=None):
        if self._command:
            self._command()

    def _on_enter(self, event=None):
        if not self._active:
            self.configure(fg_color=Colors.SIDEBAR_HOVER, corner_radius=Sizing.SMALL, border_width=1, border_color=Colors.BORDER_HOVER)
            self.text_label.configure(text_color=Colors.TEXT_PRIMARY)

    def _on_leave(self, event=None):
        if not self._active:
            self.configure(fg_color="transparent", corner_radius=0, border_width=0)
            self.text_label.configure(text_color=Colors.TEXT_SECONDARY)

    def set_active(self, active: bool):
        self._active = active
        self.configure(
            fg_color=Colors.SIDEBAR_ACTIVE if active else "transparent",
            corner_radius=Sizing.SMALL if active else 0,
            border_width=1 if active else 0,
            border_color=Colors.BORDER_HOVER if active else Colors.SIDEBAR_BG,
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
# 5.1 AVATAR & ACCOUNT ROW COMPONENTS
# ==========================================

class UserAvatar(ctk.CTkFrame):
    """
    Mikasa AI Reusable Circular User Avatar.
    Supports:
    - User initials fallback (e.g. 'MA' for 'Muxammadaziz')
    - Custom image file path (with circular cropping)
    - High-DPI supersampled anti-aliasing via PIL & Lanczos
    - Memory cache for instant rendering with zero performance regression
    """
    _CACHE = {}

    @classmethod
    def _extract_initials(cls, name: str) -> str:
        if not name:
            return "U"
        clean = name.strip()
        parts = clean.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        # Single word: check if CamelCase like 'MuhammadAziz'
        uppercase = [ch for ch in clean if ch.isupper()]
        if len(uppercase) >= 2:
            return "".join(uppercase[:2])
        # Check Uzbek compound names starting with 'muxammad' or 'muhammad'
        lower = clean.lower()
        if lower.startswith("muxammad") and len(lower) > 8:
            return ("M" + lower[8]).upper()
        if lower.startswith("muhammad") and len(lower) > 8:
            return ("M" + lower[8]).upper()
        if len(clean) >= 2:
            return clean[:2].upper()
        return clean[0].upper()

    @classmethod
    def get_avatar_image(
        cls,
        name: str = "Muxammadaziz",
        image_path: str = None,
        size: int = 36,
        bg_color: str = "#1E40AF",
        fg_color: str = "#FFFFFF",
        border_color: str = "#3B82F6",
    ) -> ctk.CTkImage:
        import tkinter
        curr_root = getattr(tkinter, "_default_root", None)
        curr_root_id = id(curr_root) if curr_root is not None else None

        key = (name, image_path, size, bg_color, fg_color, border_color)
        if key in cls._CACHE:
            cached_pil, cached_ctk, cached_root_id = cls._CACHE[key]
            if cached_root_id == curr_root_id:
                return cached_ctk

        scale = 4
        canvas_size = size * scale

        if image_path and os.path.isfile(image_path):
            try:
                with Image.open(image_path) as src:
                    src = src.convert("RGBA")
                    w, h = src.size
                    min_dim = min(w, h)
                    left = (w - min_dim) // 2
                    top = (h - min_dim) // 2
                    src_cropped = src.crop((left, top, left + min_dim, top + min_dim))
                    src_scaled = src_cropped.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)

                    mask = Image.new("L", (canvas_size, canvas_size), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.ellipse([0, 0, canvas_size - 1, canvas_size - 1], fill=255)

                    pil_img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
                    pil_img.paste(src_scaled, (0, 0), mask=mask)

                    if border_color:
                        draw_border = ImageDraw.Draw(pil_img)
                        draw_border.ellipse([0, 0, canvas_size - 1, canvas_size - 1], outline=border_color, width=scale)

                    pil_img = pil_img.resize((size, size), Image.Resampling.LANCZOS)
            except Exception:
                pil_img = cls._draw_initials_pil(cls._extract_initials(name), size, bg_color, fg_color, border_color)
        else:
            initials = cls._extract_initials(name)
            pil_img = cls._draw_initials_pil(initials, size, bg_color, fg_color, border_color)

        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
        cls._CACHE[key] = (pil_img, ctk_img, curr_root_id)
        return ctk_img

    @classmethod
    def _draw_initials_pil(cls, initials: str, size: int, bg_color: str, fg_color: str, border_color: str) -> Image.Image:
        scale = 4
        canvas_size = size * scale
        img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle
        draw.ellipse([scale, scale, canvas_size - 1 - scale, canvas_size - 1 - scale], fill=bg_color, outline=border_color, width=scale if border_color else 0)

        # Typography
        font = None
        font_size = int(size * 0.44 * scale)
        for font_name in ("segoeui.ttf", "segoeuib.ttf", "arial.ttf", "arialbd.ttf"):
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except Exception:
                continue
        if font is None:
            try:
                font = ImageFont.load_default()
            except Exception:
                pass

        bbox = draw.textbbox((0, 0), initials, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = (canvas_size - text_w) / 2 - bbox[0]
        y = (canvas_size - text_h) / 2 - bbox[1]
        draw.text((x, y), initials, fill=fg_color, font=font)

        return img.resize((size, size), Image.Resampling.LANCZOS)

    def __init__(
        self,
        master,
        name: str = "Muxammadaziz",
        image_path: str = None,
        size: int = 36,
        bg_color: str = "#1E40AF",
        fg_color: str = "#FFFFFF",
        border_color: str = "#3B82F6",
        **kwargs,
    ):
        super().__init__(
            master,
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color="transparent",
            border_width=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._name = name or "Muxammadaziz"
        self._image_path = image_path
        self._size = size
        self._avatar_bg = bg_color
        self._avatar_fg = fg_color
        self._avatar_border = border_color

        self.avatar_image = self.get_avatar_image(
            name=self._name,
            image_path=self._image_path if (self._image_path and os.path.isfile(self._image_path)) else None,
            size=self._size,
            bg_color=self._avatar_bg,
            fg_color=self._avatar_fg,
            border_color=self._avatar_border,
        )
        self.avatar_label = ctk.CTkLabel(
            self,
            text="",
            image=self.avatar_image,
            fg_color="transparent",
            width=size,
            height=size,
        )
        self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")

    def set_name(self, new_name: str):
        self._name = new_name or "Muxammadaziz"
        self.avatar_image = self.get_avatar_image(
            name=self._name,
            image_path=self._image_path if (self._image_path and os.path.isfile(self._image_path)) else None,
            size=self._size,
            bg_color=self._avatar_bg,
            fg_color=self._avatar_fg,
            border_color=self._avatar_border,
        )
        self.avatar_label.configure(image=self.avatar_image, text="")


class AssistantAvatar(ctk.CTkFrame):
    """
    Mikasa AI Distinct Assistant Vector Avatar.
    Circular badge featuring the canonical sparkles vector icon.
    Visually distinct from human user avatars.
    """
    _CACHE = {}

    @classmethod
    def get_assistant_image(
        cls,
        size: int = 28,
        bg_color: str = Colors.BG_CARD,
        border_color: str = Colors.PRIMARY,
        icon_color: str = Colors.PRIMARY,
    ) -> ctk.CTkImage:
        import tkinter
        curr_root = getattr(tkinter, "_default_root", None)
        curr_root_id = id(curr_root) if curr_root is not None else None

        key = (size, bg_color, border_color, icon_color)
        if key in cls._CACHE:
            cached_pil, cached_ctk, cached_root_id = cls._CACHE[key]
            if cached_root_id == curr_root_id:
                return cached_ctk

        scale = 4
        canvas_size = size * scale
        img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 1. Circle Background & Border
        draw.ellipse(
            [scale, scale, canvas_size - 1 - scale, canvas_size - 1 - scale],
            fill=bg_color,
            outline=border_color,
            width=scale,
        )

        # 2. Vector Sparkles Icon
        try:
            sparkle_pil_light, sparkle_pil_dark = VectorIconEngine.get_pil_images(
                "sparkles", size=int(size * 0.52 * scale), color=icon_color
            )
            w, h = sparkle_pil_dark.size
            offset_x = (canvas_size - w) // 2
            offset_y = (canvas_size - h) // 2
            img.paste(sparkle_pil_dark, (offset_x, offset_y), mask=sparkle_pil_dark)
        except Exception:
            pass

        pil_final = img.resize((size, size), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=pil_final, dark_image=pil_final, size=(size, size))
        cls._CACHE[key] = (pil_final, ctk_img, curr_root_id)
        return ctk_img

    def __init__(self, master, size: int = 28, **kwargs):
        super().__init__(
            master,
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color="transparent",
            border_width=0,
            border_color=Colors.PRIMARY,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._size = size
        self.icon_img = self.get_assistant_image(size=size)
        self.icon_label = ctk.CTkLabel(
            self,
            text="",
            image=self.icon_img,
            fg_color="transparent",
            width=size,
            height=size,
        )
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")


class AccountRow(ctk.CTkFrame):
    """
    Mikasa AI Desktop Sidebar Account Row.
    Displays user avatar, display name, 'Hisob' label, and subtle chevron.
    Interactions:
    - Default: transparent surface
    - Hover: lighter surface (Colors.SIDEBAR_HOVER) + primary chevron
    - Click: opens Settings (real functionality)
    """
    def __init__(
        self,
        master,
        name: str = "Muxammadaziz",
        image_path: str = None,
        compact: bool = False,
        command: callable = None,
        **kwargs,
    ):
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.SIDEBAR_BG

        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=Sizing.RADIUS_CARD,
            border_width=0,
            border_color=Colors.SIDEBAR_BG,
            height=46,
            cursor="hand2",
            **kwargs,
        )
        self.pack_propagate(False)

        self._command = command
        self._compact = compact
        self._name = name or "Muxammadaziz"
        self._image_path = image_path
        self._is_active = False

        # Avatar
        self.avatar = UserAvatar(
            self,
            name=self._name,
            image_path=self._image_path,
            size=32,
            bg_color="#1E40AF",
            fg_color="#FFFFFF",
            border_color="#3B82F6",
        )
        self.avatar.pack(side="left", padx=(6, 8), pady=7)

        # Matn (Name + Hisob)
        self.text_frame = ctk.CTkFrame(self, fg_color="transparent")
        if not compact:
            self.text_frame.pack(side="left", fill="both", expand=True, pady=5)

        self.name_label = ctk.CTkLabel(
            self.text_frame,
            text=self._name,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.name_label.pack(fill="x", anchor="w")

        self.sub_label = ctk.CTkLabel(
            self.text_frame,
            text="Hisob",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.sub_label.pack(fill="x", anchor="w")

        # Chevron ikonka
        chevron_img = get_vector_icon("arrow_forward", size=12, color=Colors.TEXT_MUTED, fallback="arrow_forward")
        self.chevron_label = ctk.CTkLabel(
            self,
            text="",
            image=chevron_img,
            width=16,
        )
        if not compact:
            self.chevron_label.pack(side="right", padx=(4, 8))

        # Event bindings
        interactive_widgets = [
            self,
            self.text_frame,
            self.name_label,
            self.sub_label,
            self.chevron_label,
            self.avatar,
            self.avatar.avatar_label,
        ]
        for w in interactive_widgets:
            w.bind("<Button-1>", self._on_click)
            w.bind("<Button-3>", self._show_context_menu)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        attach_tooltip(self, f"Hisob: {self._name}")

    def set_compact(self, compact: bool):
        self._compact = compact
        if compact:
            if self.text_frame.winfo_manager():
                self.text_frame.pack_forget()
            if self.chevron_label.winfo_manager():
                self.chevron_label.pack_forget()
            self.avatar.pack_configure(padx=(14, 14))
            attach_tooltip(self, f"{self._name} (Hisob)")
        else:
            self.avatar.pack_configure(padx=(6, 8))
            if not self.text_frame.winfo_manager():
                self.text_frame.pack(side="left", fill="both", expand=True, pady=5)
            if not self.chevron_label.winfo_manager():
                self.chevron_label.pack(side="right", padx=(4, 8))
            attach_tooltip(self, f"Hisob: {self._name}")

    def set_active(self, active: bool):
        self._is_active = bool(active)
        if self._is_active:
            self.configure(fg_color=Colors.BG_ACTIVE, border_width=1, border_color=Colors.PRIMARY)
            self.chevron_label.configure(image=get_vector_icon("arrow_forward", size=12, color=Colors.PRIMARY, fallback="arrow_forward"))
        else:
            self.configure(fg_color="transparent", border_width=0, border_color=Colors.SIDEBAR_BG)
            self.chevron_label.configure(image=get_vector_icon("arrow_forward", size=12, color=Colors.TEXT_MUTED, fallback="arrow_forward"))

    def _on_click(self, event=None):
        self.set_active(True)
        if self._command:
            self._command()

    def _on_enter(self, event=None):
        if not self._is_active:
            self.configure(fg_color=Colors.SIDEBAR_HOVER, border_width=1, border_color=Colors.BORDER_HOVER)
            self.chevron_label.configure(image=get_vector_icon("arrow_forward", size=12, color=Colors.PRIMARY, fallback="arrow_forward"))

    def _on_leave(self, event=None):
        if not self._is_active:
            self.configure(fg_color="transparent", border_width=0, border_color=Colors.SIDEBAR_BG)
            self.chevron_label.configure(image=get_vector_icon("arrow_forward", size=12, color=Colors.TEXT_MUTED, fallback="arrow_forward"))

    def _show_context_menu(self, event):
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=Colors.BG_PANEL,
            fg=Colors.TEXT_PRIMARY,
            activebackground=Colors.PRIMARY,
            activeforeground="#FFFFFF",
            font=(Fonts.FAMILY, 9),
            bd=1,
            relief="solid",
        )
        menu.add_command(
            label=f"Hisob: {self._name}",
            command=self._on_click,
        )
        menu.add_command(
            label="Sozlamalar",
            command=self._on_click,
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def update_user_name(self, new_name: str):
        self._name = new_name or "Muxammadaziz"
        self.name_label.configure(text=self._name)
        self.avatar.set_name(self._name)
        attach_tooltip(self, f"Hisob: {self._name}")


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
        v_dot = get_vector_icon("circle", size=8, color_dark=color, color_light=color, fallback="circle")
        self.dot = ctk.CTkLabel(
            self,
            image=v_dot,
            text="",
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
        v_dot = get_vector_icon("circle", size=8, color_dark=color, color_light=color, fallback="circle")
        self.dot.configure(image=v_dot)
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
            v_img = get_vector_icon(
                icon,
                size=13,
                color_dark=text_color or Colors.TEXT_SECONDARY,
                color_light=text_color or Colors.TEXT_SECONDARY,
                fallback="info",
            )
            if v_img:
                ctk.CTkLabel(inner, image=v_img, text="").pack(side="left", padx=(0, 4))

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
            corner_radius=Sizing.PILL,
            width=56,
            height=56,
        )
        icon_frame.pack(pady=(16, 8))
        icon_frame.pack_propagate(False)

        v_img = get_vector_icon(icon, size=24, color_dark=Colors.PRIMARY, color_light=Colors.PRIMARY, fallback="sparkles")
        if v_img:
            ctk.CTkLabel(icon_frame, image=v_img, text="").pack(expand=True)


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


class LoadingSkeleton(ctk.CTkFrame):
    """
    Mikasa AI Ultra-Lightweight Loading Skeleton.
    Shows calm placeholder cards/bars while heavy content loads lazily.
    Zero fake-blur, zero CPU lag, safe timer cancellation.
    """

    def __init__(self, master, rows=4, title="Yuklanmoqda...", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._is_active = True
        self._pulse_job = None

        # Header skeleton
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 16))

        sparkle_img = get_vector_icon("sparkles", size=18, color_dark=Colors.PRIMARY, color_light=Colors.PRIMARY)
        if sparkle_img:
            self._icon_lbl = ctk.CTkLabel(header, image=sparkle_img, text="")
            self._icon_lbl.pack(side="left", padx=(0, 10))

        self.title_label = ctk.CTkLabel(
            header,
            text=title,
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.title_label.pack(side="left")

        # Skeleton cards container
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._cards = []
        for i in range(rows):
            card = ctk.CTkFrame(
                self.cards_frame,
                fg_color=Colors.BG_CARD,
                corner_radius=Sizing.CARD,
                border_width=1,
                border_color=Colors.BORDER_SUBTLE,
                height=84,
            )
            card.pack(fill="x", pady=5)
            card.pack_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=16, pady=12)

            top_bar = ctk.CTkFrame(inner, fg_color=Colors.BG_INPUT, corner_radius=4, height=14, width=160 + (i * 40) % 120)
            top_bar.pack(anchor="w", pady=(0, 8))
            top_bar.pack_propagate(False)

            sub_bar = ctk.CTkFrame(inner, fg_color=Colors.BG_INPUT, corner_radius=4, height=10, width=280)
            sub_bar.pack(anchor="w")
            sub_bar.pack_propagate(False)

            self._cards.append((card, top_bar, sub_bar))

    def set_title(self, title: str):
        """Update skeleton header title"""
        if hasattr(self, "title_label") and self.title_label.winfo_exists():
            self.title_label.configure(text=title)

    def destroy(self):
        self._is_active = False
        if self._pulse_job:
            try:
                self.after_cancel(self._pulse_job)
            except Exception:
                pass
            self._pulse_job = None
        super().destroy()


class SearchBar(ctk.CTkFrame):
    """Qidiruv maydoni — Debounced va hotkey badge bilan"""

    def __init__(self, master, placeholder="Qidirish...", shortcut="Ctrl + K", height=40, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_INPUT,
            corner_radius=Sizing.RADIUS_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            height=height,
            **kwargs,
        )
        self.pack_propagate(False)

        s_img = get_vector_icon("search", size=16, color_dark=Colors.TEXT_MUTED, color_light=Colors.TEXT_MUTED, fallback="search")
        ctk.CTkLabel(self, image=s_img, text="").pack(side="left", padx=(12, 6))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 8))

        if shortcut:
            self.shortcut_badge = ctk.CTkFrame(
                self,
                fg_color=Colors.BG_PANEL,
                corner_radius=Sizing.SMALL,
                border_width=1,
                border_color=Colors.BORDER,
            )
            self.shortcut_badge.pack(side="right", padx=(0, 8), pady=6)
            ctk.CTkLabel(
                self.shortcut_badge,
                text=shortcut,
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
            ).pack(padx=6, pady=2)
        else:
            self.shortcut_badge = None

    def clear(self):
        """Qidiruv maydonini tozalash"""
        self.entry.delete(0, "end")

    def get(self):
        """Kiritilgan matnni olish"""
        return self.entry.get()


class StatWidget(Card):
    """Statistika vidjeti"""

    def __init__(self, master, value="0", label="", icon="", color=None, **kwargs):
        color = color or Colors.PRIMARY
        super().__init__(master, padding=Sizing.SPACING_12, **kwargs)

        top = ctk.CTkFrame(self.content, fg_color="transparent")
        top.pack(fill="x")

        if icon:
            v_img = get_vector_icon(icon, size=18, color_dark=color, color_light=color, fallback="info")
            if v_img:
                ctk.CTkLabel(top, image=v_img, text="").pack(side="left")


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
            fg_color=Colors.OVERLAY_BG,
            corner_radius=Sizing.RADIUS_BUTTON,
            border_width=1,
            border_color=accent,
            **kwargs,
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        v_img = get_vector_icon(
            toast_type if toast_type in ("info", "warning", "check", "close") else "sparkles",
            size=14,
            color_dark=accent,
            color_light=accent,
            fallback="sparkles",
        )
        if v_img:
            ctk.CTkLabel(header, image=v_img, text="").pack(side="left")

        ctk.CTkLabel(header, text=title, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=6)

        c_img = get_vector_icon("close", size=12, color_dark=Colors.TEXT_MUTED, color_light=Colors.TEXT_MUTED, fallback="close")
        ctk.CTkButton(
            header,
            text="",
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


class Tooltip:
    """
    Silliq va engil Tooltip (hover matni).
    Widget ustiga sichqoncha kelganda 400ms dan so'ng paydo bo'ladi.
    """

    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self._after_id = None

        self.widget.bind("<Enter>", self._schedule_show)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<ButtonPress>", self._hide)

    def _schedule_show(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(400, self._show)

    def _cancel(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self.tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + (self.widget.winfo_width() // 2)
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

            import tkinter as tk
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.attributes("-topmost", True)

            label = tk.Label(
                tw,
                text=self.text,
                justify="left",
                background=Colors.BG_PANEL,
                foreground=Colors.TEXT_PRIMARY,
                relief="solid",
                borderwidth=1,
                font=(Fonts.FAMILY, 9),
                padx=8,
                pady=4,
            )
            label.pack()
        except Exception:
            pass

    def _hide(self, event=None):
        self._cancel()
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


def attach_tooltip(widget, text: str):
    """Har qanday widgetga tooltip ulash yordamchisi"""
    return Tooltip(widget, text)


class CommandPaletteOverlay(ctk.CTkToplevel):
    """
    Apple Spotlight / Raycast uslubidagi Command Palette (Ctrl + K).
    Tezkor qidiruv, sahifalarga o'tish va amallarni bajarish modal oynasi.
    """

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Mikasa Command Palette")
        self.geometry("560x360")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG_DARKEST)
        self.attributes("-topmost", True)

        # Markazlashtirish
        app.update_idletasks()
        ax = app.winfo_x() + (app.winfo_width() - 560) // 2
        ay = app.winfo_y() + (app.winfo_height() - 360) // 3
        self.geometry(f"560x360+{max(ax, 50)}+{max(ay, 50)}")

        self.bind("<Escape>", lambda e: self.destroy())

        # Qidiruv qatori
        search_frame = ctk.CTkFrame(self, fg_color=Colors.BG_SURFACE, corner_radius=Sizing.CARD, border_width=1, border_color=Colors.BORDER)
        search_frame.pack(fill="x", padx=16, pady=(16, 10))

        s_icon = get_vector_icon("search", size=16, color=Colors.TEXT_MUTED)
        if s_icon:
            ctk.CTkLabel(search_frame, image=s_icon, text="").pack(side="left", padx=(12, 6))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Mikasa'dan so'rang...",
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            height=40,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.search_entry.bind("<Return>", self._on_select)
        self.search_entry.bind("<Down>", self._on_arrow_down)
        self.search_entry.bind("<Up>", self._on_arrow_up)
        self.search_entry.focus_set()

        # Natijalar ro'yxati
        self.results_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Standart amallar ro'yxati
        self._commands = [
            ("voice", "Ovozli muloqot", "Mikasa bilan ovozli dialog ochish", "mic"),
            ("chat", "AI Suhbat", "Matnli xabar yozish va maslahat olish", "chat"),
            ("commands", "Buyruqlar & Asboblar", "Barcha 29 ta tool va funksiyalar katalogi", "commands"),
            ("memory", "Xotira markazi", "Profil faktlari va muloqotlar tarixi", "memory"),
            ("scheduler", "Rejalashtiruvchi", "Eslatmalar va vazifalar taqvimi", "scheduler"),
            ("plugins", "Plaginlar", "Qo'shimcha modullarni ko'rish", "plugins"),
            ("settings", "Sozlamalar", "Tizim va AI parametrlarini sozlash", "settings"),
        ]

        self._current_filtered = list(self._commands)
        self._selected_index = 0
        self._buttons = []
        self._render_results(self._current_filtered)

    def _render_results(self, items):
        self._current_filtered = items
        self._buttons.clear()
        for w in self.results_scroll.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(
                self.results_scroll,
                text="Mos buyruq topilmadi",
                font=Fonts.SMALL,
                text_color=Colors.TEXT_MUTED,
            ).pack(pady=20)
            return

        self._selected_index = max(0, min(self._selected_index, len(items) - 1))

        for idx, (page_id, title, desc, icon_name) in enumerate(items):
            is_selected = (idx == self._selected_index)
            item_btn = ctk.CTkButton(
                self.results_scroll,
                text=f"  {title} — {desc}",
                image=get_vector_icon(icon_name, size=16, color=Colors.PRIMARY),
                compound="left",
                font=Fonts.SMALL,
                fg_color=Colors.BG_HOVER if is_selected else Colors.BG_CARD,
                hover_color=Colors.BG_HOVER,
                border_width=1 if is_selected else 0,
                border_color=Colors.PRIMARY if is_selected else Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
                height=38,
                corner_radius=Sizing.SMALL,
                command=lambda pid=page_id: self._execute_item(pid),
            )
            item_btn.pack(fill="x", pady=2)
            self._buttons.append(item_btn)

    def _highlight_selected(self):
        for idx, btn in enumerate(self._buttons):
            if idx == self._selected_index:
                btn.configure(
                    fg_color=Colors.BG_HOVER,
                    border_width=1,
                    border_color=Colors.PRIMARY,
                )
            else:
                btn.configure(
                    fg_color=Colors.BG_CARD,
                    border_width=0,
                    border_color=Colors.BORDER,
                )

    def _on_arrow_down(self, event=None):
        if self._current_filtered:
            self._selected_index = (self._selected_index + 1) % len(self._current_filtered)
            self._highlight_selected()
        return "break"

    def _on_arrow_up(self, event=None):
        if self._current_filtered:
            self._selected_index = (self._selected_index - 1) % len(self._current_filtered)
            self._highlight_selected()
        return "break"

    def _on_search(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        q = self.search_entry.get().strip().lower()
        if not q:
            self._selected_index = 0
            self._render_results(self._commands)
            return

        filtered = [
            c for c in self._commands
            if q in c[1].lower() or q in c[2].lower() or q in c[0].lower()
        ]
        self._selected_index = 0
        self._render_results(filtered)

    def _on_select(self, event=None):
        if self._current_filtered and 0 <= self._selected_index < len(self._current_filtered):
            self._execute_item(self._current_filtered[self._selected_index][0])

    def _execute_item(self, page_id):
        self.destroy()
        if hasattr(self.app, "navigate_to"):
            self.app.navigate_to(page_id)


class WindowControls(ctk.CTkFrame):
    """
    Mikasa AI Desktop Native Window Controls.
    Yuqori o'ng burchakdagi ixcham desktop boshqaruv paneli:
    Minimize (Kichraytirish), Maximize/Restore (Kattalashtirish/Tiklash), Close (Yopish).
    """

    def __init__(self, master, app=None, height=36, btn_width=44, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=0,
            height=height,
            **kwargs,
        )
        self.app = app
        self.btn_width = btn_width
        self.btn_height = height
        self._is_maximized = False

        self._build_controls()

    def _build_controls(self):
        # 1. Minimize Button
        min_icon = get_vector_icon("minimize", size=14, color=Colors.TEXT_MUTED)
        self.min_btn = ctk.CTkButton(
            self,
            text="",
            image=min_icon,
            width=self.btn_width,
            height=self.btn_height,
            corner_radius=0,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            command=self._on_minimize,
        )
        self.min_btn.pack(side="left", fill="y")
        Tooltip(self.min_btn, "Kichraytirish")

        # 2. Maximize / Restore Button
        self._max_icon = get_vector_icon("maximize", size=13, color=Colors.TEXT_MUTED)
        self._restore_icon = get_vector_icon("restore", size=13, color=Colors.TEXT_MUTED)

        self.max_btn = ctk.CTkButton(
            self,
            text="",
            image=self._max_icon,
            width=self.btn_width,
            height=self.btn_height,
            corner_radius=0,
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            command=self._on_toggle_maximize,
        )
        self.max_btn.pack(side="left", fill="y")
        self.max_tooltip = Tooltip(self.max_btn, "Kattalashtirish")

        # 3. Close Button
        self._close_icon_normal = get_vector_icon("close", size=13, color=Colors.TEXT_MUTED)
        self._close_icon_hover = get_vector_icon("close", size=13, color="#FFFFFF")

        self.close_btn = ctk.CTkButton(
            self,
            text="",
            image=self._close_icon_normal,
            width=self.btn_width,
            height=self.btn_height,
            corner_radius=0,
            fg_color="transparent",
            hover_color="#DC2626",
            command=self._on_close,
        )
        self.close_btn.pack(side="left", fill="y")
        Tooltip(self.close_btn, "Yopish")

        # Close button hover icon switch (oq rangga o'tadi)
        self.close_btn.bind(
            "<Enter>",
            lambda e: self.close_btn.configure(image=self._close_icon_hover),
            add="+",
        )
        self.close_btn.bind(
            "<Leave>",
            lambda e: self.close_btn.configure(image=self._close_icon_normal),
            add="+",
        )

    def _on_minimize(self):
        if self.app:
            try:
                self.app.iconify()
            except Exception:
                try:
                    self.app.state("iconic")
                except Exception:
                    pass

    def _on_toggle_maximize(self):
        if self.app and hasattr(self.app, "_toggle_maximize"):
            self.app._toggle_maximize()
        else:
            self._is_maximized = not self._is_maximized
            self.sync_maximized_state(self._is_maximized)

    def _on_close(self):
        if self.app:
            if hasattr(self.app, "_on_closing"):
                self.app._on_closing()
            else:
                self.app.destroy()

    def sync_maximized_state(self, is_maximized: bool):
        """Window maximized holatiga qarab icon va tooltipni yangilash"""
        self._is_maximized = is_maximized
        if is_maximized:
            self.max_btn.configure(image=self._restore_icon)
            if hasattr(self, "max_tooltip") and self.max_tooltip:
                self.max_tooltip.text = "Tiklash"
        else:
            self.max_btn.configure(image=self._max_icon)
            if hasattr(self, "max_tooltip") and self.max_tooltip:
                self.max_tooltip.text = "Kattalashtirish"

