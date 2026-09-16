# ========== test_security_api.py ==========
# Phase 20 — Security & Hardening Tests (CORS, IP Filter, Path Traversal)

import os
import sys
import json
import asyncio
import unittest
from aiohttp import web

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.api_server import cors_middleware, create_app
from core.agent_plugins import get_plugin_manager


class MockRequest:
    def __init__(self, method="GET", origin=None, remote="127.0.0.1"):
        self.method = method
        self.headers = {}
        if origin:
            self.headers["Origin"] = origin
        self.remote = remote


class TestSecurityAPI(unittest.TestCase):
    """Xavfsizlik va himoya tizimi testlari"""

    def setUp(self):
        self.pm = get_plugin_manager()

    def test_cors_allowed_origins(self):
        """Tauri va localhost originlari ruxsat etiladi"""
        async def dummy_handler(request):
            return web.Response(text="OK")

        async def _run():
            for origin in ["tauri://localhost", "http://localhost:1420", "http://127.0.0.1:18420", "https://tauri.localhost"]:
                req = MockRequest(method="GET", origin=origin, remote="127.0.0.1")
                resp = await cors_middleware(req, dummy_handler)
                self.assertEqual(resp.status, 200, f"Origin {origin} ruxsat etilmadi")
                self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), origin)

        asyncio.run(_run())

    def test_cors_rejected_foreign_origins(self):
        """Begona tashqi domenlar (CORS attack) 403 bilan to'xtatiladi"""
        async def dummy_handler(request):
            return web.Response(text="OK")

        async def _run():
            for bad_origin in ["http://evil.com", "https://attacker.site", "http://malicious.org:8080"]:
                req = MockRequest(method="GET", origin=bad_origin, remote="127.0.0.1")
                resp = await cors_middleware(req, dummy_handler)
                self.assertEqual(resp.status, 403, f"Begona origin {bad_origin} rad etilmadi")

        asyncio.run(_run())

    def test_remote_ip_blocking(self):
        """Begona lokal tarmoq yoki tashqi IP manzildan kelgan so'rovlar bloklanadi"""
        async def dummy_handler(request):
            return web.Response(text="OK")

        async def _run():
            for bad_ip in ["192.168.1.105", "10.0.0.5", "172.16.0.10"]:
                req = MockRequest(method="GET", origin=None, remote=bad_ip)
                resp = await cors_middleware(req, dummy_handler)
                self.assertEqual(resp.status, 403, f"Begona IP {bad_ip} bloklanmadi")

        asyncio.run(_run())

    def test_plugin_path_traversal_prevention(self):
        """Plagin nomi orqali katalogdan chiqish (Path Traversal) qat'iy to'xtatiladi"""
        malicious_names = [
            "../../etc/passwd",
            "..\\..\\Windows\\System32",
            "test/../../../secret",
            "plugin/subfolder",
            "evil;rm -rf /",
        ]

        for bad_name in malicious_names:
            # Install urinishi
            result_install = self.pm.install(bad_name, custom_data={"name": bad_name})
            # Path traversal hech qachon plugins_dir dan tashqarida fayl ochmasligi kerak
            target = os.path.realpath(os.path.join(self.pm.plugins_dir, f"{bad_name}.json"))
            self.assertFalse(
                os.path.exists(target) and not target.startswith(os.path.realpath(self.pm.plugins_dir)),
                f"Path traversal amalga oshdi: {bad_name}"
            )
            # Uninstall urinishi
            result_uninstall = self.pm.uninstall(bad_name)
            self.assertFalse(result_uninstall, f"Xavfli nom bilan uninstall amalga oshdi: {bad_name}")


if __name__ == "__main__":
    unittest.main()
