# ========== voice.py ==========
# Voice Interaction sahifasi — ovozli dialog interfeysi

import customtkinter as ctk
import datetime
from gui.theme import Colors, Fonts, Sizing, Icons
from gui.icons import get_vector_icon
from gui.components import AppleSiriOrb, Card, GlassButton, GlassCard, GlowButton, SecondaryButton


class VoicePage(ctk.CTkFrame):
    """Ovozli buyruq va dialog sahifasi - Voice First Premium UI"""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._is_listening = False
        self._transcript_history = []
        self._build_ui()

    def _build_ui(self):
        # Asosiy scroll konteyner
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True)
        
        # Markazlashtirish uchun ichki konteyner (max 600px kenglik)
        self.center = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.center.pack(expand=True, fill="y", padx=40)
        
        # Build sections
        self._build_orb_section(self.center)
        self._build_controls(self.center)
        self._build_transcript_section(self.center)
        self._build_activity_section(self.center)

    def _build_orb_section(self, parent):
        """Markaziy AI Orb — sahifaning dominant vizual elementi"""
        orb_container = ctk.CTkFrame(parent, fg_color="transparent")
        orb_container.pack(pady=(40, 0))
        
        # Katta orb (280px)
        self.apple_orb = AppleSiriOrb(orb_container, size=280)
        self.apple_orb.pack()
        self.orb_container = self.apple_orb
        
        # "Qanday yordam beray?" — asosiy matn
        self.orb_text = ctk.CTkLabel(
            orb_container,
            text="Qanday yordam beray?",
            font=Fonts.HEADING_1,
            text_color=Colors.TEXT_PRIMARY,
        )
        self.orb_text.pack(pady=(20, 0))
        
        # Holat indikatori: ● Online · Kutmoqda
        status_row = ctk.CTkFrame(orb_container, fg_color="transparent")
        status_row.pack(pady=(8, 0))
        
        self.voice_dot = ctk.CTkLabel(
            status_row,
            text="",
            image=get_vector_icon("circle", size=8, color=Colors.SUCCESS, fallback="circle"),
        )
        self.voice_dot.pack(side="left", padx=(0, 6))
        
        self.voice_status = ctk.CTkLabel(
            status_row,
            text="Online \u00b7 Kutmoqda",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
        )
        self.voice_status.pack(side="left")

    def _build_controls(self, parent):
        """Mikrofon tugmasi va ixcham boshqaruv tugmalari"""
        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(pady=(28, 0))
        
        # Katta mikrofon pill tugmasi
        self._mic_icon_idle = get_vector_icon("mic", size=22, color=Colors.TEXT_PRIMARY, fallback="mic")
        self._mic_icon_active = get_vector_icon("stop", size=22, color="#FFFFFF", fallback="circle")
        
        self.mic_btn = ctk.CTkButton(
            controls_frame,
            text="  Tinglashni boshlash",
            image=self._mic_icon_idle,
            compound="left",
            font=Fonts.HEADING_3,
            fg_color=Colors.GLASS_HERO_BG,
            hover_color=Colors.GLASS_HERO_HOVER,
            border_width=2,
            border_color=Colors.GLASS_HERO_BORDER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Sizing.PILL,
            height=56,
            width=300,
            command=self._toggle_listening,
        )
        self.mic_btn.pack()
        
        # Ikkilamchi tugmalar qatori
        secondary_row = ctk.CTkFrame(controls_frame, fg_color="transparent")
        secondary_row.pack(pady=(14, 0))
        
        # Use existing GlassButton from components 
        GlassButton(
            secondary_row,
            text="Tozalash",
            icon="trash",
            font=Fonts.SMALL,
            height=32,
            width=110,
            corner_radius=Sizing.RADIUS_BUTTON,
            command=self._clear_transcript,
        ).pack(side="left", padx=4)
        
        GlassButton(
            secondary_row,
            text="Chat",
            icon="chat",  
            font=Fonts.SMALL,
            height=32,
            width=110,
            corner_radius=Sizing.RADIUS_BUTTON,
            command=lambda: self.app.navigate_to("chat") if self.app else None,
        ).pack(side="left", padx=4)

    def _build_transcript_section(self, parent):
        """Transkripsiya maydoni — solid Card (80/20 design system)"""
        transcript_card = Card(parent, title="Transkripsiya")
        transcript_card.pack(fill="x", pady=(24, 0), padx=20)

        self.transcript_text = ctk.CTkTextbox(
            transcript_card.content,
            font=Fonts.BODY,
            fg_color=Colors.BG_SURFACE,
            text_color=Colors.TEXT_SECONDARY,
            corner_radius=Sizing.SMALL,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            height=120,
            wrap="word",
            state="disabled",
        )
        self.transcript_text.pack(fill="x")

    def _build_activity_section(self, parent):
        """Agent jarayoni ko'rsatish joyi"""
        self.activity_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.activity_frame.pack(fill="x", pady=(16, 30), padx=20)
        
        self.activity_label = ctk.CTkLabel(
            self.activity_frame,
            text="",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        # Initially hidden - will be shown when agent is active
        
    def show_activity(self, text):
        """Agent activity ko'rsatish"""
        self.activity_label.configure(text=text)
        self.activity_label.pack(fill="x")
        
    def hide_activity(self):
        """Agent activity yashirish"""
        self.activity_label.pack_forget()

    # ========== STUBS FOR REMOVED FEATURES ==========
    
    def add_recent_command(self, text, result="", time_str=None, track_state=True):
        """Stub — Endi bu funksiya shu sahifada emas"""
        pass

    def _build_voice_settings(self, parent):
        """Stub — Voice sozlamalari Settings sahifasiga ko'chirildi"""
        pass

    def _build_recent_commands(self, parent):
        """Stub — Oxirgi buyruqlar olib tashlandi"""
        pass

    def _on_voice_type_change(self, value):
        """Stub"""
        pass

    def _on_speed_change(self, value):
        """Stub"""
        pass

    def _on_tts_engine_change(self, value):
        """Stub"""
        pass

    def _recent_command_count(self):
        """Stub"""
        return 0

    # ========== FUNKSIYALAR ==========

    def _toggle_listening(self):
        """Tinglashni boshlash/to'xtatish"""
        self._is_listening = not self._is_listening

        if self._is_listening:
            self.mic_btn.configure(
                text="  To'xtatish",
                image=self._mic_icon_active,
                fg_color=Colors.DANGER,
                hover_color="#DC2626",
                border_color="#FF6961",
            )
            if hasattr(self, "apple_orb"):
                self.apple_orb.set_state("listening")
            self.orb_text.configure(text="Tinglayapman...", text_color=Colors.PRIMARY)
            if hasattr(self, "voice_dot"):
                self.voice_dot.configure(
                    image=get_vector_icon("circle", size=8, color=Colors.SUCCESS, fallback="circle")
                )
            self.voice_status.configure(
                text="Tinglayapman", text_color=Colors.SUCCESS
            )
            if self.app:
                self.app.set_status("listening", "Tinglayapman...")
                # Backend orqali tinglashni boshlash
                if hasattr(self.app, "bridge"):
                    self.app.bridge.start_listening()
        else:
            self.mic_btn.configure(
                text="  Tinglashni boshlash",
                image=self._mic_icon_idle,
                fg_color=Colors.GLASS_HERO_BG,
                hover_color=Colors.GLASS_HERO_HOVER,
                border_color=Colors.GLASS_HERO_BORDER,
            )
            if hasattr(self, "apple_orb"):
                self.apple_orb.set_state("idle")
            self.orb_text.configure(text="Qanday yordam beray?", text_color=Colors.TEXT_PRIMARY)
            if hasattr(self, "voice_dot"):
                self.voice_dot.configure(
                    image=get_vector_icon("circle", size=8, color=Colors.TEXT_MUTED, fallback="circle")
                )
            self.voice_status.configure(text="Online \u00b7 Kutmoqda", text_color=Colors.TEXT_MUTED)
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
        prefix = "Siz: " if role == "user" else "Mikasa: "
        self.transcript_text.insert("end", f"{prefix}{text}\n")
        self.transcript_text.see("end")
        self.transcript_text.configure(state="disabled")

    def on_show(self):
        """Sahifa ko'rsatilganda"""
        if (
            self.app
            and hasattr(self.app, "bridge")
            and self.app.bridge.is_listening
        ):
            self._is_listening = True
            self.mic_btn.configure(
                text="  To'xtatish",
                image=self._mic_icon_active,
                fg_color=Colors.DANGER,
                hover_color="#DC2626",
            )
            if hasattr(self, "voice_dot"):
                self.voice_dot.configure(
                    image=get_vector_icon("circle", size=8, color=Colors.SUCCESS, fallback="circle")
                )
            self.voice_status.configure(
                text="Tinglayapman", text_color=Colors.SUCCESS
            )
            self.orb_text.configure(
                text="Tinglayapman...", text_color=Colors.PRIMARY
            )
        else:
            self._is_listening = False
            self.mic_btn.configure(
                text="  Tinglashni boshlash",
                image=self._mic_icon_idle,
                fg_color=Colors.GLASS_HERO_BG,
                hover_color=Colors.GLASS_HERO_HOVER,
            )
            if hasattr(self, "voice_dot"):
                self.voice_dot.configure(
                    image=get_vector_icon("circle", size=8, color=Colors.TEXT_MUTED, fallback="circle")
                )
            self.voice_status.configure(
                text="Online \u00b7 Kutmoqda", text_color=Colors.TEXT_MUTED
            )
            self.orb_text.configure(text="Qanday yordam beray?", text_color=Colors.TEXT_PRIMARY)

        # Orb animatsiyasini qayta faollashtirish
        if hasattr(self, "apple_orb"):
            self.apple_orb.start()

    def on_hide(self):
        """Sahifadan chiqilganda orb animatsiyasini to'xtatish (CPU yukini 0% qilish)"""
        if hasattr(self, "apple_orb"):
            self.apple_orb.stop()

    def export_ui_state(self):
        return {
            "transcript": list(self._transcript_history),
        }

    def import_ui_state(self, state):
        state = state or {}
        self._clear_transcript()
        self._transcript_history = []

        transcript = state.get("transcript", [])

        for item in transcript:
            self.add_transcript(
                item.get("text", ""), item.get("role", "user"), track_state=True
            )
