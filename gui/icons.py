# ========== icons.py ==========
# Mikasa AI — Professional Vector Iconography Engine
# Supersampled anti-aliased vector rendering via PIL and CTkImage.
# Eliminates platform-dependent emoji variations and provides consistent,
# high-DPI Lucide/Linear-style stroke icons.

import math
from typing import Dict, Optional, Tuple
from PIL import Image, ImageDraw
import customtkinter as ctk


class VectorIconEngine:
    """
    Renders clean, stroke-based vector icons at 4x supersampled resolution
    and scales down with Lanczos resampling for silky-smooth anti-aliasing.
    Caches PIL Image prototypes for instant, root-independent CTkImage creation.
    """

    _PIL_CACHE: Dict[Tuple, Tuple[Image.Image, Image.Image]] = {}

    @staticmethod
    def _create_canvas(s: int) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        return img, draw

    @staticmethod
    def _draw_dashboard(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pad = int(s * 0.16)
        gap = int(s * 0.12)
        box_w = (s - 2 * pad - gap) // 2
        r = int(box_w * 0.3)
        for row in range(2):
            for col in range(2):
                x0 = pad + col * (box_w + gap)
                y0 = pad + row * (box_w + gap)
                x1 = x0 + box_w
                y1 = y0 + box_w
                draw.rounded_rectangle([x0, y0, x1, y1], radius=r, outline=color, width=w)

    @staticmethod
    def _draw_chat(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        x0, y0 = int(s * 0.16), int(s * 0.18)
        x1, y1 = int(s * 0.84), int(s * 0.72)
        r = int(s * 0.18)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=r, outline=color, width=w)
        tail = [(int(s * 0.28), y1 - w // 2), (int(s * 0.20), int(s * 0.88)), (int(s * 0.44), y1 - w // 2)]
        draw.polygon(tail, fill=color)

    @staticmethod
    def _draw_mic(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        cx = s // 2
        x0, y0 = int(s * 0.38), int(s * 0.16)
        x1, y1 = int(s * 0.62), int(s * 0.56)
        r = (x1 - x0) // 2
        draw.rounded_rectangle([x0, y0, x1, y1], radius=r, outline=color, width=w)
        arc_box = [int(s * 0.26), int(s * 0.32), int(s * 0.74), int(s * 0.70)]
        draw.arc(arc_box, start=0, end=180, fill=color, width=w)
        stem_top = int(s * 0.70)
        stem_bot = int(s * 0.84)
        draw.line([(cx, stem_top), (cx, stem_bot)], fill=color, width=w)
        draw.line([(int(s * 0.34), stem_bot), (int(s * 0.66), stem_bot)], fill=color, width=w)

    @staticmethod
    def _draw_commands(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pts = [
            (int(s * 0.54), int(s * 0.12)),
            (int(s * 0.28), int(s * 0.50)),
            (int(s * 0.48), int(s * 0.50)),
            (int(s * 0.42), int(s * 0.88)),
            (int(s * 0.72), int(s * 0.44)),
            (int(s * 0.52), int(s * 0.44)),
        ]
        draw.polygon(pts, fill=color)

    @staticmethod
    def _draw_memory(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pad = int(s * 0.24)
        draw.rounded_rectangle([pad, pad, s - pad, s - pad], radius=int(s * 0.1), outline=color, width=w)
        core_pad = int(s * 0.38)
        draw.rectangle([core_pad, core_pad, s - core_pad, s - core_pad], fill=color)
        for p in [int(s * 0.38), int(s * 0.62)]:
            draw.line([(p, int(s * 0.12)), (p, pad)], fill=color, width=w)
            draw.line([(p, s - pad), (p, int(s * 0.88))], fill=color, width=w)
            draw.line([(int(s * 0.12), p), (pad, p)], fill=color, width=w)
            draw.line([(s - pad, p), (int(s * 0.88), p)], fill=color, width=w)

    @staticmethod
    def _draw_scheduler(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pad = int(s * 0.16)
        draw.ellipse([pad, pad, s - pad, s - pad], outline=color, width=w)
        cx, cy = s // 2, s // 2
        draw.line([(cx, cy), (cx, int(s * 0.30))], fill=color, width=w)
        draw.line([(cx, cy), (int(s * 0.68), cy)], fill=color, width=w)

    @staticmethod
    def _draw_plugins(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pad = int(s * 0.22)
        draw.rounded_rectangle([pad, pad, s - pad, s - pad], radius=int(s * 0.12), outline=color, width=w)
        cx, cy = s // 2, s // 2
        draw.ellipse([cx - int(s * 0.08), pad - int(s * 0.08), cx + int(s * 0.08), pad + int(s * 0.08)], fill=color)
        draw.ellipse([s - pad - int(s * 0.08), cy - int(s * 0.08), s - pad + int(s * 0.08), cy + int(s * 0.08)], fill=color)

    @staticmethod
    def _draw_settings(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        cx, cy = s // 2, s // 2
        r_outer = int(s * 0.36)
        r_inner = int(s * 0.26)
        r_hole = int(s * 0.14)
        for i in range(6):
            angle = i * (math.pi / 3)
            x1 = cx + math.cos(angle) * r_outer
            y1 = cy + math.sin(angle) * r_outer
            draw.circle((int(x1), int(y1)), radius=int(s * 0.07), fill=color)
        draw.circle((cx, cy), radius=r_inner, outline=color, width=w)
        draw.circle((cx, cy), radius=r_hole, outline=color, width=w)

    @staticmethod
    def _draw_attach(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        draw.line([(int(s * 0.35), int(s * 0.65)), (int(s * 0.65), int(s * 0.35))], fill=color, width=w)
        draw.line([(int(s * 0.45), int(s * 0.75)), (int(s * 0.75), int(s * 0.45))], fill=color, width=w)
        draw.line([(int(s * 0.25), int(s * 0.55)), (int(s * 0.55), int(s * 0.25))], fill=color, width=w)
        draw.arc([int(s * 0.55), int(s * 0.25), int(s * 0.75), int(s * 0.45)], start=225, end=45, fill=color, width=w)
        draw.arc([int(s * 0.25), int(s * 0.55), int(s * 0.45), int(s * 0.75)], start=45, end=225, fill=color, width=w)

    @staticmethod
    def _draw_send(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pts = [
            (int(s * 0.86), int(s * 0.14)),
            (int(s * 0.18), int(s * 0.46)),
            (int(s * 0.46), int(s * 0.54)),
            (int(s * 0.54), int(s * 0.82)),
        ]
        draw.polygon(pts, fill=color)
        draw.line([(int(s * 0.46), int(s * 0.54)), (int(s * 0.86), int(s * 0.14))], fill=color, width=w)

    @staticmethod
    def _draw_search(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        r = int(s * 0.24)
        cx, cy = int(s * 0.42), int(s * 0.42)
        draw.circle((cx, cy), radius=r, outline=color, width=w)
        hx0 = cx + int(r * 0.7)
        hy0 = cy + int(r * 0.7)
        hx1 = int(s * 0.82)
        hy1 = int(s * 0.82)
        draw.line([(hx0, hy0), (hx1, hy1)], fill=color, width=int(w * 1.3))

    @staticmethod
    def _draw_trash(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        x0, y0 = int(s * 0.28), int(s * 0.36)
        x1, y1 = int(s * 0.72), int(s * 0.82)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=int(s * 0.06), outline=color, width=w)
        draw.line([(int(s * 0.20), y0), (int(s * 0.80), y0)], fill=color, width=w)
        draw.line([(int(s * 0.42), int(s * 0.24)), (int(s * 0.58), int(s * 0.24))], fill=color, width=w)
        draw.line([(int(s * 0.42), int(s * 0.46)), (int(s * 0.42), int(s * 0.72))], fill=color, width=w)
        draw.line([(int(s * 0.58), int(s * 0.46)), (int(s * 0.58), int(s * 0.72))], fill=color, width=w)

    @staticmethod
    def _draw_close(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pad = int(s * 0.28)
        draw.line([(pad, pad), (s - pad, s - pad)], fill=color, width=w)
        draw.line([(s - pad, pad), (pad, s - pad)], fill=color, width=w)

    @staticmethod
    def _draw_check(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pts = [(int(s * 0.20), int(s * 0.52)), (int(s * 0.42), int(s * 0.74)), (int(s * 0.82), int(s * 0.26))]
        draw.line(pts, fill=color, width=w, joint="curve")

    @staticmethod
    def _draw_plus(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pad = int(s * 0.24)
        cx, cy = s // 2, s // 2
        draw.line([(cx, pad), (cx, s - pad)], fill=color, width=w)
        draw.line([(pad, cy), (s - pad, cy)], fill=color, width=w)

    @staticmethod
    def _draw_copy(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        draw.rounded_rectangle([int(s * 0.32), int(s * 0.32), int(s * 0.82), int(s * 0.82)], radius=int(s * 0.08), outline=color, width=w)
        draw.rounded_rectangle([int(s * 0.18), int(s * 0.18), int(s * 0.68), int(s * 0.68)], radius=int(s * 0.08), outline=color, width=w)

    @staticmethod
    def _draw_sparkles(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        cx, cy = s // 2, s // 2
        r_outer = int(s * 0.38)
        r_inner = int(s * 0.12)
        pts = []
        for i in range(8):
            r = r_outer if i % 2 == 0 else r_inner
            angle = i * (math.pi / 4)
            pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        draw.polygon(pts, fill=color)

    @staticmethod
    def _draw_refresh(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pad = int(s * 0.18)
        draw.arc([pad, pad, s - pad, s - pad], start=40, end=320, fill=color, width=w)
        arrow = [(int(s * 0.72), int(s * 0.22)), (int(s * 0.86), int(s * 0.28)), (int(s * 0.78), int(s * 0.44))]
        draw.polygon(arrow, fill=color)

    @staticmethod
    def _draw_folder(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        x0, y0 = int(s * 0.16), int(s * 0.32)
        x1, y1 = int(s * 0.84), int(s * 0.78)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=int(s * 0.08), outline=color, width=w)
        draw.polygon([(x0, y0), (int(s * 0.44), y0), (int(s * 0.52), int(s * 0.22)), (x0, int(s * 0.22))], fill=color)

    @staticmethod
    def _draw_eye(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        cx, cy = s // 2, s // 2
        draw.ellipse([int(s * 0.14), int(s * 0.30), int(s * 0.86), int(s * 0.70)], outline=color, width=w)
        draw.circle((cx, cy), radius=int(s * 0.12), fill=color)

    @staticmethod
    def _draw_play(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pts = [(int(s * 0.30), int(s * 0.20)), (int(s * 0.78), int(s * 0.50)), (int(s * 0.30), int(s * 0.80))]
        draw.polygon(pts, fill=color)

    @staticmethod
    def _draw_pause(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        w_bar = int(s * 0.14)
        draw.rounded_rectangle([int(s * 0.28), int(s * 0.22), int(s * 0.28) + w_bar, int(s * 0.78)], radius=2, fill=color)
        draw.rounded_rectangle([int(s * 0.58), int(s * 0.22), int(s * 0.58) + w_bar, int(s * 0.78)], radius=2, fill=color)

    @staticmethod
    def _draw_stop(draw: ImageDraw.ImageDraw, s: int, color: str, w: int):
        pad = int(s * 0.26)
        draw.rounded_rectangle([pad, pad, s - pad, s - pad], radius=int(s * 0.08), fill=color)

    @classmethod
    def get_image(
        cls,
        name: str,
        size: int = 20,
        color_dark: str = "#FFFFFF",
        color_light: str = "#0F172A",
    ) -> Optional[ctk.CTkImage]:
        key = (name.lower(), size, color_dark, color_light)
        if key not in cls._PIL_CACHE:
            method_name = f"_draw_{name.lower()}"
            if name.lower() == "delete":
                method_name = "_draw_trash"
            elif name.lower() in ("add", "plus"):
                method_name = "_draw_plus"
            elif name.lower() == "voice":
                method_name = "_draw_mic"
            elif name.lower() == "vision":
                method_name = "_draw_eye"

            draw_func = getattr(cls, method_name, None)
            if not draw_func:
                return None

            # Supersampled canvas (4x)
            scale = 4
            s_hi = size * scale
            stroke_w = max(2, int(scale * 1.8))

            # Render dark prototype
            img_dark, draw_dark = cls._create_canvas(s_hi)
            draw_func(draw_dark, s_hi, color_dark, stroke_w)
            img_dark = img_dark.resize((size, size), Image.Resampling.LANCZOS)

            # Render light prototype
            img_light, draw_light = cls._create_canvas(s_hi)
            draw_func(draw_light, s_hi, color_light, stroke_w)
            img_light = img_light.resize((size, size), Image.Resampling.LANCZOS)

            cls._PIL_CACHE[key] = (img_light, img_dark)

        img_light, img_dark = cls._PIL_CACHE[key]
        return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=(size, size))


def get_vector_icon(name: str, size: int = 20, color_dark: str = "#FFFFFF", color_light: str = "#0F172A") -> Optional[ctk.CTkImage]:
    """Helper shortcut to get high-DPI vector CTkImage icon"""
    return VectorIconEngine.get_image(name, size=size, color_dark=color_dark, color_light=color_light)
