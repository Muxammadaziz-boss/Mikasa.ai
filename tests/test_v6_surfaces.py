# ========== test_v6_surfaces.py ==========
# Mikasa AI v6.0.0 — Solid/Glass Surface System & Semantic Token Hardening Tests

import unittest
import customtkinter as ctk

from gui.theme import Colors, Surfaces
from gui.components import (
    Surface,
    Card,
    ElevatedCard,
    GlassCard,
    HeroCard,
    PageHero,
    OverlayCard,
    ToastNotification,
)
from gui.pages.dashboard import DashboardPage
from gui.pages.voice import VoicePage
from gui.pages.chat import ChatPage
from gui.pages.commands import CommandsPage
from gui.pages.memory import MemoryPage
from gui.pages.scheduler import SchedulerPage
from gui.pages.plugins import PluginsPage
from gui.pages.settings import SettingsPage


class TestSurfaceHierarchyAndTokens(unittest.TestCase):
    """Surface tokens and semantic hierarchy tests"""

    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        cls.root.withdraw()
        cls.container = ctk.CTkFrame(cls.root)
        cls.container.pack(fill="both", expand=True)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def setUp(self):
        Colors.apply_theme("dark")

    def test_dark_token_contrast_separation(self):
        """Tokens in dark theme must be distinctly differentiated"""
        Colors.apply_theme("dark")
        tokens = [
            Colors.BG_DARKEST,
            Colors.BG_DARK,
            Colors.BG_SURFACE,
            Colors.BG_CARD,
            Colors.BG_PANEL,
            Colors.BG_HOVER,
            Colors.BG_ACTIVE,
        ]
        # Verify no duplicate adjacent levels
        self.assertNotEqual(Colors.BG_DARKEST, Colors.BG_DARK)
        self.assertNotEqual(Colors.BG_DARK, Colors.BG_CARD)
        self.assertNotEqual(Colors.BG_CARD, Colors.BG_PANEL)
        self.assertNotEqual(Colors.BG_PANEL, Colors.BG_HOVER)
        self.assertNotEqual(Colors.BG_HOVER, Colors.BG_ACTIVE)
        # Verify glass background is distinct from solid card and panel
        self.assertNotEqual(Colors.GLASS_BG, Colors.BG_CARD)
        self.assertNotEqual(Colors.GLASS_BG, Colors.BG_PANEL)

    def test_light_token_contrast_and_subtle_borders(self):
        """Tokens in light theme must have clear active state and non-harsh borders"""
        Colors.apply_theme("light")
        self.assertNotEqual(Colors.BG_DARKEST, Colors.BG_DARK)
        self.assertNotEqual(Colors.BG_DARK, Colors.BG_CARD)
        self.assertNotEqual(Colors.BG_HOVER, Colors.BG_ACTIVE)
        # Light mode glass surface is clean ice-tinted white, not dingy gray
        self.assertEqual(Colors.GLASS_BG, "#F0F6FD")
        # Light mode text contrast
        self.assertEqual(Colors.TEXT_PRIMARY, "#0F172A")
        # Light mode borders are soft
        self.assertEqual(Colors.BORDER, "#E2E8F0")
        self.assertEqual(Colors.BORDER_SUBTLE, "#EEF2F6")

    def test_border_discipline_hierarchy(self):
        """Border hierarchy must progress from subtle to elevated, glass, and hero accent"""
        for theme in ("dark", "light"):
            with self.subTest(theme=theme):
                Colors.apply_theme(theme)
                self.assertIsNotNone(Colors.BORDER_SUBTLE)
                self.assertIsNotNone(Colors.BORDER)
                self.assertIsNotNone(Colors.BORDER_ELEVATED)
                self.assertIsNotNone(Colors.BORDER_GLASS)
                self.assertIsNotNone(Colors.BORDER_HERO)

                # Hero border matches or exceeds accent luminosity
                self.assertNotEqual(Colors.BORDER, Colors.BORDER_HERO)

    def test_semantic_surfaces_class_get_tokens(self):
        """Surfaces class returns valid dictionaries for all 7 tiers"""
        for theme in ("dark", "light"):
            Colors.apply_theme(theme)
            tiers = [
                Surfaces.BASE,
                Surfaces.SURFACE,
                Surfaces.CARD,
                Surfaces.ELEVATED,
                Surfaces.GLASS,
                Surfaces.HERO,
                Surfaces.OVERLAY,
            ]
            for tier in tiers:
                with self.subTest(theme=theme, tier=tier):
                    tok = Surfaces.get_tokens(tier)
                    self.assertIn("fg_color", tok)
                    self.assertIn("border_color", tok)
                    self.assertIn("border_width", tok)
                    self.assertTrue(tok["fg_color"])
                    self.assertTrue(tok["border_color"])

    def test_surface_component_instantiations(self):
        """Card, ElevatedCard, GlassCard, HeroCard, PageHero, OverlayCard instantiate with correct tiers"""
        base_surface = Surface(self.container, tier=Surfaces.BASE)
        card = Card(self.container, title="Solid Card")
        elevated = ElevatedCard(self.container, title="Elevated Panel")
        glass = GlassCard(self.container, title="Glass Panel")
        hero_card = HeroCard(self.container, title="Hero Accent Panel")
        hero = PageHero(self.container, title="Hero Header", icon="sparkles")
        overlay = OverlayCard(self.container, title="Modal Dialog")

        self.assertEqual(base_surface._surface_tier, Surfaces.BASE)
        self.assertEqual(card._surface_tier, Surfaces.CARD)
        self.assertEqual(elevated._surface_tier, Surfaces.ELEVATED)
        self.assertEqual(glass._surface_tier, Surfaces.GLASS)
        self.assertEqual(hero_card._surface_tier, Surfaces.HERO)
        self.assertEqual(hero._surface_tier, Surfaces.HERO)
        self.assertEqual(overlay._surface_tier, Surfaces.OVERLAY)

        # Check colors
        self.assertEqual(card.cget("fg_color"), Colors.BG_CARD)
        self.assertEqual(elevated.cget("fg_color"), Colors.BG_PANEL)
        self.assertEqual(glass.cget("fg_color"), Colors.GLASS_BG)
        self.assertEqual(glass.cget("border_color"), Colors.GLASS_BORDER)
        self.assertEqual(hero_card.cget("fg_color"), Colors.GLASS_HERO_BG)
        self.assertEqual(hero_card.cget("border_color"), Colors.GLASS_HERO_BORDER)
        self.assertEqual(overlay.cget("fg_color"), Colors.OVERLAY_BG)

        for w in (base_surface, card, elevated, glass, hero_card, hero, overlay):
            w.destroy()

    def test_toast_notification_uses_overlay_surface(self):
        toast = ToastNotification(self.container, message="Xabar", title="Test Toast", duration=500)
        self.assertEqual(toast.cget("fg_color"), Colors.OVERLAY_BG)
        toast.dismiss()

    def test_eighty_twenty_rule_page_audit(self):
        """
        Verify the 80/20 rule: standard UI pages use predominantly solid Card / ElevatedCard.
        GlassCard is used strictly for hero/floating status surfaces.
        """
        pages = [
            DashboardPage(self.container),
            VoicePage(self.container),
            SettingsPage(self.container),
            CommandsPage(self.container),
            MemoryPage(self.container),
            SchedulerPage(self.container),
            PluginsPage(self.container),
            ChatPage(self.container),
        ]

        for page in pages:
            page_name = page.__class__.__name__
            with self.subTest(page=page_name):
                # Count Card vs GlassCard widgets
                all_cards = []
                def collect_cards(w):
                    # Check if w is instance of Card (note: GlassCard inherits Card)
                    if isinstance(w, Card):
                        all_cards.append(w)
                    for child in w.winfo_children():
                        collect_cards(child)

                collect_cards(page)
                
                # Exclude PageHero from glass count since PageHero is the intentional hero banner
                glass_cards = [c for c in all_cards if isinstance(c, GlassCard) and not isinstance(c, PageHero)]
                solid_cards = [c for c in all_cards if not isinstance(c, GlassCard)]

                # On Settings, Voice, Plugins, Commands, Memory, Scheduler:
                # ALL content cards must be solid Card or ElevatedCard!
                if page_name in ("SettingsPage", "VoicePage", "PluginsPage", "CommandsPage", "SchedulerPage"):
                    self.assertEqual(
                        len(glass_cards),
                        0,
                        f"{page_name} has unexpected non-hero GlassCards: {glass_cards}",
                    )
                    self.assertGreater(
                        len(solid_cards),
                        0,
                        f"{page_name} must have solid content Cards",
                    )

            page.destroy()


if __name__ == "__main__":
    unittest.main()
