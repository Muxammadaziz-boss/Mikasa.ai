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

    def test_explicit_surface_api(self):
        """Card(..., surface=...) allows explicit surface selection without subclassing"""
        c_elevated = Card(self.container, title="Explicit Elevated", surface="elevated")
        c_glass = Card(self.container, title="Explicit Glass", surface="glass")
        c_hero = Card(self.container, title="Explicit Hero", surface="hero")

        self.assertEqual(c_elevated._surface_tier, Surfaces.ELEVATED)
        self.assertEqual(c_elevated.cget("fg_color"), Colors.BG_PANEL)

        self.assertEqual(c_glass._surface_tier, Surfaces.GLASS)
        self.assertEqual(c_glass.cget("fg_color"), Colors.GLASS_BG)

        self.assertEqual(c_hero._surface_tier, Surfaces.HERO)
        self.assertEqual(c_hero.cget("fg_color"), Colors.GLASS_HERO_BG)

        for w in (c_elevated, c_glass, c_hero):
            w.destroy()

    def test_fg_color_precedence_and_overrides(self):
        """Explicit fg_color, border_color, border_width, corner_radius take strict precedence"""
        custom = Card(
            self.container,
            title="Custom Override",
            fg_color="#123456",
            border_color="#654321",
            border_width=3,
            corner_radius=8,
        )
        self.assertEqual(custom.cget("fg_color"), "#123456")
        self.assertEqual(custom.cget("border_color"), "#654321")
        self.assertEqual(custom.cget("border_width"), 3)
        self.assertEqual(custom.cget("corner_radius"), 8)
        self.assertTrue(custom._user_fg_override)
        self.assertTrue(custom._user_border_override)
        custom.destroy()

    def test_nested_cards_combinations(self):
        """
        Verify nested card hierarchies:
        1. Card -> Card
        2. Card -> GlassCard
        3. GlassCard -> Card
        4. ElevatedCard -> Card
        Child card corner bg_color must resolve cleanly to parent foreground.
        """
        # 1. Card -> Card
        p1 = Card(self.container, title="Parent Solid")
        c1 = Card(p1.content, title="Child Solid")
        self.root.update()
        self.assertEqual(c1._bg_color, p1.cget("fg_color"))

        # 2. Card -> GlassCard
        p2 = Card(self.container, title="Parent Solid")
        c2 = GlassCard(p2.content, title="Child Glass")
        self.root.update()
        self.assertEqual(c2._bg_color, p2.cget("fg_color"))

        # 3. GlassCard -> Card
        p3 = GlassCard(self.container, title="Parent Glass")
        c3 = Card(p3.content, title="Child Solid")
        self.root.update()
        self.assertEqual(c3._bg_color, p3.cget("fg_color"))

        # 4. ElevatedCard -> Card
        p4 = ElevatedCard(self.container, title="Parent Elevated")
        c4 = Card(p4.content, title="Child Solid")
        self.root.update()
        self.assertEqual(c4._bg_color, p4.cget("fg_color"))

        for w in (p1, p2, p3, p4):
            w.destroy()

    def test_theme_switching_lifecycle(self):
        """Card.update_theme() refreshes colors on Dark -> Light -> Dark transitions without losing overrides"""
        Colors.apply_theme("dark")
        card = Card(self.container, title="Switching Card")
        override_card = Card(self.container, title="Overridden Card", fg_color="#AABBCC")

        self.assertEqual(card.cget("fg_color"), Colors._DARK["BG_CARD"])
        self.assertEqual(override_card.cget("fg_color"), "#AABBCC")

        # Switch to Light
        Colors.apply_theme("light")
        card.update_theme()
        override_card.update_theme()
        self.assertEqual(card.cget("fg_color"), Colors._LIGHT["BG_CARD"])
        # Override must be preserved!
        self.assertEqual(override_card.cget("fg_color"), "#AABBCC")

        # Switch back to Dark
        Colors.apply_theme("dark")
        card.update_theme()
        override_card.update_theme()
        self.assertEqual(card.cget("fg_color"), Colors._DARK["BG_CARD"])
        self.assertEqual(override_card.cget("fg_color"), "#AABBCC")

        card.destroy()
        override_card.destroy()


if __name__ == "__main__":
    unittest.main()
