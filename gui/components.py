# ========== components.py ==========
# Mikasa AI — qayta ishlatiladigan UI komponentlar

import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing


class GlassCard(ctk.CTkFrame):
    """Apple uslubidagi zamonaviy minimal karta"""

    def __init__(
        self,
        master,
        title="",
        subtitle="",
        padding=None,
        accent_color=None,
        **kwargs,
    ):
        padding = Sizing.CARD_PADDING if padding is None else padding
        accent_color = accent_color or Colors.PRIMARY
        
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_DARK

        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizing.CARD_RADIUS,
            border_width=1,
            border_color=Colors.BORDER,
            **kwargs,
        )

        self._padding = padding
        self._accent_color = accent_color

        if title or subtitle:
            self.header = ctk.CTkFrame(self, fg_color="transparent")
            self.header.pack(fill="x", padx=padding, pady=(padding, 8))

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

            if subtitle:
                self.subtitle_label = ctk.CTkLabel(
                    self.header,
                    text=subtitle,
                    font=Fonts.SMALL,
                    text_color=Colors.TEXT_MUTED,
                    anchor="w",
                    justify="left",
                    wraplength=900,
                )
                self.subtitle_label.pack(fill="x", pady=(4, 0))

            ctk.CTkFrame(
                self,
                fg_color=Colors.BORDER,
                height=1,
            ).pack(fill="x", padx=padding, pady=(0, padding))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=padding, pady=(0, padding))


class InfoChip(ctk.CTkFrame):
    """Kichik pill badge"""

    def __init__(
        self,
        master,
        text,
        icon="",
        fg_color=None,
        text_color=None,
        **kwargs,
    ):
        fg_color = fg_color or Colors.BG_PANEL
        text_color = text_color or Colors.TEXT_SECONDARY
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_CARD
        super().__init__(master, fg_color=fg_color, corner_radius=12, **kwargs)

        self._icon = icon
        self.label = ctk.CTkLabel(
            self,
            text=f"{icon} {text}" if icon else text,
            font=Fonts.TINY,
            text_color=text_color,
        )
        self.label.pack(padx=10, pady=5)

    def set_text(self, text):
        self.label.configure(text=f"{self._icon} {text}" if self._icon else text)


class PageHero(GlassCard):
    """Sahifa sarlavhasi uchun katta intro blok"""

    def __init__(
        self,
        master,
        title,
        subtitle="",
        icon="✨",
        accent_color=None,
        chips=None,
        **kwargs,
    ):
        accent_color = accent_color or Colors.PRIMARY
        super().__init__(
            master,
            padding=Sizing.CARD_PADDING + 2,
            accent_color=accent_color,
            **kwargs,
        )

        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="x")

        left = ctk.CTkFrame(body, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.pack(side="right", anchor="ne")

        icon_wrap = ctk.CTkFrame(
            left,
            fg_color=Colors.BG_ACCENT,
            corner_radius=16,
            width=50 if Sizing.SIDEBAR_WIDTH_EXPANDED < 120 else 58,
            height=50 if Sizing.SIDEBAR_WIDTH_EXPANDED < 120 else 58,
            border_width=1,
            border_color=accent_color,
            bg_color=Colors.BG_CARD,
        )
        icon_wrap.pack(side="left", padx=(0, 14))
        icon_wrap.pack_propagate(False)

        ctk.CTkLabel(
            icon_wrap,
            text=icon,
            font=(Fonts.FAMILY, 28),
            text_color=accent_color,
        ).pack(expand=True)

        text_wrap = ctk.CTkFrame(left, fg_color="transparent")
        text_wrap.pack(side="left", fill="x", expand=True)

        self.title_label = ctk.CTkLabel(
            text_wrap,
            text=title,
            font=Fonts.HEADING_1,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.subtitle_label = ctk.CTkLabel(
            text_wrap,
            text=subtitle,
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=800,
        )
        self.subtitle_label.pack(fill="x", pady=(4, 0))

        self.meta = ctk.CTkFrame(text_wrap, fg_color="transparent")
        self.meta.pack(fill="x", pady=(12, 0))

        self.actions = right

        if chips:
            for chip in chips:
                if isinstance(chip, tuple):
                    self.add_chip(*chip)
                else:
                    self.add_chip(str(chip))

    def add_chip(
        self,
        text,
        icon="",
        fg_color=None,
        text_color=None,
    ):
        chip = InfoChip(
            self.meta,
            text=text,
            icon=icon,
            fg_color=fg_color or Colors.BG_PANEL,
            text_color=text_color or Colors.TEXT_SECONDARY,
        )
        chip.pack(side="left", padx=(0, 6))
        return chip


class EmptyState(ctk.CTkFrame):
    """Bo'sh holatni bir xil ko'rsatish"""

    def __init__(self, master, icon="✨", title="", description="", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self,
            text=icon,
            font=(Fonts.FAMILY, 34),
            text_color=Colors.TEXT_MUTED,
        ).pack(pady=(12, 6))

        ctk.CTkLabel(
            self,
            text=title,
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_PRIMARY,
        ).pack()

        ctk.CTkLabel(
            self,
            text=description,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            justify="center",
            wraplength=480,
        ).pack(pady=(6, 0))


class StatusBadge(ctk.CTkFrame):
    """Holat ko'rsatgich — dot + text (Apple capsule badge)"""

    def __init__(self, master, status="online", text="", **kwargs):
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_DARKEST
        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=999,
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


class GlassButton(ctk.CTkButton):
    """Apple Glassmorphism tugma — frosted shisha fon, 1px hoshiya va yorug'lik hoveri"""

    def __init__(
        self,
        master,
        text="",
        icon="",
        size=None,
        fg_color=None,
        hover_color=None,
        border_color=None,
        border_hover_color=None,
        border_width=1,
        corner_radius=None,
        **kwargs,
    ):
        display = f"{icon}  {text}".strip() if icon and text else (icon or text)
        fg_col = fg_color or Colors.GLASS_BG
        h_col = hover_color or Colors.GLASS_BG_HOVER
        b_col = border_color or Colors.GLASS_BORDER
        b_hover = border_hover_color or Colors.GLASS_BORDER_HOVER
        radius = corner_radius if corner_radius is not None else Sizing.BUTTON_RADIUS
        height = size if size else kwargs.pop("height", Sizing.BUTTON_HEIGHT)
        width = size if size else kwargs.pop("width", 100)

        super().__init__(
            master,
            text=display,
            font=kwargs.pop("font", Fonts.BODY),
            fg_color=fg_col,
            hover_color=h_col,
            text_color=kwargs.pop("text_color", Colors.GLASS_TEXT),
            border_width=border_width,
            border_color=b_col,
            corner_radius=radius,
            height=height,
            width=width,
            **kwargs,
        )

        self._normal_border = b_col
        self._hover_border = b_hover
        self._current_icon = icon
        self._current_text = text
        self._ensure_centering()

        # Dynamic frosted glass border highlight on hover
        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")

    def _ensure_centering(self):
        try:
            if hasattr(self, "_text_label") and self._text_label is not None:
                self._text_label.grid(row=0, column=0, rowspan=5, columnspan=5, sticky="nsew")
                for r in range(5):
                    self.grid_rowconfigure(r, weight=1)
                for c in range(5):
                    self.grid_columnconfigure(c, weight=1)
        except Exception:
            pass

    def configure(self, require_redraw=False, **kwargs):
        if "icon" in kwargs or "text" in kwargs:
            icon = kwargs.pop("icon", getattr(self, "_current_icon", ""))
            text = kwargs.pop("text", getattr(self, "_current_text", ""))
            self._current_icon = icon
            self._current_text = text
            kwargs["text"] = f"{icon}  {text}".strip() if icon and text else (icon or text)
        if "border_color" in kwargs:
            self._normal_border = kwargs["border_color"]
        super().configure(require_redraw=require_redraw, **kwargs)
        self._ensure_centering()

    def _on_enter(self, event=None):
        try:
            super().configure(border_color=self._hover_border)
        except Exception:
            pass

    def _on_leave(self, event=None):
        try:
            super().configure(border_color=self._normal_border)
        except Exception:
            pass


class CircleIconButton(GlassButton):
    """Apple dumaloq shisha icon tugma (Action / Attach / Mic / Toolbar)"""

    def __init__(
        self,
        master,
        icon="",
        size=38,
        tooltip="",
        fg_color=None,
        hover_color=None,
        border_color=None,
        border_hover_color=None,
        text_color=None,
        **kwargs,
    ):
        radius = size // 2
        font = kwargs.pop("font", (Fonts.FAMILY, 15))
        super().__init__(
            master,
            text="",
            icon=icon,
            size=size,
            corner_radius=radius,
            font=font,
            fg_color=fg_color,
            hover_color=hover_color,
            border_color=border_color,
            border_hover_color=border_hover_color,
            text_color=text_color,
            **kwargs,
        )
        self._tooltip = tooltip


class GlowButton(ctk.CTkButton):
    """Asosiy CTA tugma — Apple Blue Hero Action with subtle glass border"""

    def __init__(self, master, text="", icon="", **kwargs):
        display = f"{icon}  {text}".strip() if icon and text else (icon or text)
        fg_col = kwargs.pop("fg_color", Colors.GLASS_HERO_BG)
        h_col = kwargs.pop("hover_color", Colors.GLASS_HERO_HOVER)
        b_col = kwargs.pop("border_color", Colors.GLASS_HERO_BORDER)
        super().__init__(
            master,
            text=display,
            font=kwargs.pop("font", Fonts.BODY_BOLD),
            fg_color=fg_col,
            hover_color=h_col,
            text_color=kwargs.pop("text_color", Colors.TEXT_PRIMARY),
            border_width=kwargs.pop("border_width", 1),
            border_color=b_col,
            corner_radius=kwargs.pop("corner_radius", Sizing.BUTTON_RADIUS),
            height=kwargs.pop("height", Sizing.BUTTON_HEIGHT),
            **kwargs,
        )
        self._ensure_centering()

    def _ensure_centering(self):
        try:
            if hasattr(self, "_text_label") and self._text_label is not None:
                self._text_label.grid(row=0, column=0, rowspan=5, columnspan=5, sticky="nsew")
                for r in range(5):
                    self.grid_rowconfigure(r, weight=1)
                for c in range(5):
                    self.grid_columnconfigure(c, weight=1)
        except Exception:
            pass

    def configure(self, require_redraw=False, **kwargs):
        super().configure(require_redraw=require_redraw, **kwargs)
        self._ensure_centering()


class SecondaryButton(GlassButton):
    """Ikkinchi darajali tugma — Apple Glass Capsule"""

    def __init__(self, master, text="", icon="", **kwargs):
        super().__init__(
            master,
            text=text,
            icon=icon,
            font=kwargs.pop("font", Fonts.BODY),
            **kwargs,
        )


class IconButton(GlassButton):
    """Icon tugma — toolbar va kartalar uchun shisha tugma"""

    def __init__(self, master, icon="", tooltip="", size=38, **kwargs):
        font = kwargs.pop("font", (Fonts.FAMILY, 15))
        super().__init__(
            master,
            icon=icon,
            size=size,
            font=font,
            corner_radius=kwargs.pop("corner_radius", Sizing.BUTTON_RADIUS),
            **kwargs,
        )
        self._tooltip = tooltip


class SearchBar(ctk.CTkFrame):
    """Qidiruv paneli"""

    def __init__(self, master, placeholder="Qidirish...", command=None, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_PANEL,
            corner_radius=Sizing.INPUT_RADIUS,
            border_width=1,
            border_color=Colors.BORDER,
            height=Sizing.INPUT_HEIGHT,
            **kwargs,
        )
        self.pack_propagate(False)

        self.icon = ctk.CTkLabel(
            self,
            text="🔍",
            font=(Fonts.FAMILY, 13),
            text_color=Colors.TEXT_MUTED,
            width=32,
        )
        self.icon.pack(side="left", padx=(10, 0))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            height=Sizing.INPUT_HEIGHT - 4,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=4)

        self.clear_btn = ctk.CTkButton(
            self,
            text="✕",
            width=28,
            height=28,
            font=(Fonts.FAMILY, 11),
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_MUTED,
            corner_radius=999,
            command=self.clear,
        )
        self.clear_btn.pack(side="right", padx=8)

        if command:
            self.entry.bind("<Return>", lambda e: command(self.get()))

    def get(self):
        return self.entry.get()

    def clear(self):
        self.entry.delete(0, "end")


class StatWidget(ctk.CTkFrame):
    """Statistika widget — Apple uslubidagi nafis raqamli karta"""

    def __init__(self, master, value="0", label="", icon="", color=None, **kwargs):
        color = color or Colors.PRIMARY
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_DARK

        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizing.CARD_RADIUS,
            border_width=1,
            border_color=Colors.BORDER,
            **kwargs,
        )

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 6))

        self.icon_label = ctk.CTkLabel(
            top,
            text=icon,
            font=(Fonts.FAMILY, 18),
            text_color=color,
            width=24,
        )
        self.icon_label.pack(side="left")

        self.desc_label = ctk.CTkLabel(
            top,
            text=label.upper(),
            font=(Fonts.FAMILY, 10, "bold"),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.desc_label.pack(side="left", padx=(8, 0), fill="x", expand=True)

        self.value_label = ctk.CTkLabel(
            self,
            text=str(value),
            font=(Fonts.FAMILY, 24, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.value_label.pack(fill="x", padx=16, pady=(0, 14))

        self._color = color

    def set_value(self, value):
        self.value_label.configure(text=str(value))


class MessageBubble(ctk.CTkFrame):
    """Apple macOS / iMessage uslubidagi toza chat xabar pufakchasi"""

    def __init__(self, master, text="", role="user", timestamp="", **kwargs):
        is_user = role == "user"

        # Apple styling:
        # Foydalanuvchi: boy ko'k (#0A84FF), oq matn, hoshiyasiz, radius 16
        # Mikasa: chuqur grafit (#181820), nozik hoshiya (#242430), radius 16
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

        # Assistant uchun ixcham mikrosarlavha (✦ Mikasa va vaqt)
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
                ).pack(side="right")
        elif timestamp:
            # User uchun burchakda vaqt
            meta_row = ctk.CTkFrame(container, fg_color="transparent")
            meta_row.pack(fill="x", pady=(0, 2))
            ctk.CTkLabel(
                meta_row,
                text=timestamp,
                font=Fonts.TINY,
                text_color=time_color,
                anchor="e",
            ).pack(side="right")

        # Xabar matni
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


class TypingBubble(ctk.CTkFrame):
    """
    Apple Intelligence uslubidagi animatsion pufakcha.
    AI o'ylayotgan yoki javob yozayotgan paytda ko'rsatiladi:
    'yozyapti .', 'yozyapti . .', 'yozyapti . . .'
    """

    def __init__(self, master, prefix="yozyapti", **kwargs):
        if "bg_color" not in kwargs:
            kwargs["bg_color"] = Colors.BG_SURFACE

        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
            **kwargs,
        )
        self._prefix = prefix
        self._step = 0
        self._anim_id = None
        self._is_running = True

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(padx=14, pady=10)

        # Sparkle ikonka
        self.icon_label = ctk.CTkLabel(
            body,
            text="✦",
            font=(Fonts.FAMILY, 14, "bold"),
            text_color=Colors.PRIMARY,
        )
        self.icon_label.pack(side="left", padx=(0, 8))

        # Matn va nuqtalar
        self.text_label = ctk.CTkLabel(
            body,
            text=f"{self._prefix} .",
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.text_label.pack(side="left")

        self._animate()

    def set_prefix(self, prefix):
        self._prefix = prefix
        try:
            if self.winfo_exists():
                self.text_label.configure(text=f"{self._prefix} .")
        except Exception:
            pass

    def _animate(self):
        if not self._is_running:
            return
        dots = [" .", " . .", " . . ."]
        self._step = (self._step + 1) % len(dots)
        try:
            if self.winfo_exists():
                self.text_label.configure(text=f"{self._prefix}{dots[self._step]}")
                self._anim_id = self.after(350, self._animate)
        except Exception:
            pass

    def stop(self):
        self._is_running = False
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

    def destroy(self):
        self.stop()
        super().destroy()


class NavItem(ctk.CTkFrame):
    """Apple macOS uslubidagi sidebar navigatsiya elementi"""

    def __init__(
        self,
        master,
        icon="",
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
            corner_radius=8 if active else 0,
            height=42,
            cursor="hand2",
            **kwargs,
        )
        self.pack_propagate(False)

        self._command = command
        self._active = active
        self._compact = compact

        # Chap tomondagi nozik vertikal indikator
        self.indicator = ctk.CTkFrame(
            self,
            fg_color=Colors.SIDEBAR_INDICATOR if active else "transparent",
            width=3,
            corner_radius=0,
        )
        self.indicator.pack(side="left", fill="y", padx=(2, 6), pady=6)

        # To'g'ridan-to'g'ri toza ikonka (ortiqcha kvadrat konteynerlarsiz)
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=Fonts.NAV_ICON,
            text_color=Colors.PRIMARY if active else Colors.TEXT_SECONDARY,
            width=28,
        )
        self.icon_label.pack(side="left", padx=(2, 6))

        self.text_label = ctk.CTkLabel(
            self,
            text=label,
            font=Fonts.NAV_LABEL,
            text_color=Colors.TEXT_PRIMARY if active else Colors.TEXT_SECONDARY,
            anchor="w",
        )
        if not compact:
            self.text_label.pack(side="left", fill="x", expand=True, padx=(0, 8))

        for widget in [
            self,
            self.icon_label,
            self.text_label,
            self.indicator,
        ]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

        self.set_compact(compact)

    def _on_click(self, event=None):
        if self._command:
            self._command()

    def _on_enter(self, event=None):
        if not self._active:
            self.configure(fg_color=Colors.SIDEBAR_HOVER, corner_radius=8)
            self.text_label.configure(text_color=Colors.TEXT_PRIMARY)

    def _on_leave(self, event=None):
        if not self._active:
            self.configure(fg_color="transparent", corner_radius=0)
            self.text_label.configure(text_color=Colors.TEXT_SECONDARY)

    def set_active(self, active):
        self._active = active
        self.configure(
            fg_color=Colors.SIDEBAR_ACTIVE if active else "transparent",
            corner_radius=8 if active else 0,
        )
        self.indicator.configure(
            fg_color=Colors.SIDEBAR_INDICATOR if active else "transparent"
        )
        self.icon_label.configure(
            text_color=Colors.PRIMARY if active else Colors.TEXT_SECONDARY
        )
        self.text_label.configure(
            text_color=Colors.TEXT_PRIMARY if active else Colors.TEXT_SECONDARY
        )

    def set_compact(self, compact):
        self._compact = compact
        self.configure(height=38 if compact else 42)
        if compact:
            self.text_label.pack_forget()
            self.indicator.pack_configure(padx=(1, 2))
        else:
            if not self.text_label.winfo_manager():
                self.text_label.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.indicator.pack_configure(padx=(2, 6))


class ProgressRing(ctk.CTkFrame):
    """Progress ko'rsatkichi"""

    def __init__(self, master, value=0, max_value=100, label="", size=60, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._value = value
        self._max = max_value

        self.progress = ctk.CTkProgressBar(
            self,
            width=size,
            height=6,
            progress_color=Colors.PRIMARY,
            fg_color=Colors.BG_DARK,
            corner_radius=3,
        )
        self.progress.set(value / max_value if max_value > 0 else 0)
        self.progress.pack(pady=(4, 2))

        self.value_label = ctk.CTkLabel(
            self,
            text=f"{value}/{max_value}",
            font=Fonts.TINY,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.value_label.pack()

        if label:
            self.name_label = ctk.CTkLabel(
                self,
                text=label,
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
            )
            self.name_label.pack()

    def set_value(self, value, max_value=None):
        if max_value is not None:
            self._max = max_value
        self._value = value
        ratio = value / self._max if self._max > 0 else 0
        self.progress.set(ratio)
        self.value_label.configure(text=f"{value}/{self._max}")


class ToastNotification(ctk.CTkFrame):
    """
    Silliq paydo bo'luvchi va avtomatik yo'qoluvchi proaktiv bildirishnoma (Toast).
    """

    def __init__(
        self,
        master,
        message: str,
        title: str = "Mikasa AI",
        duration: int = 4500,
        accent_color: str = None,
        **kwargs,
    ):
        accent_color = accent_color or Colors.PRIMARY
        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=accent_color,
            **kwargs,
        )

        self._duration = duration

        # Content frame
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        # Header row
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            header,
            text="✨",
            font=(Fonts.FAMILY, 12),
            text_color=accent_color,
            width=18,
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=title,
            font=Fonts.SUBTITLE,
            text_color=Colors.TEXT_PRIMARY,
        ).pack(side="left", padx=4)

        close_btn = ctk.CTkButton(
            header,
            text="✕",
            font=(Fonts.FAMILY, 10),
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=Colors.BG_DARK,
            text_color=Colors.TEXT_MUTED,
            command=self.dismiss,
        )
        close_btn.pack(side="right")

        # Message
        msg_label = ctk.CTkLabel(
            inner,
            text=message,
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
            wraplength=280,
            justify="left",
        )
        msg_label.pack(fill="x")

        # Joylashtirish va avtomatik yopilish
        self.place(relx=0.98, rely=0.96, anchor="se")
        self.after(self._duration, self.dismiss)

    def dismiss(self):
        """Bildirishnomani yopish"""
        try:
            self.destroy()
        except Exception:
            pass


def show_toast(root_widget, message: str, title: str = "Mikasa AI", duration: int = 4500):
    """Xavfsiz Toast chiqarish funksiyasi"""
    try:
        root_widget.after(0, lambda: ToastNotification(root_widget, message, title=title, duration=duration))
    except Exception as e:
        pass

