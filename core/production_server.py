# ========== core/production_server.py ==========
# Railway / production entrypoint — Mikasa Backend API + Universal Telegram Gateway
# Binds 0.0.0.0:$PORT per platform requirements.

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("MIKASA_API_HOST", "0.0.0.0")
os.environ.setdefault("MIKASA_ALLOW_REMOTE_API", "true")

from core.api_server import run_server  # noqa: E402


if __name__ == "__main__":
    host = os.environ.get("MIKASA_API_HOST", "0.0.0.0")
    port_raw = os.environ.get("PORT") or os.environ.get("MIKASA_API_PORT", "18420")
    try:
        port = int(port_raw)
    except ValueError:
        port = 18420
    run_server(host=host, port=port)
