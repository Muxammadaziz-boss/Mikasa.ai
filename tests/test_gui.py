# ========== test_gui.py ==========
# GUI ni mustaqil test qilish
# Ishga tushirish: python test_gui.py

import sys
import os

# Loyiha papkasini PATH ga qo'shish
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import MisaApp


def main():
    print("🔷 MISA AI — GUI Test ishga tushmoqda...")
    app = MisaApp()
    app.mainloop()
    print("✅ GUI yopildi.")


if __name__ == "__main__":
    main()
