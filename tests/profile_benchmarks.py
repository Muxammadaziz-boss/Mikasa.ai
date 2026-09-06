"""
Profiling script for Mikasa AI UI performance baseline.
Measures:
1. Startup page initialization time.
2. Navigation transition time between pages.
3. Tool catalog initial build and search time.
4. Widget creation count.
"""

import time
import customtkinter as ctk
from gui.theme import Colors, Fonts, Sizing
from gui.app import MikasaApp
from gui.pages.dashboard import DashboardPage
from gui.pages.voice import VoicePage
from gui.pages.chat import ChatPage
from gui.pages.commands import CommandsPage
from gui.pages.memory import MemoryPage
from gui.pages.scheduler import SchedulerPage
from gui.pages.plugins import PluginsPage
from gui.pages.settings import SettingsPage


def profile_baseline():
    root = ctk.CTk()
    root.withdraw()

    print("=== 1. INDIVIDUAL PAGE INSTANTIATION TIME ===")
    page_classes = {
        "dashboard": DashboardPage,
        "voice": VoicePage,
        "chat": ChatPage,
        "commands": CommandsPage,
        "memory": MemoryPage,
        "scheduler": SchedulerPage,
        "plugins": PluginsPage,
        "settings": SettingsPage,
    }

    instantiation_times = {}
    instantiated_pages = {}
    total_widgets = 0

    for name, cls in page_classes.items():
        t0 = time.perf_counter()
        p = cls(root)
        dt = (time.perf_counter() - t0) * 1000
        instantiation_times[name] = dt
        instantiated_pages[name] = p
        count = len(p.winfo_children())
        total_widgets += count
        print(f"Page '{name:12}': {dt:6.2f} ms | direct children: {count}")

    print(f"Total startup instantiation: {sum(instantiation_times.values()):.2f} ms\n")

    print("=== 2. ON_SHOW EXECUTION TIME ===")
    on_show_times = {}
    for name, p in instantiated_pages.items():
        if hasattr(p, "on_show"):
            t0 = time.perf_counter()
            p.on_show()
            dt = (time.perf_counter() - t0) * 1000
            on_show_times[name] = dt
            print(f"on_show '{name:12}': {dt:6.2f} ms")
        else:
            print(f"on_show '{name:12}':   None")

    print("\n=== 3. COMMANDS PAGE SEARCH & RENDERING BENCHMARK ===")
    cmd_page = instantiated_pages["commands"]
    t0 = time.perf_counter()
    cmd_page._build_tools_grid()
    dt_grid = (time.perf_counter() - t0) * 1000
    print(f"Full _build_tools_grid (29 tools): {dt_grid:.2f} ms")

    # Simulate search typing without debounce
    keystrokes = ["s", "sy", "sys", "syst", "syste", "system"]
    search_times = []
    for ks in keystrokes:
        cmd_page.search.entry.delete(0, "end")
        cmd_page.search.entry.insert(0, ks)
        t0 = time.perf_counter()
        cmd_page._on_search()
        dt = (time.perf_counter() - t0) * 1000
        search_times.append(dt)
        print(f"Search '{ks:6}': {dt:6.2f} ms")

    print(f"Total simulated typing lag: {sum(search_times):.2f} ms\n")

    # Cleanup
    for p in instantiated_pages.values():
        p.destroy()
    root.destroy()


if __name__ == "__main__":
    profile_baseline()
