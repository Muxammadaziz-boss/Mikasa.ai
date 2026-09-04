# ========== run_gui.py ==========
# Mikasa AI — GUI ishga tushiruvchi skript

import os
import sys

# Toza geometriya — burchaklarda font glif to'rtburchaklari chiqmasligi uchun
from customtkinter.windows.widgets.core_rendering import DrawEngine
DrawEngine.preferred_drawing_method = "circle_shapes"

from gui.app import MikasaApp

if __name__ == "__main__":
    print("🔷 MIKASA AI v6.0.0 — Apple Dark Minimal GUI ishga tushmoqda...")
    app = MikasaApp(connect_backend=True)
    app.mainloop()
