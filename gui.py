import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import os

class OvozliYordamchiGUI:
    def __init__(self, foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func):
        self.foydalanuvchi_ismi = foydalanuvchi_ismi
        self.ovoz_turi = ovoz_turi
        self.fon_xizmat_func = fon_xizmat_func
        self.ishga_tushgan = False
        self.root = None
        self.xabarlar_tarixi = []

    def gui_qaytarish_funksiyasi(self, xabar):
        """Asosiy dasturdan xabarlarni qabul qilish"""
        self.xabarlar_tarixi.append({
            "vaqt": time.strftime('%H:%M:%S'),
            "xabar": xabar
        })
        self.yangi_xabar(xabar)

    def gui_ishga_tushir(self):
        # Asosiy dasturga qaytarish funksiyasini ro'yxatdan o'tkazish
        import main
        main.gui_bilan_integratsiya(self.gui_qaytarish_funksiyasi)
        
        self.root = tk.Tk()
        self.root.title("🎙️ Ovozli Yordamchi")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(True, True)
        
        # Icon (agar mavjud bo'lsa)
        try:
            if os.path.exists('icon.ico'):
                self.root.iconbitmap('icon.ico')
        except:
            pass

        # Modern uslub
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Tugmalar uchun uslub
        self.style.configure("TButton", 
                           font=("Segoe UI", 11, "bold"),
                           padding=8,
                           foreground="white",
                           background="#16213e")
        self.style.map("TButton",
                      foreground=[('pressed', 'white'), ('active', 'white')],
                      background=[('pressed', '!disabled', '#0f3460'), ('active', '#1f4068')],
                      )

        # Header
        header_frame = tk.Frame(self.root, bg="#0f3460", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🎙️ Ovozli Yordamchi", 
            font=("Segoe UI", 20, "bold"),
            fg="#e94560", 
            bg="#0f3460"
        )
        title_label.pack(pady=15)

        # Status panel
        status_frame = tk.Frame(self.root, bg="#16213e", height=60)
        status_frame.pack(fill="x", padx=20, pady=10)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="🔴 Tizim tayyor. Boshlash tugmasini bosing",
            font=("Segoe UI", 12),
            fg="#e94560",
            bg="#16213e"
        )
        self.status_label.pack(side="left", padx=20, pady=15)
        
        # Asosiy maydon
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Text area
        self.text_area = scrolledtext.ScrolledText(
            main_frame, 
            width=100, 
            height=20, 
            font=("Consolas", 11),
            bg="#1f4068", 
            fg="#eeeeee", 
            insertbackground="white", 
            relief="flat",
            padx=15,
            pady=15
        )
        self.text_area.pack(fill="both", expand=True, pady=(0, 15))
        
        # Tugmalar paneli
        button_frame = tk.Frame(main_frame, bg="#1a1a2e")
        button_frame.pack(fill="x", pady=10)
        
        # Birinchi qator tugmalar
        row1_frame = tk.Frame(button_frame, bg="#1a1a2e")
        row1_frame.pack(fill="x", pady=5)
        
        self.btn_start = ttk.Button(
            row1_frame, 
            text="▶️ Boshlash", 
            command=self.tinglashni_boshla,
            style="TButton"
        )
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ttk.Button(
            row1_frame, 
            text="⏹️ To'xtatish", 
            command=self.tinglashni_to_xtat,
            style="TButton",
            state="disabled"
        )
        self.btn_stop.pack(side="left", padx=5)
        
        btn_history = ttk.Button(
            row1_frame, 
            text="📜 Tarix", 
            command=self.tarix_ko_rsat,
            style="TButton"
        )
        btn_history.pack(side="left", padx=5)
        
        btn_reminders = ttk.Button(
            row1_frame, 
            text="📌 Eslatmalar", 
            command=self.eslatmalar_ko_rsat,
            style="TButton"
        )
        btn_reminders.pack(side="left", padx=5)
        
        # Ikkinchi qator tugmalar
        row2_frame = tk.Frame(button_frame, bg="#1a1a2e")
        row2_frame.pack(fill="x", pady=5)
        
        btn_clear = ttk.Button(
            row2_frame, 
            text="🗑️ Tozalash", 
            command=self.maydonni_tozala,
            style="TButton"
        )
        btn_clear.pack(side="left", padx=5)
        
        btn_settings = ttk.Button(
            row2_frame, 
            text="⚙️ Sozlamalar", 
            command=self.sozlamalar_och,
            style="TButton"
        )
        btn_settings.pack(side="left", padx=5)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg="#0f3460", height=40)
        footer_frame.pack(fill="x")
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(
            footer_frame,
            text="💻 Barcha huquqlar himoyalangan | Ovozli Yordamchi v1.0",
            font=("Segoe UI", 9),
            fg="#e94560",
            bg="#0f3460"
        )
        footer_label.pack(side="right", padx=20, pady=10)

        self.root.mainloop()

    def yangi_xabar(self, xabar):
        """GUI ga yangi xabar qo'shish"""
        vaqt_belgisi = time.strftime('%H:%M:%S')
        formatted_xabar = f"[{vaqt_belgisi}] {xabar}"
        self.text_area.insert(tk.END, f"{formatted_xabar}\n")
        self.text_area.see(tk.END)
        self.text_area.update()

    def tinglashni_boshla(self):
        if not self.ishga_tushgan:
            self.ishga_tushgan = True
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            self.status_label.config(text="🟢 Tinglanmoqda...", fg="#4ade80")
            
            # Yangi thread da fon xizmatini ishga tushirish
            threading.Thread(target=self._fon_xizmat_ishga_tushir, daemon=True).start()
            
            self.yangi_xabar("🟢 Yordamchi ishga tushdi!")
            self.yangi_xabar("Gapiring: 'Yordamchi ...'")

    def _fon_xizmat_ishga_tushir(self):
        """Fon xizmatini ishga tushirish"""
        try:
            self.fon_xizmat_func(self.foydalanuvchi_ismi, self.ovoz_turi, self.gui_qaytarish_funksiyasi)
        except Exception as e:
            self.yangi_xabar(f"❌ Xatolik yuz berdi: {e}")
            self.tinglashni_to_xtat()

    def tinglashni_to_xtat(self):
        self.ishga_tushgan = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_label.config(text="🔴 To'xtatildi", fg="#e94560")
        self.yangi_xabar("⏹️ Yordamchi to'xtatildi")

    def tarix_ko_rsat(self):
        try:
            with open("buyruqlar_tarixi.txt", "r", encoding="utf-8") as f:
                history = f.read()
            self.text_area.delete(1.0, tk.END)
            if history.strip():
                self.text_area.insert(tk.END, "=== BUYRUQLAR TARIXI ===\n\n")
                self.text_area.insert(tk.END, history)
            else:
                self.text_area.insert(tk.END, "Tarix bo'sh.")
        except FileNotFoundError:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "Tarix fayli topilmadi.")

    def eslatmalar_ko_rsat(self):
        try:
            with open("eslatmalar.txt", "r", encoding="utf-8") as f:
                reminders = f.read()
            self.text_area.delete(1.0, tk.END)
            if reminders.strip():
                self.text_area.insert(tk.END, "=== ESLATMALAR ===\n\n")
                self.text_area.insert(tk.END, reminders)
            else:
                self.text_area.insert(tk.END, "Eslatmalar yo'q.")
        except FileNotFoundError:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "Eslatmalar fayli yo'q.")

    def maydonni_tozala(self):
        self.text_area.delete(1.0, tk.END)
        self.yangi_xabar("🗑️ Maydon tozalandi")

    def sozlamalar_och(self):
        messagebox.showinfo("Sozlamalar", "⚙️ Sozlamalar hozircha mavjud emas\nKeyingi versiyalarda qo'shiladi!")

# GUI ni ishga tushirish funksiyasi
def gui_ishga_tushir(foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func):
    app = OvozliYordamchiGUI(foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func)
    app.gui_ishga_tushir()