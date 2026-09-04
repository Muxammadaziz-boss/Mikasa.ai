import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import time
import os
from datetime import datetime

class OvozliYordamchiGUI:
    def __init__(self, foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func):
        self.foydalanuvchi_ismi = foydalanuvchi_ismi
        self.ovoz_turi = ovoz_turi
        self.fon_xizmat_func = fon_xizmat_func
        self.ishga_tushgan = False
        self.root = None
        self.xabarlar_tarixi = []
        self.animatsiya_aktiv = False
        self.fon_thread = None

    def gui_qaytarish_funksiyasi(self, xabar):
        """Asosiy dasturdan xabarlarni qabul qilish"""
        self.xabarlar_tarixi.append({
            "vaqt": time.strftime('%H:%M:%S'),
            "xabar": xabar
        })
        # Thread-safe yangilanish
        if self.root:
            self.root.after(0, lambda: self.yangi_xabar(xabar))

    def gui_ishga_tushir(self, register_callback_func=None):
        # Asosiy dasturga qaytarish funksiyasini ro'yxatdan o'tkazish
        if register_callback_func:
            register_callback_func(self.gui_qaytarish_funksiyasi)
        
        # CustomTkinter sozlamalari
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("🎙️ Ovozli Yordamchi Pro v2.0")
        self.root.geometry("1100x800")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try:
            if os.path.exists('icon.ico'):
                self.root.iconbitmap('icon.ico')
        except:
            pass

        # Header
        header_frame = ctk.CTkFrame(self.root, height=120, corner_radius=0)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Logo va title
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(
            title_frame, 
            text="🎙️", 
            font=ctk.CTkFont(size=40, weight="bold"),
            text_color="#a78bfa"
        ).pack(side="left", padx=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Ovozli Yordamchi Pro", 
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#a78bfa"
        )
        title_label.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            title_frame, 
            text="v2.0", 
            font=ctk.CTkFont(size=12),
            text_color="#6366f1"
        ).pack(side="left", padx=10)

        # User info panel
        user_frame = ctk.CTkFrame(self.root, height=70)
        user_frame.pack(fill="x", padx=20, pady=10)
        user_frame.pack_propagate(False)
        
        info_left = ctk.CTkFrame(user_frame, fg_color="transparent")
        info_left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(
            info_left,
            text=f"👤 {self.foydalanuvchi_ismi}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e2e8f0"
        ).pack(side="left", padx=15)
        
        ctk.CTkLabel(
            info_left,
            text=f"📊 {self.ovoz_turi.capitalize()}",
            font=ctk.CTkFont(size=11),
            text_color="#cbd5e1"
        ).pack(side="left", padx=15)
        
        # Real-time clock
        self.clock_label = ctk.CTkLabel(
            user_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#a78bfa"
        )
        self.clock_label.pack(side="right", padx=20, pady=15)
        self.update_clock()

        # Status panel
        status_frame = ctk.CTkFrame(self.root, height=80)
        status_frame.pack(fill="x", padx=20, pady=10)
        status_frame.pack_propagate(False)
        
        # Status indicator
        indicator_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        indicator_frame.pack(side="left", padx=20, pady=20)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="🔴 Tizim tayyor. 'Boshlash' tugmasini bosing",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ef4444"
        )
        self.status_label.pack(side="left", padx=15, pady=20)
        
        # Asosiy maydon
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Text area
        text_frame = ctk.CTkFrame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(
            text_frame,
            text="📋 Faoliyat Jurnali",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#a78bfa"
        ).pack(anchor="w", padx=15, pady=12)
        
        self.text_area = ctk.CTkTextbox(
            text_frame, 
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#e2e8f0",
            fg_color="#0f172a",
            border_width=0,
            corner_radius=8
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Text input area
        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", pady=(0, 10))
        
        self.entry_var = ctk.StringVar()
        self.entry_field = ctk.CTkEntry(
            input_frame,
            textvariable=self.entry_var,
            font=ctk.CTkFont(size=12),
            fg_color="#1e293b",
            text_color="white",
            border_width=0,
            corner_radius=8,
            height=40
        )
        self.entry_field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_field.bind("<Return>", self.text_cmd_yubor)
        
        self.btn_send = ctk.CTkButton(
            input_frame,
            text="Yuborish",
            command=self.text_cmd_yubor,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#6366f1",
            hover_color="#4f46e5",
            width=100,
            height=40,
            corner_radius=8
        )
        self.btn_send.pack(side="right")

        # Tugmalar paneli
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Birinchi qator - Asosiy boshqaruv
        control_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        control_frame.pack(pady=8)
        
        self.btn_start = ctk.CTkButton(
            control_frame,
            text="▶️ Boshlash",
            command=self.tinglashni_boshla,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#22c55e",
            hover_color="#16a34a",
            width=180,
            height=50,
            corner_radius=8
        )
        self.btn_start.pack(side="left", padx=8)
        
        self.btn_stop = ctk.CTkButton(
            control_frame,
            text="⏹️ To'xtat",
            command=self.tinglashni_to_xtat,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            width=180,
            height=50,
            corner_radius=8
        )
        self.btn_stop.pack(side="left", padx=8)
        
        self.btn_clear = ctk.CTkButton(
            control_frame,
            text="🗑️ Tozalash",
            command=self.maydonni_tozala,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#f59e0b",
            hover_color="#d97706",
            width=180,
            height=50,
            corner_radius=8
        )
        self.btn_clear.pack(side="left", padx=8)
        
        # Ikkinchi qator - Qo'shimcha funksiyalar
        tools_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        tools_frame.pack(pady=8)
        
        self.btn_history = ctk.CTkButton(
            tools_frame,
            text="📊 Tarix",
            command=self.tarix_ko_rsat,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            width=140,
            height=40,
            corner_radius=8
        )
        self.btn_history.pack(side="left", padx=5)
        
        self.btn_reminders = ctk.CTkButton(
            tools_frame,
            text="📌 Eslatmalar",
            command=self.eslatmalar_ko_rsat,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#ec4899",
            hover_color="#db2777",
            width=140,
            height=40,
            corner_radius=8
        )
        self.btn_reminders.pack(side="left", padx=5)
        
        self.btn_stats = ctk.CTkButton(
            tools_frame,
            text="📈 Statistika",
            command=self.statistika_ko_rsat,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#06b6d4",
            hover_color="#0891b2",
            width=140,
            height=40,
            corner_radius=8
        )
        self.btn_stats.pack(side="left", padx=5)
        
        self.btn_help = ctk.CTkButton(
            tools_frame,
            text="❓ Yordam",
            command=self.yordam_ko_rsat,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#64748b",
            hover_color="#475569",
            width=140,
            height=40,
            corner_radius=8
        )
        self.btn_help.pack(side="left", padx=5)
        
        # Dasturni ishga tushirish
        self.root.mainloop()

    def on_closing(self):
        """Dasturni yopishdan oldin"""
        if self.ishga_tushgan:
            self.tinglashni_to_xtat()
        self.root.destroy()

    def update_clock(self):
        """Soatni yangilash"""
        if self.root:
            try:
                current_time = datetime.now().strftime('%H:%M:%S')
                self.clock_label.configure(text=f"🕐 {current_time}")
                self.root.after(1000, self.update_clock)
            except:
                pass

    def yangi_xabar(self, xabar):
        """GUI ga yangi xabar qo'shish"""
        try:
            vaqt_belgisi = time.strftime('%H:%M:%S')
            
            # Emoji va rang
            if "xatolik" in xabar.lower() or "error" in xabar.lower() or "❌" in xabar:
                color_tag = "error"
            elif "bajarildi" in xabar.lower() or "✅" in xabar:
                color_tag = "success"
            elif "⚠️" in xabar:
                color_tag = "warning"
            else:
                color_tag = "info"
            
            formatted_xabar = f"[{vaqt_belgisi}] {xabar}\n"
            
            # CustomTkinter da rangli text uchun
            self.text_area.insert(tk.END, formatted_xabar)
            self.text_area.see(tk.END)
        except:
            pass

    def text_cmd_yubor(self, event=None):
        text = self.entry_var.get().strip()
        if not text:
            return
        
        self.entry_var.set("")
        self.yangi_xabar(f"⌨️ Siz: {text}")
        
        # Asosiy funksiyaga yuborish
        try:
            import main
            threading.Thread(target=main.buyruqni_tushun, 
                             args=(text, self.foydalanuvchi_ismi, self.ovoz_turi),
                             daemon=True).start()
        except Exception as e:
            self.yangi_xabar(f"❌ Xatolik: {e}")

    def tinglashni_boshla(self):
        if not self.ishga_tushgan:
            self.ishga_tushgan = True
            self.animatsiya_aktiv = True
            
            # Statusni yangilash
            self.status_label.configure(text="🟢 Yordamchi ishlamoqda...", text_color="#22c55e")
            
            # Tugmalarni yangilash
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            
            # Fon xizmatini ishga tushirish
            self.fon_thread = threading.Thread(
                target=self._fon_xizmat_ishga_tushir,
                daemon=True
            )
            self.fon_thread.start()
            
            self.yangi_xabar("🚀 Yordamchi ishga tushdi!")
            self.yangi_xabar("🎤 Gapiring: 'YouTube och', 'Musiqa', 'Ovozni 50 qil' va h.k.")

    def _fon_xizmat_ishga_tushir(self):
        """Fon xizmatini ishga tushirish"""
        try:
            self.fon_xizmat_func(
                self.foydalanuvchi_ismi, 
                self.ovoz_turi, 
                self.gui_qaytarish_funksiyasi
            )
        except Exception as e:
            self.root.after(0, lambda: self.yangi_xabar(f"❌ Xatolik: {e}"))
            self.root.after(0, self.tinglashni_to_xtat)

    def tinglashni_to_xtat(self):
        self.ishga_tushgan = False
        self.animatsiya_aktiv = False
        
        # Statusni yangilash
        self.status_label.configure(text="🔴 Tizim to'xtatildi", text_color="#ef4444")
        
        # Tugmalarni yangilash
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        
        self.yangi_xabar("⏹️ Yordamchi to'xtatildi")

    def tarix_ko_rsat(self):
        try:
            with open("buyruqlar_tarixi.txt", "r", encoding="utf-8") as f:
                history = f.read()
            self.text_area.delete("1.0", tk.END)
            if history.strip():
                self.text_area.insert(tk.END, history)
            else:
                self.text_area.insert(tk.END, "🔭 Tarix bo'sh.")
        except FileNotFoundError:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, "❌ Tarix fayli topilmadi.")

    def eslatmalar_ko_rsat(self):
        try:
            with open("eslatmalar.txt", "r", encoding="utf-8") as f:
                reminders = f.read()
            self.text_area.delete("1.0", tk.END)
            if reminders.strip():
                self.text_area.insert(tk.END, reminders)
            else:
                self.text_area.insert(tk.END, "🔭 Eslatmalar yo'q.")
        except FileNotFoundError:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, "❌ Eslatmalar fayli yo'q.")

    def statistika_ko_rsat(self):
        """Statistika"""
        try:
            buyruqlar_soni = 0
            if os.path.exists("buyruqlar_tarixi.txt"):
                with open("buyruqlar_tarixi.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    buyruqlar_soni = len([line for line in lines if line.strip()])
            
            eslatmalar_soni = 0
            if os.path.exists("eslatmalar.txt"):
                with open("eslatmalar.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    eslatmalar_soni = len([line for line in lines if line.strip()])
            
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, "📊 STATISTIKA\n")
            self.text_area.insert(tk.END, "=" * 40 + "\n\n")
            self.text_area.insert(tk.END, f"🎯 Jami buyruqlar: {buyruqlar_soni}\n")
            self.text_area.insert(tk.END, f"📌 Eslatmalar: {eslatmalar_soni}\n")
            self.text_area.insert(tk.END, f"👤 Foydalanuvchi: {self.foydalanuvchi_ismi}\n")
            self.text_area.insert(tk.END, f"🎙️ Ovoz turi: {self.ovoz_turi}\n")
            self.text_area.insert(tk.END, f"\n🎯 Versiya: v2.2.5\n")
            self.text_area.insert(tk.END, f"🔧 Yangi: CustomTkinter, edge-tts, Windows Audio API\n")
            
        except Exception as e:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, f"❌ Xatolik: {e}")

    def yordam_ko_rsat(self):
        """Yordam oynasi"""
        yordam_win = ctk.CTkToplevel(self.root)
        yordam_win.title("ℹ️ Yordam - Buyruqlar Ro'yxati")
        yordam_win.geometry("600x500")
        
        # Scrollable text
        text_area = ctk.CTkTextbox(yordam_win, font=ctk.CTkFont(size=11))
        text_area.pack(fill="both", expand=True, padx=20, pady=20)
        
        buyruqlar = """
🎵 MUSIQA VA MEDIA:
  • "youtube" / "yutub" - YouTube ochish
  • "musiqa" / "qo'shiq" - Musiqa qidirish
  • "video qo'y" / "to'xtat" - Video boshqaruvi

🔊 OVOZ BOSHQARUV:
  • "ovozni 50 qil" - Ovoz darajasini o'rnatish
  • "ovozni oshir" - Ovozni ko'tarish
  • "ovozni pasaytir" - Ovozni pasaytirish
  • "o'chir" / "och" - Ovozni o'chirish/ochish

🌤️ MA'LUMOT:
  • "vaqt" / "soat" - Joriy vaqt
  • "sana" - Bugungi sana

📌 ESLATMALAR:
  • "eslatma" - Yangi eslatma
  • "eslatmalar" - Barcha eslatmalarni ko'rsatish

🤖 AI SUHBAT:
  • "ai" / "suhbat qil" - AI bilan suhbat

🔧 SISTEMA:
  • "kompyuterni o'chir" - Kompyuterni o'chirish
  • "ekranni yop" - Ekranni qulflash

📱 ILovalar:
  • "telegram" - Telegram ochish
  • "chrome" / "brave" - Brauzer ochish
  • "vs code" - VS Code ochish
  • "discord" - Discord ochish
        """
        
        text_area.insert("1.0", buyruqlar)
        text_area.configure(state="disabled")

    def maydonni_tozala(self):
        self.text_area.delete("1.0", tk.END)
        self.yangi_xabar("🗑️ Maydon tozalandi")


def gui_ishga_tushir(foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func, register_callback_func):
    """main.py dan chaqiriladigan wrapper funksiya"""
    app = OvozliYordamchiGUI(foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func)
    app.gui_ishga_tushir(register_callback_func)
