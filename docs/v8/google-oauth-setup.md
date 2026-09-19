# Mikasa AI v8.0.0 — Google OAuth Setup Guide

## 1. Overview
Mikasa AI v8.0.0 integrates Google OAuth via **Supabase Auth**. Users can authenticate seamlessly using the **"Google bilan davom etish"** action on both the Login and Registration screens.

```
+----------------+      +---------------+      +----------------------+
|  Mikasa UI     | ---> | Supabase Auth | ---> | Google OAuth 2.0 API |
| (AuthPage.tsx) | <--- | (OAuth Flow)  | <--- | (Google Cloud)       |
+----------------+      +---------------+      +----------------------+
```

---

## 2. Google Cloud Console Setup

1. Go to the [Google Cloud Console Credentials Page](https://console.cloud.google.com/apis/credentials).
2. Create or select your Google Cloud project (e.g., `mikasa-ai-auth`).
3. Configure the **OAuth Consent Screen**:
   - User Type: **External**
   - App Name: `Mikasa AI`
   - User Support Email: your developer or support email
   - Developer Contact Email: your developer email
   - Scopes: `openid`, `email`, `profile`
4. Create **OAuth 2.0 Client ID**:
   - Application Type: **Web application**
   - Name: `Mikasa AI Web Client`
   - Authorized JavaScript Origins:
     - `https://<your-project-id>.supabase.co`
     - `http://localhost:1420` (Vite dev server)
     - `tauri://localhost` (Tauri Desktop App)
     - `https://tauri.localhost`
   - Authorized Redirect URIs:
     - `https://<your-project-id>.supabase.co/auth/v1/callback`
5. Copy your **Client ID** and **Client Secret**.

---

## 3. Supabase Dashboard Configuration

1. In your [Supabase Dashboard](https://supabase.com/dashboard), navigate to **Authentication** -> **Providers**.
2. Click on **Google**.
3. Toggle **Enable Google provider**.
4. Paste the **Client ID** and **Client Secret** obtained from Google Cloud Console.
5. In **Authentication** -> **URL Configuration**:
   - **Site URL**: `http://localhost:1420` (or your production web host)
   - **Redirect URLs**: Add:
     - `tauri://localhost`
     - `https://tauri.localhost`
     - `http://localhost:1420/*`
     - `http://127.0.0.1:1420/*`
6. Click **Save**.

---

## 4. Frontend Integration & Lifecycle

### Method Call
`backendService.signInWithGoogle()` calls:
```typescript
const redirectTo = typeof window !== "undefined" ? window.location.origin : undefined;
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: "google",
  options: {
    redirectTo,
    queryParams: {
      access_type: "offline",
      prompt: "consent",
    },
  },
});
```

### Auto Session Detection
On component mount, `AuthPage.tsx` listens for the returned session via:
```typescript
supabase.auth.onAuthStateChange(async (event, session) => {
  if ((event === "SIGNED_IN" || event === "USER_UPDATED") && session?.user) {
    onAuthSuccess(user);
  }
});
```

### Desktop App Content Security Policy
In `mikasa-7/src-tauri/tauri.conf.json`, `connect-src` is configured with:
```
connect-src 'self' tauri: http://localhost:18420 ws://localhost:18420 http://127.0.0.1:18420 ws://127.0.0.1:18420 https://*.supabase.co wss://*.supabase.co https://accounts.google.com https://*.googleapis.com;
```
This ensures that the WebView2 engine does not block OAuth redirects, Google UserInfo APIs, or token exchanges.

---

## 5. Phase 44: Account Linking & Lockout Protection

### Explicit Linking Flow
1. Authenticated user navigates to **Sozlamalar -> Akkaunt -> Ulangan hisoblar**.
2. Frontend calls `/api/account/identities/link/initiate` to obtain a session-bound `link_` cryptographic state token.
3. OAuth flow authenticates Google and links it to the active Supabase user identity.

### Anti-Auto-Merge Policy
Identical emails do not automatically merge accounts. If another user attempts to link an already linked Google account, an explicit error is returned:
> *"Bu Google hisob allaqachon boshqa Mikasa akkauntiga ulangan."*

### Account Lockout Prevention
If Google is the only authentication method on the account, unlinking is blocked (`can_unlink_google: false`):
> *"Google sizning yagona kirish usulingizdir. Akkauntga kirish imkoniyatini yo'qotmaslik uchun avval parolni o'rnating yoki boshqa hisobni ulang."*
