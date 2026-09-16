# ========== test_tool_capabilities.py ==========
# Phase 32 — Capability Discovery & Smart Selection Unit Tests
# Semantic Capabilities, Intent Recognition, Multi-factor Scoring & Fallback

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.intelligence.types import RiskLevel
from core.tools.contract import ToolContract2, ToolHealth
from core.tools.discovery import CapabilityRegistry
from core.tools.selector import SmartToolSelector, ToolSelectionResult


class TestToolCapabilities(unittest.TestCase):
    """Qobiliyatlarni indekslash, aniqlash va Smart Tool Selection testlari"""

    def setUp(self):
        self.registry = CapabilityRegistry()
        self.registry.register_tool(
            tool_name="calculator",
            capabilities=["calculation", "math", "arithmetic"],
            aliases=["hisobla", "calc"]
        )
        self.registry.register_tool(
            tool_name="weather_service",
            capabilities=["weather", "forecast", "climate"],
            aliases=["obhavo", "ob-havo"]
        )
        self.registry.register_tool(
            tool_name="web_searcher",
            capabilities=["web_search", "google_search", "lookup"],
            aliases=["qidiruv", "search"]
        )

    def test_capability_registration_and_lookup(self):
        """Qobiliyat bo'yicha asboblarni qidirish va topish"""
        tools = self.registry.find_by_capability("calculation")
        self.assertIn("calculator", tools)

        # Case insensitive
        tools_upper = self.registry.find_by_capability("CALCULATION")
        self.assertIn("calculator", tools_upper)

        # Nomining o'zi ham qobiliyat sifatida ro'yxatdan o'tadi
        name_tools = self.registry.find_by_capability("weather_service")
        self.assertIn("weather_service", name_tools)

    def test_alias_resolution(self):
        """Taxalluslar (aliases) orqali asosiy asbob nomini aniqlash"""
        self.assertEqual(self.registry.find_by_alias("hisobla"), "calculator")
        self.assertEqual(self.registry.find_by_alias("CALC"), "calculator")
        self.assertEqual(self.registry.find_by_alias("obhavo"), "weather_service")
        self.assertIsNone(self.registry.find_by_alias("unknown_alias"))

    def test_unregister_tool(self):
        """Asbob ro'yxatdan o'chirilganda indekslar to'liq tozalanishi"""
        self.registry.unregister_tool("calculator")
        self.assertEqual(self.registry.find_by_capability("calculation"), [])
        self.assertIsNone(self.registry.find_by_alias("hisobla"))

    def test_intent_to_capability_discovery_uzbek(self):
        """O'zbek tilidagi tabiiy matndan talab qilinayotgan qobiliyatni aniqlash"""
        query1 = "Iltimos 25 ni 4 ga ko'paytir va hisobla"
        discovered1 = dict(self.registry.discover_capabilities_for_text(query1))
        self.assertIn("calculation", discovered1)
        self.assertGreater(discovered1["calculation"], 0.0)

        query2 = "Ertaga Toshkentda ob-havo qanday bo'ladi?"
        discovered2 = dict(self.registry.discover_capabilities_for_text(query2))
        self.assertIn("weather", discovered2)

        query3 = "Internetdan yangiliklarni qidir"
        discovered3 = dict(self.registry.discover_capabilities_for_text(query3))
        self.assertIn("web_search", discovered3)

    def test_intent_to_capability_discovery_english(self):
        """Ingliz tilidagi so'rovlardan qobiliyatni aniqlash"""
        query = "Please calculate the total sum of numbers"
        discovered = dict(self.registry.discover_capabilities_for_text(query))
        self.assertIn("calculation", discovered)

        query_web = "Search for latest python documentation"
        discovered_web = dict(self.registry.discover_capabilities_for_text(query_web))
        self.assertIn("web_search", discovered_web)

    def test_smart_selector_prefers_healthy_tool(self):
        """SmartToolSelector salomat (AVAILABLE) asbobni nosoz (DEGRADED) asbobdan ustun qo'yishi"""
        tool_a = ToolContract2(
            name="primary_calc",
            description="Primary calculator",
            capabilities=["calculation"],
            function=lambda: None,
            parameters={},
            health=ToolHealth.DEGRADED,
        )
        tool_b = ToolContract2(
            name="backup_calc",
            description="Backup calculator",
            capabilities=["calculation"],
            function=lambda: None,
            parameters={},
            health=ToolHealth.AVAILABLE,
        )

        result = SmartToolSelector.select_best_tool(
            required_capability="calculation",
            candidate_tools=[tool_a, tool_b]
        )

        self.assertIsNotNone(result.tool)
        self.assertEqual(result.tool.name, "backup_calc")
        self.assertIn("backup_calc", result.explanation)
        self.assertIsNotNone(result.fallback_tool)
        self.assertEqual(result.fallback_tool.name, "tool_a" if result.fallback_tool.name == "tool_a" else "primary_calc")

    def test_smart_selector_rejects_disabled_and_unavailable(self):
        """DISABLED yoki UNAVAILABLE holatdagi asboblar tanlanmasligi (0.0 ball)"""
        disabled_tool = ToolContract2(
            name="disabled_tool",
            description="Disabled",
            capabilities=["data_export"],
            function=lambda: None,
            parameters={},
            health=ToolHealth.DISABLED,
        )
        unavailable_tool = ToolContract2(
            name="unavailable_tool",
            description="Unavailable",
            capabilities=["data_export"],
            function=lambda: None,
            parameters={},
            health=ToolHealth.UNAVAILABLE,
        )

        result = SmartToolSelector.select_best_tool(
            required_capability="data_export",
            candidate_tools=[disabled_tool, unavailable_tool]
        )

        self.assertIsNone(result.tool)
        self.assertEqual(result.score, 0.0)
        self.assertIn("yaroqsiz yoki o'chirilgan", result.explanation)

    def test_smart_selector_prefers_low_risk(self):
        """Risk darajasi past (LOW) bo'lgan vositani HIGH vositadan afzal ko'rish"""
        high_risk_tool = ToolContract2(
            name="cmd_calc",
            description="Runs shell math",
            capabilities=["calculation"],
            function=lambda: None,
            parameters={},
            risk_level=RiskLevel.HIGH,
        )
        low_risk_tool = ToolContract2(
            name="safe_calc",
            description="Pure python math",
            capabilities=["calculation"],
            function=lambda: None,
            parameters={},
            risk_level=RiskLevel.LOW,
        )

        result = SmartToolSelector.select_best_tool(
            required_capability="calculation",
            candidate_tools=[high_risk_tool, low_risk_tool],
            prefer_low_risk=True
        )

        self.assertIsNotNone(result.tool)
        self.assertEqual(result.tool.name, "safe_calc")

    def test_smart_selector_scoring_explanation_observability(self):
        """Selection natijasida to'liq tushuntirish va ballar taqsimoti qaytarilishi"""
        tool = ToolContract2(
            name="json_formatter",
            description="Formats JSON string",
            capabilities=["json_formatting"],
            parameters={"data": {"type": "string", "required": True}},
            function=lambda data: data,
        )

        result = SmartToolSelector.select_best_tool(
            required_capability="json_formatting",
            candidate_tools=[tool],
            candidate_params={"data": "{}"}
        )

        self.assertIsNotNone(result.tool)
        self.assertEqual(result.tool.name, "json_formatter")
        self.assertGreater(result.score, 0.5)
        self.assertTrue(len(result.explanation) > 0)
        self.assertIn("health", result.scoring_breakdown)
        self.assertIn("capability_match", result.scoring_breakdown)
        self.assertIn("parameters", result.scoring_breakdown)

        # to_dict serialization
        d = result.to_dict()
        self.assertEqual(d["selected_tool"], "json_formatter")
        self.assertIn("scoring_breakdown", d)


if __name__ == "__main__":
    unittest.main()
