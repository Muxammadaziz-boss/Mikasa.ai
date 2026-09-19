# Mikasa AI v8.0.0 — Supabase Auth Setup & Architecture Guide

## 1. Overview
Mikasa AI v8.0.0 uses **Supabase Auth** as the primary Identity Provider (IdP) for client registration, login, session persistence, and multi-tenant isolation.
- **Client**: Connects directly to Supabase via `@supabase/supabase-js`. Passwords are never sent to, received by, or stored in the Python backend.
- **Backend**: Verifies incoming requests via RFC 7519 compliant Supabase JWT Bearer tokens using asymmetric JWKS public keys (`ES256` ECDSA with DER conversion, `RS256` RSA) or configured symmetric secret (`HS256`).
- **Authorization**: Enforces strict multi-tenant isolation via `JWT.sub`. Any cross-tenant parameter or header tampering returns `403 Forbidden`.
- **PostgreSQL Database**: Enforces Row Level Security (RLS) on all user-owned tables via PostgreSQL `auth.uid()`.

---

## 2. Environment Variables Configuration

### Frontend (`mikasa-7/.env`)
> [!IMPORTANT]
> Never store `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY` in frontend `.env` files or bundles. Only `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` (or `VITE_SUPABASE_ANON_KEY`) are allowed.

```env
# Supabase Project URL
VITE_SUPABASE_URL=https://your-project-id.supabase.co

# Supabase Publishable Key (New standard: VITE_SUPABASE_PUBLISHABLE_KEY)
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_your_key_here
# Backward compatibility fallback
VITE_SUPABASE_ANON_KEY=sb_publishable_your_key_here

# Mikasa Local Backend URL
VITE_API_URL=http://127.0.0.1:18420
```

### Backend (`.env`)
```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
# Publishable Key (sb_publishable_...)
SUPABASE_PUBLISHABLE_KEY=sb_publishable_your_key_here
SUPABASE_ANON_KEY=sb_publishable_your_key_here

# Backend Secret Key (sb_secret_... or service_role)
SUPABASE_SECRET_KEY=sb_secret_your_key_here
SUPABASE_SERVICE_ROLE_KEY=sb_secret_your_key_here

# Asymmetric / Symmetric JWT Verification
# Supabase JWKS endpoint is queried automatically:
# https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
# Optional symmetric secret:
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# Security & CORS
MIKASA_REQUIRE_AUTH=true
MIKASA_ALLOWED_ORIGINS=http://localhost:1420,http://127.0.0.1:1420,tauri://localhost,https://tauri.localhost

# Server Environment
ENVIRONMENT=development
MIKASA_API_HOST=127.0.0.1
MIKASA_API_PORT=18420
```

---

## 3. Database Schema & RLS Migrations

Migrations are stored in:
- `supabase/migrations/20260918_phase41_supabase_auth.sql`
- `supabase/migrations/20260918_phase42_device_enrollment.sql`

### Tables Created:
1. `public.profiles`: 1:1 mapping with `auth.users(id)`. Populated automatically via PostgreSQL trigger `on_auth_user_created`.
2. `public.devices`: User-enrolled host and agent devices.
3. `public.telegram_links`: Telegram identities bound to Mikasa profiles.
4. `public.permissions`: Device permission profiles and blocked command lists.
5. `public.device_pairing_sessions`: 5-minute ephemeral numeric pairing codes for desktop agents.
6. `public.device_credentials`: Asymmetric Ed25519 public keys for PC agents.
7. `public.device_auth_challenges`: Single-use nonces for replay attack prevention.

### Row Level Security (RLS) Verification:
All tables enforce multi-tenant isolation via:
```sql
ALTER TABLE public.<table_name> ENABLE ROW LEVEL SECURITY;

CREATE POLICY "<table_name>_select_own"
    ON public.<table_name>
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());
```

---

## 4. Error Handling & Diagnostics

In previous releases, an unconfigured `.env` fell back to `placeholder-project.supabase.co`, causing DNS resolution errors resulting in a raw `TypeError: Failed to fetch` on the Register/Login pages.

In v8.0.0:
1. **Pre-flight Check**: `isSupabaseConfigured` detects whether real credentials exist.
2. **Visual Alert**: An amber configuration banner guides the developer if `.env` is unconfigured.
3. **Friendly Error Mapping**: Any network or Supabase connection issue displays a clear, localized Uzbek message:
   `"Supabase serveriga ulanib bo'lmadi. Internet aloqangiz yoki loyiha URL manzilini tekshiring."`
4. **Health Check Endpoint**: `/api/health` reports runtime connectivity without leaking secrets.
