# ========== scheduler.py ==========
# Scheduler sahifasi — vaqtli vazifalar va eslatmalar

import datetime
import customtkinter as ctk
from tkinter import messagebox
from gui.theme import Colors, Fonts
from gui.components import EmptyState, GlassCard, GlowButton, InfoChip, PageHero


class SchedulerPage(ctk.CTkFrame):
    """Vaqtli vazifalar rejalashtiruvchisi"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._tasks = []
        self._timeline_running = False
        self._build_ui()

    def _build_ui(self):
        self.hero = PageHero(
            self,
            title="Planner va eslatmalar",
            subtitle="Vaqtli vazifa, buyruq yoki takroriy reminder qo'shing. Mikasa kerakli vaqtda ishga tushiradi.",
            icon="⏰",
            accent_color=Colors.WARNING,
            chips=[
                ("Reminder", "📌", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
                ("Takroriy task", "🔁", Colors.BG_PANEL, Colors.TEXT_SECONDARY),
            ],
        )
        self.hero.pack(fill="x", padx=20, pady=(16, 12))

        self.task_count_chip = InfoChip(
            self.hero.actions,
            text="0 ta aktiv vazifa",
            icon="📋",
            fg_color=Colors.WARNING_SOFT,
            text_color=Colors.WARNING,
        )
        self.task_count_chip.pack(anchor="e", pady=(0, 6))

        self.next_task_chip = InfoChip(
            self.hero.actions,
            text="Keyingi task yo'q",
            icon="🕐",
            fg_color=Colors.BG_PANEL,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.next_task_chip.pack(anchor="e")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        self._build_add_form(left)
        self._build_task_list(left)
        self._build_timeline(right)

    def _build_add_form(self, parent):
        form_card = GlassCard(
            parent,
            title="Yangi vazifa",
            subtitle="Daqiqalarda vaqt kiriting. Takroriy rejim uchun interval ham shu qiymatdan olinadi.",
            accent_color=Colors.PRIMARY,
        )
        form_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            form_card.content,
            text="Vazifa matni",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.task_text = ctk.CTkEntry(
            form_card.content,
            placeholder_text="Masalan: Suv ichish",
            font=Fonts.BODY,
            fg_color=Colors.BG_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=38,
        )
        self.task_text.pack(fill="x", pady=(0, 10))

        time_row = ctk.CTkFrame(form_card.content, fg_color="transparent")
        time_row.pack(fill="x", pady=(0, 10))

        time_col = ctk.CTkFrame(time_row, fg_color="transparent")
        time_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            time_col,
            text="Vaqt (daqiqalarda)",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.task_time = ctk.CTkEntry(
            time_col,
            placeholder_text="Masalan: 5",
            font=Fonts.BODY,
            fg_color=Colors.BG_INPUT,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=38,
        )
        self.task_time.pack(fill="x")

        ctk.CTkLabel(
            form_card.content,
            text="Turi",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
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
            text_color=Colors.TEXT_PRIMARY,
        )
        self.task_type.set("📌 Eslatma")
        self.task_type.pack(fill="x", pady=(0, 12))

        GlowButton(
            form_card.content,
            text="Jadvalga qo'shish",
            icon="➕",
            command=self._add_task,
        ).pack(anchor="e")

    def _build_task_list(self, parent):
        list_card = GlassCard(
            parent,
            title="Aktiv vazifalar",
            subtitle="Yaqinlashayotgan task'lar shu yerda ko'rinadi. Istalgan vaqtda bekor qilish mumkin.",
            accent_color=Colors.WARNING,
        )
        list_card.pack(fill="both", expand=True)

        self.tasks_scroll = ctk.CTkScrollableFrame(
            list_card.content, fg_color="transparent"
        )
        self.tasks_scroll.pack(fill="both", expand=True)

    def _build_timeline(self, parent):
        timeline_card = GlassCard(
            parent,
            title="Bugungi timeline",
            subtitle="Jonli vaqt va eng yaqin task holati.",
            accent_color=Colors.INFO,
        )
        timeline_card.pack(fill="both", expand=True)

        now = datetime.datetime.now()
        self.date_label = ctk.CTkLabel(
            timeline_card.content,
            text=now.strftime("%d %B, %Y"),
            font=Fonts.HEADING_3,
            text_color=Colors.TEXT_PRIMARY,
        )
        self.date_label.pack(pady=(0, 6))

        self.time_label = ctk.CTkLabel(
            timeline_card.content,
            text=now.strftime("%H:%M:%S"),
            font=(Fonts.FAMILY, 32, "bold"),
            text_color=Colors.PRIMARY,
        )
        self.time_label.pack(pady=(0, 12))

        self.timeline_summary = ctk.CTkLabel(
            timeline_card.content,
            text="Task yo'q",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        )
        self.timeline_summary.pack(pady=(0, 12))

        ctk.CTkFrame(timeline_card.content, fg_color=Colors.BORDER, height=1).pack(
            fill="x", pady=(0, 12)
        )

        self.timeline_list = ctk.CTkFrame(timeline_card.content, fg_color="transparent")
        self.timeline_list.pack(fill="both", expand=True)

    def _add_task(self):
        text = self.task_text.get().strip()
        time_expr = self.task_time.get().strip()

        if not text or not time_expr:
            messagebox.showwarning(
                "Xatolik", "Vazifa matni va vaqt (daqiqalarda) yozilishi shart!"
            )
            return

        try:
            delay_minutes = float(time_expr)
            exec_time = datetime.datetime.now().timestamp() + (delay_minutes * 60)

            if (
                self.app
                and hasattr(self.app, "bridge")
                and self.app.bridge._agent_scheduler
            ):
                task_id = self.app.bridge._agent_scheduler.add_task(
                    type="reminder" if "Eslatma" in self.task_type.get() else "command",
                    data=text,
                    execution_time=exec_time,
                    recurring="Takroriy" in self.task_type.get(),
                    interval_minutes=delay_minutes
                    if "Takroriy" in self.task_type.get()
                    else None,
                )
                if task_id:
                    self.task_text.delete(0, "end")
                    self.task_time.delete(0, "end")
                    self._refresh_task_list()
        except ValueError:
            messagebox.showwarning("Xatolik", "Vaqtni raqamda kiriting, masalan: 5")

    def _refresh_task_list(self):
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()

        tasks = []
        if self.app and hasattr(self.app, "bridge"):
            tasks = self.app.bridge.get_scheduler_tasks()

        self._tasks = sorted(tasks, key=lambda item: item["execution_time"])

        if not self._tasks:
            EmptyState(
                self.tasks_scroll,
                icon="📭",
                title="Task yo'q",
                description="Yuqoridagi formadan yangi vazifa qo'shing. Mikasa uni kerakli vaqtda eslatadi.",
            ).pack(fill="x", pady=24)
            self.task_count_chip.set_text("0 ta aktiv vazifa")
            self.next_task_chip.set_text("Keyingi task yo'q")
            self._refresh_timeline()
            return

        for task in self._tasks:
            row = ctk.CTkFrame(
                self.tasks_scroll,
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
                text=self._task_badge(task),
                font=Fonts.SMALL_BOLD,
                text_color=self._task_color(task),
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                head,
                text=self._format_exec_time(task),
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
            ).pack(side="right")

            ctk.CTkLabel(
                inner,
                text=task["data"],
                font=Fonts.BODY,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
                justify="left",
                wraplength=620,
            ).pack(fill="x", pady=(8, 8))

            footer = ctk.CTkFrame(inner, fg_color="transparent")
            footer.pack(fill="x")

            ctk.CTkLabel(
                footer,
                text=self._remaining_text(task),
                font=Fonts.TINY,
                text_color=Colors.TEXT_MUTED,
            ).pack(side="left")

            ctk.CTkButton(
                footer,
                text="Bekor qilish",
                font=Fonts.SMALL,
                fg_color="transparent",
                hover_color=Colors.DANGER_SOFT,
                text_color=Colors.DANGER,
                border_width=1,
                border_color=Colors.BORDER,
                corner_radius=999,
                height=30,
                command=lambda tid=task["id"]: self._remove_task(tid),
            ).pack(side="right")

        self.task_count_chip.set_text(f"{len(self._tasks)} ta aktiv vazifa")
        self.next_task_chip.set_text(self._next_task_text())
        self._refresh_timeline()

    def _remove_task(self, task_id):
        if (
            self.app
            and hasattr(self.app, "bridge")
            and self.app.bridge._agent_scheduler
        ):
            self.app.bridge._agent_scheduler.cancel_task(task_id)
            self._refresh_task_list()

    def _refresh_timeline(self):
        for widget in self.timeline_list.winfo_children():
            widget.destroy()

        if not self._tasks:
            self.timeline_summary.configure(text="Bugun uchun reja yo'q")
            EmptyState(
                self.timeline_list,
                icon="🗓️",
                title="Timeline bo'sh",
                description="Yangi task qo'shilgach shu yerda vaqt bo'yicha ko'rinadi.",
            ).pack(fill="x", pady=16)
            return

        recurring_count = sum(1 for task in self._tasks if task.get("recurring"))
        self.timeline_summary.configure(
            text=f"{len(self._tasks)} ta task • {recurring_count} ta takroriy"
        )

        for task in self._tasks[:6]:
            row = ctk.CTkFrame(self.timeline_list, fg_color="transparent")
            row.pack(fill="x", pady=4)

            ctk.CTkLabel(
                row,
                text=datetime.datetime.fromtimestamp(task["execution_time"]).strftime(
                    "%H:%M"
                ),
                font=Fonts.SMALL_BOLD,
                text_color=self._task_color(task),
                width=58,
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=task["data"][:34],
                font=Fonts.SMALL,
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

    def _task_badge(self, task):
        if task.get("recurring"):
            return "🔁 Takroriy"
        return "📌 Eslatma" if task.get("type") == "reminder" else "⚡ Buyruq"

    def _task_color(self, task):
        if task.get("recurring"):
            return Colors.SECONDARY
        return Colors.WARNING if task.get("type") == "reminder" else Colors.PRIMARY

    def _format_exec_time(self, task):
        return datetime.datetime.fromtimestamp(task["execution_time"]).strftime(
            "%H:%M:%S"
        )

    def _remaining_text(self, task):
        delta = max(
            0, int(task["execution_time"] - datetime.datetime.now().timestamp())
        )
        minutes, seconds = divmod(delta, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"Qolgan vaqt: {hours} soat {minutes} daqiqa"
        if minutes:
            return f"Qolgan vaqt: {minutes} daqiqa {seconds} soniya"
        return f"Qolgan vaqt: {seconds} soniya"

    def _next_task_text(self):
        if not self._tasks:
            return "Keyingi task yo'q"
        next_task = self._tasks[0]
        return f"Keyingi: {self._format_exec_time(next_task)}"

    def _update_clock(self):
        if not self._timeline_running:
            return

        try:
            now = datetime.datetime.now()
            self.date_label.configure(text=now.strftime("%d %B, %Y"))
            self.time_label.configure(text=now.strftime("%H:%M:%S"))
            if self._tasks:
                self.next_task_chip.set_text(self._next_task_text())
        except Exception:
            pass

        if self.winfo_exists():
            self.after(1000, self._update_clock)

    def on_show(self):
        self._refresh_task_list()
        if not self._timeline_running:
            self._timeline_running = True
            self._update_clock()

    def destroy(self):
        self._timeline_running = False
        super().destroy()
