# ========== voice.py ==========
# Voice Interaction sahifasi — ovozli dialog interfeysi

import customtkinter as ctk
import datetime
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.components import GlassCard, GlowButton, SecondaryButton


class VoicePage(ctk.CTkFrame):
    """Ovozli buyruq va dialog sahifasi"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._is_listening = False
        self._transcript_history = []
        self._recent_commands_data = []
        self._build_ui()

    def _build_ui(self):
        # Markaziy layout
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.pack(fill="both", expand=True, padx=20, pady=16)

        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header,
            text="🎤  Ovozli Dialog",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        self.voice_status = ctk.CTkLabel(
            header,
            text="● Kutmoqda",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_MUTED,
        )
        self.voice_status.pack(side="right")

        # ===== ASOSIY KONTENT — 2 COLUMN =====
        content = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # --- CHAP: ORB VA TRANSKRIPSIYA ---
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._build_orb(left)
        self._build_transcript(left)
        self._build_mic_button(left)

        # --- O'NG: SOZLAMALAR VA TARIX ---
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        self._build_voice_settings(right)
        self._build_recent_commands(right)

    def _build_orb(self, parent):
        """Markaziy AI Orb"""
        orb_frame = ctk.CTkFrame(parent, fg_color="transparent")
        orb_frame.pack(pady=(20, 10))

        # Orb konteyner (border bilan)
        self.orb_container = ctk.CTkFrame(
            orb_frame,
            fg_color=Colors.BG_CARD,
            corner_radius=150,
            width=200,
            height=200,
            border_width=1,
            border_color=Colors.BORDER,
            bg_color=Colors.BG_DARK,
        )
        self.orb_container.pack()
        self.orb_container.pack_propagate(False)

        # Orb emoji
        self.orb_emoji = ctk.CTkLabel(
            self.orb_container,
            text="🔵",
            font=(Fonts.FAMILY, 72),
            text_color=Colors.PRIMARY,
        )
        self.orb_emoji.place(relx=0.5, rely=0.5, anchor="center")

        # Status matni
        self.orb_text = ctk.CTkLabel(
            orb_frame,
            text="Tayyor",
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_SECONDARY,
        )
        self.orb_text.pack(pady=(10, 0))

        self.orb_hint = ctk.CTkLabel(
            orb_frame,
            text="Ovozli buyruq berish uchun tugmani bosing",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        )
        self.orb_hint.pack(pady=(4, 0))

    def _build_transcript(self, parent):
        """Real-time transkripsiya maydoni"""
        transcript_card = GlassCard(parent, title="📝 Transkripsiya")
        transcript_card.pack(fill="x", padx=20, pady=10)

        self.transcript_text = ctk.CTkTextbox(
            transcript_card.content,
            font=Fonts.BODY,
            fg_color=Colors.BG_INPUT,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=8,
            height=100,
            wrap="word",
            state="disabled",
        )
        self.transcript_text.pack(fill="x")

    def _build_mic_button(self, parent):
        """Mikrofon tugmasi"""
        mic_frame = ctk.CTkFrame(parent, fg_color="transparent")
        mic_frame.pack(pady=16)

        self.mic_btn = ctk.CTkButton(
            mic_frame,
            text="🎙️  Tinglashni boshlash",
            font=Fonts.HEADING_3,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=25,
            height=56,
            width=280,
            bg_color=Colors.BG_DARK,
            command=self._toggle_listening,
        )
        self.mic_btn.pack()

        # Qo'shimcha tugmalar
        btn_row = ctk.CTkFrame(mic_frame, fg_color="transparent")
        btn_row.pack(pady=(10, 0))

        SecondaryButton(
            btn_row, text="Tozalash", icon="🗑️", command=self._clear_transcript
        ).pack(side="left", padx=4)

    def _build_voice_settings(self, parent):
        """Ovoz sozlamalari paneli"""
        settings_card = GlassCard(parent, title="🔊 Ovoz sozlamalari")
        settings_card.pack(fill="x", pady=(0, 10))

        # Ovoz turi
        ctk.CTkLabel(
            settings_card.content,
            text="Ovoz turi",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.voice_type = ctk.CTkSegmentedButton(
            settings_card.content,
            values=["Erkak", "Ayol"],
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            selected_color=Colors.PRIMARY_DARK,
            selected_hover_color=Colors.PRIMARY,
            unselected_color=Colors.BG_INPUT,
            unselected_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            command=self._on_voice_type_change,
        )
        self.voice_type.set("Erkak")
        self.voice_type.pack(fill="x", pady=(0, 12))

        # Ovoz tezligi
        ctk.CTkLabel(
            settings_card.content,
            text="Tezlik",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.speed_slider = ctk.CTkSlider(
            settings_card.content,
            from_=0.5,
            to=2.0,
            number_of_steps=15,
            progress_color=Colors.PRIMARY,
            button_color=Colors.PRIMARY,
            button_hover_color=Colors.PRIMARY_DARK,
            fg_color=Colors.BG_INPUT,
            command=self._on_speed_change,
        )
        self.speed_slider.set(1.0)
        self.speed_slider.pack(fill="x", pady=(0, 12))

        # TTS Engine
        ctk.CTkLabel(
            settings_card.content,
            text="TTS Engine",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.tts_engine_var = ctk.CTkSegmentedButton(
            settings_card.content,
            values=["Silero", "Edge TTS"],
            font=Fonts.SMALL,
            fg_color=Colors.BG_INPUT,
            selected_color=Colors.PRIMARY_DARK,
            selected_hover_color=Colors.PRIMARY,
            unselected_color=Colors.BG_INPUT,
            unselected_hover_color=Colors.BG_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            command=self._on_tts_engine_change,
        )
        self.tts_engine_var.set("Silero")
        self.tts_engine_var.pack(fill="x")

    def _build_recent_commands(self, parent):
        """Oxirgi buyruqlar"""
        recent_card = GlassCard(parent, title="📋 Oxirgi buyruqlar")
        recent_card.pack(fill="both", expand=True, pady=(10, 0))

        # Bo'sh holat
        self.recent_list = ctk.CTkFrame(recent_card.content, fg_color="transparent")
        self.recent_list.pack(fill="both", expand=True)

        self.recent_count = ctk.CTkLabel(
            recent_card.content,
            text="0 buyruq",
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self.recent_count.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            self.recent_list,
            text="Hali buyruq berilmagan",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        ).pack(pady=20)

    # ========== FUNKSIYALAR ==========

    def _toggle_listening(self):
        """Tinglashni boshlash/to'xtatish"""
        self._is_listening = not self._is_listening

        if self._is_listening:
            self.mic_btn.configure(
                text="⏹  To'xtatish", fg_color=Colors.DANGER, hover_color="#DC2626"
            )
            self.orb_container.configure(border_color=Colors.PRIMARY)
            self.orb_text.configure(text="Tinglayapman...", text_color=Colors.PRIMARY)
            self.voice_status.configure(
                text="● Tinglayapman", text_color=Colors.SUCCESS
            )
            self.orb_hint.configure(text="Mikrofondan tinglayapman...")
            if self.app:
                self.app.set_status("listening", "Tinglayapman...")
                # Backend orqali tinglashni boshlash
                if hasattr(self.app, "bridge"):
                    self.app.bridge.start_listening()
        else:
            self.mic_btn.configure(
                text="🎙️  Tinglashni boshlash",
                fg_color=Colors.PRIMARY_DARK,
                hover_color=Colors.PRIMARY,
            )
            self.orb_container.configure(border_color=Colors.BORDER)
            self.orb_text.configure(text="Tayyor", text_color=Colors.TEXT_SECONDARY)
            self.voice_status.configure(text="● Kutmoqda", text_color=Colors.TEXT_MUTED)
            self.orb_hint.configure(text="Ovozli buyruq berish uchun tugmani bosing")
            if self.app:
                self.app.set_status("online", "Tayyor")
                # Backend orqali tinglashni to'xtatish
                if hasattr(self.app, "bridge"):
                    self.app.bridge.stop_listening()

    def _clear_transcript(self):
        """Transkripsiyani tozalash"""
        self.transcript_text.configure(state="normal")
        self.transcript_text.delete("1.0", "end")
        self.transcript_text.configure(state="disabled")
        self._transcript_history.clear()

    def add_transcript(self, text, role="user", track_state=True):
        """Transkripsiyaga matn qo'shish"""
        if track_state:
            self._transcript_history.append({"text": text, "role": role})
        self.transcript_text.configure(state="normal")
        prefix = "🧑 " if role == "user" else "🤖 "
        self.transcript_text.insert("end", f"{prefix}{text}\n")
        self.transcript_text.see("end")
        self.transcript_text.configure(state="disabled")

    def add_recent_command(self, text, result="", time_str=None, track_state=True):
        """Oxirgi buyruqlar ro'yxatiga qo'shish"""
        time_str = time_str or datetime.datetime.now().strftime("%H:%M")

        if track_state:
            self._recent_commands_data.append(
                {"text": text, "result": result, "time": time_str}
            )
            self._recent_commands_data = self._recent_commands_data[-10:]

        # Birinchi element placeholder bo'lsa, o'chirib tashlash
        children = self.recent_list.winfo_children()
        if len(children) == 1 and isinstance(children[0], ctk.CTkLabel):
            children[0].destroy()
            children = []

        # Maksimal 10 ta saqlash
        if len(children) >= 10:
            children[0].destroy()

        row = ctk.CTkFrame(self.recent_list, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(
            row,
            text=f"● {text}",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            row, text=time_str, font=Fonts.TINY, text_color=Colors.TEXT_MUTED
        ).pack(side="right")

        self.recent_count.configure(text=f"{self._recent_command_count()} buyruq")

    def _on_voice_type_change(self, value):
        """Ovoz turi o'zgarganda — config ga saqlash va backend ga xabar"""
        try:
            from config import set_config

            ovoz = "erkak" if value == "Erkak" else "ayol"
            set_config("user.voice_type", ovoz)
            # main.py global_state ni ham yangilash
            try:
                import main

                main.global_state.ovoz_turi_global = ovoz
            except Exception:
                pass
        except Exception:
            pass

    def _on_speed_change(self, value):
        """Ovoz tezligi o'zgarganda — config ga saqlash"""
        try:
            from config import set_config

            set_config("audio.tts_speed", round(value, 1))
        except Exception:
            pass

    def _on_tts_engine_change(self, value):
        """TTS Engine o'zgarganda — config ga saqlash"""
        try:
            from config import set_config

            engine = "silero" if value == "Silero" else "edge_tts"
            set_config("audio.tts_engine", engine)
        except Exception:
            pass

    def on_show(self):
        """Sahifa ko'rsatilganda — config dan joriy qiymatlarni yuklash"""
        try:
            from config import get_config

            # Ovoz turi
            ovoz = get_config("user.voice_type", "erkak")
            self.voice_type.set("Ayol" if ovoz == "ayol" else "Erkak")
            # Tezlik
            speed = get_config("audio.tts_speed", 1.0)
            self.speed_slider.set(float(str(speed)))
            # TTS Engine
            engine = get_config("audio.tts_engine", "silero")
            self.tts_engine_var.set("Edge TTS" if engine == "edge_tts" else "Silero")

            if (
                self.app
                and hasattr(self.app, "bridge")
                and self.app.bridge.is_listening
            ):
                self._is_listening = True
                self.mic_btn.configure(
                    text="⏹  To'xtatish",
                    fg_color=Colors.DANGER,
                    hover_color="#DC2626",
                )
                self.voice_status.configure(
                    text="● Tinglayapman", text_color=Colors.SUCCESS
                )
                self.orb_text.configure(
                    text="Tinglayapman...", text_color=Colors.PRIMARY
                )
                self.orb_hint.configure(text="Mikrofondan tinglayapman...")
            else:
                self._is_listening = False
                self.mic_btn.configure(
                    text="🎙️  Tinglashni boshlash",
                    fg_color=Colors.PRIMARY_DARK,
                    hover_color=Colors.PRIMARY,
                )
                self.voice_status.configure(
                    text="● Kutmoqda", text_color=Colors.TEXT_MUTED
                )
                self.orb_text.configure(text="Tayyor", text_color=Colors.TEXT_SECONDARY)
                self.orb_hint.configure(
                    text="Ovozli buyruq berish uchun tugmani bosing"
                )

            self.recent_count.configure(text=f"{self._recent_command_count()} buyruq")
        except Exception:
            pass

    def _recent_command_count(self):
        return sum(
            1
            for child in self.recent_list.winfo_children()
            if isinstance(child, ctk.CTkFrame)
        )

    def export_ui_state(self):
        return {
            "transcript": list(self._transcript_history),
            "recent_commands": list(self._recent_commands_data),
        }

    def import_ui_state(self, state):
        state = state or {}
        self._clear_transcript()
        for child in self.recent_list.winfo_children():
            child.destroy()

        self._recent_commands_data = []
        self._transcript_history = []

        transcript = state.get("transcript", [])
        recent_commands = state.get("recent_commands", [])

        for item in transcript:
            self.add_transcript(
                item.get("text", ""), item.get("role", "user"), track_state=True
            )

        for item in recent_commands:
            self.add_recent_command(
                item.get("text", ""),
                item.get("result", ""),
                time_str=item.get("time", ""),
                track_state=True,
            )

        if not recent_commands:
            ctk.CTkLabel(
                self.recent_list,
                text="Hali buyruq berilmagan",
                font=Fonts.SMALL,
                text_color=Colors.TEXT_MUTED,
            ).pack(pady=20)

        self.recent_count.configure(text=f"{self._recent_command_count()} buyruq")
