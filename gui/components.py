# ========== components.py ==========
# Mikasa AI — Qayta ishlatiladigan UI komponentlar
# GlassCard, StatusBadge, IconButton, GlowButton, SearchBar, StatWidget

import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing


class GlassCard(ctk.CTkFrame):
    """Glassmorphism effektli karta"""
    
    def __init__(self, master, title="", padding=16, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_CARD,
            corner_radius=Sizing.CARD_RADIUS,
            border_width=1,
            border_color=Colors.BORDER,
            **kwargs
        )
        
        self._padding = padding
        
        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=Fonts.HEADING_3,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w"
            )
            self.title_label.pack(
                fill="x", padx=padding, 
                pady=(padding, 8)
            )
        
        # Kontent konteyner
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(
            fill="both", expand=True,
            padx=padding, pady=(0, padding)
        )


class StatusBadge(ctk.CTkFrame):
    """Holat ko'rsatgich — dot + text"""
    
    STATUS_COLORS = {
        "online": Colors.SUCCESS,
        "offline": Colors.DANGER,
        "busy": Colors.WARNING,
        "idle": Colors.TEXT_MUTED,
        "listening": Colors.PRIMARY,
        "speaking": Colors.SECONDARY,
    }
    
    def __init__(self, master, status="online", text="", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        color = self.STATUS_COLORS.get(status, Colors.TEXT_MUTED)
        
        self.dot = ctk.CTkLabel(
            self, text="●", 
            font=(Fonts.FAMILY, 10),
            text_color=color,
            width=14
        )
        self.dot.pack(side="left", padx=(0, 4))
        
        display_text = text or status.capitalize()
        self.label = ctk.CTkLabel(
            self, text=display_text,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY
        )
        self.label.pack(side="left")
        
        self._status = status
    
    def set_status(self, status, text=None):
        """Holatni yangilash"""
        self._status = status
        color = self.STATUS_COLORS.get(status, Colors.TEXT_MUTED)
        self.dot.configure(text_color=color)
        if text:
            self.label.configure(text=text)
        else:
            self.label.configure(text=status.capitalize())


class IconButton(ctk.CTkButton):
    """Icon tugma — sidebar va toolbar uchun"""
    
    def __init__(self, master, icon="", tooltip="", size=40, **kwargs):
        super().__init__(
            master,
            text=icon,
            width=size,
            height=size,
            font=(Fonts.FAMILY, 16),
            fg_color="transparent",
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_SECONDARY,
            corner_radius=Sizing.BUTTON_RADIUS,
            **kwargs
        )
        self._tooltip = tooltip


class GlowButton(ctk.CTkButton):
    """Yaltiroq tugma — asosiy harakatlar uchun"""
    
    def __init__(self, master, text="", icon="", **kwargs):
        display = f"{icon}  {text}" if icon else text
        super().__init__(
            master,
            text=display,
            font=Fonts.BODY_BOLD,
            fg_color=Colors.PRIMARY_DARK,
            hover_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Sizing.BUTTON_RADIUS,
            height=Sizing.BUTTON_HEIGHT,
            **kwargs
        )


class SecondaryButton(ctk.CTkButton):
    """Ikkinchi darajali tugma"""
    
    def __init__(self, master, text="", icon="", **kwargs):
        display = f"{icon}  {text}" if icon else text
        super().__init__(
            master,
            text=display,
            font=Fonts.BODY,
            fg_color=Colors.BG_CARD,
            hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_SECONDARY,
            border_width=1,
            border_color=Colors.BORDER,
            corner_radius=Sizing.BUTTON_RADIUS,
            height=Sizing.BUTTON_HEIGHT,
            **kwargs
        )


class SearchBar(ctk.CTkFrame):
    """Qidiruv paneli"""
    
    def __init__(self, master, placeholder="Qidirish...", 
                 command=None, **kwargs):
        super().__init__(
            master, fg_color=Colors.BG_INPUT,
            corner_radius=Sizing.INPUT_RADIUS,
            border_width=1, border_color=Colors.BORDER,
            height=Sizing.INPUT_HEIGHT,
            **kwargs
        )
        self.pack_propagate(False)
        
        # Search icon
        self.icon = ctk.CTkLabel(
            self, text="🔍",
            font=(Fonts.FAMILY, 13),
            text_color=Colors.TEXT_MUTED,
            width=30
        )
        self.icon.pack(side="left", padx=(10, 0))
        
        # Input
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            height=Sizing.INPUT_HEIGHT - 4
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=4)
        
        if command:
            self.entry.bind("<Return>", lambda e: command(self.get()))
    
    def get(self):
        return self.entry.get()
    
    def clear(self):
        self.entry.delete(0, "end")


class StatWidget(ctk.CTkFrame):
    """Statistika widget — raqam + tavsif"""
    
    def __init__(self, master, value="0", label="", 
                 icon="", color=Colors.PRIMARY, **kwargs):
        super().__init__(
            master, fg_color=Colors.BG_CARD,
            corner_radius=Sizing.CARD_RADIUS,
            border_width=1, border_color=Colors.BORDER,
            **kwargs
        )
        
        # Icon
        if icon:
            self.icon_label = ctk.CTkLabel(
                self, text=icon,
                font=(Fonts.FAMILY, 22),
                text_color=color
            )
            self.icon_label.pack(pady=(14, 2))
        
        # Qiymat
        self.value_label = ctk.CTkLabel(
            self, text=str(value),
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY
        )
        self.value_label.pack(pady=(4, 0))
        
        # Tavsif
        self.desc_label = ctk.CTkLabel(
            self, text=label,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY
        )
        self.desc_label.pack(pady=(0, 14))
        
        self._color = color
    
    def set_value(self, value):
        self.value_label.configure(text=str(value))


class MessageBubble(ctk.CTkFrame):
    """Chat xabar pufakchasi"""
    
    def __init__(self, master, text="", role="user", 
                 timestamp="", **kwargs):
        is_user = role == "user"
        
        super().__init__(
            master,
            fg_color=Colors.BG_INPUT if is_user else Colors.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER if is_user else Colors.PRIMARY_DARK,
            **kwargs
        )
        
        # Xabar matni
        self.text_label = ctk.CTkLabel(
            self, text=text,
            font=Fonts.BODY,
            text_color=Colors.TEXT_PRIMARY,
            wraplength=450,
            justify="left",
            anchor="w"
        )
        self.text_label.pack(
            fill="x", padx=14, 
            pady=(10, 4)
        )
        
        # Vaqt
        if timestamp:
            self.time_label = ctk.CTkLabel(
                self, text=timestamp,
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
                anchor="e" if is_user else "w"
            )
            self.time_label.pack(
                fill="x", padx=14, 
                pady=(0, 8)
            )


class NavItem(ctk.CTkFrame):
    """Sidebar navigatsiya elementar"""
    
    def __init__(self, master, icon="", label="", 
                 active=False, command=None, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.SIDEBAR_ACTIVE if active else "transparent",
            corner_radius=8,
            height=48,
            cursor="hand2",
            **kwargs
        )
        self.pack_propagate(False)
        
        self._command = command
        self._active = active
        self._icon = icon
        self._label = label
        
        # Aktiv indikator (chap chiziq)
        self.indicator = ctk.CTkFrame(
            self,
            fg_color=Colors.SIDEBAR_INDICATOR if active else "transparent",
            width=3,
            corner_radius=2
        )
        self.indicator.pack(side="left", fill="y", padx=(0, 4))
        
        # Icon
        self.icon_label = ctk.CTkLabel(
            self, text=icon,
            font=Fonts.NAV_ICON,
            text_color=Colors.PRIMARY if active else Colors.TEXT_MUTED,
            width=40
        )
        self.icon_label.pack(side="left", padx=(8, 4))
        
        # Label
        self.text_label = ctk.CTkLabel(
            self, text=label,
            font=Fonts.NAV_LABEL,
            text_color=Colors.TEXT_PRIMARY if active else Colors.TEXT_SECONDARY,
            anchor="w"
        )
        self.text_label.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # Barcha elementlarga click event
        for widget in [self, self.icon_label, self.text_label, self.indicator]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
    
    def _on_click(self, event=None):
        if self._command:
            self._command()
    
    def _on_enter(self, event=None):
        if not self._active:
            self.configure(fg_color=Colors.SIDEBAR_HOVER)
    
    def _on_leave(self, event=None):
        if not self._active:
            self.configure(fg_color="transparent")
    
    def set_active(self, active):
        self._active = active
        self.configure(
            fg_color=Colors.SIDEBAR_ACTIVE if active else "transparent"
        )
        self.indicator.configure(
            fg_color=Colors.SIDEBAR_INDICATOR if active else "transparent"
        )
        self.icon_label.configure(
            text_color=Colors.PRIMARY if active else Colors.TEXT_MUTED
        )
        self.text_label.configure(
            text_color=Colors.TEXT_PRIMARY if active else Colors.TEXT_SECONDARY
        )


class ProgressRing(ctk.CTkFrame):
    """Doiraviy progress — API limit va boshqalar uchun"""
    
    def __init__(self, master, value=0, max_value=100,
                 label="", size=60, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self._value = value
        self._max = max_value
        
        percentage = int((value / max_value) * 100) if max_value > 0 else 0
        
        self.progress = ctk.CTkProgressBar(
            self,
            width=size,
            height=6,
            progress_color=Colors.PRIMARY,
            fg_color=Colors.BG_DARK,
            corner_radius=3
        )
        self.progress.set(value / max_value if max_value > 0 else 0)
        self.progress.pack(pady=(4, 2))
        
        display = f"{value}/{max_value}"
        self.value_label = ctk.CTkLabel(
            self, text=display,
            font=Fonts.TINY,
            text_color=Colors.TEXT_SECONDARY
        )
        self.value_label.pack()
        
        if label:
            self.name_label = ctk.CTkLabel(
                self, text=label,
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED
            )
            self.name_label.pack()
    
    def set_value(self, value, max_value=None):
        if max_value is not None:
            self._max = max_value
        self._value = value
        ratio = value / self._max if self._max > 0 else 0
        self.progress.set(ratio)
        self.value_label.configure(text=f"{value}/{self._max}")
