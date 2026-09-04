# ========== settings.py ==========
# Sozlamalar sahifasi

import os
import shutil
import customtkinter as ctk
from tkinter import messagebox
from gui.theme import Colors, Fonts
from gui.components import GlassCard, GlowButton, InfoChip, PageHero, SecondaryButton


def _safe_remove(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except Exception:
        pass


class SettingsPage(ctk.CTkFrame):
    """Mikasa AI umumiy sozlamalar sahifasi"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._inputs = {}
        self._aliases = {
            "audio.tts_engine": "voice.tts_engine",
            "audio.tts_speed": "voice.speed",
            "audio.sample_rate": "voice.sample_rate",
            "api.timeout": "ai.timeout",
            "gui.color": "gui.color_scheme",
        }
        self._build_ui()

    def _build_ui(self):
        self.hero = PageHero(
            self,
            title="Sozlamalar markazi",
            subtitle="Mikasa interfeysi, AI ulanishlari va ovoz parametrlarini bir joydan boshqaring.",
            icon="⚙️",
            accent_color=Colors.PRIMARY,
            chips=[
                ("Real-time saqlash", "💾", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
                ("Voice bilan sinxron", "🎤", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
            ],
        )
        self.hero.pack(fill="x", padx=20, pady=(16, 12))

        self.save_state_chip = InfoChip(
            self.hero.actions,
            text="O'zgarishlar saqlanmagan",
            icon="📝",
            fg_color=Colors.BG_PANEL,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.save_state_chip.pack(anchor="e", pady=(0, 6))

        self.save_btn = GlowButton(
            self.hero.actions,
            text="Saqlash",
            icon="💾",
            command=self._save_settings,
        )
        self.save_btn.pack(anchor="e")

        self.summary_card = GlassCard(
            self,
            title="Joriy ko'rinish",
            subtitle="Asosiy sozlamalarning tezkor xulosasi.",
            accent_color=Colors.INFO,
        )
        self.summary_card.pack(fill="x", padx=20, pady=(0, 12))

        self.summary_row = ctk.CTkFrame(
            self.summary_card.content, fg_color="transparent"
        )
        self.summary_row.pack(fill="x")

        self.summary_voice = InfoChip(
            self.summary_row,
            text="TTS: -",
            icon="🔊",
            fg_color=Colors.BG_PANEL,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.summary_voice.pack(side="left", padx=(0, 8))

        self.summary_ai = InfoChip(
            self.summary_row,
            text="AI: -",
            icon="🤖",
            fg_color=Colors.BG_PANEL,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.summary_ai.pack(side="left", padx=(0, 8))

        self.summary_ui = InfoChip(
            self.summary_row,
            text="UI: -",
            icon="🎨",
            fg_color=Colors.BG_PANEL,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.summary_ui.pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self._build_voice_section()
        self._build_ai_section()
        self._build_gui_section()
        self._build_data_section()

    def _build_voice_section(self):
        card = GlassCard(
            self.scroll,
            title="Ovoz",
            subtitle="TTS engine, model va sample rate sozlamalari.",
            accent_color=Colors.SUCCESS,
        )
        card.pack(fill="x", pady=(0, 12))

        self._inputs["audio.tts_engine"] = self._add_segmented(
            card.content, "TTS engine", ["silero", "edge_tts"], "silero"
        )
        self._inputs["voice.silero_model"] = self._add_dropdown(
            card.content,
            "Model",
            ["v4_uz", "v3_uz", "uz-UZ-MadinaNeural", "uz-UZ-MansurNeural"],
            "v4_uz",
        )
        self._inputs["audio.tts_speed"] = self._add_slider(
            card.content, "Ovoz tezligi", 0.5, 2.0, 1.0, step=0.1
        )
        self._inputs["audio.sample_rate"] = self._add_dropdown(
            card.content, "Sample rate", ["16000", "22050", "44100"], "16000"
        )

    def _build_ai_section(self):
        card = GlassCard(
            self.scroll,
            title="AI",
            subtitle="Model va API kalitlari shu yerda saqlanadi.",
            accent_color=Colors.SECONDARY,
        )
        card.pack(fill="x", pady=(0, 12))

        self._inputs["ai.gemini_api_key"] = self._add_field(
            card.content, "Gemini API key", show="●"
        )
        self._inputs["ai.openrouter_api_key"] = self._add_field(
            card.content, "OpenRouter key", show="●"
        )
        self._inputs["ai.model"] = self._add_dropdown(
            card.content, "AI model", ["gemini", "openrouter"], "gemini"
        )
        self._inputs["api.timeout"] = self._add_slider(
            card.content, "API timeout (s)", 5, 30, 20, step=1
        )

    def _build_gui_section(self):
        card = GlassCard(
            self.scroll,
            title="Interfeys",
            subtitle="Tashqi ko'rinish va animatsiya parametrlari.",
            accent_color=Colors.INFO,
        )
        card.pack(fill="x", pady=(0, 12))

        self._inputs["gui.theme"] = self._add_segmented(
            card.content, "Mavzu", ["dark", "light", "system"], "dark"
        )
        self._inputs["gui.color"] = self._add_dropdown(
            card.content, "Rang sxemasi", ["blue", "green", "dark-blue"], "blue"
        )
        self._inputs["gui.compact_mode"] = self._add_toggle(
            card.content, "Compact mode", False
        )
        self._inputs["gui.animations"] = self._add_toggle(
            card.content, "Animatsiyalar", True
        )

    def _build_data_section(self):
        card = GlassCard(
            self.scroll,
            title="Ma'lumotlar va servis",
            subtitle="Lokal kesh, loglar va eksport amallari.",
            accent_color=Colors.WARNING,
        )
        card.pack(fill="x", pady=(0, 12))

        actions = ctk.CTkFrame(card.content, fg_color="transparent")
        actions.pack(fill="x")

        btn_data = [
            ("Keshni tozalash", "🗑️", self._clear_cache),
            ("Loglarni tozalash", "📋", self._clear_logs),
            ("Ma'lumot eksport", "📤", self._export_data),
        ]

        for i, (text, icon, command) in enumerate(btn_data):
            button = SecondaryButton(actions, text=text, icon=icon, command=command)
            button.grid(row=0, column=i, padx=4, pady=4, sticky="ew")
            actions.columnconfigure(i, weight=1)

    def _add_field(self, parent, label, default="", show=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        ctk.CTkLabel(
            row,
            text=label,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=160,
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
            show=show or "",
        )
        if default and show is None:
            entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _add_dropdown(self, parent, label, values, default=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        ctk.CTkLabel(
            row,
            text=label,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=160,
            anchor="w",
        ).pack(side="left")

        dropdown = ctk.CTkOptionMenu(
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
        if default:
            dropdown.set(default)
        dropdown.pack(side="left", fill="x", expand=True)
        return dropdown

    def _add_segmented(self, parent, label, values, default=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        ctk.CTkLabel(
            row,
            text=label,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=160,
            anchor="w",
        ).pack(side="left")

        seg = ctk.CTkSegmentedButton(
            row,
            values=values,
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            selected_color=Colors.PRIMARY_DARK,
            selected_hover_color=Colors.PRIMARY,
            unselected_color=Colors.BG_INPUT,
            unselected_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
        )
        if default:
            seg.set(default)
        seg.pack(side="left", fill="x", expand=True)
        return seg

    def _add_slider(self, parent, label, from_, to, default, step=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        ctk.CTkLabel(
            row,
            text=label,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=160,
            anchor="w",
        ).pack(side="left")

        kwargs = {}
        if step is not None:
            kwargs["number_of_steps"] = int((to - from_) / step)

        slider = ctk.CTkSlider(
            row,
            from_=from_,
            to=to,
            progress_color=Colors.PRIMARY,
            button_color=Colors.PRIMARY,
            button_hover_color=Colors.PRIMARY_DARK,
            fg_color=Colors.BG_INPUT,
            **kwargs,
        )
        slider.set(default)
        slider.pack(side="left", fill="x", expand=True, padx=(0, 8))

        value_label = ctk.CTkLabel(
            row,
            text=str(default),
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            width=48,
        )
        value_label.pack(side="right")

        def update_label(value):
            fmt = "{:.1f}" if step and step < 1 else "{:.0f}"
            value_label.configure(text=fmt.format(value))

        slider.configure(command=update_label)
        return slider

    def _add_toggle(self, parent, label, default=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)

        ctk.CTkLabel(
            row,
            text=label,
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            width=160,
            anchor="w",
        ).pack(side="left")

        switch = ctk.CTkSwitch(
            row,
            text="",
            progress_color=Colors.PRIMARY,
            button_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.BG_INPUT,
        )
        if default:
            switch.select()
        switch.pack(side="left")
        return switch

    def _clear_cache(self):
        if messagebox.askyesno(
            "Tasdiqlash", "Loyihadagi barcha kesh fayllarni o'chirasizmi?"
        ):
            try:
                base_dir = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                count = 0
                for root, dirs, files in os.walk(base_dir):
                    if "__pycache__" in dirs:
                        _safe_remove(os.path.join(root, "__pycache__"))
                        count += 1
                messagebox.showinfo("Muvaffaqiyatli", f"{count} ta papka tozalandi!")
            except Exception as exc:
                messagebox.showerror("Xatolik", str(exc))

    def _clear_logs(self):
        if messagebox.askyesno("Tasdiqlash", "Barcha tizim loglarini o'chirasizmi?"):
            try:
                base_dir = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                logs_dir = os.path.join(base_dir, "logs")
                count = 0
                if os.path.exists(logs_dir):
                    for filename in os.listdir(logs_dir):
                        if filename.endswith(".log"):
                            _safe_remove(os.path.join(logs_dir, filename))
                            count += 1
                messagebox.showinfo(
                    "Muvaffaqiyatli", f"{count} ta log fayli o'chirildi!"
                )
            except Exception as exc:
                messagebox.showerror("Xatolik", str(exc))

    def _export_data(self):
        if self.app:
            self.app.navigate_to("memory")
            mem_page = self.app._pages.get("memory")
            if mem_page:
                mem_page._export_data()

    def _read_widget_value(self, key, widget):
        if isinstance(widget, ctk.CTkEntry):
            return widget.get().strip()
        if isinstance(widget, (ctk.CTkOptionMenu, ctk.CTkSegmentedButton)):
            value = widget.get()
            if key == "audio.sample_rate":
                return int(value)
            return value
        if isinstance(widget, ctk.CTkSlider):
            if key == "api.timeout":
                return int(widget.get())
            return float(widget.get())
        if isinstance(widget, ctk.CTkSwitch):
            return bool(widget.get())
        return None

    def _save_settings(self):
        try:
            from config import set_config

            for key, widget in self._inputs.items():
                value = self._read_widget_value(key, widget)
                if value is None or str(value) == "":
                    continue

                set_config(key, value)
                alias = self._aliases.get(key)
                if alias:
                    set_config(alias, value)

            theme_value = self._inputs["gui.theme"].get().lower()
            compact_mode = bool(self._inputs["gui.compact_mode"].get())
            color_theme = self._inputs["gui.color"].get()

            if self.app and hasattr(self.app, "apply_ui_preferences"):
                self.app.apply_ui_preferences(
                    theme=theme_value,
                    compact_mode=compact_mode,
                    color_theme=color_theme,
                )
                new_settings = self.app._pages.get("settings")
                if new_settings and hasattr(new_settings, "_show_saved_feedback"):
                    new_settings._show_saved_feedback()
                return

            appearance = (
                "Dark"
                if theme_value == "dark"
                else "Light"
                if theme_value == "light"
                else "System"
            )
            ctk.set_appearance_mode(appearance)
            ctk.set_default_color_theme(color_theme)

            self._show_saved_feedback()
            self._refresh_summary()
        except Exception as exc:
            messagebox.showerror("Saqlashda xatolik", str(exc))

    def _show_saved_feedback(self):
        self.save_btn.configure(text="✅  Saqlandi", fg_color=Colors.SUCCESS)
        self.save_state_chip.set_text("Saqlandi")
        self.after(
            1800,
            self._reset_save_feedback,
        )

    def _reset_save_feedback(self):
        try:
            if self.winfo_exists() and self.save_btn.winfo_exists():
                self.save_btn.configure(
                    text="💾  Saqlash", fg_color=Colors.PRIMARY_DARK
                )
        except Exception:
            pass

    def _get_config_value(self, getter, key):
        value = getter(key)
        if value is None and key in self._aliases:
            value = getter(self._aliases[key])
        return value

    def _refresh_summary(self):
        voice = self._inputs["audio.tts_engine"].get()
        model = self._inputs["ai.model"].get()
        theme = self._inputs["gui.theme"].get()
        color = self._inputs["gui.color"].get()
        compact = bool(self._inputs["gui.compact_mode"].get())

        self.summary_voice.set_text(f"TTS: {voice}")
        self.summary_ai.set_text(f"AI: {model}")
        self.summary_ui.set_text(
            f"UI: {theme}/{color}/{'compact' if compact else 'standard'}"
        )

    def on_show(self):
        try:
            from config import get_config

            for key, widget in self._inputs.items():
                value = self._get_config_value(get_config, key)
                if value is None:
                    continue

                if isinstance(widget, ctk.CTkEntry):
                    widget.delete(0, "end")
                    widget.insert(0, str(value))
                elif isinstance(widget, (ctk.CTkOptionMenu, ctk.CTkSegmentedButton)):
                    widget.set(str(value))
                elif isinstance(widget, ctk.CTkSlider):
                    try:
                        numeric_value = float(str(value))
                        widget.set(numeric_value)
                        if hasattr(widget, "_command") and widget._command:
                            widget._command(numeric_value)
                    except Exception:
                        pass
                elif isinstance(widget, ctk.CTkSwitch):
                    if value:
                        widget.select()
                    else:
                        widget.deselect()

            self.save_state_chip.set_text("Tayyor")
            self._refresh_summary()
        except Exception:
            pass
