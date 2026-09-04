# ========== memory.py ==========
# Memory Hub sahifasi — xotira boshqaruvi

import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
from gui.theme import Colors, Fonts
from gui.components import (
    EmptyState,
    GlassCard,
    GlowButton,
    PageHero,
    SearchBar,
    SecondaryButton,
    StatWidget,
)


class MemoryPage(ctk.CTkFrame):
    """AI xotira markazi — profil, bilimlar, tarix"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._profile_entries = {}
        self._knowledge_scroll = None
        self._history_scroll = None
        self._build_ui()

    def _build_ui(self):
        self.hero = PageHero(
            self,
            title="Xotira markazi",
            subtitle="Profil, bilimlar bazasi va suhbat tarixini bir joydan boshqaring.",
            icon="🧠",
            accent_color=Colors.SECONDARY,
            chips=[
                ("Uzoq muddatli xotira", "📚", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
                ("Suhbat bilan sinxron", "🔄", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
            ],
        )
        self.hero.pack(fill="x", padx=20, pady=(16, 12))

        SecondaryButton(
            self.hero.actions,
            text="Eksport",
            icon="📤",
            command=self._export_data,
        ).pack(anchor="e")

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 12))

        self._stat_widgets = []
        stats_data = [
            ("0", "Kontekst", "💭", Colors.PRIMARY),
            ("0", "Suhbatlar", "💬", Colors.SECONDARY),
            ("0", "Bilimlar", "📚", Colors.SUCCESS),
            ("Noaniq", "Profil", "👤", Colors.INFO),
        ]

        for i, (val, label, icon, color) in enumerate(stats_data):
            widget = StatWidget(
                stats_frame, value=val, label=label, icon=icon, color=color
            )
            widget.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            self._stat_widgets.append(widget)
            stats_frame.columnconfigure(i, weight=1)

        self.tabs = ctk.CTkTabview(
            self,
            fg_color=Colors.BG_SURFACE,
            segmented_button_fg_color=Colors.BG_INPUT,
            segmented_button_selected_color=Colors.PRIMARY_DARK,
            segmented_button_selected_hover_color=Colors.PRIMARY,
            segmented_button_unselected_color=Colors.BG_INPUT,
            segmented_button_unselected_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        tab1 = self.tabs.add("👤 Profil")
        tab2 = self.tabs.add("📚 Bilimlar")
        tab3 = self.tabs.add("💬 Suhbat tarixi")

        self._build_profile_tab(tab1)
        self._build_knowledge_tab(tab2)
        self._build_history_tab(tab3)

    def _build_profile_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        summary = GlassCard(
            scroll,
            title="Profil holati",
            subtitle="Mikasa sizni to'g'ri taniy olishi uchun asosiy ma'lumotlarni saqlang.",
            accent_color=Colors.INFO,
        )
        summary.pack(fill="x", padx=16, pady=(16, 12))

        self.profile_status = ctk.CTkLabel(
            summary.content,
            text="Profil ma'lumotlari yuklanmoqda...",
            font=Fonts.BODY,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.profile_status.pack(fill="x")

        form_card = GlassCard(
            scroll,
            title="Asosiy maydonlar",
            subtitle="Bu qiymatlar ovozli dialog, chat va agent xotirasida ishlatiladi.",
            accent_color=Colors.PRIMARY,
        )
        form_card.pack(fill="x", padx=16, pady=(0, 16))

        self._profile_entries["user.name"] = self._add_profile_entry(
            form_card.content, "Ism", "Foydalanuvchi"
        )
        self._profile_entries["user.voice_type"] = self._add_profile_option(
            form_card.content, "Ovoz turi", ["erkak", "ayol"], "erkak"
        )
        self._profile_entries["user.language"] = self._add_profile_entry(
            form_card.content, "Til", "O'zbek"
        )

        self.profile_save_btn = GlowButton(
            form_card.content,
            text="Saqlash",
            icon="💾",
            command=self._save_profile,
        )
        self.profile_save_btn.pack(anchor="e", pady=(10, 0))

    def _build_knowledge_tab(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 12))

        self.knowledge_search = SearchBar(
            top, placeholder="Kalit, qiymat yoki tag qidiring..."
        )
        self.knowledge_search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.knowledge_search.entry.bind(
            "<KeyRelease>", lambda e: self._refresh_knowledge()
        )

        add_card = GlassCard(
            parent,
            title="Yangi bilim qo'shish",
            subtitle="Kalit va qiymat kiriting. Bu ma'lumot keyingi suhbatlarda ishlatiladi.",
            accent_color=Colors.SUCCESS,
        )
        add_card.pack(fill="x", padx=16, pady=(0, 12))

        add_row = ctk.CTkFrame(add_card.content, fg_color="transparent")
        add_row.pack(fill="x")

        self.new_key = ctk.CTkEntry(
            add_row,
            placeholder_text="Kalit",
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=36,
            width=160,
        )
        self.new_key.pack(side="left", padx=(0, 6))

        self.new_value = ctk.CTkEntry(
            add_row,
            placeholder_text="Qiymat",
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=36,
        )
        self.new_value.pack(side="left", fill="x", expand=True, padx=(0, 6))

        GlowButton(
            add_row, text="Qo'shish", icon="➕", command=self._add_knowledge
        ).pack(side="right")

        list_card = GlassCard(
            parent,
            title="Bilimlar ro'yxati",
            subtitle="Saqlangan bilimlar va ularning foydalanish statistikasi.",
            accent_color=Colors.SUCCESS,
        )
        list_card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._knowledge_scroll = ctk.CTkScrollableFrame(
            list_card.content, fg_color="transparent"
        )
        self._knowledge_scroll.pack(fill="both", expand=True)

    def _build_history_tab(self, parent):
        intro = GlassCard(
            parent,
            title="Suhbat oqimi",
            subtitle="Oxirgi dialoglar shu yerda saqlanadi. Har bir yozuv context tiklash uchun ishlatiladi.",
            accent_color=Colors.SECONDARY,
        )
        intro.pack(fill="x", padx=16, pady=(16, 12))

        self._history_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self._history_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _add_profile_entry(self, parent, label, default=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        ctk.CTkLabel(
            row,
            text=label,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=120,
            anchor="w",
        ).pack(side="left")

        entry = ctk.CTkEntry(
            row,
            font=Fonts.BODY,
            fg_color=Colors.BG_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=36,
        )
        entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _add_profile_option(self, parent, label, values, default):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        ctk.CTkLabel(
            row,
            text=label,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=120,
            anchor="w",
        ).pack(side="left")

        option = ctk.CTkOptionMenu(
            row,
            values=values,
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            button_color=Colors.BG_PANEL,
            button_hover_color=Colors.BG_HOVER,
            dropdown_fg_color=Colors.BG_CARD,
            dropdown_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            height=36,
        )
        option.set(default)
        option.pack(side="left", fill="x", expand=True)
        return option

    def _save_profile(self):
        try:
            from config import set_config

            for config_key, widget in self._profile_entries.items():
                value = widget.get().strip()
                if value:
                    set_config(config_key, value)

            try:
                import main

                name_widget = self._profile_entries.get("user.name")
                voice_widget = self._profile_entries.get("user.voice_type")
                if name_widget:
                    setattr(main.global_state, "ism", name_widget.get().strip())
                if voice_widget:
                    setattr(
                        main.global_state,
                        "ovoz_turi_global",
                        voice_widget.get().strip(),
                    )
            except Exception:
                pass

            self.profile_save_btn.configure(
                text="✅  Saqlandi", fg_color=Colors.SUCCESS
            )
            self.after(
                1800,
                lambda: self.profile_save_btn.configure(
                    text="💾  Saqlash", fg_color=Colors.PRIMARY_DARK
                ),
            )
            if self.app and hasattr(self.app, "user_label"):
                self.app.user_label.configure(
                    text=f"User: {self._profile_entries['user.name'].get().strip()}"
                )
            self._update_profile_status()
        except Exception as exc:
            messagebox.showerror("Profil xatoligi", str(exc))

    def _add_knowledge(self):
        key = self.new_key.get().strip()
        value = self.new_value.get().strip()
        if not key or not value:
            return

        if self.app and hasattr(self.app, "bridge"):
            self.app.bridge.save_knowledge(key, value)

        self.new_key.delete(0, "end")
        self.new_value.delete(0, "end")
        self._refresh_knowledge()

    def _export_data(self):
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON fayllar", "*.json")],
                title="Ma'lumotlarni eksport qilish",
            )
            if not filepath:
                return

            export_data = {}
            if self.app and hasattr(self.app, "bridge"):
                bridge = self.app.bridge
                export_data["stats"] = bridge.get_memory_stats()
                export_data["profile"] = bridge.get_memory_profile()
                export_data["knowledge"] = bridge.get_memory_knowledge()
                export_data["conversations"] = bridge.get_memory_conversations(50)

            with open(filepath, "w", encoding="utf-8") as file:
                json.dump(export_data, file, ensure_ascii=False, indent=2)

            messagebox.showinfo(
                "Eksport", "Ma'lumotlar muvaffaqiyatli eksport qilindi."
            )
        except Exception as exc:
            messagebox.showerror("Eksport xatoligi", str(exc))

    def _refresh_knowledge(self):
        if not self._knowledge_scroll:
            return

        for child in self._knowledge_scroll.winfo_children():
            child.destroy()

        knowledge = {}
        if self.app and hasattr(self.app, "bridge"):
            knowledge = self.app.bridge.get_memory_knowledge()

        query = (
            self.knowledge_search.get().strip().lower()
            if hasattr(self, "knowledge_search")
            else ""
        )
        rows = []
        for key, value in knowledge.items():
            payload = value.get("value") if isinstance(value, dict) else value
            serialized = f"{key} {payload}".lower()
            if query and query not in serialized:
                continue
            rows.append((key, value))

        if not rows:
            EmptyState(
                self._knowledge_scroll,
                icon="📚",
                title="Bilim topilmadi",
                description="Yangi bilim qo'shing yoki qidiruv matnini o'zgartiring.",
            ).pack(fill="x", pady=20)
            return

        for key, value in rows:
            payload = value.get("value") if isinstance(value, dict) else value
            saved_at = value.get("saved_at", "") if isinstance(value, dict) else ""
            access_count = (
                value.get("access_count", 0) if isinstance(value, dict) else 0
            )

            row = ctk.CTkFrame(
                self._knowledge_scroll,
                fg_color=Colors.BG_INPUT,
                corner_radius=12,
                border_width=1,
                border_color=Colors.BORDER,
            )
            row.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            head = ctk.CTkFrame(inner, fg_color="transparent")
            head.pack(fill="x")

            ctk.CTkLabel(
                head,
                text=f"🔑 {key}",
                font=Fonts.SMALL_BOLD,
                text_color=Colors.SUCCESS,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                head,
                text=f"{access_count} marta ishlatilgan",
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
            ).pack(side="right")

            ctk.CTkLabel(
                inner,
                text=str(payload),
                font=Fonts.SMALL,
                text_color=Colors.TEXT_PRIMARY,
                wraplength=700,
                justify="left",
                anchor="w",
            ).pack(fill="x", pady=(8, 6))

            if saved_at:
                ctk.CTkLabel(
                    inner,
                    text=f"Saqlangan vaqt: {str(saved_at)[:19]}",
                    font=Fonts.TINY,
                    text_color=Colors.TEXT_MUTED,
                    anchor="w",
                ).pack(fill="x")

    def _refresh_history(self):
        if not self._history_scroll:
            return

        for child in self._history_scroll.winfo_children():
            child.destroy()

        conversations = []
        if self.app and hasattr(self.app, "bridge"):
            conversations = self.app.bridge.get_memory_conversations(20)

        if not conversations:
            EmptyState(
                self._history_scroll,
                icon="💬",
                title="Tarix bo'sh",
                description="Mikasa bilan suhbat boshlang. Yangi dialoglar shu yerda paydo bo'ladi.",
            ).pack(fill="x", pady=24)
            return

        for conv in reversed(conversations):
            user_text = conv.get("user", conv.get("input", ""))
            ai_text = conv.get("agent", conv.get("assistant", conv.get("output", "")))
            timestamp = conv.get("time", conv.get("timestamp", ""))

            row = GlassCard(self._history_scroll, accent_color=Colors.SECONDARY)
            row.pack(fill="x", pady=6)

            ctk.CTkLabel(
                row.content,
                text=f"👤 {user_text[:180]}",
                font=Fonts.SMALL_BOLD,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
                wraplength=760,
                justify="left",
            ).pack(fill="x")

            ctk.CTkLabel(
                row.content,
                text=f"🤖 {ai_text[:260]}",
                font=Fonts.SMALL,
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
                wraplength=760,
                justify="left",
            ).pack(fill="x", pady=(8, 6))

            if timestamp:
                ctk.CTkLabel(
                    row.content,
                    text=f"🕐 {str(timestamp)[:19]}",
                    font=Fonts.TINY,
                    text_color=Colors.TEXT_MUTED,
                    anchor="e",
                ).pack(fill="x")

    def _update_profile_status(self):
        name = self._profile_entries["user.name"].get().strip()
        voice = self._profile_entries["user.voice_type"].get().strip()
        lang = self._profile_entries["user.language"].get().strip()

        if name:
            voice_label = voice or "ovoz yo'q"
            lang_label = lang or "til yo'q"
            self.profile_status.configure(
                text=f"Profil tayyor: {name} • {voice_label} • {lang_label}"
            )
            if len(self._stat_widgets) > 3:
                self._stat_widgets[3].set_value("Tayyor")
        else:
            self.profile_status.configure(
                text="Profil to'liq emas. Kamida ismni kiriting."
            )
            if len(self._stat_widgets) > 3:
                self._stat_widgets[3].set_value("Qisman")

    def on_show(self):
        try:
            if self.app and hasattr(self.app, "bridge"):
                stats = self.app.bridge.get_memory_stats()
                values = [
                    str(stats.get("kontekst_hajmi", 0)),
                    str(stats.get("suhbatlar_soni", 0)),
                    str(stats.get("bilimlar_soni", 0)),
                ]
                for index, value in enumerate(values):
                    if index < len(self._stat_widgets):
                        self._stat_widgets[index].set_value(value)

            try:
                from config import get_config

                for config_key, widget in self._profile_entries.items():
                    value = get_config(config_key)
                    if value is not None:
                        if isinstance(widget, ctk.CTkEntry):
                            widget.delete(0, "end")
                            widget.insert(0, str(value))
                        else:
                            widget.set(str(value))
            except Exception:
                pass

            self._update_profile_status()
            self._refresh_knowledge()
            self._refresh_history()
        except Exception:
            pass
