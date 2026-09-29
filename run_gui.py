# ========== run_gui.py ==========
# Misa AI — GUI ishga tushiruvchi skript

import os
import sys

# Toza geometriya — burchaklarda font glif to'rtburchaklari chiqmasligi uchun
from customtkinter.windows.widgets.core_rendering import DrawEngine
DrawEngine.preferred_drawing_method = "circle_shapes"

from gui.app import MisaApp

if __name__ == "__main__":
    print("🔷 MISA AI v9.0.0 — Apple Dark Minimal GUI ishga tushmoqda...")
    app = MisaApp(connect_backend=True)
    app.mainloop()
