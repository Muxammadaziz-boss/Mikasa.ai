# Phase 46 — Universal Telegram Bot Railway Production Deployment

## 1. Architecture

```
Telegram User
      ↓ HTTPS
Telegram Bot API (webhook)
      ↓ POST /telegram/webhook/{TELEGRAM_WEBHOOK_SECRET}
Railway — Mikasa Production Server (core.production_server)
      ├── Universal Telegram Gateway (core/v8/telegram_webhook.py)
      ├── UniversalTelegramBot (core/v8/universal_bot.py)
      └── Mikasa Backend API (core/api_server.py)
              ↓
          Supabase Auth / PostgreSQL / RLS
              ↓
          Windows Agent (user PC, HTTPS to MIKASA_BACKEND_URL)
```

Single Railway service runs Backend API + Telegram Gateway in one process so identity/device state stays consistent (JSON persistence under `data/`).

## 2. Railway Setup

1. Create a Railway project linked to GitHub branch `dev-v8.0.0`.
2. Set builder to Dockerfile (`railway.toml` included) or Nixpacks with start command:
   ```bash
   python -m core.production_server
   ```
3. Configure health check path: `/health`
4. Readiness probe: `/ready`

## 3. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | BotFather token |
| `TELEGRAM_BOT_USERNAME` | Yes | Bot username without `@` |
| `TELEGRAM_WEBHOOK_SECRET` | Yes (prod) | Random secret; never commit |
| `TELEGRAM_USE_WEBHOOK` | No | `true` production, `false` local polling |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_PUBLISHABLE_KEY` | Yes | Publishable/anon key |
| `SUPABASE_SECRET_KEY` | Yes | Server-side secret only |
| `MIKASA_BACKEND_URL` | Recommended | Public backend URL for agents |
| `RAILWAY_PUBLIC_DOMAIN` | Auto | Set by Railway for webhook registration |
| `PORT` | Auto | Set by Railway |
| `ENVIRONMENT` | Yes | `production` |
| `MIKASA_API_HOST` | No | Default `0.0.0.0` in Docker |

See `.env.example` for placeholders only — never store real secrets in Git.

## 4. Telegram Webhook

- Endpoint: `POST /telegram/webhook/{TELEGRAM_WEBHOOK_SECRET}`
- Header validation: `X-Telegram-Bot-Api-Secret-Token` (set via `setWebhook`)
- Duplicate protection: `update_id` idempotency store
- Max payload: 256 KB
- Auto-registration on startup when `RAILWAY_PUBLIC_DOMAIN` or `MIKASA_PUBLIC_URL` is set

Manual registration after deploy:

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://YOUR_DOMAIN/telegram/webhook/YOUR_SECRET","secret_token":"YOUR_SECRET","allowed_updates":["message","edited_message","callback_query"]}'
```

Verify:

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

## 5. Supabase Configuration

- Backend uses `SUPABASE_SECRET_KEY` server-side only.
- Telegram bot never receives or logs Supabase secrets.
- RLS policies from Phase 41+ migrations remain authoritative for Postgres-backed flows.

## 6. Local Development

```bash
# Polling mode (no HTTPS webhook required)
TELEGRAM_USE_WEBHOOK=false
TELEGRAM_BOT_TOKEN=your-token
python -m core.production_server
```

Production secrets must not be used as local fallbacks.

## 7. Production Deployment Checklist

1. Push `dev-v8.0.0` branch
2. Set all environment variables in Railway
3. Deploy and confirm `GET /health` → `{"status":"ok"}`
4. Confirm `GET /ready` → `status: ready`
5. Check logs for webhook registration success
6. Send `/start` to bot in Telegram
7. Complete OTP linking from Mikasa App
8. Verify `/devices`, `/select`, `/status`, `/session`, `/logout`

## 8. Health Checks

| Path | Purpose |
|------|---------|
| `GET /health` | Liveness — always `{"status":"ok"}` |
| `GET /ready` | Readiness — bot + Supabase config |
| `GET /api/health` | Extended diagnostics (no secrets) |

## 9. Logs

Format: `timestamp [LEVEL] component: message`

Never logged: tokens, OTP, webhook secret, Supabase secret, session tokens, passwords.

## 10. Security

- Multi-tenant isolation: every command resolves `telegram_user_id → UserTelegramLink → MikasaUser → Device`
- No global user state
- IDOR protection via user-scoped managers
- Webhook secret in URL path + Telegram secret header
- Graceful shutdown on SIGTERM (30s handler timeout)

## 11. Troubleshooting

| Issue | Action |
|-------|--------|
| 403 on webhook | Verify `TELEGRAM_WEBHOOK_SECRET` matches URL and header |
| Webhook not registered | Set `RAILWAY_PUBLIC_DOMAIN` or register manually |
| Bot silent | Check `TELEGRAM_BOT_TOKEN`, Railway logs |
| Linking fails | Verify backend reachable; check OTP rate limits |
| Data lost on restart | Attach Railway volume or migrate to Supabase-backed storage |

## 12. Rollback

1. Railway → Deployments → select previous successful deploy → Redeploy
2. Re-run `getWebhookInfo` to confirm URL
3. If needed, `deleteWebhook` then `setWebhook` to previous URL

## 13. Webhook Recovery

```bash
# Delete broken webhook
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"

# Re-register
curl "https://api.telegram.org/bot<TOKEN>/setWebhook" -d '{"url":"..."}'
```

After recovery, send a test `/start` and confirm 200 responses in Railway logs.
