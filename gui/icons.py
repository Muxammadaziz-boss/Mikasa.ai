# ========== icons.py ==========
# Mikasa AI — Professional Vector Iconography Engine
# Supersampled anti-aliased vector rendering via PIL and CTkImage.
# Eliminates platform-dependent emoji variations and provides consistent,
# high-DPI Lucide/Linear-style stroke icons.

import math
import tkinter
from typing import Dict, Optional, Tuple, Union
from PIL import Image, ImageDraw
import customtkinter as ctk


LOGICAL_GRID = 24
SUPERSAMPLE_FACTOR = 4
CANVAS_SIZE = LOGICAL_GRID * SUPERSAMPLE_FACTOR  # 96x96 supersampled canvas


def compute_canvas_stroke(target_size: int, canvas_size: int = CANVAS_SIZE) -> int:
    """
    Computes anti-aliasing stroke width on the supersampled canvas (96x96)
    such that after Lanczos downsampling to target_size, the displayed stroke
    precisely adheres to the unified design token:
      16px -> ~1.50px
      18px -> ~1.625px
      20px -> ~1.75px
      24px -> ~2.00px
      32px -> ~2.50px
    """
    if target_size <= 16:
        t_stroke = 1.5
    elif target_size <= 24:
        t_stroke = 1.5 + (target_size - 16) * (0.5 / 8.0)
    else:
        t_stroke = 2.0 + (target_size - 24) * (0.5 / 8.0)

    scale_factor = canvas_size / float(target_size)
    return max(2, int(round(t_stroke * scale_factor)))


class IconCanvas:
    """
    Precision coordinate mapper over PIL.ImageDraw operating in logical 24x24 space.
    Automatically scales logical coordinates by 4x onto the 96x96 canvas.
    """
    __slots__ = ("draw", "scale", "stroke")

    def __init__(self, draw: ImageDraw.ImageDraw, stroke: int, scale: float = float(SUPERSAMPLE_FACTOR)):
        self.draw = draw
        self.stroke = stroke
        self.scale = scale

    def pt(self, x: float, y: float) -> Tuple[float, float]:
        return (x * self.scale, y * self.scale)

    def line(self, p1: Tuple[float, float], p2: Tuple[float, float], color: str, width: Optional[int] = None):
        w = width if width is not None else self.stroke
        self.draw.line([self.pt(*p1), self.pt(*p2)], fill=color, width=w)

    def polyline(self, points: list, color: str, width: Optional[int] = None, joint: str = "curve"):
        w = width if width is not None else self.stroke
        pts = [self.pt(*p) for p in points]
        self.draw.line(pts, fill=color, width=w, joint=joint)

    def rect(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        radius: float = 0,
        outline: Optional[str] = None,
        fill: Optional[str] = None,
        width: Optional[int] = None,
    ):
        w = width if width is not None else self.stroke
        box = [x0 * self.scale, y0 * self.scale, x1 * self.scale, y1 * self.scale]
        r = radius * self.scale
        if r > 0:
            self.draw.rounded_rectangle(box, radius=r, outline=outline, fill=fill, width=w if outline else 0)
        else:
            self.draw.rectangle(box, outline=outline, fill=fill, width=w if outline else 0)

    def circle(
        self,
        cx: float,
        cy: float,
        radius: float,
        outline: Optional[str] = None,
        fill: Optional[str] = None,
        width: Optional[int] = None,
    ):
        w = width if width is not None else self.stroke
        x, y = cx * self.scale, cy * self.scale
        r = radius * self.scale
        box = [x - r, y - r, x + r, y + r]
        self.draw.ellipse(box, outline=outline, fill=fill, width=w if outline else 0)

    def arc(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        start: float,
        end: float,
        color: str,
        width: Optional[int] = None,
    ):
        w = width if width is not None else self.stroke
        box = [x0 * self.scale, y0 * self.scale, x1 * self.scale, y1 * self.scale]
        self.draw.arc(box, start=start, end=end, fill=color, width=w)

    def polygon(
        self,
        points: list,
        fill: Optional[str] = None,
        outline: Optional[str] = None,
        width: Optional[int] = None,
    ):
        w = width if width is not None else self.stroke
        pts = [self.pt(*p) for p in points]
        self.draw.polygon(pts, fill=fill, outline=outline)


class VectorIconEngine:
    """
    Renders clean, stroke-based vector icons at 4x supersampled resolution (96x96)
    and scales down with Lanczos resampling for silky-smooth anti-aliasing.
    Caches PIL Image prototypes and CTkImage instances for instant, root-independent retrieval.
    """

    _PIL_CACHE: Dict[Tuple, Tuple[Image.Image, Image.Image]] = {}
    _CTK_CACHE: Dict[Tuple, ctk.CTkImage] = {}

    @staticmethod
    def _create_canvas() -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        return img, draw

    # ==========================================
    # 26 CANONICAL ICONS (Unified 24x24 Logical Grid)
    # ==========================================

    @staticmethod
    def _draw_dashboard(c: IconCanvas, color: str):
        """Dashboard: 4 balanced rounded modules (16x16 optical bounding box)"""
        c.rect(4.0, 4.0, 10.5, 10.5, radius=1.5, outline=color)
        c.rect(13.5, 4.0, 20.0, 10.5, radius=1.5, outline=color)
        c.rect(4.0, 13.5, 10.5, 20.0, radius=1.5, outline=color)
        c.rect(13.5, 13.5, 20.0, 20.0, radius=1.5, outline=color)

    @staticmethod
    def _draw_chat(c: IconCanvas, color: str):
        """Chat: Speech bubble with integrated corner tail"""
        c.rect(3.0, 3.5, 21.0, 16.0, radius=3.5, outline=color)
        c.polygon([(7.0, 15.0), (3.5, 20.5), (11.5, 15.0)], fill=color)

    @staticmethod
    def _draw_mic(c: IconCanvas, color: str):
        """Mic: Capsule, cradle arc, stem and horizontal base"""
        c.rect(9.0, 2.5, 15.0, 12.5, radius=3.0, outline=color)
        c.arc(5.5, 6.0, 18.5, 15.5, start=0, end=180, color=color)
        c.line((12.0, 15.5), (12.0, 19.5), color=color)
        c.line((8.0, 19.5), (16.0, 19.5), color=color)

    @staticmethod
    def _draw_commands(c: IconCanvas, color: str):
        """Commands: Sharp dynamic lightning bolt with optical centroid alignment"""
        pts = [
            (13.0, 2.5),
            (6.5, 12.0),
            (12.0, 12.0),
            (11.0, 21.5),
            (17.5, 11.0),
            (12.5, 11.0),
        ]
        c.polygon(pts, fill=color)

    @staticmethod
    def _draw_memory(c: IconCanvas, color: str):
        """Memory: Microchip package with dual symmetric pins and processor core"""
        c.rect(5.5, 5.5, 18.5, 18.5, radius=2.5, outline=color)
        c.rect(9.0, 9.0, 15.0, 15.0, fill=color)
        # Top & Bottom pins
        for x in (9.0, 15.0):
            c.line((x, 2.5), (x, 5.5), color=color)
            c.line((x, 18.5), (x, 21.5), color=color)
        # Left & Right pins
        for y in (9.0, 15.0):
            c.line((2.5, y), (5.5, y), color=color)
            c.line((18.5, y), (21.5, y), color=color)

    @staticmethod
    def _draw_scheduler(c: IconCanvas, color: str):
        """Scheduler: Clock dial with hour (12:00) and minute (3:00) hands"""
        c.circle(12.0, 12.0, radius=9.0, outline=color)
        c.circle(12.0, 12.0, radius=1.0, fill=color)
        c.line((12.0, 12.0), (12.0, 7.5), color=color)
        c.line((12.0, 12.0), (16.5, 12.0), color=color)

    @staticmethod
    def _draw_plugins(c: IconCanvas, color: str):
        """Plugins: Modular interlocking extension block"""
        c.rect(6.0, 6.0, 18.0, 18.0, radius=2.5, outline=color)
        c.circle(12.0, 6.0, radius=2.2, fill=color)
        c.circle(18.0, 12.0, radius=2.2, fill=color)

    @staticmethod
    def _draw_settings(c: IconCanvas, color: str):
        """Settings: 6-tooth gear with open hub, razor-sharp down to 16px"""
        cx, cy = 12.0, 12.0
        r_inner = 6.5
        r_outer = 9.5
        tooth_w = max(2, int(c.stroke * 1.3))
        for i in range(6):
            angle = i * (math.pi / 3.0)
            x1 = cx + math.cos(angle) * r_inner
            y1 = cy + math.sin(angle) * r_inner
            x2 = cx + math.cos(angle) * r_outer
            y2 = cy + math.sin(angle) * r_outer
            c.line((x1, y1), (x2, y2), color=color, width=tooth_w)
        c.circle(cx, cy, radius=r_inner, outline=color)
        c.circle(cx, cy, radius=3.2, outline=color)

    @staticmethod
    def _draw_search(c: IconCanvas, color: str):
        """Search: 45° angled magnifying glass with 13px lens and proportional handle"""
        c.circle(10.5, 10.5, radius=6.5, outline=color)
        c.line((15.2, 15.2), (21.0, 21.0), color=color, width=int(c.stroke * 1.25))

    @staticmethod
    def _draw_attach(c: IconCanvas, color: str):
        """Attach: Elegant 45° diagonal paperclip"""
        c.line((7.5, 16.5), (16.5, 7.5), color=color)
        c.line((9.5, 18.5), (18.5, 9.5), color=color)
        c.line((5.5, 14.5), (13.5, 6.5), color=color)
        c.arc(14.0, 5.0, 19.0, 10.0, start=225, end=45, color=color)
        c.arc(5.0, 14.0, 10.0, 19.0, start=45, end=225, color=color)

    @staticmethod
    def _draw_send(c: IconCanvas, color: str):
        """Send: Modern paper airplane along 45° diagonal"""
        pts = [
            (21.5, 2.5),
            (3.0, 10.0),
            (10.5, 13.5),
            (14.0, 21.0),
        ]
        c.polygon(pts, fill=color)
        c.line((10.5, 13.5), (21.5, 2.5), color=color)

    @staticmethod
    def _draw_trash(c: IconCanvas, color: str):
        """Trash: Wastebin with lid bar, top handle, and inner vertical ribs"""
        c.line((4.0, 6.0), (20.0, 6.0), color=color)
        c.line((9.0, 3.5), (15.0, 3.5), color=color)
        c.rect(6.0, 6.0, 18.0, 20.5, radius=2.0, outline=color)
        c.line((10.0, 10.0), (10.0, 16.5), color=color)
        c.line((14.0, 10.0), (14.0, 16.5), color=color)

    @staticmethod
    def _draw_minimize(c: IconCanvas, color: str):
        """Minimize: Single horizontal bar aligned to logical center"""
        c.line((5.0, 12.0), (19.0, 12.0), color=color)

    @staticmethod
    def _draw_maximize(c: IconCanvas, color: str):
        """Maximize: Clean square outline"""
        c.rect(5.5, 5.5, 18.5, 18.5, radius=1.0, outline=color)

    @staticmethod
    def _draw_restore(c: IconCanvas, color: str):
        """Restore: Two overlapping square outlines (desktop restore)"""
        c.polyline([(8.5, 5.5), (18.5, 5.5), (18.5, 15.5)], color=color)
        c.rect(5.5, 8.5, 15.5, 18.5, radius=1.0, outline=color)

    @staticmethod
    def _draw_close(c: IconCanvas, color: str):
        """Close: Symmetrical 45° cross with optical centering"""
        c.line((5.5, 5.5), (18.5, 18.5), color=color)
        c.line((18.5, 5.5), (5.5, 18.5), color=color)

    @staticmethod
    def _draw_check(c: IconCanvas, color: str):
        """Check: High-readability checkmark with curved apex joint"""
        c.polyline([(4.5, 12.5), (9.5, 17.5), (19.5, 6.5)], color=color, joint="curve")

    @staticmethod
    def _draw_plus(c: IconCanvas, color: str):
        """Plus: Symmetrical cross aligned to logical grid"""
        c.line((12.0, 4.5), (12.0, 19.5), color=color)
        c.line((4.5, 12.0), (19.5, 12.0), color=color)

    @staticmethod
    def _draw_copy(c: IconCanvas, color: str):
        """Copy: Overlapping document sheets with distinct depths"""
        c.rect(8.5, 8.5, 20.0, 20.0, radius=2.0, outline=color)
        c.polyline([(15.5, 8.5), (15.5, 4.0), (4.0, 4.0), (4.0, 15.5), (8.5, 15.5)], color=color)

    @staticmethod
    def _draw_sparkles(c: IconCanvas, color: str):
        """Sparkles: Primary 4-point AI star with companion sparkle"""
        cx, cy = 10.5, 12.5
        r_out, r_in = 7.5, 2.2
        pts = []
        for i in range(8):
            r = r_out if i % 2 == 0 else r_in
            angle = i * (math.pi / 4.0)
            pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        c.polygon(pts, fill=color)
        # Companion sparkle
        c.circle(18.5, 5.5, radius=1.8, fill=color)

    @staticmethod
    def _draw_refresh(c: IconCanvas, color: str):
        """Refresh: Circular clockwise arrow with clean arrowhead"""
        c.arc(3.5, 3.5, 20.5, 20.5, start=40, end=315, color=color)
        arrow = [(16.0, 4.5), (21.0, 4.5), (20.0, 9.5)]
        c.polygon(arrow, fill=color)

    @staticmethod
    def _draw_folder(c: IconCanvas, color: str):
        """Folder: File folder with tab header and rounded base"""
        c.rect(3.5, 7.5, 20.5, 19.5, radius=2.0, outline=color)
        c.polygon([(3.5, 7.5), (3.5, 4.5), (9.5, 4.5), (12.0, 7.5)], fill=color)

    @staticmethod
    def _draw_eye(c: IconCanvas, color: str):
        """Eye: Almond contour with central iris and pupil dot"""
        c.arc(2.5, 4.5, 21.5, 19.5, start=0, end=180, color=color)
        c.arc(2.5, 4.5, 21.5, 19.5, start=180, end=360, color=color)
        c.circle(12.0, 12.0, radius=3.5, outline=color)
        c.circle(12.0, 12.0, radius=1.4, fill=color)

    @staticmethod
    def _draw_play(c: IconCanvas, color: str):
        """Play: Right-pointing triangle with optical centroid balance"""
        pts = [(8.5, 5.5), (18.5, 12.0), (8.5, 18.5)]
        c.polygon(pts, fill=color)

    @staticmethod
    def _draw_pause(c: IconCanvas, color: str):
        """Pause: Dual vertical pill bars with consistent spacing"""
        c.rect(7.0, 5.5, 10.0, 18.5, radius=1.5, fill=color)
        c.rect(14.0, 5.5, 17.0, 18.5, radius=1.5, fill=color)

    @staticmethod
    def _draw_stop(c: IconCanvas, color: str):
        """Stop: Solid rounded square optically balanced against play/pause"""
        c.rect(6.0, 6.0, 18.0, 18.0, radius=2.5, fill=color)

    @staticmethod
    def _draw_info(c: IconCanvas, color: str):
        """Info: Circular badge with upper dot and information stem"""
        c.circle(12.0, 12.0, radius=9.0, outline=color)
        c.circle(12.0, 7.5, radius=1.2, fill=color)
        c.line((12.0, 11.0), (12.0, 16.5), color=color)
        c.line((10.5, 16.5), (13.5, 16.5), color=color)

    @staticmethod
    def _draw_circle(c: IconCanvas, color: str):
        """Circle: Solid status dot for presence and badges"""
        c.circle(12.0, 12.0, radius=6.5, fill=color)

    @staticmethod
    def _draw_circle_outline(c: IconCanvas, color: str):
        """Circle Outline: Hollow circle for idle/pending status"""
        c.circle(12.0, 12.0, radius=8.0, outline=color)

    @staticmethod
    def _draw_mute(c: IconCanvas, color: str):
        """Mikrofon o'chirilgan — diagonal chiziq bilan"""
        c.rect(9.5, 4.0, 14.5, 13.0, radius=2.5, outline=color)
        c.arc(7.0, 8.0, 17.0, 17.0, start=0, end=180, color=color)
        c.line((12.0, 17.0), (12.0, 19.5), color=color)
        c.line((9.0, 19.5), (15.0, 19.5), color=color)
        c.line((5.0, 19.0), (19.0, 5.0), color=color)

    @staticmethod
    def _draw_arrow_back(c: IconCanvas, color: str):
        """Chapga strelka"""
        c.polyline([(14.0, 5.0), (7.0, 12.0), (14.0, 19.0)], color=color)

    @staticmethod
    def _draw_arrow_forward(c: IconCanvas, color: str):
        """O'ngga strelka"""
        c.polyline([(10.0, 5.0), (17.0, 12.0), (10.0, 19.0)], color=color)

    @staticmethod
    def _draw_notification(c: IconCanvas, color: str):
        """Qo'ng'iroq (bildirishnoma)"""
        c.arc(6.0, 3.0, 18.0, 16.0, start=180, end=360, color=color)
        c.line((6.0, 9.5), (6.0, 17.0), color=color)
        c.line((18.0, 9.5), (18.0, 17.0), color=color)
        c.line((4.5, 17.0), (19.5, 17.0), color=color)
        c.circle(12.0, 20.0, radius=1.5, fill=color)

    @staticmethod
    def _draw_switch_mode(c: IconCanvas, color: str):
        """Almashtirish (↔)"""
        c.polyline([(4.0, 9.0), (8.0, 5.0), (8.0, 13.0)], color=color)
        c.line((8.0, 9.0), (20.0, 9.0), color=color)
        c.polyline([(20.0, 15.0), (16.0, 19.0), (16.0, 11.0)], color=color)
        c.line((4.0, 15.0), (16.0, 15.0), color=color)

    @staticmethod
    def _draw_chevron_down(c: IconCanvas, color: str):
        """Pastga chevron"""
        c.polyline([(7.0, 9.0), (12.0, 15.0), (17.0, 9.0)], color=color)

    REGISTRY: Tuple[str, ...] = (
        "dashboard",
        "chat",
        "mic",
        "commands",
        "memory",
        "scheduler",
        "plugins",
        "settings",
        "search",
        "attach",
        "send",
        "trash",
        "close",
        "minimize",
        "maximize",
        "restore",
        "check",
        "plus",
        "copy",
        "sparkles",
        "refresh",
        "folder",
        "eye",
        "play",
        "pause",
        "stop",
        "info",
        "circle",
        "circle_outline",
        "mute",
        "arrow_back",
        "arrow_forward",
        "notification",
        "switch_mode",
        "chevron_down",
    )

    SEMANTIC_ALIASES: Dict[str, str] = {
        # Window control aliases
        "win_minimize": "minimize",
        "win_min": "minimize",
        "win_maximize": "maximize",
        "win_max": "maximize",
        "win_restore": "restore",
        "win_close": "close",
        "window_close": "close",
        "window_min": "minimize",
        "window_max": "maximize",
        "window_restore": "restore",

        # English aliases
        "home": "dashboard",
        "voice": "mic",
        "microphone": "mic",
        "mic_off": "mute",
        "vision": "eye",
        "view": "eye",
        "delete": "trash",
        "remove": "trash",
        "trash-2": "trash",
        "add": "plus",
        "create": "plus",
        "edit": "info",
        "details": "info",
        "history": "scheduler",
        "timer": "scheduler",
        "alarm": "scheduler",
        "calendar": "scheduler",
        "save": "check",
        "disk": "check",
        "file": "folder",
        "directory": "folder",
        "open": "folder",
        "ai": "sparkles",
        "robot": "sparkles",
        "star": "sparkles",
        "bullet": "circle",
        "dot": "circle",
        "status": "circle",
        "x": "close",
        "cancel": "close",
        "back": "arrow_back",
        "forward": "arrow_forward",
        "bell": "notification",
        "alert": "notification",
        "swap": "switch_mode",
        "toggle": "switch_mode",
        "dropdown": "chevron_down",
        "expand": "chevron_down",

        # Unicode Symbols & Decorative Glyphs
        "✦": "sparkles",
        "★": "sparkles",
        "✨": "sparkles",
        "⚡": "commands",
        "●": "circle",
        "•": "circle",
        "○": "circle",
        "◌": "circle",
        "⌕": "search",
        "🔍": "search",
        "🔎": "search",
        "💬": "chat",
        "💭": "chat",
        "🧠": "memory",
        "⚙️": "settings",
        "⚙": "settings",
        "🔌": "plugins",
        "⏰": "scheduler",
        "🕐": "scheduler",
        "🗓️": "scheduler",
        "🗓": "scheduler",
        "🎤": "mic",
        "🎙️": "mic",
        "🎙": "mic",
        "🗑️": "trash",
        "🗑": "trash",
        "📁": "folder",
        "📂": "folder",
        "📎": "attach",
        "➤": "send",
        "➕": "plus",
        "💾": "check",
        "✅": "check",
        "✓": "check",
        "❌": "close",
        "✕": "close",
        "❐": "copy",
        "🔁": "refresh",
        "🔄": "refresh",
        "♻️": "refresh",
        "♻": "refresh",
        "👁️": "eye",
        "👁": "eye",
        "ℹ️": "info",
        "ℹ": "info",
        "💡": "sparkles",
        "🌐": "search",
        "🔧": "settings",
        "💻": "commands",
        "🎵": "play",
        "🌤️": "sparkles",
        "🌤": "sparkles",
        "📌": "commands",
        "📚": "memory",
        "📦": "plugins",
        "🧩": "plugins",
        "🧰": "commands",
        "📋": "commands",
        "📝": "info",
        "👤": "settings",
        "🧑": "settings",
        "🤖": "sparkles",
        "📤": "send",
        "📥": "folder",
        "▶": "play",
        "⏸": "pause",
        "⏹": "stop",
    }

    @classmethod
    def resolve_icon_name(cls, name: Optional[str], fallback: str = "sparkles") -> str:
        """Resolve any semantic name, legacy symbol, or emoji to a canonical vector icon name"""
        if not name or not isinstance(name, str):
            return fallback
        raw = name.strip()
        if raw in cls.SEMANTIC_ALIASES:
            return cls.SEMANTIC_ALIASES[raw]
        clean = raw.lower()
        if clean in cls.REGISTRY:
            return clean
        if clean in cls.SEMANTIC_ALIASES:
            return cls.SEMANTIC_ALIASES[clean]
        return fallback

    @classmethod
    def get_image(
        cls,
        name: Optional[str],
        size: Union[int, tuple, list] = 20,
        color_dark: str = "#FFFFFF",
        color_light: str = "#0F172A",
        color: Optional[str] = None,
        fallback: str = "sparkles",
        **kwargs,
    ) -> Optional[ctk.CTkImage]:
        if color is not None:
            color_dark = color
            color_light = color
        if isinstance(size, (tuple, list)):
            px_size = int(size[0]) if size else 20
        else:
            px_size = int(size)

        resolved = cls.resolve_icon_name(name, fallback=fallback)
        key = (resolved, px_size, color_dark, color_light)

        curr_root = getattr(tkinter, "_default_root", None)
        curr_root_id = id(curr_root) if curr_root is not None else None

        if key in cls._CTK_CACHE:
            cached_img = cls._CTK_CACHE[key]
            if getattr(cached_img, "_tk_root_id", None) == curr_root_id:
                return cached_img

        if key not in cls._PIL_CACHE:
            method_name = f"_draw_{resolved}"
            draw_func = getattr(cls, method_name, None)
            if not draw_func:
                fallback_resolved = cls.resolve_icon_name(fallback, fallback="sparkles")
                fallback_method = f"_draw_{fallback_resolved}"
                draw_func = getattr(cls, fallback_method, cls._draw_sparkles)

            canvas_stroke = compute_canvas_stroke(px_size, CANVAS_SIZE)

            # Render dark prototype on 96x96 canvas
            img_dark, draw_dark = cls._create_canvas()
            canvas_dark = IconCanvas(draw_dark, stroke=canvas_stroke)
            draw_func(canvas_dark, color_dark)
            img_dark = img_dark.resize((px_size, px_size), Image.Resampling.LANCZOS)

            # Render light prototype on 96x96 canvas
            img_light, draw_light = cls._create_canvas()
            canvas_light = IconCanvas(draw_light, stroke=canvas_stroke)
            draw_func(canvas_light, color_light)
            img_light = img_light.resize((px_size, px_size), Image.Resampling.LANCZOS)

            cls._PIL_CACHE[key] = (img_light, img_dark)

        img_light, img_dark = cls._PIL_CACHE[key]
        ctk_img = ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=(px_size, px_size))
        ctk_img._tk_root_id = curr_root_id
        cls._CTK_CACHE[key] = ctk_img
        return ctk_img

    @classmethod
    def get_pil_images(
        cls,
        name: Optional[str],
        size: Union[int, tuple, list] = 20,
        color_dark: str = "#FFFFFF",
        color_light: str = "#0F172A",
        color: Optional[str] = None,
        fallback: str = "sparkles",
    ) -> Tuple[Image.Image, Image.Image]:
        """Returns (light_image, dark_image) PIL Image tuple for a given icon"""
        cls.get_image(name, size=size, color_dark=color_dark, color_light=color_light, color=color, fallback=fallback)
        if color is not None:
            color_dark = color
            color_light = color
        px_size = int(size[0]) if isinstance(size, (tuple, list)) else int(size)
        resolved = cls.resolve_icon_name(name, fallback=fallback)
        key = (resolved, px_size, color_dark, color_light)
        return cls._PIL_CACHE[key]

    @classmethod
    def clear_cache(cls):
        """Clears both PIL and CTkImage caches"""
        cls._PIL_CACHE.clear()
        cls._CTK_CACHE.clear()



def get_vector_icon(
    name: Optional[str],
    size: Union[int, tuple, list] = 20,
    color_dark: str = "#FFFFFF",
    color_light: str = "#0F172A",
    color: Optional[str] = None,
    fallback: str = "sparkles",
    **kwargs,
) -> Optional[ctk.CTkImage]:
    """Helper shortcut to get high-DPI vector CTkImage icon with fallback support"""
    return VectorIconEngine.get_image(
        name,
        size=size,
        color_dark=color_dark,
        color_light=color_light,
        color=color,
        fallback=fallback,
        **kwargs,
    )


IconEngine = VectorIconEngine

