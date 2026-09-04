# ========== theme.py ==========
# Mikasa AI — Dizayn tokenlari va rang palitralari

import customtkinter as ctk


class Colors:
    """Rang palitralari"""

    _DARK = {
        "BG_DARKEST": "#08080C",
        "BG_DARK": "#0D0D14",
        "BG_SURFACE": "#12121A",
        "BG_CARD": "#161622",
        "BG_PANEL": "#1C1C2A",
        "BG_HOVER": "#2A2A3E",
        "BG_INPUT": "#181824",
        "BG_SOFT": "#1E1E2C",
        "BG_ACCENT": "#0F1E33",
        "PRIMARY": "#0A84FF",
        "PRIMARY_DARK": "#0066CC",
        "PRIMARY_HOVER": "#0071E3",
        "PRIMARY_GLOW": "#2997FF",
        "PRIMARY_SOFT": "#12253E",
        "SECONDARY": "#5E5CE6",
        "SECONDARY_DARK": "#4442A8",
        "SECONDARY_SOFT": "#1E1E36",
        "ACCENT_GRADIENT_START": "#0A84FF",
        "ACCENT_GRADIENT_END": "#5E5CE6",
        "SUCCESS": "#30D158",
        "SUCCESS_SOFT": "#102E1B",
        "WARNING": "#FF9F0A",
        "WARNING_SOFT": "#35240B",
        "DANGER": "#FF453A",
        "DANGER_SOFT": "#351515",
        "INFO": "#64D2FF",
        "INFO_SOFT": "#112638",
        "TEXT_PRIMARY": "#FFFFFF",
        "TEXT_SECONDARY": "#DCE0EA",
        "TEXT_MUTED": "#989EAE",
        "TEXT_ACCENT": "#2997FF",
        "BORDER": "#2E2E40",
        "BORDER_HOVER": "#4A4A66",
        "BORDER_ACCENT": "#0A84FF",
        "SIDEBAR_BG": "#0A0A0E",
        "SIDEBAR_ACTIVE": "#1E1E2C",
        "SIDEBAR_HOVER": "#181824",
        "SIDEBAR_INDICATOR": "#0A84FF",
        "STATUSBAR_BG": "#08080C",
        # Glassmorphism tokens
        "GLASS_BG": "#2A2A42",
        "GLASS_BG_HOVER": "#383854",
        "GLASS_BORDER": "#50506E",
        "GLASS_BORDER_HOVER": "#7A7AA0",
        "GLASS_TEXT": "#FFFFFF",
        "GLASS_HERO_BG": "#0A84FF",
        "GLASS_HERO_HOVER": "#0071E3",
        "GLASS_HERO_BORDER": "#409CFF",
    }

    _LIGHT = {
        "BG_DARKEST": "#F4F7FB",
        "BG_DARK": "#EEF3F8",
        "BG_SURFACE": "#FFFFFF",
        "BG_CARD": "#FFFFFF",
        "BG_PANEL": "#E5EEF8",
        "BG_HOVER": "#D9E5F3",
        "BG_INPUT": "#F7FAFD",
        "BG_SOFT": "#EAF1F8",
        "BG_ACCENT": "#E1F2FF",
        "PRIMARY": "#0284C7",
        "PRIMARY_DARK": "#0369A1",
        "PRIMARY_HOVER": "#0369A1",
        "PRIMARY_GLOW": "#38BDF8",
        "PRIMARY_SOFT": "#D7EDF9",
        "SECONDARY": "#7C3AED",
        "SECONDARY_DARK": "#6D28D9",
        "SECONDARY_SOFT": "#EEE7FF",
        "ACCENT_GRADIENT_START": "#38BDF8",
        "ACCENT_GRADIENT_END": "#8B5CF6",
        "SUCCESS": "#059669",
        "SUCCESS_SOFT": "#D8F5EA",
        "WARNING": "#D97706",
        "WARNING_SOFT": "#FFF1D6",
        "DANGER": "#DC2626",
        "DANGER_SOFT": "#FBE4E4",
        "INFO": "#2563EB",
        "INFO_SOFT": "#DFEAFE",
        "TEXT_PRIMARY": "#0F172A",
        "TEXT_SECONDARY": "#475569",
        "TEXT_MUTED": "#64748B",
        "TEXT_ACCENT": "#0284C7",
        "BORDER": "#D6DFEA",
        "BORDER_HOVER": "#BAC8D8",
        "BORDER_ACCENT": "#0284C7",
        "SIDEBAR_BG": "#E7EEF7",
        "SIDEBAR_ACTIVE": "#D7E4F4",
        "SIDEBAR_HOVER": "#DCE8F5",
        "SIDEBAR_INDICATOR": "#0284C7",
        "STATUSBAR_BG": "#E7EEF7",
        # Glassmorphism tokens
        "GLASS_BG": "#E8EFF7",
        "GLASS_BG_HOVER": "#DCE7F3",
        "GLASS_BORDER": "#CBD8E7",
        "GLASS_BORDER_HOVER": "#A6BCD4",
        "GLASS_TEXT": "#0F172A",
        "GLASS_HERO_BG": "#0284C7",
        "GLASS_HERO_HOVER": "#0369A1",
        "GLASS_HERO_BORDER": "#38BDF8",
    }

    CURRENT_THEME = "dark"

    BG_DARKEST = _DARK["BG_DARKEST"]
    BG_DARK = _DARK["BG_DARK"]
    BG_SURFACE = _DARK["BG_SURFACE"]
    BG_CARD = _DARK["BG_CARD"]
    BG_PANEL = _DARK["BG_PANEL"]
    BG_HOVER = _DARK["BG_HOVER"]
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
    BORDER = _DARK["BORDER"]
    BORDER_HOVER = _DARK["BORDER_HOVER"]
    BORDER_ACCENT = _DARK["BORDER_ACCENT"]
    SIDEBAR_BG = _DARK["SIDEBAR_BG"]
    SIDEBAR_ACTIVE = _DARK["SIDEBAR_ACTIVE"]
    SIDEBAR_HOVER = _DARK["SIDEBAR_HOVER"]
    SIDEBAR_INDICATOR = _DARK["SIDEBAR_INDICATOR"]
    STATUSBAR_BG = _DARK["STATUSBAR_BG"]
    # Glassmorphism tokens
    GLASS_BG = _DARK["GLASS_BG"]
    GLASS_BG_HOVER = _DARK["GLASS_BG_HOVER"]
    GLASS_BORDER = _DARK["GLASS_BORDER"]
    GLASS_BORDER_HOVER = _DARK["GLASS_BORDER_HOVER"]
    GLASS_TEXT = _DARK["GLASS_TEXT"]
    GLASS_HERO_BG = _DARK["GLASS_HERO_BG"]
    GLASS_HERO_HOVER = _DARK["GLASS_HERO_HOVER"]
    GLASS_HERO_BORDER = _DARK["GLASS_HERO_BORDER"]

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


class Fonts:
    """Shrift sozlamalari"""

    FAMILY = "Segoe UI"
    FAMILY_MONO = "Cascadia Code"

    _BASE = {
        "HEADING_1": (FAMILY, 22, "bold"),
        "HEADING_2": (FAMILY, 18, "bold"),
        "HEADING_3": (FAMILY, 15, "bold"),
        "BODY": (FAMILY, 13),
        "BODY_BOLD": (FAMILY, 13, "bold"),
        "SMALL": (FAMILY, 12),
        "SMALL_BOLD": (FAMILY, 12, "bold"),
        "TINY": (FAMILY, 10),
        "MONO": (FAMILY_MONO, 12),
        "NAV_ICON": (FAMILY, 18),
        "NAV_LABEL": (FAMILY, 13),
        "STATUS": (FAMILY, 11),
    }

    _COMPACT = {
        "HEADING_1": (FAMILY, 19, "bold"),
        "HEADING_2": (FAMILY, 16, "bold"),
        "HEADING_3": (FAMILY, 14, "bold"),
        "BODY": (FAMILY, 12),
        "BODY_BOLD": (FAMILY, 12, "bold"),
        "SMALL": (FAMILY, 11),
        "SMALL_BOLD": (FAMILY, 11, "bold"),
        "TINY": (FAMILY, 9),
        "MONO": (FAMILY_MONO, 11),
        "NAV_ICON": (FAMILY, 16),
        "NAV_LABEL": (FAMILY, 11),
        "STATUS": (FAMILY, 10),
    }

    HEADING_1 = _BASE["HEADING_1"]
    HEADING_2 = _BASE["HEADING_2"]
    HEADING_3 = _BASE["HEADING_3"]
    BODY = _BASE["BODY"]
    BODY_BOLD = _BASE["BODY_BOLD"]
    SMALL = _BASE["SMALL"]
    SMALL_BOLD = _BASE["SMALL_BOLD"]
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
    """O'lcham konstantalari"""

    _BASE = {
        "SIDEBAR_WIDTH_COLLAPSED": 64,
        "SIDEBAR_WIDTH_EXPANDED": 200,
        "STATUSBAR_HEIGHT": 32,
        "CARD_RADIUS": 22,
        "CARD_PADDING": 18,
        "BUTTON_HEIGHT": 42,
        "BUTTON_RADIUS": 999,
        "BUTTON_PADDING_X": 16,
        "INPUT_HEIGHT": 44,
        "INPUT_RADIUS": 16,
        "ICON_SIZE": 20,
        "AVATAR_SIZE": 36,
        "PAGE_PADDING": 20,
    }

    _COMPACT = {
        "SIDEBAR_WIDTH_COLLAPSED": 60,
        "SIDEBAR_WIDTH_EXPANDED": 86,
        "STATUSBAR_HEIGHT": 28,
        "CARD_RADIUS": 16,
        "CARD_PADDING": 12,
        "BUTTON_HEIGHT": 36,
        "BUTTON_RADIUS": 14,
        "BUTTON_PADDING_X": 12,
        "INPUT_HEIGHT": 40,
        "INPUT_RADIUS": 14,
        "ICON_SIZE": 18,
        "AVATAR_SIZE": 32,
        "PAGE_PADDING": 14,
    }

    SIDEBAR_WIDTH_COLLAPSED = _BASE["SIDEBAR_WIDTH_COLLAPSED"]
    SIDEBAR_WIDTH_EXPANDED = _BASE["SIDEBAR_WIDTH_EXPANDED"]
    STATUSBAR_HEIGHT = _BASE["STATUSBAR_HEIGHT"]
    CARD_RADIUS = _BASE["CARD_RADIUS"]
    CARD_PADDING = _BASE["CARD_PADDING"]
    BUTTON_HEIGHT = _BASE["BUTTON_HEIGHT"]
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


class Icons:
    """Unicode ikonkalar (Emoji based — kengaytirish mumkin)"""

    # Navigatsiya
    DASHBOARD = "⬡"
    VOICE = "◎"
    CHAT = "◇"
    COMMANDS = "⚡"
    MEMORY = "◈"
    SCHEDULER = "◷"
    PLUGINS = "⬢"
    SETTINGS = "⚙"

    # Holatlar
    ONLINE = "●"
    OFFLINE = "●"
    BUSY = "●"

    # Harakatlar
    PLAY = "▶"
    PAUSE = "⏸"
    STOP = "⏹"
    MIC = "◉"
    MIC_OFF = "○"
    SEND = "➤"
    SEARCH = "⌕"
    ADD = "+"
    DELETE = "✕"
    EDIT = "✎"
    COPY = "❐"
    CLOSE = "✕"

    # Tool kategoriyalar
    INTERNET = "◎"
    CALCULATOR = "#"
    SYSTEM = "▣"
    MEDIA = "♫"
    WEATHER = "☁"
    FILE = "▤"
    KNOWLEDGE = "▥"
    CLOCK = "◷"
    CURRENCY = "¤"
    TRANSLATE = "⊕"
    SCREEN = "◱"
    REMINDER = "◈"


Colors.apply_theme("dark")
Fonts.apply_density(False)
Sizing.apply_density(False)
