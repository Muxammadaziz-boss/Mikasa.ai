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
        self._build_ui()
    
    def _build_ui(self):
        # Markaziy layout
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.pack(fill="both", expand=True, padx=20, pady=16)
        
        # ===== SARLAVHA =====
        header = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header, text="🎤  Ovozli Dialog",
            font=Fonts.HEADING_2,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left")
        
        self.voice_status = ctk.CTkLabel(
            header, text="● Kutmoqda",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_MUTED
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
            width=200, height=200,
            border_width=2,
            border_color=Colors.BORDER
        )
        self.orb_container.pack()
        self.orb_container.pack_propagate(False)
        
        # Orb emoji
        self.orb_emoji = ctk.CTkLabel(
            self.orb_container,
            text="🔵",
            font=(Fonts.FAMILY, 72),
            text_color=Colors.PRIMARY
        )
        self.orb_emoji.place(relx=0.5, rely=0.5, anchor="center")
        
        # Status matni
        self.orb_text = ctk.CTkLabel(
            orb_frame,
            text="Tayyor",
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_SECONDARY
        )
        self.orb_text.pack(pady=(10, 0))
    
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
            state="disabled"
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
            fg_color=Colors.PRIMARY_DARK,
            hover_color=Colors.PRIMARY,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=25,
            height=56,
            width=280,
            command=self._toggle_listening
        )
        self.mic_btn.pack()
        
        # Qo'shimcha tugmalar
        btn_row = ctk.CTkFrame(mic_frame, fg_color="transparent")
        btn_row.pack(pady=(10, 0))
        
        SecondaryButton(
            btn_row, text="Tozalash", icon="🗑️",
            command=self._clear_transcript
        ).pack(side="left", padx=4)
    
    def _build_voice_settings(self, parent):
        """Ovoz sozlamalari paneli"""
        settings_card = GlassCard(parent, title="🔊 Ovoz sozlamalari")
        settings_card.pack(fill="x", pady=(0, 10))
        
        # Ovoz turi
        ctk.CTkLabel(
            settings_card.content, text="Ovoz turi",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY, anchor="w"
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
            text_color=Colors.TEXT_PRIMARY
        )
        self.voice_type.set("Erkak")
        self.voice_type.pack(fill="x", pady=(0, 12))
        
        # Ovoz tezligi
        ctk.CTkLabel(
            settings_card.content, text="Tezlik",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", pady=(0, 4))
        
        self.speed_slider = ctk.CTkSlider(
            settings_card.content,
            from_=0.5, to=2.0,
            number_of_steps=15,
            progress_color=Colors.PRIMARY,
            button_color=Colors.PRIMARY,
            button_hover_color=Colors.PRIMARY_DARK,
            fg_color=Colors.BG_INPUT
        )
        self.speed_slider.set(1.0)
        self.speed_slider.pack(fill="x", pady=(0, 12))
        
        # TTS Engine
        ctk.CTkLabel(
            settings_card.content, text="TTS Engine",
            font=Fonts.SMALL_BOLD,
            text_color=Colors.TEXT_SECONDARY, anchor="w"
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
            text_color=Colors.TEXT_PRIMARY
        )
        self.tts_engine_var.set("Silero")
        self.tts_engine_var.pack(fill="x")
    
    def _build_recent_commands(self, parent):
        """Oxirgi buyruqlar"""
        recent_card = GlassCard(parent, title="📋 Oxirgi buyruqlar")
        recent_card.pack(fill="both", expand=True, pady=(10, 0))
        
        # Bo'sh holat
        self.recent_list = ctk.CTkFrame(
            recent_card.content, fg_color="transparent"
        )
        self.recent_list.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            self.recent_list,
            text="Hali buyruq berilmagan",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED
        ).pack(pady=20)
    
    # ========== FUNKSIYALAR ==========
    
    def _toggle_listening(self):
        """Tinglashni boshlash/to'xtatish"""
        self._is_listening = not self._is_listening
        
        if self._is_listening:
            self.mic_btn.configure(
                text="⏹  To'xtatish",
                fg_color=Colors.DANGER,
                hover_color="#DC2626"
            )
            self.orb_container.configure(border_color=Colors.PRIMARY)
            self.orb_text.configure(
                text="Tinglayapman...",
                text_color=Colors.PRIMARY
            )
            self.voice_status.configure(
                text="● Tinglayapman",
                text_color=Colors.SUCCESS
            )
            if self.app:
                self.app.set_status("listening", "Tinglayapman...")
                # Backend orqali tinglashni boshlash
                if hasattr(self.app, 'bridge'):
                    self.app.bridge.start_listening()
        else:
            self.mic_btn.configure(
                text="🎙️  Tinglashni boshlash",
                fg_color=Colors.PRIMARY_DARK,
                hover_color=Colors.PRIMARY
            )
            self.orb_container.configure(border_color=Colors.BORDER)
            self.orb_text.configure(
                text="Tayyor",
                text_color=Colors.TEXT_SECONDARY
            )
            self.voice_status.configure(
                text="● Kutmoqda",
                text_color=Colors.TEXT_MUTED
            )
            if self.app:
                self.app.set_status("online", "Tayyor")
                # Backend orqali tinglashni to'xtatish
                if hasattr(self.app, 'bridge'):
                    self.app.bridge.stop_listening()
    
    def _clear_transcript(self):
        """Transkripsiyani tozalash"""
        self.transcript_text.configure(state="normal")
        self.transcript_text.delete("1.0", "end")
        self.transcript_text.configure(state="disabled")
    
    def add_transcript(self, text, role="user"):
        """Transkripsiyaga matn qo'shish"""
        self.transcript_text.configure(state="normal")
        prefix = "🧑 " if role == "user" else "🤖 "
        self.transcript_text.insert("end", f"{prefix}{text}\n")
        self.transcript_text.see("end")
        self.transcript_text.configure(state="disabled")
    
    def add_recent_command(self, text, result=""):
        """Oxirgi buyruqlar ro'yxatiga qo'shish"""
        # Birinchi element placeholder bo'lsa, o'chirib tashlash
        children = self.recent_list.winfo_children()
        if len(children) == 1 and isinstance(children[0], ctk.CTkLabel):
            children[0].destroy()
            children = []
            
        # Maksimal 10 ta saqlash
        if len(children) >= 10:
            children[0].destroy()
        
        time_str = datetime.datetime.now().strftime("%H:%M")
        row = ctk.CTkFrame(self.recent_list, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            row, text=f"● {text}",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            row, text=time_str,
            font=Fonts.TINY,
            text_color=Colors.TEXT_MUTED
        ).pack(side="right")
    
    def on_show(self):
        """Sahifa ko'rsatilganda"""
        pass
