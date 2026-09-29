# ========== core/v8/telegram_webhook.py ==========
# Phase 46 — Production Telegram Webhook Gateway
# HTTPS webhook ingestion, secret validation, idempotent update processing,
# webhook registration lifecycle, and optional long-polling for local development.

import os
import re
import hmac
import json
import time
import asyncio
import logging
import signal
from typing import Any, Dict, Optional, Set, Tuple

from aiohttp import web

from core.v8.events import sanitize_sensitive_string
from core.v8.telegram_gateway import AiohttpTelegramTransport, TelegramTransport
from core.v8.universal_bot import UniversalTelegramBot

logger = logging.getLogger("core.v8.telegram_webhook")

MAX_WEBHOOK_BODY_BYTES = 256 * 1024
UPDATE_ID_TTL_SECONDS = 86400.0
UPDATE_ID_MAX_ENTRIES = 10000
SHUTDOWN_TIMEOUT_SECONDS = 8.0
TELEGRAM_API_BASE = "https://api.telegram.org/bot"


class UpdateIdempotencyStore:
    """In-memory deduplication of Telegram update_id values."""

    def __init__(self, ttl: float = UPDATE_ID_TTL_SECONDS, max_entries: int = UPDATE_ID_MAX_ENTRIES):
        self.ttl = ttl
        self.max_entries = max_entries
        self._seen: Dict[int, float] = {}
        self._last_prune: float = 0.0

    def _prune(self, now: float) -> None:
        self._last_prune = now
        cutoff = now - self.ttl
        expired = [uid for uid, ts in self._seen.items() if ts < cutoff]
        for uid in expired:
            self._seen.pop(uid, None)
        if len(self._seen) > self.max_entries:
            sorted_items = sorted(self._seen.items(), key=lambda item: item[1])
            for uid, _ in sorted_items[: len(self._seen) - self.max_entries]:
                self._seen.pop(uid, None)

    def claim(self, update_id: Any) -> bool:
        """Return True if this update_id is new and should be processed."""
        try:
            uid = int(update_id)
        except (TypeError, ValueError):
            return True
        now = time.time()
        if (now - self._last_prune >= 60.0) or (len(self._seen) >= self.max_entries):
            self._prune(now)
        existing_ts = self._seen.get(uid)
        if existing_ts is not None:
            if (now - existing_ts) < self.ttl:
                return False
            self._seen.pop(uid, None)
        self._seen[uid] = now
        if len(self._seen) > self.max_entries:
            self._prune(now)
        return True

    def unclaim(self, update_id: Any) -> None:
        """Release update_id if processing failed unexpectedly before completion."""
        try:
            uid = int(update_id)
            self._seen.pop(uid, None)
        except (TypeError, ValueError):
            pass


class TelegramWebhookService:
    """
    Production webhook handler for UniversalTelegramBot.
    Validates secrets, isolates failures, and never logs sensitive values.
    """

    def __init__(
        self,
        bot: UniversalTelegramBot,
        transport: TelegramTransport,
        webhook_secret: str,
        bot_token: str = "",
        idempotency: Optional[UpdateIdempotencyStore] = None,
    ):
        if not webhook_secret or not str(webhook_secret).strip():
            raise ValueError("TELEGRAM_WEBHOOK_SECRET is required for webhook mode")
        self.bot = bot
        self.transport = transport
        self.webhook_secret = str(webhook_secret).strip()
        self.bot_token = bot_token or ""
        self.idempotency = idempotency or UpdateIdempotencyStore()
        self._accepting_updates = True
        self._active_handlers: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()

    @property
    def accepting_updates(self) -> bool:
        return self._accepting_updates

    def webhook_path(self) -> str:
        return f"/telegram/webhook/{self.webhook_secret}"

    def _header_secret_token(self) -> str:
        """Telegram X-Telegram-Bot-Api-Secret-Token header allows only [A-Za-z0-9_-] (1..256 chars)."""
        cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", self.webhook_secret)
        return cleaned[:256]

    def _validate_secret(self, request: web.Request) -> bool:
        path_secret = request.match_info.get("secret", "")
        if not path_secret and request.path.startswith("/telegram/webhook/"):
            path_secret = request.path[len("/telegram/webhook/"):].split("/")[0]
        if not path_secret or not hmac.compare_digest(path_secret, self.webhook_secret):
            return False
        header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header_secret:
            expected_header = self._header_secret_token()
            if not (
                hmac.compare_digest(header_secret, self.webhook_secret)
                or (expected_header and hmac.compare_digest(header_secret, expected_header))
            ):
                return False
        return True

    @staticmethod
    def _classify_update(update: Dict[str, Any]) -> Tuple[str, Any, Any, str]:
        """Extract non-sensitive metadata (update_type, chat_id, tg_user_id, action_kind)."""
        if "callback_query" in update and isinstance(update["callback_query"], dict):
            cq = update["callback_query"]
            from_u = cq.get("from", {}) if isinstance(cq.get("from"), dict) else {}
            msg = cq.get("message", {}) if isinstance(cq.get("message"), dict) else {}
            chat = msg.get("chat", {}) if isinstance(msg.get("chat"), dict) else {}
            return "callback_query", chat.get("id"), from_u.get("id"), "callback"

        update_type = "edited_message" if "edited_message" in update else ("message" if "message" in update else "other")
        msg = update.get("message") or update.get("edited_message")
        if not isinstance(msg, dict):
            return update_type, None, None, "non_message"

        chat = msg.get("chat", {}) if isinstance(msg.get("chat"), dict) else {}
        from_u = msg.get("from", {}) if isinstance(msg.get("from"), dict) else {}
        chat_id = chat.get("id")
        tg_user_id = from_u.get("id") or chat_id
        raw_text = str(msg.get("text", "")).strip()

        if not raw_text:
            return update_type, chat_id, tg_user_id, "empty_or_media"
        if raw_text.startswith("/"):
            cmd_head = raw_text.split()[0].split("@")[0].lower()
            has_arg = len(raw_text.split()) > 1
            return update_type, chat_id, tg_user_id, f"{cmd_head}_with_arg" if has_arg else cmd_head
        if UniversalTelegramBot.OTP_REGEX.match(raw_text):
            return update_type, chat_id, tg_user_id, "otp_code_input"
        return update_type, chat_id, tg_user_id, "plain_text"

    async def handle_webhook(self, request: web.Request) -> web.Response:
        if not self._accepting_updates:
            return web.Response(status=503, text="Service shutting down")

        if not self._validate_secret(request):
            logger.warning(
                "[TelegramWebhook] Rejected request: invalid webhook secret "
                f"( correlation={id(request)} )"
            )
            return web.Response(status=403, text="Forbidden")

        if request.content_type not in ("application/json", "application/json; charset=utf-8", None):
            return web.Response(status=415, text="Unsupported Media Type")

        raw = await request.read()
        if len(raw) > MAX_WEBHOOK_BODY_BYTES:
            logger.warning("[TelegramWebhook] Rejected oversized payload")
            return web.Response(status=413, text="Payload Too Large")

        try:
            update = json.loads(raw.decode("utf-8"))
        except Exception:
            return web.Response(status=400, text="Invalid JSON")

        if not isinstance(update, dict):
            return web.Response(status=400, text="Malformed update")

        update_id = update.get("update_id")
        if update_id is not None and not self.idempotency.claim(update_id):
            logger.info(f"[TelegramWebhook] Duplicate update ignored: update_id={update_id}")
            return web.Response(status=200, text="OK")

        update_type, chat_id, tg_user_id, action_kind = self._classify_update(update)
        logger.info(
            f"[TelegramWebhook] Incoming update: update_id={update_id}, "
            f"type={update_type}, chat_id={chat_id}, tg_user_id={tg_user_id}, action={action_kind}"
        )

        task = asyncio.create_task(self._process_update_safe(update, update_id))
        self._active_handlers.add(task)
        task.add_done_callback(self._active_handlers.discard)
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=25.0)
        except asyncio.TimeoutError:
            logger.warning(f"[TelegramWebhook] Update processing still running after 25s (update_id={update_id})")
        return web.Response(status=200, text="OK")

    async def _process_update_safe(self, update: Dict[str, Any], update_id: Any) -> None:
        try:
            result = await self.bot.process_update(update)
            if isinstance(result, dict):
                if result.get("ok"):
                    logger.info(f"[TelegramWebhook] Update processed & reply sent (update_id={update_id})")
                else:
                    safe_desc = sanitize_sensitive_string(str(result.get("description", "")))
                    logger.error(
                        f"[TelegramWebhook] Bot reply failed "
                        f"(update_id={update_id}, error_code={result.get('error_code')}, description={safe_desc})"
                    )
            else:
                logger.info(f"[TelegramWebhook] Update processed with no reply required (update_id={update_id})")
        except Exception as exc:
            if update_id is not None:
                self.idempotency.unclaim(update_id)
            logger.exception(
                "[TelegramWebhook] Update processing failed "
                f"(update_id={update_id}, error={type(exc).__name__})"
            )

    async def begin_shutdown(self) -> None:
        self._accepting_updates = False
        self._shutdown_event.set()
        if self._active_handlers:
            logger.info(
                f"[TelegramWebhook] Waiting for {len(self._active_handlers)} active handler(s)..."
            )
            try:
                await asyncio.wait_for(
                    asyncio.gather(*list(self._active_handlers), return_exceptions=True),
                    timeout=SHUTDOWN_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.warning("[TelegramWebhook] Shutdown timeout — cancelling pending handlers")
                for task in list(self._active_handlers):
                    task.cancel()

        if isinstance(self.transport, AiohttpTelegramTransport):
            await self.transport.close()

    async def register_webhook(self, public_base_url: str) -> Tuple[bool, str]:
        """
        Idempotent Telegram setWebhook registration.
        public_base_url: e.g. https://your-service.up.railway.app (no trailing slash)
        """
        if not self.bot_token:
            return False, "TELEGRAM_BOT_TOKEN not configured"

        base = public_base_url.strip().rstrip("/")
        if "/telegram/webhook" in base:
            base = base.split("/telegram/webhook")[0].rstrip("/")
        webhook_url = f"{base}{self.webhook_path()}"
        safe_webhook_url = f"{base}/telegram/webhook/[REDACTED]"

        import aiohttp

        header_secret = self._header_secret_token()
        payload: Dict[str, Any] = {
            "url": webhook_url,
            "allowed_updates": ["message", "edited_message", "callback_query"],
            "drop_pending_updates": False,
        }
        if header_secret:
            payload["secret_token"] = header_secret

        api_url = f"{TELEGRAM_API_BASE}{self.bot_token}/setWebhook"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    data = await resp.json()
                    if data.get("ok"):
                        logger.info(
                            "[TelegramWebhook] Webhook registered "
                            f"(url={safe_webhook_url}, token={sanitize_sensitive_string(self.bot_token)})"
                        )
                        return True, "registered"
                    desc = str(data.get("description", "unknown error"))
                    if "secret_token" in desc.lower() and "secret_token" in payload:
                        payload.pop("secret_token", None)
                        async with session.post(api_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as retry_resp:
                            retry_data = await retry_resp.json()
                            if retry_data.get("ok"):
                                logger.info(
                                    "[TelegramWebhook] Webhook registered (path-secret mode) "
                                    f"(url={safe_webhook_url}, token={sanitize_sensitive_string(self.bot_token)})"
                                )
                                return True, "registered"
                    logger.error(f"[TelegramWebhook] setWebhook failed: {sanitize_sensitive_string(desc)}")
                    return False, desc
        except Exception as exc:
            logger.error(f"[TelegramWebhook] setWebhook network error: {type(exc).__name__}")
            return False, str(type(exc).__name__)

    async def verify_webhook_info(self) -> Dict[str, Any]:
        if not self.bot_token:
            return {"ok": False, "configured": False}

        import aiohttp

        api_url = f"{TELEGRAM_API_BASE}{self.bot_token}/getWebhookInfo"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = await resp.json()
                    return data.get("result", {}) if data.get("ok") else {"ok": False}
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__}


class TelegramPollingRunner:
    """Long-polling transport for local development (TELEGRAM_USE_WEBHOOK=false)."""

    def __init__(self, bot: UniversalTelegramBot, transport: AiohttpTelegramTransport):
        self.bot = bot
        self.transport = transport
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._offset: Optional[int] = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("[TelegramPolling] Started long-polling mode")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self.transport.close()
        logger.info("[TelegramPolling] Stopped")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                updates = await self.transport.get_updates(offset=self._offset, timeout=25)
                for update in updates:
                    uid = update.get("update_id")
                    if uid is not None:
                        self._offset = int(uid) + 1
                    await self.bot.process_update(update)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(f"[TelegramPolling] Poll error: {type(exc).__name__}")
                await asyncio.sleep(2.0)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "")
    if raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def build_telegram_webhook_service() -> Optional[TelegramWebhookService]:
    """Factory: returns None when Telegram bot is not configured."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        return None

    webhook_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    bot_username = os.environ.get("TELEGRAM_BOT_USERNAME", "Mikasa_ai_agent_bot").strip() or "Mikasa_ai_agent_bot"

    transport = AiohttpTelegramTransport(bot_token)
    bot = UniversalTelegramBot(
        transport=transport,
        bot_username=bot_username,
    )

    if _env_bool("TELEGRAM_USE_WEBHOOK", default=True):
        if not webhook_secret:
            logger.error("[TelegramWebhook] TELEGRAM_WEBHOOK_SECRET required when TELEGRAM_USE_WEBHOOK=true")
            return None
        return TelegramWebhookService(
            bot=bot,
            transport=transport,
            webhook_secret=webhook_secret,
            bot_token=bot_token,
        )
    return None


def register_telegram_routes(app: web.Application, webhook_service: Optional[TelegramWebhookService]) -> None:
    """Attach webhook and readiness routes to an aiohttp application."""
    app["telegram_webhook_service"] = webhook_service

    if webhook_service:
        route_pattern = "/telegram/webhook/{secret}"
        app.router.add_post(route_pattern, webhook_service.handle_webhook)
        app.router.add_post("/telegram/webhook", webhook_service.handle_webhook)
        logger.info(f"[TelegramWebhook] Route registered: POST {route_pattern}")

    async def handle_ready(request: web.Request) -> web.Response:
        import sys
        svc = app.get("telegram_webhook_service")
        use_webhook = _env_bool("TELEGRAM_USE_WEBHOOK", default=True)
        bot_configured = bool(os.environ.get("TELEGRAM_BOT_TOKEN", "").strip())
        backend_url = os.environ.get("MIKASA_BACKEND_URL", "").strip() or os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()

        checks: Dict[str, Any] = {
            "telegram_bot": "configured" if bot_configured else "missing",
            "webhook_mode": "enabled" if use_webhook else "polling",
            "webhook_service": "ready" if svc else ("not_required" if not use_webhook else "not_ready"),
            "platform": sys.platform,
        }

        if backend_url:
            checks["backend_url"] = "configured"

        reg_state = app.get("telegram_webhook_registration")
        if isinstance(reg_state, dict):
            checks["webhook_registration"] = {
                "ok": bool(reg_state.get("ok")),
                "message": sanitize_sensitive_string(str(reg_state.get("message", ""))),
            }

        wh_info = app.get("telegram_webhook_info")
        if isinstance(wh_info, dict) and wh_info:
            checks["webhook_info"] = {
                "pending_update_count": wh_info.get("pending_update_count", 0),
                "last_error_message": sanitize_sensitive_string(str(wh_info.get("last_error_message", ""))),
                "has_custom_certificate": bool(wh_info.get("has_custom_certificate", False)),
            }

        supabase_url = os.environ.get("SUPABASE_URL", "")
        supabase_key = (
            os.environ.get("SUPABASE_PUBLISHABLE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or ""
        )
        supabase_secret = (
            os.environ.get("SUPABASE_SECRET_KEY")
            or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or ""
        )
        checks["supabase"] = (
            "configured"
            if supabase_url and supabase_key and "placeholder" not in supabase_url
            else "not_configured"
        )
        checks["supabase_service_role"] = (
            "configured"
            if supabase_secret and "placeholder" not in supabase_secret
            else "not_configured"
        )

        ready = (not bot_configured) or (svc is not None) or (not use_webhook)
        return web.json_response(
            {"status": "ready" if ready else "not_ready", "checks": checks},
            status=200 if ready else 503,
        )

    app.router.add_get("/ready", handle_ready)
    app.router.add_get("/api/ready", handle_ready)


async def setup_telegram_lifecycle(app: web.Application) -> None:
    """Startup: register webhook. Shutdown: graceful stop."""
    svc: Optional[TelegramWebhookService] = app.get("telegram_webhook_service")
    polling: Optional[TelegramPollingRunner] = None

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    use_webhook = _env_bool("TELEGRAM_USE_WEBHOOK", default=True)

    if bot_token and not use_webhook:
        transport = AiohttpTelegramTransport(bot_token)
        bot = UniversalTelegramBot(
            transport=transport,
            bot_username=os.environ.get("TELEGRAM_BOT_USERNAME", "Mikasa_ai_agent_bot").strip() or "Mikasa_ai_agent_bot",
        )
        polling = TelegramPollingRunner(bot, transport)
        app["telegram_polling_runner"] = polling
        await polling.start()

    if svc and use_webhook:
        public_url = (
            os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
            or os.environ.get("MIKASA_PUBLIC_URL", "").strip()
            or os.environ.get("MIKASA_BACKEND_URL", "").strip()
            or os.environ.get("TELEGRAM_WEBHOOK_URL", "").strip()
        )
        if public_url and not public_url.startswith("http"):
            public_url = f"https://{public_url}"
        if public_url:
            ok, msg = await svc.register_webhook(public_url)
            app["telegram_webhook_registration"] = {"ok": ok, "message": msg}
            if ok:
                info = await svc.verify_webhook_info()
                app["telegram_webhook_info"] = info
        else:
            logger.warning(
                "[TelegramWebhook] RAILWAY_PUBLIC_DOMAIN / MIKASA_PUBLIC_URL not set — "
                "skipping automatic setWebhook (register manually after deploy)"
            )


async def cleanup_telegram_lifecycle(app: web.Application) -> None:
    polling: Optional[TelegramPollingRunner] = app.get("telegram_polling_runner")
    if polling:
        await polling.stop()
    svc: Optional[TelegramWebhookService] = app.get("telegram_webhook_service")
    if svc:
        await svc.begin_shutdown()


def install_signal_handlers(loop: asyncio.AbstractEventLoop, runner: web.AppRunner) -> None:
    """SIGTERM/SIGINT graceful shutdown for Railway deploys."""

    async def _shutdown():
        logger.info("[Production] Graceful shutdown initiated")
        await cleanup_telegram_lifecycle(runner.app)
        await runner.cleanup()
        loop.stop()

    def _signal_handler():
        asyncio.ensure_future(_shutdown())

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows dev environments may not support add_signal_handler
            signal.signal(sig, lambda s, f: _signal_handler())
