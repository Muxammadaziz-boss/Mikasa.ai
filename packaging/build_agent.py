# ========== packaging/build_agent.py ==========
# Phase 45 — Windows Agent Build Automation Script
# Builds MikasaAgent.exe standalone binary with strict security checks

import os
import sys
import shutil
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_agent")

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SPEC_FILE = os.path.join(BASE_DIR, "packaging", "agent.spec")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")


def pre_build_checks() -> bool:
    """Pre-build security and integrity checks"""
    logger.info("[Pre-Build] Checking source integrity...")
    agent_dir = os.path.join(BASE_DIR, "agent")
    if not os.path.exists(agent_dir):
        logger.error(f"[Pre-Build] agent directory missing: {agent_dir}")
        return False

    required_files = [
        "__init__.py", "config.py", "identity.py", "crypto.py",
        "audit.py", "recovery.py", "transport.py", "enrollment.py",
        "auth.py", "heartbeat.py", "startup.py", "lifecycle.py",
        "windows_agent.py"
    ]
    for rf in required_files:
        p = os.path.join(agent_dir, rf)
        if not os.path.exists(p):
            logger.error(f"[Pre-Build] Missing agent module: {rf}")
            return False

    # Check for hardcoded secrets
    sensitive_keywords = ["eyJh", "service_role", "sk-", "AIzaSy", "ghp_"]
    for root, _, files in os.walk(agent_dir):
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    for kw in sensitive_keywords:
                        if kw in content:
                            logger.error(f"[Pre-Build] Potential hardcoded secret ({kw}) found in {f}")
                            return False

    logger.info("[Pre-Build] Checks passed! Zero hardcoded secrets detected.")
    return True


def clean_artifacts():
    """Old build artifacts cleanup"""
    for d in (DIST_DIR, BUILD_DIR):
        if os.path.exists(d):
            logger.info(f"[Clean] Removing {d}")
            shutil.rmtree(d, ignore_errors=True)


def build_binary() -> bool:
    """Run PyInstaller build"""
    logger.info("[Build] Starting PyInstaller compilation...")
    try:
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            SPEC_FILE
        ]
        result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"[Build] PyInstaller failed with exit code {result.returncode}")
            logger.error(result.stderr)
            return False
        logger.info("[Build] PyInstaller compilation completed successfully!")
        return True
    except FileNotFoundError:
        logger.error("[Build] Python/PyInstaller not found in path")
        return False
    except Exception as e:
        logger.error(f"[Build] Build exception: {e}")
        return False


def post_build_verify() -> bool:
    """Post-build executable verification"""
    exe_path = os.path.join(DIST_DIR, "MikasaAgent.exe")
    if sys.platform != "win32":
        exe_path = os.path.join(DIST_DIR, "MikasaAgent")

    if not os.path.exists(exe_path):
        logger.error(f"[Post-Build] Executable not found at {exe_path}")
        return False

    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    logger.info(f"[Post-Build] Binary verified: {exe_path} ({size_mb:.2f} MB)")
    return True


def main():
    if not pre_build_checks():
        sys.exit(1)

    clean_artifacts()

    # Agar PyInstaller mavjud bo'lsa build qiladi
    try:
        import PyInstaller  # noqa: F401
        has_pyinstaller = True
    except ImportError:
        has_pyinstaller = False

    if not has_pyinstaller:
        logger.warning(
            "[Build] PyInstaller o'rnatilmagan. Standalone binary yaratish uchun: "
            "pip install pyinstaller && python packaging/build_agent.py"
        )
        sys.exit(0)

    success = build_binary()
    if not success:
        sys.exit(1)

    if not post_build_verify():
        sys.exit(1)

    logger.info("[SUCCESS] MikasaAgent binar fayli tayyor!")


if __name__ == "__main__":
    main()
