import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import os
from datetime import datetime

class AnimatedButton(tk.Canvas):
    """Animatsiyali tugma"""
    def __init__(self, parent, text, command, bg_color, hover_color, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.current_color = bg_color
        
        # Tugma o'lchamlari
        self.width = kwargs.get('width', 150)
        self.height = kwargs.get('height', 45)
        self.configure(width=self.width, height=self.height, highlightthickness=0)
        
        # Gradient fon
        self.create_gradient()
        
        # Matn
        self.text_id = self.create_text(
            self.width // 2,
            self.height // 2,
            text=text,
            fill="white",
            font=("Segoe UI", 11, "bold")
        )
        
        # Event'lar
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
    
    def create_gradient(self):
        """Gradient fon yaratish"""
        self.configure(bg=self.bg_color)
        self.create_rectangle(0, 0, self.width, self.height, 
                            fill=self.bg_color, outline="", tags="bg")
    
    def on_enter(self, event):
        """Hover effekti"""
        self.animate_color(self.hover_color)
    
    def on_leave(self, event):
        """Hover tugashi"""
        self.animate_color(self.bg_color)
    
    def on_click(self, event):
        """Click effekti"""
        self.scale(1.05)
        self.after(100, lambda: self.scale(0.95))
        self.after(200, lambda: self.scale(1.0))
        self.after(250, self.command)
    
    def animate_color(self, target_color):
        """Rang animatsiyasi"""
        self.itemconfig("bg", fill=target_color)
    
    def scale(self, factor):
        """Tugmani katta/kichik qilish"""
        center_x, center_y = self.width // 2, self.height // 2
        self.scale("all", center_x, center_y, factor, factor)

class OvozliYordamchiGUI:
    def __init__(self, foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func):
        self.foydalanuvchi_ismi = foydalanuvchi_ismi
        self.ovoz_turi = ovoz_turi
        self.fon_xizmat_func = fon_xizmat_func
        self.ishga_tushgan = False
        self.root = None
        self.xabarlar_tarixi = []
        self.animatsiya_aktiv = False

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
        self.root.title("🎙️ Ovozli Yordamchi Pro v2.0")
        self.root.geometry("1100x800")
        self.root.configure(bg="#0a0e27")
        self.root.resizable(True, True)
        
        try:
            if os.path.exists('icon.ico'):
                self.root.iconbitmap('icon.ico')
        except:
            pass

        # Header
        header_frame = tk.Frame(self.root, bg="#1e1b4b", height=120)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Logo va title
        title_frame = tk.Frame(header_frame, bg="#1e1b4b")
        title_frame.pack(expand=True)
        
        tk.Label(
            title_frame, 
            text="🎙️", 
            font=("Segoe UI", 40),
            fg="#a78bfa", 
            bg="#1e1b4b"
        ).pack(side="left", padx=10)
        
        title_label = tk.Label(
            title_frame, 
            text="Ovozli Yordamchi Pro", 
            font=("Segoe UI", 26, "bold"),
            fg="#a78bfa", 
            bg="#1e1b4b"
        )
        title_label.pack(side="left")
        
        tk.Label(
            title_frame, 
            text="v2.0", 
            font=("Segoe UI", 12),
            fg="#6366f1", 
            bg="#1e1b4b"
        ).pack(side="left", padx=10)

        # User info panel
        user_frame = tk.Frame(self.root, bg="#1e293b", height=70)
        user_frame.pack(fill="x", padx=20, pady=10)
        user_frame.pack_propagate(False)
        
        info_left = tk.Frame(user_frame, bg="#1e293b")
        info_left.pack(side="left", padx=20, pady=15)
        
        tk.Label(
            info_left,
            text=f"👤 {self.foydalanuvchi_ismi}",
            font=("Segoe UI", 12, "bold"),
            fg="#e2e8f0",
            bg="#1e293b"
        ).pack(side="left", padx=15)
        
        tk.Label(
            info_left,
            text=f"🔊 {self.ovoz_turi.capitalize()}",
            font=("Segoe UI", 11),
            fg="#cbd5e1",
            bg="#1e293b"
        ).pack(side="left", padx=15)
        
        # Real-time clock
        self.clock_label = tk.Label(
            user_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            fg="#a78bfa",
            bg="#1e293b"
        )
        self.clock_label.pack(side="right", padx=20, pady=15)
        self.update_clock()

        # Status panel with animation
        status_frame = tk.Frame(self.root, bg="#0f172a", height=80)
        status_frame.pack(fill="x", padx=20, pady=10)
        status_frame.pack_propagate(False)
        
        # Status indicator (animated)
        indicator_frame = tk.Frame(status_frame, bg="#0f172a")
        indicator_frame.pack(side="left", padx=20, pady=20)
        
        self.status_circle = tk.Canvas(indicator_frame, width=24, height=24, 
                                       bg="#0f172a", highlightthickness=0)
        self.status_circle.pack()
        self.status_indicator = self.status_circle.create_oval(2, 2, 22, 22, 
                                                                fill="#ef4444", outline="")
        
        self.status_label = tk.Label(
            status_frame,
            text="🔴 Tizim tayyor. 'Boshlash' tugmasini bosing",
            font=("Segoe UI", 14, "bold"),
            fg="#ef4444",
            bg="#0f172a"
        )
        self.status_label.pack(side="left", padx=15, pady=20)
        
        # Asosiy maydon
        main_frame = tk.Frame(self.root, bg="#0a0e27")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Text area
        text_frame = tk.Frame(main_frame, bg="#1e293b", relief="flat", bd=2)
        text_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        tk.Label(
            text_frame,
            text="📝 Faoliyat Jurnali",
            font=("Segoe UI", 13, "bold"),
            fg="#a78bfa",
            bg="#1e293b"
        ).pack(anchor="w", padx=15, pady=12)
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame, 
            width=110, 
            height=20, 
            font=("Cascadia Code", 10),
            bg="#0f172a", 
            fg="#e2e8f0", 
            insertbackground="#a78bfa", 
            relief="flat",
            padx=15,
            pady=15,
            wrap=tk.WORD
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Animatsiyali tugmalar paneli
        button_frame = tk.Frame(main_frame, bg="#0a0e27")
        button_frame.pack(fill="x", pady=10)
        
        # Birinchi qator - Asosiy boshqaruv
        control_frame = tk.Frame(button_frame, bg="#0a0e27")
        control_frame.pack(pady=8)
        
        self.btn_start = AnimatedButton(
            control_frame,
            text="▶️ Boshlash",
            command=self.tinglashni_boshla,
            bg_color="#22c55e",
            hover_color="#16a34a",
            width=180,
            height=50
        )
        self.btn_start.pack(side="left", padx=8)
        
        self.btn_stop = AnimatedButton(
            control_frame,
            text="⏹️ To'xtatish",
            command=self.tinglashni_to_xtat,
            bg_color="#ef4444",
            hover_color="#dc2626",
            width=180,
            height=50
        )
        self.btn_stop.pack(side="left", padx=8)
        
        # Ikkinchi qator - Ma'lumotlar
        data_frame = tk.Frame(button_frame, bg="#0a0e27")
        data_frame.pack(pady=8)
        
        AnimatedButton(
            data_frame,
            text="📜 Tarix",
            command=self.tarix_ko_rsat,
            bg_color="#3b82f6",
            hover_color="#2563eb",
            width=140,
            height=45
        ).pack(side="left", padx=5)
        
        AnimatedButton(
            data_frame,
            text="📌 Eslatmalar",
            command=self.eslatmalar_ko_rsat,
            bg_color="#8b5cf6",
            hover_color="#7c3aed",
            width=140,
            height=45
        ).pack(side="left", padx=5)
        
        AnimatedButton(
            data_frame,
            text="📊 Statistika",
            command=self.statistika_ko_rsat,
            bg_color="#06b6d4",
            hover_color="#0891b2",
            width=140,
            height=45
        ).pack(side="left", padx=5)
        
        AnimatedButton(
            data_frame,
            text="ℹ️ Yordam",
            command=self.yordam_ko_rsat,
            bg_color="#f59e0b",
            hover_color="#d97706",
            width=140,
            height=45
        ).pack(side="left", padx=5)
        
        # Uchinchi qator - Qo'shimcha
        extra_frame = tk.Frame(button_frame, bg="#0a0e27")
        extra_frame.pack(pady=8)
        
        AnimatedButton(
            extra_frame,
            text="🗑️ Tozalash",
            command=self.maydonni_tozala,
            bg_color="#64748b",
            hover_color="#475569",
            width=140,
            height=45
        ).pack(side="left", padx=5)
        
        AnimatedButton(
            extra_frame,
            text="⚙️ Sozlamalar",
            command=self.sozlamalar_och,
            bg_color="#6366f1",
            hover_color="#4f46e5",
            width=140,
            height=45
        ).pack(side="left", padx=5)

        # Footer
        footer_frame = tk.Frame(self.root, bg="#1e1b4b", height=55)
        footer_frame.pack(fill="x")
        footer_frame.pack_propagate(False)
        
        tk.Label(
            footer_frame,
            text="💻 Ovozli Yordamchi Pro v2.0 | NirCmd + OpenRouter AI | © 2024",
            font=("Segoe UI", 9),
            fg="#a78bfa",
            bg="#1e1b4b"
        ).pack(pady=18)

        # Xush kelibsiz xabari
        self.yangi_xabar("🎉 Ovozli Yordamchi Pro v2.0 ishga tayyor!")
        self.yangi_xabar("✨ Yangi: NirCmd ovoz boshqaruvi, musiqa platformalari, video koordinatalari")
        self.yangi_xabar("💡 'Boshlash' tugmasini bosing va ovozli buyruq bering")

        self.root.mainloop()

    def update_clock(self):
        """Soatni yangilash"""
        if self.root:
            current_time = datetime.now().strftime('%H:%M:%S')
            self.clock_label.config(text=f"🕐 {current_time}")
            self.root.after(1000, self.update_clock)

    def animate_status(self):
        """Status indikatori animatsiyasi (pulsatsiya)"""
        if self.animatsiya_aktiv and self.ishga_tushgan:
            colors = ['#22c55e', '#4ade80', '#86efac', '#4ade80']
            for i, color in enumerate(colors):
                if self.ishga_tushgan:
                    self.status_circle.itemconfig(self.status_indicator, fill=color)
                    # O'lchamni o'zgartirish (pulsatsiya)
                    sizes = [2, 1, 0, 1]
                    size = sizes[i]
                    self.status_circle.coords(self.status_indicator, 
                                             2-size, 2-size, 22+size, 22+size)
                    self.root.update()
                    time.sleep(0.2)
            if self.ishga_tushgan:
                self.root.after(100, self.animate_status)

    def yangi_xabar(self, xabar):
        """GUI ga yangi xabar qo'shish"""
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
        
        # Rang teglari
        self.text_area.tag_config("error", foreground="#ef4444")
        self.text_area.tag_config("success", foreground="#22c55e")
        self.text_area.tag_config("warning", foreground="#f59e0b")
        self.text_area.tag_config("info", foreground="#60a5fa")
        
        self.text_area.insert(tk.END, formatted_xabar, color_tag)
        self.text_area.see(tk.END)
        self.text_area.update()

    def tinglashni_boshla(self):
        if not self.ishga_tushgan:
            self.ishga_tushgan = True
            self.animatsiya_aktiv = True
            
            # Status o'zgartirish
            self.status_circle.itemconfig(self.status_indicator, fill="#22c55e")
            self.status_label.config(text="🟢 Faol tinglanmoqda...", fg="#22c55e")
            
            # Animatsiyani boshlash
            threading.Thread(target=self.animate_status, daemon=True).start()
            
            # Fon xizmatini ishga tushirish
            threading.Thread(target=self._fon_xizmat_ishga_tushir, daemon=True).start()
            
            self.yangi_xabar("🚀 Yordamchi ishga tushdi!")
            self.yangi_xabar("🎤 Gapiring: 'YouTube och', 'Musiqa', 'Ovozni 50 qil' va h.k.")

    def _fon_xizmat_ishga_tushir(self):
        """Fon xizmatini ishga tushirish"""
        try:
            self.fon_xizmat_func(self.foydalanuvchi_ismi, self.ovoz_turi, self.gui_qaytarish_funksiyasi)
        except Exception as e:
            self.yangi_xabar(f"❌ Xatolik: {e}")
            self.tinglashni_to_xtat()

    def tinglashni_to_xtat(self):
        self.ishga_tushgan = False
        self.animatsiya_aktiv = False
        
        # Status o'zgartirish
        self.status_circle.itemconfig(self.status_indicator, fill="#ef4444")
        self.status_label.config(text="🔴 To'xtatildi", fg="#ef4444")
        
        self.yangi_xabar("⏹️ Yordamchi to'xtatildi")

    def tarix_ko_rsat(self):
        try:
            with open("buyruqlar_tarixi.txt", "r", encoding="utf-8") as f:
                history = f.read()
            self.text_area.delete(1.0, tk.END)
            if history.strip():
                self.text_area.insert(tk.END, "═══════════════════════════════════════\n")
                self.text_area.insert(tk.END, "           📜 BUYRUQLAR TARIXI\n")
                self.text_area.insert(tk.END, "═══════════════════════════════════════\n\n")
                self.text_area.insert(tk.END, history)
            else:
                self.text_area.insert(tk.END, "📭 Tarix bo'sh.")
        except FileNotFoundError:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "❌ Tarix fayli topilmadi.")

    def eslatmalar_ko_rsat(self):
        try:
            with open("eslatmalar.txt", "r", encoding="utf-8") as f:
                reminders = f.read()
            self.text_area.delete(1.0, tk.END)
            if reminders.strip():
                self.text_area.insert(tk.END, "═══════════════════════════════════════\n")
                self.text_area.insert(tk.END, "              📌 ESLATMALAR\n")
                self.text_area.insert(tk.END, "═══════════════════════════════════════\n\n")
                self.text_area.insert(tk.END, reminders)
            else:
                self.text_area.insert(tk.END, "📭 Eslatmalar yo'q.")
        except FileNotFoundError:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "❌ Eslatmalar fayli yo'q.")

    def statistika_ko_rsat(self):
        """Statistika"""
        try:
            buyruqlar_soni = 0
            if os.path.exists("buyruqlar_tarixi.txt"):
                with open("buyruqlar_tarixi.txt", "r", encoding="utf-8") as f:
                    buyruqlar_soni = len(f.readlines())
            
            eslatmalar_soni = 0
            if os.path.exists("eslatmalar.txt"):
                with open("eslatmalar.txt", "r", encoding="utf-8") as f:
                    eslatmalar_soni = len([line for line in f if line.strip()])
            
            xabarlar_soni = len(self.xabarlar_tarixi)
            
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "═══════════════════════════════════════\n")
            self.text_area.insert(tk.END, "              📊 STATISTIKA\n")
            self.text_area.insert(tk.END, "═══════════════════════════════════════\n\n")
            self.text_area.insert(tk.END, f"👤 Foydalanuvchi: {self.foydalanuvchi_ismi}\n")
            self.text_area.insert(tk.END, f"🔊 Ovoz turi: {self.ovoz_turi.capitalize()}\n\n")
            self.text_area.insert(tk.END, f"📝 Jami buyruqlar: {buyruqlar_soni}\n")
            self.text_area.insert(tk.END, f"📌 Eslatmalar: {eslatmalar_soni}\n")
            self.text_area.insert(tk.END, f"💬 Joriy sessiya: {xabarlar_soni} xabar\n")
            self.text_area.insert(tk.END, f"⏰ Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.text_area.insert(tk.END, f"\n🎯 Versiya: v2.0.0\n")
            self.text_area.insert(tk.END, f"🔧 Yangi: NirCmd, Video koordinatalari, Platformalar\n")
            
        except Exception as e:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, f"❌ Xatolik: {e}")

    def yordam_ko_rsat(self):
        """Yordam oynasi"""
        yordam_win = tk.Toplevel(self.root)
        yordam_win.title("ℹ️ Yordam - Buyruqlar Ro'yxati")
        yordam_win.geometry("700x600")
        yordam_win.configure(bg="#0f172a")
        
        tk.Label(
            yordam_win, 
            text="📚 Buyruqlar Ro'yxati (v2.0)", 
            font=("Segoe UI", 18, "bold"),
            fg="#a78bfa", 
            bg="#0f172a"
        ).pack(pady=15)
        
        text = scrolledtext.ScrolledText(
            yordam_win, 
            width=80, 
            height=30,
            font=("Segoe UI", 10),
            bg="#1e293b",
            fg="#e2e8f0",
            wrap=tk.WORD
        )
        text.pack(padx=20, pady=10, fill="both", expand=True)
        
        buyruqlar = """
🎬 YouTube:
  • "yutub" - YouTube ochish
  • "1-video" / "2-video" - Video raqami bo'yicha ochish
  • "video qo'y" - Video ijro etish (play)
  • "to'xtat" / "pauza" - Videoni to'xtatish

🎵 Musiqa (Yangi!):
  • "musiqa" - Platform tanlash: YouTube, Yandex Music, Spotify
  • Misol: "musiqa" → "Yandex" → "Sevinch Mo'minova"

🔊 Ovoz Boshqaruvi (NirCmd - Yangi!):
  • "ovozni 50 qil" - 50% ga o'rnatish
  • "ovoz 30" - 30% ga o'rnatish
  • "ovozni oshir 5" - 5% oshirish
  • "ovozni pasaytir 10" - 10% kamaytirish
  • "ovozni o'chir" - Mute
  • "ovozni och" - Unmute

💬 Messenjlar:
  • "telegram" - Telegram
  • "discord" - Discord

🌤️ Ma'lumot:
  • "vaqt" / "soat" - Joriy vaqt
  • "sana" - Bugungi sana

📌 Eslatmalar:
  • "eslatma" - Yangi eslatma
  • "eslatmalar" - Eslatmalar ro'yxati

🤖 AI Suhbat:
  • "ai" / "suhbat qil" - OpenRouter AI bilan suhbat

💡 Maslahatlar:
  • Aniq va ravon gapiring
  • Raqamlarni to'g'ri talaffuz qiling
  • "Bajarildi" ovozi eshitilsa, buyruq muvaffaqiyatli bajarildi
        """
        
        text.insert(tk.END, buyruqlar)
        text.config(state="disabled")

    def maydonni_tozala(self):
        self.text_area.delete(1.0, tk.END)
        self.yangi_xabar("🗑️ Maydon tozalandi")

    def sozlamalar_och(self):
        messagebox.showinfo(
            "Sozlamalar", 
            "⚙️ Sozlamalar:\n\n"
            "✅ NirCmd o'rnatilganligini tekshiring\n"
            "✅ .env faylidagi API kalitlarni tekshiring\n"
            "✅ Mikrofonga ruxsat berilganligini tekshiring\n\n"
            "Qo'shimcha sozlamalar keyingi versiyada!"
        )

def gui_ishga_tushir(foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func):
    app = OvozliYordamchiGUI(foydalanuvchi_ismi, ovoz_turi, fon_xizmat_func)
    app.gui_ishga_tushir()