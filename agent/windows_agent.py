# ========== agent/windows_agent.py ==========
# Phase 45 — Windows PC Agent Top-Level Coordinator & CLI
# Programmatic interface and command-line execution for Windows agent

import sys
import signal
import asyncio
import logging
import argparse
from typing import Optional

from agent.config import AgentConfig, load_config
from agent.lifecycle import AgentLifecycleManager
from agent.startup import WindowsStartupManager
from agent.audit import AgentAuditLogger

logger = logging.getLogger("mikasa.agent.main")


class WindowsAgent:
    """
    Mikasa Windows PC Agentining bosh koordinatori.
    Dasturiy va CLI interfeyslarini taqdim etadi.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or load_config()
        self.lifecycle = AgentLifecycleManager(self.config)
        self._audit = AgentAuditLogger.get_instance()

    async def run(self):
        """Asosiy siklni ishga tushirish va signal nazorati"""
        self._register_signals()
        await self.lifecycle.start()
        await self.lifecycle.run_forever()

    async def pair(self, pin: str) -> bool:
        """6 xonali PIN orqali qurilmani hisob bilan bog'lash"""
        ok, msg, _ = await self.lifecycle.enrollment.complete_pairing(pin)
        if ok:
            print(f"[SUCCESS] Qurilma muvaffaqiyatli ulandi: {msg}")
            logger.info(f"[WindowsAgent] Pairing muvaffaqiyatli: {msg}")
            return True
        else:
            print(f"[ERROR] Pairing xatosi: {msg}")
            logger.error(f"[WindowsAgent] Pairing xatosi: {msg}")
            return False

    def print_status(self):
        """Qurilma holati va identifikatorini chiqarish"""
        ident = self.lifecycle.identity
        print("=" * 60)
        print(" MIKASA WINDOWS AGENT — STATUS")
        print("=" * 60)
        print(f"Device ID:          {ident.device_id}")
        print(f"Device Name:        {ident.name}")
        print(f"Platform:           {ident.platform}")
        print(f"Agent Version:      {self.config.agent_version}")
        print(f"Backend URL:        {self.config.backend_url}")
        print(f"Hardware FP:        {ident.hardware_fingerprint[:16]}...")
        print(f"Vault Directory:    {self.config.vault_dir}")
        print(f"Autostart Enabled:  {WindowsStartupManager.is_startup_enabled()}")
        print(f"Agent State:        {self.lifecycle.heartbeat.state.value}")
        print("=" * 60)

    async def shutdown(self):
        """Toza to'xtatish"""
        await self.lifecycle.shutdown()

    def _register_signals(self):
        """SIGINT va SIGTERM signallarini ushlash"""
        loop = asyncio.get_event_loop()

        def _handle_signal():
            logger.info("[WindowsAgent] To'xtatish signali qabul qilindi, shutdown chaqirilmoqda...")
            asyncio.create_task(self.shutdown())

        if sys.platform != "win32":
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, _handle_signal)
        else:
            # Windows'da signal.signal ishlatiladi
            signal.signal(signal.SIGINT, lambda s, f: _handle_signal())
            signal.signal(signal.SIGTERM, lambda s, f: _handle_signal())


def main():
    """CLI buyruqlar satri kirish nuqtasi"""
    parser = argparse.ArgumentParser(
        description="Mikasa AI — Production Windows PC Agent (Phase 45)",
        prog="MikasaAgent"
    )
    subparsers = parser.add_subparsers(dest="command", help="Amallar")

    # 1. start
    subparsers.add_parser("start", help="Agentni ishga tushirish")

    # 2. pair <pin>
    pair_parser = subparsers.add_parser("pair", help="6 xonali PIN orqali agentni ulash")
    pair_parser.add_argument("pin", help="6 xonali raqamli PIN kod")

    # 3. status
    subparsers.add_parser("status", help="Agent holatini ko'rsatish")

    # 4. autostart
    autostart_parser = subparsers.add_parser("autostart", help="Windows avtomatik ishga tushishini boshqarish")
    autostart_parser.add_argument("action", choices=["enable", "disable", "status"], help="Amal")

    args = parser.parse_args()

    # Logging sozlamalari
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    agent = WindowsAgent()

    if args.command == "start" or args.command is None:
        try:
            asyncio.run(agent.run())
        except KeyboardInterrupt:
            logger.info("[WindowsAgent] Foydalanuvchi tomonidan to'xtatildi (KeyboardInterrupt)")

    elif args.command == "pair":
        try:
            asyncio.run(agent.pair(args.pin))
        except Exception as e:
            print(f"[ERROR] Pairing jarayonida kutilmagan xatolik: {e}")

    elif args.command == "status":
        agent.print_status()

    elif args.command == "autostart":
        if args.action == "enable":
            ok = WindowsStartupManager.enable_startup(sys.executable, "--start")
            print(f"Autostart enable: {'OK' if ok else 'FAILED'}")
        elif args.action == "disable":
            ok = WindowsStartupManager.disable_startup()
            print(f"Autostart disable: {'OK' if ok else 'FAILED'}")
        elif args.action == "status":
            enabled = WindowsStartupManager.is_startup_enabled()
            print(f"Autostart enabled: {enabled}")


if __name__ == "__main__":
    main()
