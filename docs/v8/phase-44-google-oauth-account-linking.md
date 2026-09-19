# Mikasa AI v8.0.0 — Phase 44: Google OAuth & Account Linking

**Author**: Senior Full-Stack & Security Architect  
**Branch**: `dev-v8.0.0`  
**Status**: Completed & Verified  
**Date**: September 19, 2026  

---

## 1. Executive Summary

Phase 44 introduces production-grade **Google OAuth 2.0** authentication and **Cryptographic Account Linking** for Mikasa AI v8.0.0. Building upon the real Supabase Auth infrastructure established in Phase 43, Phase 44 allows users to:
1. Seamlessly sign in or sign up using their Google account via Supabase Auth as the authoritative Identity Provider.
2. Link their Google account to an existing Mikasa account from the Settings / Account page.
3. Unlink a connected Google account safely, enforced by strict **Account Lockout Protection**.
4. Prevent unauthorized merging of accounts with identical emails via our **Anti-Auto-Merge Policy**.
5. Maintain end-to-end multi-tenant isolation, replay protection, and zero confidential key exposure.

---

## 2. Architectural Security Principles

### 2.1 State-Bound Replay-Proof Flow
- Every OAuth initiation produces a cryptographically secure, high-entropy state identifier (`link_` or random UUID) with a strictly enforced TTL of 300 seconds (5 minutes).
- States are single-use (`dict.pop` semantics): once an authorization code or callback session is consumed, the state is immediately invalidated, preventing replay and CSRF attacks.
- Concurrent logins from multiple clients or tabs operate in isolated memory partitions without state cross-contamination.

### 2.2 Strict Anti-Auto-Merge Policy
- An unauthenticated user signing in via Google with an email matching an existing password-based account **never** automatically merges into that account without prior authenticated verification.
- Separate `user_id` (`auth.uid()`) records remain completely isolated across all PostgreSQL tables (`profiles`, `devices`, `sessions`, `credentials`, `commands`, `memory`).
- Attempting to link a Google identity that is already bound to another Mikasa account raises an unambiguous, localized error:
  > *"Bu Google hisob allaqachon boshqa Mikasa akkauntiga ulangan."*

### 2.3 Account Lockout Protection (Sole Identity Guard)
- If a user registered solely through Google OAuth without setting a password, unlinking Google would permanently render the account inaccessible.
- Both the backend API (`POST /api/account/identities/unlink`) and the frontend UI (`AccountPage.tsx`) evaluate `can_unlink_google`.
- Unlinking is blocked with an informative Uzbek guidance message:
  > *"Google sizning yagona kirish usulingizdir. Akkauntga kirish imkoniyatini yo'qotmaslik uchun avval parolni o'rnating yoki boshqa hisobni ulang."*

### 2.4 Multi-Tenant Boundary Enforcement
- All Account Identities API endpoints (`/api/account/identities`, `/api/account/identities/unlink`, `/api/account/identities/link/initiate`) strictly resolve `user_id` from the verified Supabase JWT (`sub` claim).
- Any attempt by an authenticated user to pass cross-tenant query parameters (`?user_id=attacker`) or spoof headers (`X-Mikasa-User-Id`) is rejected immediately with `403 Forbidden`.

---

## 3. API Endpoints Specification

### 3.1 `GET /api/account/identities`
Retrieves the authenticated user's connected identity providers and security capabilities.

- **Headers**: `Authorization: Bearer <Supabase_JWT>`
- **Response `200 OK`**:
```json
{
  "ok": true,
  "user_id": "8f03c004-9277-459f-93d3-f5c71a3de764",
  "providers": ["email", "google"],
  "primary_provider": "email",
  "identities": [
    {
      "provider": "email",
      "email": "user@example.com",
      "is_primary": true,
      "is_verified": true
    },
    {
      "provider": "google",
      "email": "user@gmail.com",
      "name": "Dilshodbek",
      "avatar_url": "https://lh3.googleusercontent.com/...",
      "is_primary": false
    }
  ],
  "is_google_linked": true,
  "can_unlink_google": true
}
```

### 3.2 `POST /api/account/identities/unlink`
Unlinks a secondary Google account.

- **Headers**: `Authorization: Bearer <Supabase_JWT>`
- **Body**: `{"provider": "google"}`
- **Response `200 OK`**:
```json
{
  "ok": true,
  "message": "Google hisobi muvaffaqiyatli uzildi",
  "user_id": "8f03c004-9277-459f-93d3-f5c71a3de764",
  "unlinked_provider": "google"
}
```
- **Error `400 Bad Request`** (Lockout protection):
```json
{
  "ok": false,
  "error": "Google sizning yagona kirish usulingizdir. Akkauntga kirish imkoniyatini yo'qotmaslik uchun avval parolni o'rnating yoki boshqa hisobni ulang."
}
```

### 3.3 `POST /api/account/identities/link/initiate`
Initiates linking of a Google identity to an existing authenticated session.

- **Headers**: `Authorization: Bearer <Supabase_JWT>`
- **Response `200 OK`**:
```json
{
  "ok": true,
  "state": "link_k8A2v_...9Z",
  "user_id": "8f03c004-9277-459f-93d3-f5c71a3de764",
  "expires_in": 300
}
```

---

## 4. Frontend Implementation

### 4.1 `AuthPage.tsx`
- **Google Sign-In Button**:
  - Rendered with accessible labels: `aria-label="Google orqali tizimga kirish"` / `aria-label="Google orqali ro'yxatdan o'tish"`.
  - Automatically disabled when `loading || oauthLoading || oauthWaiting`.
  - Visual spinner during asynchronous redirect and token exchange.
- **Deep-Link State Listener**:
  - Listens to Supabase Auth state changes (`SIGNED_IN`, `USER_UPDATED`) and queries local backend `/api/account/oauth/session` using the cryptographic `state` parameter.

### 4.2 `AccountPage.tsx`
- **Linked Accounts Card Layout**:
  - Displays **Email & Parol** and **Google Hisobi** cards.
  - Live status indicators: `Ulangan` (Emerald badge) and `Ulanmagan` (Muted badge).
  - Profile metadata display: Google email, display name, and avatar picture.
  - Action buttons: "Bog'lash" (Link Google) and "Uzish" (Unlink Google).
  - Integrated lockout warning dialog/toast when `can_unlink_google === false`.

### 4.3 Desktop Tauri CSP (`tauri.conf.json`)
- Updated `connect-src` whitelist with:
  `https://*.googleapis.com https://accounts.google.com`
  Ensures native WebView2 does not block Google token exchange or userinfo endpoints.

---

## 5. Audit Logging & Security Redaction

Seven new audit event types added to `core/v8/events.py`:
- `OAUTH_STARTED`
- `OAUTH_COMPLETED`
- `OAUTH_FAILED`
- `GOOGLE_LINK_STARTED`
- `GOOGLE_LINK_COMPLETED`
- `GOOGLE_LINK_FAILED`
- `GOOGLE_UNLINKED`

Automatic redaction in `sanitize_event_data()` strictly scrubs:
`access_token`, `refresh_token`, `authorization_code`, `client_secret`, `google_token`, `id_token`.

---

## 6. Verification & Test Suite Summary

### Automated Test Coverage
- **Phase 44 Dedicated Test Suite (`tests/test_v8_phase44.py`)**:
  - **30/30 tests passed** (100%).
  - Tests 1-7: OAuth State Security, entropy, TTL, single-use, concurrency.
  - Tests 8-10: Audit logging & sensitive token redaction.
  - Tests 11-16: `/api/account/identities` resolution, multi-tenant 403, lockout flag.
  - Tests 17-21: `/api/account/identities/unlink` authentication, lockout guards, provider validation.
  - Tests 22-24: `/api/account/identities/link/initiate` session-bound tokens and multi-tenant isolation.
  - Tests 25-28: Anti-auto-merge validation, error contract, multi-tenant resource isolation.
  - Tests 29-30: Live PostgreSQL RLS policy verification & Supabase provider probe.

- **Full Backend Regression Suite**:
  - **236/236 tests passed** across all Phase 38-44 test modules (`0 failed`, `0 errors`).

- **Frontend Verification**:
  - `npx tsc --noEmit`: 0 TypeScript errors.
  - `npm test`: 15/15 Vitest tests passed.
  - `npm run build`: Production build succeeded in 411ms.
  - Secret scan: Zero leaks in `dist/`.

---

## 7. Supabase Provider Live Verification Status

Live probe against real Supabase project `https://vdcssmzguxfknqkfxbed.supabase.co`:
- **Current Provider Status**: `CONFIGURED & VERIFIED`
- **Google OAuth Provider**: `ENABLED`
- **Client Configuration**: Verified active web client on Google Cloud (`445850190028-...apps.googleusercontent.com`)
- **Authorized Redirect URI**: `https://vdcssmzguxfknqkfxbed.supabase.co/auth/v1/callback` (HTTP 200 OK from Google OAuth Screen, no `redirect_uri_mismatch`)
- **Desktop/Local Redirects**: Supported and whitelisted
- **End-to-End Status**: Fully operational for production Google Sign-In and Account Linking without secret leakage.
