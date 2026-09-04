# ========== theme.py ==========
# Mikasa AI — Dizayn tokenlari va rang palitralari
# JARVIS-style dark cyberpunk + glassmorphism

class Colors:
    """Rang palitralari"""
    # Asosiy fonlar
    BG_DARKEST = "#060A14"
    BG_DARK = "#0A0E1A"
    BG_SURFACE = "#111827"
    BG_CARD = "#1A2332"
    BG_HOVER = "#1F2B3D"
    BG_INPUT = "#0D1321"
    
    # Accent ranglar
    PRIMARY = "#00D4FF"        # Cyan — asosiy accent
    PRIMARY_DARK = "#0099CC"
    PRIMARY_GLOW = "#00D4FF"
    SECONDARY = "#7C3AED"      # Purple — gradient
    SECONDARY_DARK = "#5B21B6"
    ACCENT_GRADIENT_START = "#00D4FF"
    ACCENT_GRADIENT_END = "#7C3AED"
    
    # Holat ranglar
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    INFO = "#3B82F6"
    
    # Matn ranglar
    TEXT_PRIMARY = "#F9FAFB"
    TEXT_SECONDARY = "#9CA3AF"
    TEXT_MUTED = "#6B7280"
    TEXT_ACCENT = "#00D4FF"
    
    # Chegara / ajratgich
    BORDER = "#1E293B"
    BORDER_HOVER = "#334155"
    BORDER_ACCENT = "#00D4FF"
    
    # Sidebar
    SIDEBAR_BG = "#080C16"
    SIDEBAR_ACTIVE = "#0A1628"
    SIDEBAR_HOVER = "#0E1A2E"
    SIDEBAR_INDICATOR = "#00D4FF"
    
    # Status bar
    STATUSBAR_BG = "#060A14"


class Fonts:
    """Shrift sozlamalari"""
    FAMILY = "Segoe UI"
    FAMILY_MONO = "Cascadia Code"
    
    # O'lchamlar
    HEADING_1 = (FAMILY, 22, "bold")
    HEADING_2 = (FAMILY, 18, "bold")
    HEADING_3 = (FAMILY, 15, "bold")
    BODY = (FAMILY, 13)
    BODY_BOLD = (FAMILY, 13, "bold")
    SMALL = (FAMILY, 11)
    SMALL_BOLD = (FAMILY, 11, "bold")
    TINY = (FAMILY, 10)
    MONO = (FAMILY_MONO, 12)
    
    # Nav
    NAV_ICON = (FAMILY, 18)
    NAV_LABEL = (FAMILY, 11)
    STATUS = (FAMILY, 10)


class Sizing:
    """O'lcham konstantalari"""
    # Sidebar
    SIDEBAR_WIDTH_COLLAPSED = 64
    SIDEBAR_WIDTH_EXPANDED = 200
    
    # Status bar
    STATUSBAR_HEIGHT = 32
    
    # Kartalar
    CARD_RADIUS = 12
    CARD_PADDING = 16
    
    # Tugmalar
    BUTTON_HEIGHT = 36
    BUTTON_RADIUS = 8
    BUTTON_PADDING_X = 16
    
    # Inputlar
    INPUT_HEIGHT = 40
    INPUT_RADIUS = 8
    
    # Boshqa
    ICON_SIZE = 20
    AVATAR_SIZE = 36
    

class Icons:
    """Unicode ikonkalar (Emoji based — kengaytirish mumkin)"""
    # Navigatsiya
    DASHBOARD = "🏠"
    VOICE = "🎤"
    CHAT = "💬"
    COMMANDS = "⚡"
    MEMORY = "🧠"
    SCHEDULER = "⏰"
    PLUGINS = "🔌"
    SETTINGS = "⚙️"
    
    # Holatlar
    ONLINE = "🟢"
    OFFLINE = "🔴"
    BUSY = "🟡"
    
    # Harakatlar
    PLAY = "▶"
    PAUSE = "⏸"
    STOP = "⏹"
    MIC = "🎙️"
    MIC_OFF = "🔇"
    SEND = "➤"
    SEARCH = "🔍"
    ADD = "➕"
    DELETE = "🗑️"
    EDIT = "✏️"
    COPY = "📋"
    CLOSE = "✕"
    
    # Tool kategoriyalar
    INTERNET = "🌐"
    CALCULATOR = "🔢"
    SYSTEM = "💻"
    MEDIA = "🎵"
    WEATHER = "🌤️"
    FILE = "📁"
    KNOWLEDGE = "📚"
    CLOCK = "🕐"
    CURRENCY = "💱"
    TRANSLATE = "🌍"
    SCREEN = "👁️"
    REMINDER = "📌"
