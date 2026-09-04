# ========== backend.py ==========
# Mikasa AI — Backend Bridge
# Yangi GUI ni mavjud main.py funksiyalari bilan bog'laydi

import threading
import logging
import datetime
import re
import queue

logger = logging.getLogger(__name__)


class BackendBridge:
    """
    Yangi GUI ←→ main.py orasidagi ko'prik.

    MikasaApp yaratilganda BackendBridge ham yaratiladi.
    GUI dagi harakatlar (mic tugma, matn kiritish) → main.py funksiyalariga yo'naltiriladi.
    main.py dagi natijalar → GUI sahifalariga qaytariladi.
    """

    # main.py callback xabarlari — user gapirgani
    USER_PREFIXES = ("🗣️", "📝 Buyruq:")

    # Ichki holat xabarlari — chatga qo'shmaymiz (faqat status bar)
    STATUS_PREFIXES = (
        "🎙️ Tinglash",
        "🛑 Tinglash",
        "🎯 Buyruq:",  # intent aniqlanishi — ichki log
    )

    def __init__(self, app):
        self.app = app
        self._listening = False
        self._listening_thread = None
        self._ui_queue = queue.Queue()

        # main.py dan importlar (lazy — xato bo'lmasligi uchun)
        self._main_module = None
        self._ai_engine = None
        self._agent_memory = None
        self._agent_scheduler = None
        self._proactive_watcher = None
        self._ready = False

        # Duplikat xabar himoyasi (thread-safe)
        self._pending_lock = threading.Lock()
        self._pending_user_texts = set()

        # Activity feed
        self._activities = []

        try:
            self.app.after(40, self._process_ui_queue)
        except Exception:
            pass

    def _queue_ui(self, callback):
        """Background thread lardan UI ishlarini main thread ga uzatish."""
        self._ui_queue.put(callback)

    def _process_ui_queue(self):
        """Main thread da kutayotgan UI callbacklarni bajarish."""
        try:
            while True:
                callback = self._ui_queue.get_nowait()
                try:
                    callback()
                except Exception as e:
                    logger.debug(f"UI queue callback xatolik: {e}")
        except queue.Empty:
            pass

        try:
            if self.app.winfo_exists():
                self.app.after(40, self._process_ui_queue)
        except Exception:
            pass

    def init_backend(self):
        """Backend modullarini ishga tushirish (background thread da)"""

        def _init():
            try:
                import main as main_module

                self._main_module = main_module

                # GUI callback ni o'rnatish
                main_module.gui_bilan_integratsiya(self._gui_callback)

                # AI engine
                try:
                    from core import ai_engine

                    self._ai_engine = ai_engine
                except ImportError:
                    logger.warning("ai_engine topilmadi")

                # Agent Memory (singleton — duplikat yaratmaslik!)
                try:
                    from core.agent_memory import get_memory

                    self._agent_memory = get_memory()
                except ImportError:
                    # get_memory yo'q bo'lsa, to'g'ridan yaratish
                    from core.agent_memory import AgentMemory

                    self._agent_memory = AgentMemory()
                except Exception as e:
                    logger.warning(f"AgentMemory yuklanmadi: {e}")

                # Agent Scheduler
                try:
                    from core.agent_scheduler import get_scheduler

                    self._agent_scheduler = get_scheduler()
                except Exception as e:
                    logger.warning(f"Scheduler yuklanmadi: {e}")

                # Proactive Watcher — fon rejimida kuzatish
                try:
                    from core.proactive_watcher import (
                        start_proactive_watcher,
                        get_proactive_watcher,
                    )

                    start_proactive_watcher(on_suggestion=self._on_proactive_suggestion)
                    self._proactive_watcher = get_proactive_watcher()
                    logger.info("Proactive Watcher ishga tushdi")
                except Exception as e:
                    logger.warning(f"Proactive Watcher yuklanmadi: {e}")

                self._ready = True
                logger.info("Backend bridge tayyor")

                # GUI ga xabar
                self._queue_ui(lambda: self.app.set_status("online", "Tayyor"))
                self._add_activity("🟢 Backend ishga tushdi", "success")

            except Exception as e:
                logger.error(f"Backend init xatolik: {e}")
                self._queue_ui(lambda: self.app.set_status("offline", f"Xatolik: {e}"))

        thread = threading.Thread(target=_init, daemon=True, name="BackendInit")
        thread.start()

    # ========== GUI → BACKEND ==========

    def send_text_command(self, text):
        """
        Matnli buyruqni bajarish (Chat sahifasidan).
        Bu main.py dagi buyruqni_tushun() ni chaqiradi.
        """
        if not self._ready or not self._main_module:
            self._gui_callback("⚠️ Backend hali tayyor emas, biroz kuting...")
            return

        # Bu matnni duplikat sifatida belgilash
        with self._pending_lock:
            self._pending_user_texts.add(text)

        # Status yangilash
        self._queue_ui(lambda: self.app.set_status("busy", "Ishlamoqda..."))
        self._add_activity(f"💬 Buyruq: {text[:50]}", "primary")

        def _process():
            try:
                # Faollikni qayd etish (Proactive Watcher uchun)
                self.record_activity()

                m = self._main_module
                if not m:
                    return
                foydalanuvchi = m.foydalanuvchi_ismi_ol()
                ovoz = m.ovoz_turi_ol()
                m.buyruqni_tushun(text, foydalanuvchi, ovoz)
            except Exception as e:
                logger.error(f"Buyruq bajarishda xato: {e}")
                self._gui_callback(f"❌ Xatolik: {e}")
            finally:
                # Duplikat ro'yxatdan o'chirish
                with self._pending_lock:
                    self._pending_user_texts.discard(text)
                self._queue_ui(lambda: self.app.set_status("online", "Tayyor"))

        thread = threading.Thread(target=_process, daemon=True, name="CmdExec")
        thread.start()

    def start_listening(self):
        """Ovozli tinglashni boshlash"""
        if self._listening:
            return

        if not self._ready or not self._main_module:
            self._gui_callback("⚠️ Backend hali tayyor emas")
            return

        self._listening = True
        m = self._main_module
        if not m:
            self._listening = False
            return
        m.global_state.tinglash_faol = True

        # Faollikni qayd etish
        self.record_activity()

        self._queue_ui(lambda: self.app.set_status("listening", "Tinglayapman..."))
        self._add_activity("🎤 Tinglash boshlandi", "info")

        def _listen_loop():
            try:
                foydalanuvchi = m.foydalanuvchi_ismi_ol()
                ovoz = m.ovoz_turi_ol()
                m.fon_xizmat(foydalanuvchi, ovoz, self._gui_callback)
            except Exception as e:
                logger.error(f"Tinglash xatolik: {e}")
                self._gui_callback(f"❌ Tinglash xatoligi: {e}")
            finally:
                self._listening = False
                self._queue_ui(lambda: self.app.set_status("online", "Tayyor"))

        self._listening_thread = threading.Thread(
            target=_listen_loop, daemon=True, name="VoiceListener"
        )
        self._listening_thread.start()

    def stop_listening(self):
        """Tinglashni to'xtatish"""
        if not self._listening:
            return

        if self._main_module:
            self._main_module.global_state.tinglash_faol = False

        self._listening = False
        self._queue_ui(lambda: self.app.set_status("online", "Tayyor"))
        self._add_activity("🛑 Tinglash to'xtatildi", "warning")

    @property
    def is_listening(self):
        return self._listening

    # ========== BACKEND → GUI ==========

    def _gui_callback(self, xabar):
        """
        main.py → GUI xabar yuborish.
        Bu gui_ga_xabar_yuborish() dan chaqiriladi.
        Thread-safe — UI queue orqali main thread ga uzatiladi.
        """

        def _update():
            try:
                chat_page = self.app._pages.get("chat")
                voice_page = self.app._pages.get("voice")

                # ICHKI STATUS XABARLAR — chatga qo'shmaymiz
                if any(xabar.startswith(p) for p in self.STATUS_PREFIXES):
                    return

                # USER GAPIRGANI (ovozli yoki callback'dan)
                is_user_speech = any(xabar.startswith(p) for p in self.USER_PREFIXES)

                if is_user_speech:
                    # Foydalanuvchi matni — tozalash
                    clean = xabar
                    clean = clean.replace("🗣️ Siz: ", "")
                    clean = clean.replace("📝 Buyruq: ", "")
                    clean = clean.strip()

                    # Duplikat tekshirish — Chat dan yuborilgan matn bo'lsa, ko'rsatmaymiz
                    with self._pending_lock:
                        is_pending = clean in self._pending_user_texts
                    if is_pending:
                        # Bu matn allaqachon Chat da ko'rsatilgan — faqat voice ga qo'shamiz
                        pass
                    else:
                        # Ovozdan kelgan yangi buyruq — chatga ham qo'shamiz
                        if chat_page:
                            chat_page.add_message(clean, "user")

                    # Voice sahifasiga doim qo'shamiz
                    if voice_page:
                        voice_page.add_transcript(clean, "user")
                        voice_page.add_recent_command(clean)

                else:
                    # AI JAVOBI — har doim chatga qo'shamiz
                    if chat_page:
                        chat_page.add_message(xabar, "assistant")

                    # Voice sahifasiga ham AI javobini qo'shamiz
                    if voice_page and self._listening:
                        voice_page.add_transcript(xabar, "assistant")

                    # Activity feed
                    self._add_activity(
                        xabar[:60], "success" if "✅" in xabar else "info"
                    )

            except Exception as e:
                logger.debug(f"GUI callback xatolik: {e}")

        self._queue_ui(_update)

    # ========== ACTIVITY FEED ==========

    def _add_activity(self, text, category="info"):
        """Dashboard activity feed ga element qo'shish"""
        color_map = {
            "success": "#10B981",
            "primary": "#00D4FF",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "info": "#3B82F6",
        }

        now = datetime.datetime.now().strftime("%H:%M:%S")
        activity = {
            "text": text[:80],
            "time": now,
            "color": color_map.get(category, "#9CA3AF"),
        }

        self._activities.insert(0, activity)
        # Max 20 ta saqlash
        self._activities = self._activities[:20]

        self._queue_ui(self._refresh_dashboard_activity)

    def _refresh_dashboard_activity(self):
        """Dashboard activity feed ni qayta chizish"""
        try:
            from gui.theme import Colors, Fonts
            import customtkinter as ctk

            dashboard = self.app._pages.get("dashboard")
            if not dashboard:
                return

            # activity_card ni topish
            if not hasattr(dashboard, "_activity_list"):
                return

            # Tozalash
            for w in dashboard._activity_list.winfo_children():
                w.destroy()

            # Yangi elementlar
            for act in self._activities[:8]:
                row = ctk.CTkFrame(dashboard._activity_list, fg_color="transparent")
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    row,
                    text="●",
                    font=(Fonts.FAMILY, 8),
                    text_color=act["color"],
                    width=14,
                ).pack(side="left", padx=(0, 6))

                ctk.CTkLabel(
                    row,
                    text=act["text"],
                    font=Fonts.SMALL,
                    text_color=Colors.TEXT_PRIMARY,
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    row, text=act["time"], font=Fonts.TINY, text_color=Colors.TEXT_MUTED
                ).pack(side="right")

        except Exception as e:
            logger.debug(f"Dashboard activity yangilash xato: {e}")

    # ========== PROAKTIV WATCHER ==========

    def _on_proactive_suggestion(self, suggestion):
        """Proactive Watcher taklifini GUI ga ko'rsatish"""
        logger.info(f"Proactive suggestion: {suggestion}")

        def _show():
            try:
                chat_page = self.app._pages.get("chat")
                if chat_page:
                    # AI xabari sifatida ko'rsatish
                    chat_page.add_message(suggestion, "assistant")

                # Activity feed ga ham qo'shish
                self._add_activity(f"💡 {suggestion[:50]}", "primary")

                # Status bar yangilash
                self.app.set_status("info", "Taklif keldi")

            except Exception as e:
                logger.debug(f"Proactive suggestion display error: {e}")

        self._queue_ui(_show)

    def record_activity(self):
        """Foydalanuvchi faolligini Proactive Watcher ga xabar qilish"""
        if hasattr(self, "_proactive_watcher") and self._proactive_watcher:
            try:
                self._proactive_watcher.record_activity()
            except Exception:
                pass

    # ========== MA'LUMOT OLISH ==========

    def get_memory_stats(self):
        """Xotira statistikasi"""
        if self._agent_memory:
            return self._agent_memory.stats
        return {"kontekst_hajmi": 0, "suhbatlar_soni": 0, "bilimlar_soni": 0}

    def get_memory_conversations(self, last_n=20):
        """Suhbat tarixi"""
        if self._agent_memory:
            return self._agent_memory.get_conversations(last_n)
        return []

    def get_memory_knowledge(self):
        """Bilimlar bazasi"""
        if self._agent_memory:
            return self._agent_memory.get_knowledge()
        return {}

    def get_memory_profile(self):
        """Foydalanuvchi profili"""
        if self._agent_memory:
            return self._agent_memory.get_profile()
        return {}

    def get_scheduler_tasks(self):
        """Rejalashtirilgan vazifalar"""
        if self._agent_scheduler:
            return self._agent_scheduler.list_tasks()
        return []

    def save_knowledge(self, key, value):
        """Bilim saqlash"""
        if self._agent_memory:
            self._agent_memory.save_knowledge(key, value)

    def set_voice_type(self, voice_type):
        """Ovoz turini o'zgartirish"""
        if self._main_module:
            self._main_module.global_state.ovoz_turi_global = voice_type
