# Phase 41 — Supabase Auth Migration & Central Identity Architecture

## 1. Umumiy Arxitektura va Maqsad

Mikasa AI v8.0.0 loyihasida autentifikatsiya tizimi **Supabase Auth** platformasiga to'liq ko'chirildi. Custom password hashing (PBKDF2) va backend sessiya boshqaruvi o'rniga zamonaviy, xavfsiz va bulutli Identity Provider modeli joriy etildi.

### Identity Zanjiri
```
Mikasa Frontend (mikasa-7)
       │
       ▼ (To'g'ridan-to'g'ri Supabase Auth SDK orqali)
Supabase Auth (Cloud / Self-Hosted)
       │
       ├── Register (signUp)
       ├── Login (signInWithPassword)
       ├── Email Verification
       ├── Password Reset (resetPasswordForEmail)
       ├── Session Management
       └── Logout (signOut)
       │
       ▼
Supabase auth.users (UUID `sub`)
       │
       ▼ (1:1 munosabat & avtomatik trigger)
Mikasa public.profiles (id UUID PRIMARY KEY REFERENCES auth.users)
       │
       ├─────────────────┬─────────────────┬──────────────────┐
       ▼                 ▼                 ▼                  ▼
public.devices    telegram_links     permissions      RemoteAuthSession
(Host / Agent)   (Telegram ID)     (RBAC Profiles)   (PC Masofaviy Boshqaruv)
```

---

## 2. Asosiy Xavfsizlik Invariantlari (Security Invariants)

1. **Backendda Nol Parol Saqlash (Zero Backend Password Storage):**
   - Mikasa Python backend serveri hech qachon foydalanuvchi parollarini (na ochiq matnda, na xesh qilingan shaklda) qabul qilmaydi, ko'rmaydi va saqlamaydi.
   - `MikasaUser` (va `MikasaProfile`) modellarida `password_hash`, `password_salt` yoki `password` maydonlari butunlay mavjud emas.
   - Parol bilan bog'liq barcha amallar (ro'yxatdan o'tish, login, parolni o'zgartirish va tiklash) frontend mijozida to'g'ridan-to'g'ri `@supabase/supabase-js` orqali bajariladi.

2. **JWT Bearer Token Verifikatsiyasi (RFC 7519):**
   - Frontend har bir API so'rovida `Authorization: Bearer <supabase_access_token>` sarlavhasini yuboradi.
   - `SupabaseAuthManager.verify_supabase_jwt(token)` algoritmi:
     - Strukturaviy yaxlitlikni tekshiradi (`header.payload.signature`).
     - HMAC-SHA256 (HS256) imzosini `SUPABASE_JWT_SECRET` kaliti bilan tekshiradi.
     - Token muddati o'tmaganligini (`exp > now`) tekshiradi.
     - `sub` (UUID) orqali foydalanuvchini aniqlaydi.
   - `authenticate_token(token)` orqali `auth.users` dan olingan ma'lumotlar avtomatik tarzda `public.profiles` (`MikasaUser`) bilan sinxronizatsiya qilinadi.

3. **Row Level Security (RLS) va Ko'p Foydalanuvchili Izolyatsiya (Multi-Tenant Isolation):**
   - PostgreSQL darajasida barcha jadvallar (`public.profiles`, `public.devices`, `public.telegram_links`, `public.permissions`) uchun `ENABLE ROW LEVEL SECURITY` faollashtirilgan.
   - Har bir operatsiya (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) `auth.uid() = id` yoki `auth.uid() = user_id` sharti orqali tekshiriladi.
   - User A hech qachon User B ning qurilmalari, Telegram bog'lanishlari yoki ruxsatlariga kira olmaydi.

4. **Sessiyalarning To'liq Ajratilishi (Separation of Concerns):**
   - **Supabase Auth Session (`SupabaseSessionClaims`):** Web va ilovaga kirish, foydalanuvchi kimligini tasdiqlash uchun xizmat qiladi.
   - **RemoteAuthSession (Phase 37):** Kompyuterni apparat darajasida masofaviy boshqarish (Screen, Mouse, Keyboard, Terminal) uchun vaqt chegaralangan (TTL), challenge-response asosidagi apparat sessiyasi hisoblanadi.
   - Bu ikki qatlam arxitekturaviy jihatdan bir-biridan to'liq ajratilgan.

5. **Kalitlar va Atrof-muhit Xavfsizligi:**
   - `SUPABASE_SERVICE_ROLE_KEY` va `SUPABASE_JWT_SECRET` faqat backend (`.env`) da saqlanadi va frontendga hech qachon berilmaydi.
   - Frontend faqat ochiq anonim kalitlarni (`VITE_SUPABASE_URL` va `VITE_SUPABASE_ANON_KEY`) ishlatadi.

---

## 3. PostgreSQL Migratsiya Strukturasi (`supabase/migrations/20260918_phase41_supabase_auth.sql`)

### Jadvallar
- **`public.profiles`**: `id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE`, `username`, `email`, `display_name`, `avatar_url`, `is_verified`, `created_at`, `updated_at`.
- **`public.devices`**: `id UUID PRIMARY KEY`, `user_id UUID REFERENCES public.profiles(id)`, `device_id`, `name`, `hostname`, `mac_address`, `ip_address`, `os`, `agent_version`, `is_revoked`.
- **`public.telegram_links`**: `id UUID PRIMARY KEY`, `user_id UUID REFERENCES public.profiles(id)`, `telegram_user_id BIGINT UNIQUE`, `telegram_username`, `first_name`.
- **`public.permissions`**: `id UUID PRIMARY KEY`, `user_id UUID REFERENCES public.profiles(id)`, `device_id`, `allowed_categories`, `require_confirmation_categories`, `blocked_commands`.

### Avtomatik Trigger
`auth.users` jadvaliga yangi foydalanuvchi qo'shilganda `public.handle_new_user()` funksiyasi ishga tushib, `public.profiles` jadvalida avtomatik ravishda profil yaratadi:
```sql
CREATE TRIGGER on_auth_user_created
    AFTER INSERT OR UPDATE OF email, email_confirmed_at ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

---

## 4. Test Qamrovi (30/30 Muvaffaqiyatli)

`tests/test_v8_phase41.py` test to'plami 30 ta ssenariyni 100% qamrab olgan:
- **1–6:** Supabase JWT HS256 imzosi, muddati o'tgan token, soxta imzo, buzuq format, claims modeli, dev muhitidagi fallback.
- **7–12:** MikasaUser da parol maydonlari yo'qligi, yangi profil yaratish, mavjud profilni yangilash, token autentifikatsiyasi, username generatsiyasi, JSON xavfsizligi.
- **13–18:** Username va email validatsiyasi, Brute-force va Rate limiter himoyasi.
- **19–24:** SQL migratsiya fayli, RLS faolligi, `auth.uid()` siyosatlari, `handle_new_user` triggeri, ko'p ijarachili qurilma va Telegram izolyatsiyasi.
- **25–30:** Bearer token orqali `/api/auth/me` (200 va 401), `/api/devices` izolyatsiyasi, Supabase SDK to'g'ridan-to'g'ri xabarlari, RemoteAuthSession va Supabase sessiyasining ajratilishi, `.env` kalitlar xavfsizligi.

Jami v8 regressiya to'plamida **181 ta test** to'liq muvaffaqiyatli o'tgan.
