# ========== theme.py ==========
# Mikasa AI — Premium Futuristic Design System Tokens
# 80% minimal solid surfaces / 20% glass/accent surfaces
# Strict 8-point spacing, semantic radii, and typography hierarchy

import customtkinter as ctk


class Colors:
    """Yagona semantik ranglar tizimi"""

    _DARK = {
        # Sirtlar ierarxiyasi (80% Minimal Solid Surfaces)
        "BG_DARKEST": "#08080C",       # Base canvas / statusbar
        "BG_DARK": "#0D0D14",          # Page backgrounds, scroll areas
        "BG_SURFACE": "#12121A",       # Inner content surface
        "BG_CARD": "#161622",          # Solid 80% Card default
        "BG_PANEL": "#1C1C2A",         # Elevated card, dropdown, tool items
        "BG_HOVER": "#242436",         # Hover state
        "BG_ACTIVE": "#2E2E44",        # Active state / pressed
        "BG_INPUT": "#13131D",         # Textbox, input fields
        "BG_SOFT": "#1A1A26",
        "BG_ACCENT": "#0F1E33",
        # Asosiy aksentlar
        "PRIMARY": "#0A84FF",          # Electric Blue
        "PRIMARY_DARK": "#0066CC",
        "PRIMARY_HOVER": "#0071E3",
        "PRIMARY_GLOW": "#2997FF",
        "PRIMARY_SOFT": "#0E2A4A",
        "SECONDARY": "#5E5CE6",        # Deep Violet
        "SECONDARY_DARK": "#4442A8",
        "SECONDARY_HOVER": "#4E4CD4",
        "SECONDARY_SOFT": "#1E1E38",
        "ACCENT_GRADIENT_START": "#0A84FF",
        "ACCENT_GRADIENT_END": "#5E5CE6",
        # Holat ranglari
        "SUCCESS": "#30D158",
        "SUCCESS_SOFT": "#102E1B",
        "WARNING": "#FF9F0A",
        "WARNING_SOFT": "#35240B",
        "DANGER": "#FF453A",
        "DANGER_SOFT": "#351515",
        "INFO": "#64D2FF",
        "INFO_SOFT": "#112638",
        # Matn ranglari
        "TEXT_PRIMARY": "#FFFFFF",
        "TEXT_SECONDARY": "#C5C9D6",
        "TEXT_MUTED": "#868B9D",
        "TEXT_ACCENT": "#0A84FF",
        # Hoshiyalar (Border discipline)
        "BORDER_SUBTLE": "#1A1A28",    # Primary surface subtle 1px border
        "BORDER": "#232334",           # Standard card border
        "BORDER_ELEVATED": "#2C2C3E",  # Elevated surface border
        "BORDER_GLASS": "#383850",     # Glass-like surface border
        "BORDER_HERO": "#409CFF",      # Hero accent border
        "BORDER_HOVER": "#3C3C54",
        "BORDER_ACCENT": "#0A84FF",
        # Sidebar va status
        "SIDEBAR_BG": "#0A0A0E",
        "SIDEBAR_ACTIVE": "#1C1C2A",
        "SIDEBAR_HOVER": "#14141E",
        "SIDEBAR_INDICATOR": "#0A84FF",
        "STATUSBAR_BG": "#08080C",
        # 20% Glassmorphism / Accent tokens (Glass-like opaque surface: Hero, Floating, Modals)
        "GLASS_BG": "#1E1E2E",
        "GLASS_BG_HOVER": "#2A2A3E",
        "GLASS_BORDER": "#383850",     # Slightly stronger glass highlight border
        "GLASS_BORDER_HOVER": "#525274",
        "GLASS_TEXT": "#FFFFFF",
        "GLASS_HERO_BG": "#0A84FF",
        "GLASS_HERO_HOVER": "#0071E3",
        "GLASS_HERO_BORDER": "#409CFF",
        # Overlay / Modal tokens
        "OVERLAY_BG": "#161622",
        "OVERLAY_BACKDROP": "#050508",
    }

    _LIGHT = {
        # Sirtlar ierarxiyasi (Light theme)
        "BG_DARKEST": "#F1F5F9",       # Base canvas (Slate 100)
        "BG_DARK": "#F8FAFC",          # Page background (Slate 50)
        "BG_SURFACE": "#FFFFFF",       # Content surface (Pure white)
        "BG_CARD": "#FFFFFF",          # 80% Solid Card (Pure white)
        "BG_PANEL": "#F1F5F9",         # Elevated panel (Slate 100)
        "BG_HOVER": "#E2E8F0",         # Hover state (Slate 200)
        "BG_ACTIVE": "#CBD5E1",        # Active state (Slate 300 - clearly visible!)
        "BG_INPUT": "#F8FAFC",         # Textbox, input fields (Slate 50)
        "BG_SOFT": "#F1F5F9",
        "BG_ACCENT": "#E0F2FE",
        # Asosiy aksentlar
        "PRIMARY": "#0284C7",
        "PRIMARY_DARK": "#0369A1",
        "PRIMARY_HOVER": "#0369A1",
        "PRIMARY_GLOW": "#38BDF8",
        "PRIMARY_SOFT": "#D7EDF9",
        "SECONDARY": "#7C3AED",
        "SECONDARY_DARK": "#6D28D9",
        "SECONDARY_HOVER": "#6D28D9",
        "SECONDARY_SOFT": "#EDE9FE",
        "ACCENT_GRADIENT_START": "#38BDF8",
        "ACCENT_GRADIENT_END": "#8B5CF6",
        # Holat ranglari
        "SUCCESS": "#059669",
        "SUCCESS_SOFT": "#D1FAE5",
        "WARNING": "#D97706",
        "WARNING_SOFT": "#FEF3C7",
        "DANGER": "#DC2626",
        "DANGER_SOFT": "#FEE2E2",
        "INFO": "#2563EB",
        "INFO_SOFT": "#DBEAFE",
        # Matn ranglari (High contrast)
        "TEXT_PRIMARY": "#0F172A",     # Slate 900
        "TEXT_SECONDARY": "#334155",   # Slate 700
        "TEXT_MUTED": "#64748B",       # Slate 500
        "TEXT_ACCENT": "#0284C7",
        # Hoshiyalar (Border discipline - softer, non-aggressive in light mode)
        "BORDER_SUBTLE": "#EEF2F6",    # Subtle border for primary cards
        "BORDER": "#E2E8F0",           # Standard border (Slate 200)
        "BORDER_ELEVATED": "#CBD5E1",  # Elevated border (Slate 300)
        "BORDER_GLASS": "#CBD8E7",     # Glass-like surface border
        "BORDER_HERO": "#38BDF8",      # Hero accent border
        "BORDER_HOVER": "#94A3B8",     # Border hover (Slate 400)
        "BORDER_ACCENT": "#0284C7",
        # Sidebar va status
        "SIDEBAR_BG": "#F1F5F9",
        "SIDEBAR_ACTIVE": "#E2E8F0",
        "SIDEBAR_HOVER": "#E8EFF7",
        "SIDEBAR_INDICATOR": "#0284C7",
        "STATUSBAR_BG": "#F1F5F9",
        # 20% Glassmorphism / Accent tokens (Glass-like opaque surface - crisp ice-tinted white, NOT dingy grey!)
        "GLASS_BG": "#F0F6FD",         # Crisp cool ice-tint
        "GLASS_BG_HOVER": "#E2EDF9",
        "GLASS_BORDER": "#CBD8E7",     # Clean, cool-tinted border
        "GLASS_BORDER_HOVER": "#A6BCD4",
        "GLASS_TEXT": "#0F172A",
        "GLASS_HERO_BG": "#0284C7",
        "GLASS_HERO_HOVER": "#0369A1",
        "GLASS_HERO_BORDER": "#38BDF8",
        # Overlay / Modal tokens
        "OVERLAY_BG": "#FFFFFF",
        "OVERLAY_BACKDROP": "#0F172A",
    }

    CURRENT_THEME = "dark"

    # Dinamik property lar
    BG_DARKEST = _DARK["BG_DARKEST"]
    BG_DARK = _DARK["BG_DARK"]
    BG_SURFACE = _DARK["BG_SURFACE"]
    BG_CARD = _DARK["BG_CARD"]
    BG_PANEL = _DARK["BG_PANEL"]
    BG_HOVER = _DARK["BG_HOVER"]
    BG_ACTIVE = _DARK["BG_ACTIVE"]
    BG_INPUT = _DARK["BG_INPUT"]
    BG_SOFT = _DARK["BG_SOFT"]
    BG_ACCENT = _DARK["BG_ACCENT"]
    PRIMARY = _DARK["PRIMARY"]
    PRIMARY_DARK = _DARK["PRIMARY_DARK"]
    PRIMARY_HOVER = _DARK["PRIMARY_HOVER"]
    PRIMARY_GLOW = _DARK["PRIMARY_GLOW"]
    PRIMARY_SOFT = _DARK["PRIMARY_SOFT"]
    SECONDARY = _DARK["SECONDARY"]
    SECONDARY_DARK = _DARK["SECONDARY_DARK"]
    SECONDARY_HOVER = _DARK["SECONDARY_HOVER"]
    SECONDARY_SOFT = _DARK["SECONDARY_SOFT"]
    ACCENT_GRADIENT_START = _DARK["ACCENT_GRADIENT_START"]
    ACCENT_GRADIENT_END = _DARK["ACCENT_GRADIENT_END"]
    SUCCESS = _DARK["SUCCESS"]
    SUCCESS_SOFT = _DARK["SUCCESS_SOFT"]
    WARNING = _DARK["WARNING"]
    WARNING_SOFT = _DARK["WARNING_SOFT"]
    DANGER = _DARK["DANGER"]
    DANGER_SOFT = _DARK["DANGER_SOFT"]
    INFO = _DARK["INFO"]
    INFO_SOFT = _DARK["INFO_SOFT"]
    TEXT_PRIMARY = _DARK["TEXT_PRIMARY"]
    TEXT_SECONDARY = _DARK["TEXT_SECONDARY"]
    TEXT_MUTED = _DARK["TEXT_MUTED"]
    TEXT_ACCENT = _DARK["TEXT_ACCENT"]
    BORDER_SUBTLE = _DARK["BORDER_SUBTLE"]
    BORDER = _DARK["BORDER"]
    BORDER_ELEVATED = _DARK["BORDER_ELEVATED"]
    BORDER_GLASS = _DARK["BORDER_GLASS"]
    BORDER_HERO = _DARK["BORDER_HERO"]
    BORDER_HOVER = _DARK["BORDER_HOVER"]
    BORDER_ACCENT = _DARK["BORDER_ACCENT"]
    SIDEBAR_BG = _DARK["SIDEBAR_BG"]
    SIDEBAR_ACTIVE = _DARK["SIDEBAR_ACTIVE"]
    SIDEBAR_HOVER = _DARK["SIDEBAR_HOVER"]
    SIDEBAR_INDICATOR = _DARK["SIDEBAR_INDICATOR"]
    STATUSBAR_BG = _DARK["STATUSBAR_BG"]
    GLASS_BG = _DARK["GLASS_BG"]
    GLASS_BG_HOVER = _DARK["GLASS_BG_HOVER"]
    GLASS_BORDER = _DARK["GLASS_BORDER"]
    GLASS_BORDER_HOVER = _DARK["GLASS_BORDER_HOVER"]
    GLASS_TEXT = _DARK["GLASS_TEXT"]
    GLASS_HERO_BG = _DARK["GLASS_HERO_BG"]
    GLASS_HERO_HOVER = _DARK["GLASS_HERO_HOVER"]
    GLASS_HERO_BORDER = _DARK["GLASS_HERO_BORDER"]
    OVERLAY_BG = _DARK["OVERLAY_BG"]
    OVERLAY_BACKDROP = _DARK["OVERLAY_BACKDROP"]

    @classmethod
    def apply_theme(cls, theme="dark"):
        requested = (theme or "dark").lower()
        if requested == "system":
            actual = ctk.get_appearance_mode().lower()
            palette = cls._LIGHT if actual == "light" else cls._DARK
        else:
            palette = cls._LIGHT if requested == "light" else cls._DARK

        for key, value in palette.items():
            setattr(cls, key, value)

        cls.CURRENT_THEME = requested


class Surfaces:
    """
    Mikasa AI 7-Tier Semantic Surface Architecture
    
    1. BASE: Window root canvas, deepest background container (BG_DARKEST)
    2. SURFACE: Page canvas, scroll frame background (BG_DARK / BG_SURFACE)
    3. CARD: 80% Solid container for general UI, forms, tables, lists (BG_CARD)
    4. ELEVATED: Elevated panels, grouped tool cards, sidebars, dropdowns (BG_PANEL)
    5. GLASS: 20% Glass-like opaque tinted surface for floating panels, heroes, pinned status (GLASS_BG)
    6. HERO: Prominent accent banner with highlight borders (GLASS_HERO_BG / BG_ACCENT)
    7. OVERLAY: Modals, dialogs, popovers, and toast notifications (OVERLAY_BG)
    """
    BASE = "base"
    SURFACE = "surface"
    CARD = "card"
    ELEVATED = "elevated"
    GLASS = "glass"
    HERO = "hero"
    OVERLAY = "overlay"

    @classmethod
    def get_tokens(cls, tier: str) -> dict:
        """Returns standard {fg_color, border_color, border_width, corner_radius} for a given surface tier"""
        t = (tier or cls.CARD).lower()
        if t == cls.BASE:
            return {"fg_color": Colors.BG_DARKEST, "border_color": Colors.BORDER_SUBTLE, "border_width": 0, "corner_radius": 0}
        elif t == cls.SURFACE:
            return {"fg_color": Colors.BG_DARK, "border_color": Colors.BORDER_SUBTLE, "border_width": 0, "corner_radius": 0}
        elif t == cls.CARD:
            return {"fg_color": Colors.BG_CARD, "border_color": Colors.BORDER, "border_width": 1, "corner_radius": Sizing.CARD}
        elif t == cls.ELEVATED:
            return {"fg_color": Colors.BG_PANEL, "border_color": Colors.BORDER_ELEVATED, "border_width": 1, "corner_radius": Sizing.CARD}
        elif t == cls.GLASS:
            return {"fg_color": Colors.GLASS_BG, "border_color": Colors.GLASS_BORDER, "border_width": 1, "corner_radius": Sizing.CARD}
        elif t == cls.HERO:
            return {"fg_color": Colors.GLASS_HERO_BG, "border_color": Colors.GLASS_HERO_BORDER, "border_width": 1, "corner_radius": Sizing.LARGE}
        elif t == cls.OVERLAY:
            return {"fg_color": Colors.OVERLAY_BG, "border_color": Colors.BORDER_ELEVATED, "border_width": 1, "corner_radius": Sizing.CARD}
        return {"fg_color": Colors.BG_CARD, "border_color": Colors.BORDER, "border_width": 1, "corner_radius": Sizing.CARD}


class Fonts:
    """Tipografiya tizimi — Segoe UI va Cascadia Code"""

    FAMILY = "Segoe UI"
    FAMILY_MONO = "Cascadia Code"

    _BASE = {
        "DISPLAY": (FAMILY, 28, "bold"),
        "HEADING_1": (FAMILY, 22, "bold"),
        "HEADING_2": (FAMILY, 18, "bold"),
        "HEADING_3": (FAMILY, 15, "bold"),
        "BODY": (FAMILY, 13),
        "BODY_BOLD": (FAMILY, 13, "bold"),
        "SMALL": (FAMILY, 12),
        "SMALL_BOLD": (FAMILY, 12, "bold"),
        "CAPTION": (FAMILY, 11),
        "TINY": (FAMILY, 10),
        "MONO": (FAMILY_MONO, 12),
        "NAV_ICON": (FAMILY, 18),
        "NAV_LABEL": (FAMILY, 13),
        "STATUS": (FAMILY, 11),
    }

    _COMPACT = {
        "DISPLAY": (FAMILY, 24, "bold"),
        "HEADING_1": (FAMILY, 19, "bold"),
        "HEADING_2": (FAMILY, 16, "bold"),
        "HEADING_3": (FAMILY, 14, "bold"),
        "BODY": (FAMILY, 12),
        "BODY_BOLD": (FAMILY, 12, "bold"),
        "SMALL": (FAMILY, 11),
        "SMALL_BOLD": (FAMILY, 11, "bold"),
        "CAPTION": (FAMILY, 10),
        "TINY": (FAMILY, 9),
        "MONO": (FAMILY_MONO, 11),
        "NAV_ICON": (FAMILY, 16),
        "NAV_LABEL": (FAMILY, 11),
        "STATUS": (FAMILY, 10),
    }

    DISPLAY = _BASE["DISPLAY"]
    HEADING_1 = _BASE["HEADING_1"]
    HEADING_2 = _BASE["HEADING_2"]
    HEADING_3 = _BASE["HEADING_3"]
    BODY = _BASE["BODY"]
    BODY_BOLD = _BASE["BODY_BOLD"]
    SMALL = _BASE["SMALL"]
    SMALL_BOLD = _BASE["SMALL_BOLD"]
    CAPTION = _BASE["CAPTION"]
    TINY = _BASE["TINY"]
    MONO = _BASE["MONO"]
    NAV_ICON = _BASE["NAV_ICON"]
    NAV_LABEL = _BASE["NAV_LABEL"]
    STATUS = _BASE["STATUS"]

    @classmethod
    def apply_density(cls, compact=False):
        selected = cls._COMPACT if compact else cls._BASE
        for key, value in selected.items():
            setattr(cls, key, value)


class Sizing:
    """O'lcham va Spacing konstantalari (8-point scale)"""

    # Spacing scale
    SPACING_4 = 4
    SPACING_8 = 8
    SPACING_12 = 12
    SPACING_16 = 16
    SPACING_20 = 20
    SPACING_24 = 24
    SPACING_32 = 32
    SPACING_40 = 40
    SPACING_48 = 48

    # Semantik radiuslar (Semantic Radii Hierarchy)
    SMALL = 10
    CARD = 16
    LARGE = 20
    PILL = 999

    # Radius ierarxiyasi
    RADIUS_PILL = PILL
    RADIUS_HERO = LARGE
    RADIUS_CARD = CARD
    RADIUS_CARD_SM = SMALL
    RADIUS_INPUT = 14
    RADIUS_BUTTON = 12
    RADIUS_SMALL = SMALL
    RADIUS_ICON = 12

    _BASE = {
        "SIDEBAR_WIDTH_COLLAPSED": 68,
        "SIDEBAR_WIDTH_EXPANDED": 210,
        "STATUSBAR_HEIGHT": 32,
        "CARD_RADIUS": RADIUS_CARD,
        "CARD_PADDING": 16,
        "BUTTON_HEIGHT": 42,
        "BUTTON_HEIGHT_COMPACT": 36,
        "BUTTON_RADIUS": RADIUS_BUTTON,
        "BUTTON_PADDING_X": 16,
        "INPUT_HEIGHT": 44,
        "INPUT_RADIUS": RADIUS_INPUT,
        "ICON_SIZE": 20,
        "AVATAR_SIZE": 36,
        "PAGE_PADDING": 20,
    }

    _COMPACT = {
        "SIDEBAR_WIDTH_COLLAPSED": 60,
        "SIDEBAR_WIDTH_EXPANDED": 86,
        "STATUSBAR_HEIGHT": 28,
        "CARD_RADIUS": 14,
        "CARD_PADDING": 12,
        "BUTTON_HEIGHT": 36,
        "BUTTON_HEIGHT_COMPACT": 32,
        "BUTTON_RADIUS": 10,
        "BUTTON_PADDING_X": 12,
        "INPUT_HEIGHT": 40,
        "INPUT_RADIUS": 12,
        "ICON_SIZE": 18,
        "AVATAR_SIZE": 32,
        "PAGE_PADDING": 14,
    }

    SIDEBAR_WIDTH_COLLAPSED = _BASE["SIDEBAR_WIDTH_COLLAPSED"]
    SIDEBAR_WIDTH_EXPANDED = _BASE["SIDEBAR_WIDTH_EXPANDED"]
    STATUSBAR_HEIGHT = _BASE["STATUSBAR_HEIGHT"]
    CARD_RADIUS = _BASE["CARD_RADIUS"]
    CARD = CARD_RADIUS
    SMALL = RADIUS_SMALL
    LARGE = RADIUS_HERO
    PILL = RADIUS_PILL
    CARD_PADDING = _BASE["CARD_PADDING"]
    BUTTON_HEIGHT = _BASE["BUTTON_HEIGHT"]
    BUTTON_HEIGHT_COMPACT = _BASE["BUTTON_HEIGHT_COMPACT"]
    BUTTON_RADIUS = _BASE["BUTTON_RADIUS"]
    BUTTON_PADDING_X = _BASE["BUTTON_PADDING_X"]
    INPUT_HEIGHT = _BASE["INPUT_HEIGHT"]
    INPUT_RADIUS = _BASE["INPUT_RADIUS"]
    ICON_SIZE = _BASE["ICON_SIZE"]
    AVATAR_SIZE = _BASE["AVATAR_SIZE"]
    PAGE_PADDING = _BASE["PAGE_PADDING"]

    @classmethod
    def apply_density(cls, compact=False):
        selected = cls._COMPACT if compact else cls._BASE
        for key, value in selected.items():
            setattr(cls, key, value)
        cls.CARD = cls.CARD_RADIUS


class Icons:
    """Ikonkalar — VectorIconEngine integratsiyasi va fallback Unicode belgilar"""

    # Navigatsiya
    DASHBOARD = "dashboard"
    VOICE = "voice"
    CHAT = "chat"
    COMMANDS = "commands"
    MEMORY = "memory"
    SCHEDULER = "scheduler"
    PLUGINS = "plugins"
    SETTINGS = "settings"

    # Holatlar
    ONLINE = "circle"
    OFFLINE = "circle"
    BUSY = "circle"

    # Harakatlar
    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"
    MIC = "mic"
    MIC_OFF = "mic_off"
    SEND = "send"
    SEARCH = "search"
    ADD = "add"
    DELETE = "delete"
    EDIT = "edit"
    COPY = "copy"
    CLOSE = "close"
    ATTACH = "attach"
    CHECK = "check"

    # Kategoriyalar
    INTERNET = "search"
    SYSTEM = "commands"
    MEDIA = "play"
    FILE = "folder"
    KNOWLEDGE = "memory"
    CLOCK = "scheduler"

    @classmethod
    def get(cls, name: str, size: int = 20, color_dark=None, color_light=None):
        from gui.icons import get_vector_icon
        c_dark = color_dark or Colors.TEXT_PRIMARY
        c_light = color_light or Colors.TEXT_PRIMARY
        return get_vector_icon(name, size=size, color_dark=c_dark, color_light=c_light)


Colors.apply_theme("dark")
Fonts.apply_density(False)
Sizing.apply_density(False)
