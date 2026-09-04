# ========== scheduler.py ==========
# Scheduler sahifasi — vaqtli vazifalar va eslatmalar

import customtkinter as ctk
import datetime
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, GlowButton, SecondaryButton


class SchedulerPage(ctk.CTkFrame):
    """Vaqtli vazifalar rejalashtiruvchisi"""
    
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._tasks = []
        self._build_ui()
    
    def _build_ui(self):
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))
        
        ctk.CTkLabel(
            header, text="⏰  Rejalashtiruvchi",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left")
        
        self.task_count_label = ctk.CTkLabel(
            header, text="0 ta aktiv vazifa",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED
        )
        self.task_count_label.pack(side="right")
        
        # ===== KONTENT — 2 COLUMN =====
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)
        
        # --- CHAP: VAZIFALAR ---
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self._build_add_form(left)
        self._build_task_list(left)
        
        # --- O'NG: TIMELINE ---
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        
        self._build_timeline(right)
    
    def _build_add_form(self, parent):
        """Yangi vazifa qo'shish formasi"""
        form_card = GlassCard(parent, title="➕  Yangi vazifa")
        form_card.pack(fill="x", pady=(0, 10))
        
        # Vazifa matni
        ctk.CTkLabel(
            form_card.content, text="Matn",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", pady=(0, 4))
        
        self.task_text = ctk.CTkEntry(
            form_card.content,
            placeholder_text="Masalan: Suv ichish",
            font=Fonts.BODY,
            fg_color=Colors.BG_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=36
        )
        self.task_text.pack(fill="x", pady=(0, 8))
        
        # Vaqt
        ctk.CTkLabel(
            form_card.content, text="Vaqt ifodasi",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", pady=(0, 4))
        
        self.task_time = ctk.CTkEntry(
            form_card.content,
            placeholder_text="5 daqiqadan keyin / soat 14:00",
            font=Fonts.BODY,
            fg_color=Colors.BG_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=36
        )
        self.task_time.pack(fill="x", pady=(0, 8))
        
        # Turi
        ctk.CTkLabel(
            form_card.content, text="Turi",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", pady=(0, 4))
        
        self.task_type = ctk.CTkSegmentedButton(
            form_card.content,
            values=["📌 Eslatma", "⚡ Buyruq", "🔁 Takroriy"],
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            selected_color=Colors.PRIMARY_DARK,
            selected_hover_color=Colors.PRIMARY,
            unselected_color=Colors.BG_INPUT,
            unselected_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY
        )
        self.task_type.set("📌 Eslatma")
        self.task_type.pack(fill="x", pady=(0, 12))
        
        # Tugma
        GlowButton(
            form_card.content, text="Qo'shish", icon="➕",
            command=self._add_task
        ).pack(fill="x")
    
    def _build_task_list(self, parent):
        """Aktiv vazifalar ro'yxati"""
        list_card = GlassCard(parent, title="📋  Aktiv vazifalar")
        list_card.pack(fill="both", expand=True, pady=(10, 0))
        
        self.tasks_scroll = ctk.CTkScrollableFrame(
            list_card.content, fg_color="transparent"
        )
        self.tasks_scroll.pack(fill="both", expand=True)
        
        # Bo'sh holat
        self.empty_label = ctk.CTkLabel(
            self.tasks_scroll,
            text="Hali vazifa yo'q\nYuqoridagi formadan qo'shing",
            font=Fonts.BODY,
            text_color=Colors.TEXT_MUTED
        )
        self.empty_label.pack(pady=30)
    
    def _build_timeline(self, parent):
        """Bugungi vaqt chizig'i"""
        timeline_card = GlassCard(parent, title="📅  Bugungi kun")
        timeline_card.pack(fill="both", expand=True)
        
        # Hozirgi vaqt
        now = datetime.datetime.now()
        ctk.CTkLabel(
            timeline_card.content,
            text=now.strftime("%d %B, %Y"),
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(0, 8))
        
        ctk.CTkLabel(
            timeline_card.content,
            text=now.strftime("%H:%M"),
            font=(Fonts.FAMILY, 36, "bold"),
            text_color=Colors.PRIMARY
        ).pack(pady=(0, 16))
        
        # Ajratgich
        ctk.CTkFrame(
            timeline_card.content,
            fg_color=Colors.BORDER, height=1
        ).pack(fill="x", pady=8)
        
        # Timeline
        self.timeline_list = ctk.CTkFrame(
            timeline_card.content, fg_color="transparent"
        )
        self.timeline_list.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            self.timeline_list,
            text="Bugun rejalashtirilgan\nvazifalar yo'q",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED
        ).pack(pady=20)
    
    # ========== FUNKSIYALAR ==========
    
    def _add_task(self):
        """Yangi vazifa qo'shish"""
        text = self.task_text.get().strip()
        time_expr = self.task_time.get().strip()
        
        if not text:
            return
        
        # Formani tozalash
        self.task_text.delete(0, "end")
        self.task_time.delete(0, "end")
        
        # Ro'yxatga qo'shish
        self._tasks.append({
            "text": text,
            "time": time_expr or "Belgilanmagan",
            "type": self.task_type.get()
        })
        
        self._refresh_task_list()
    
    def _refresh_task_list(self):
        """Vazifalar ro'yxatini yangilash"""
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()
        
        if not self._tasks:
            self.empty_label = ctk.CTkLabel(
                self.tasks_scroll,
                text="Hali vazifa yo'q",
                font=Fonts.BODY,
                text_color=Colors.TEXT_MUTED
            )
            self.empty_label.pack(pady=30)
            return
        
        for i, task in enumerate(self._tasks):
            row = ctk.CTkFrame(
                self.tasks_scroll,
                fg_color=Colors.BG_INPUT,
                corner_radius=8,
                border_width=1,
                border_color=Colors.BORDER
            )
            row.pack(fill="x", pady=3)
            
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=8)
            
            ctk.CTkLabel(
                inner, text=task["text"],
                font=Fonts.BODY,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w"
            ).pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                inner, text=task["time"],
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED
            ).pack(side="right", padx=(8, 0))
            
            # O'chirish tugma
            ctk.CTkButton(
                inner, text="✕",
                font=(Fonts.FAMILY, 12),
                fg_color="transparent",
                hover_color=Colors.DANGER,
                text_color=Colors.TEXT_MUTED,
                width=28, height=28,
                corner_radius=14,
                command=lambda idx=i: self._remove_task(idx)
            ).pack(side="right")
        
        self.task_count_label.configure(
            text=f"{len(self._tasks)} ta aktiv vazifa"
        )
    
    def _remove_task(self, index):
        """Vazifani o'chirish"""
        if 0 <= index < len(self._tasks):
            self._tasks.pop(index)
            self._refresh_task_list()
    
    def on_show(self):
        """Sahifa ko'rsatilganda"""
        pass
