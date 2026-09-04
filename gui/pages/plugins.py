# ========== plugins.py ==========
# Plugin Manager sahifasi

import json
import os
import customtkinter as ctk
from tkinter import messagebox
from gui.theme import Colors, Fonts
from gui.components import EmptyState, GlassCard, InfoChip, PageHero, SecondaryButton


class PluginsPage(ctk.CTkFrame):
    """Plugin boshqaruvi sahifasi"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        from core.agent_plugins import PLUGINS_DIR

        self.plugins_dir = PLUGINS_DIR
        self._build_ui()

    def _build_ui(self):
        self.hero = PageHero(
            self,
            title="Plugin markazi",
            subtitle="JSON va Python plugin'larni ko'ring, yoqing va yangi template yarating.",
            icon="🔌",
            accent_color=Colors.INFO,
            chips=[
                ("JSON + Python", "🧩", Colors.GLASS_BG, Colors.TEXT_SECONDARY),
                (
                    "Qayta ishga tushganda faollashadi",
                    "♻️",
                    Colors.GLASS_BG,
                    Colors.TEXT_SECONDARY,
                ),
            ],
        )
        self.hero.pack(fill="x", padx=20, pady=(16, 12))

        self.plugin_count_chip = InfoChip(
            self.hero.actions,
            text="0 ta plugin",
            icon="📦",
            fg_color=Colors.INFO_SOFT,
            text_color=Colors.INFO,
        )
        self.plugin_count_chip.pack(anchor="e", pady=(0, 6))

        SecondaryButton(
            self.hero.actions,
            text="Papkani ochish",
            icon="📁",
            corner_radius=999,
            command=self._open_plugins_folder,
        ).pack(anchor="e")

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD,
            scrollbar_button_hover_color=Colors.BG_HOVER,
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self._build_plugin_info()

        self.installed_card = GlassCard(
            self.scroll,
            title="O'rnatilgan pluginlar",
            subtitle="Faol va nofaol pluginlar statusi shu yerda ko'rinadi.",
            accent_color=Colors.INFO,
        )
        self.installed_card.pack(fill="x", pady=(0, 12))

        self.installed_list = ctk.CTkFrame(
            self.installed_card.content, fg_color="transparent"
        )
        self.installed_list.pack(fill="both", expand=True)

        self._build_templates()

    def _build_plugin_info(self):
        info_card = GlassCard(
            self.scroll,
            title="Plugin tizimi",
            subtitle="Plugin'lar `plugins/` papkasida saqlanadi va dastur ishga tushganda yuklanadi.",
            accent_color=Colors.SUCCESS,
        )
        info_card.pack(fill="x", pady=(0, 12))

        path_row = ctk.CTkFrame(
            info_card.content, fg_color=Colors.BG_INPUT, corner_radius=12
        )
        path_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            path_row,
            text=f"📁 {self.plugins_dir}",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=12, pady=10)

        chip_row = ctk.CTkFrame(info_card.content, fg_color="transparent")
        chip_row.pack(fill="x")

        InfoChip(
            chip_row,
            text="JSON plugin",
            icon="📄",
            fg_color=Colors.GLASS_BG,
            text_color=Colors.INFO,
        ).pack(side="left", padx=(0, 8))
        InfoChip(
            chip_row,
            text="Python plugin",
            icon="🐍",
            fg_color=Colors.GLASS_BG,
            text_color=Colors.SUCCESS,
        ).pack(side="left", padx=(0, 8))
        InfoChip(
            chip_row,
            text="Explorer orqali boshqarish",
            icon="🗂️",
            fg_color=Colors.GLASS_BG,
            text_color=Colors.TEXT_SECONDARY,
        ).pack(side="left")

    def _refresh_installed_plugins(self):
        for widget in self.installed_list.winfo_children():
            widget.destroy()

        plugins = []
        if os.path.exists(self.plugins_dir):
            for fname in os.listdir(self.plugins_dir):
                full_path = os.path.join(self.plugins_dir, fname)
                if os.path.isfile(full_path) and (
                    fname.endswith(".json")
                    or fname.endswith(".py")
                    or fname.startswith("_")
                ):
                    is_enabled = not fname.startswith("_")
                    ptype = "JSON" if ".json" in fname else "Python"
                    desc = "Custom plugin"
                    name = fname.lstrip("_")

                    if fname.endswith(".json") and is_enabled:
                        try:
                            with open(full_path, "r", encoding="utf-8") as file:
                                data = json.load(file)
                                name = data.get("name", name)
                                desc = data.get("description", desc)
                        except Exception:
                            pass

                    plugins.append((name, fname, ptype, is_enabled, desc[:80]))

        self.plugin_count_chip.set_text(f"{len(plugins)} ta plugin")

        if not plugins:
            EmptyState(
                self.installed_list,
                icon="🧩",
                title="Plugin topilmadi",
                description="Template yaratib boshlang yoki plugin fayllarni plugins papkasiga joylang.",
            ).pack(fill="x", pady=20)
            return

        for name, file_name, ptype, enabled, desc in sorted(
            plugins, key=lambda item: item[0]
        ):
            row = ctk.CTkFrame(
                self.installed_list,
                fg_color=Colors.GLASS_BG,
                corner_radius=12,
                border_width=1,
                border_color=Colors.GLASS_BORDER if enabled else Colors.BORDER,
            )
            row.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            head = ctk.CTkFrame(info, fg_color="transparent")
            head.pack(fill="x")

            ctk.CTkLabel(
                head,
                text=f"🔌 {name}",
                font=Fonts.BODY_BOLD,
                text_color=Colors.TEXT_PRIMARY if enabled else Colors.TEXT_MUTED,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            InfoChip(
                head,
                text="Faol" if enabled else "Nofaol",
                fg_color=Colors.SUCCESS_SOFT if enabled else Colors.GLASS_BG,
                text_color=Colors.SUCCESS if enabled else Colors.TEXT_MUTED,
            ).pack(side="right")

            ctk.CTkLabel(
                info,
                text=desc,
                font=Fonts.SMALL,
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=640,
            ).pack(fill="x", pady=(8, 6))

            ctk.CTkLabel(
                info,
                text=f"{ptype} • {file_name}",
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x")

            switch = ctk.CTkSwitch(
                inner,
                text="",
                progress_color=Colors.PRIMARY,
                button_color=Colors.TEXT_PRIMARY,
                fg_color=Colors.BG_DARK,
                command=lambda f=file_name, s=enabled: self._toggle_plugin(f, s),
            )
            if enabled:
                switch.select()
            switch.pack(side="right", padx=(10, 0))

    def _build_templates(self):
        templates_card = GlassCard(
            self.scroll,
            title="Plugin template'lari",
            subtitle="Bir klik bilan boshlang'ich plugin fayllarini yaratib oling.",
            accent_color=Colors.WARNING,
        )
        templates_card.pack(fill="x", pady=(0, 12))

        templates = [
            (
                "🌐",
                "Web opener",
                "Har qanday saytni voice command bilan ochish",
                self._create_web_template,
                Colors.INFO,
            ),
            (
                "🖥️",
                "System command",
                "Windows CLI yoki script buyruqlarini chaqirish",
                self._create_cmd_template,
                Colors.WARNING,
            ),
        ]

        for icon, name, desc, cmd, color in templates:
            row = ctk.CTkFrame(
                templates_card.content,
                fg_color=Colors.BG_INPUT,
                corner_radius=12,
                border_width=1,
                border_color=Colors.BORDER,
            )
            row.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                left,
                text=f"{icon} {name}",
                font=Fonts.BODY_BOLD,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                left,
                text=desc,
                font=Fonts.SMALL,
                text_color=Colors.TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", pady=(4, 0))

            SecondaryButton(
                inner,
                text="Yaratish",
                icon="✨",
                corner_radius=999,
                command=cmd,
            ).pack(side="right")

    def _open_plugins_folder(self):
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
        try:
            os.startfile(self.plugins_dir)
        except Exception as exc:
            messagebox.showerror("Xatolik", f"Papkani ochib bo'lmadi: {exc}")

    def _toggle_plugin(self, filename, currently_enabled):
        try:
            old_path = os.path.join(self.plugins_dir, filename)

            if currently_enabled:
                new_filename = f"_{filename}"
                new_path = os.path.join(self.plugins_dir, new_filename)
            else:
                new_filename = filename.lstrip("_")
                new_path = os.path.join(self.plugins_dir, new_filename)

            os.rename(old_path, new_path)
            messagebox.showinfo(
                "Muvaffaqiyatli",
                "O'zgarishlar dastur qayta ishga tushganda faollashadi.",
            )
            self._refresh_installed_plugins()
        except Exception as exc:
            messagebox.showerror(
                "Xatolik", f"Plugin holatini o'zgartirib bo'lmadi: {exc}"
            )
            self._refresh_installed_plugins()

    def _create_web_template(self):
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)

        tpl_path = os.path.join(self.plugins_dir, "my_website.json")
        if os.path.exists(tpl_path):
            messagebox.showwarning("Eslatma", f"{tpl_path} allaqachon mavjud.")
            return

        data = {
            "name": "open_my_website",
            "description": "Mening sevimli saytimni ochish",
            "category": "internet",
            "type": "url",
            "url": "https://example.com/search?q={query}",
            "parameters": {"query": {"type": "string", "description": "Qidiruv so'zi"}},
        }

        try:
            with open(tpl_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            messagebox.showinfo(
                "Yaratildi",
                "Shablon yaratildi: my_website.json. Endi uni tahrir qilishingiz mumkin.",
            )
            self._refresh_installed_plugins()
        except Exception as exc:
            messagebox.showerror("Xato", str(exc))

    def _create_cmd_template(self):
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)

        tpl_path = os.path.join(self.plugins_dir, "my_command.json")
        if os.path.exists(tpl_path):
            messagebox.showwarning("Eslatma", f"{tpl_path} allaqachon mavjud.")
            return

        data = {
            "name": "run_my_script",
            "description": "Men yozgan maxsus scriptni ishga tushirish",
            "category": "system",
            "type": "command",
            "command": "python C:/scripts/myscript.py {arg1}",
            "parameters": {"arg1": {"type": "string", "description": "Argument"}},
        }

        try:
            with open(tpl_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            messagebox.showinfo(
                "Yaratildi",
                "Shablon yaratildi: my_command.json. Endi uni tahrir qilishingiz mumkin.",
            )
            self._refresh_installed_plugins()
        except Exception as exc:
            messagebox.showerror("Xato", str(exc))

    def on_show(self):
        self._refresh_installed_plugins()
