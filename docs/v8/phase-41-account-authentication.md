# Phase 41 — Account Registration & Authentication System

## 1. Umumiy Maqsad va Arxitektura

Mikasa AI v8.0.0 arxitekturasida foydalanuvchi tizimga kirishidan oldin **Mikasa Account** yaratishi yoki mavjud hisobiga login qilishi shart.
Phase 40 dagi mavjud zanjir:
```
TelegramIdentity ──► MikasaUser ──► Device ──► PermissionProfile ──► RemoteAuthSession
```
Phase 41 bilan to'liq integratsiyalashib, quyidagi markaziy identity layer shakllantirildi:

```
                      ┌──────────────────────────────────────┐
                      │            Mikasa Account            │
                      │        (Login / Registration)        │
                      └──────────────────┬───────────────────┘
                                         │
        ┌───────────────────┬────────────┴───────┬────────────────────┐
        ▼                   ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│ Web / Client  │   │   Telegram    │   │     Devices     │   │  Permissions  │
│   Sessions    │   │  Identities   │   │  (Host / Agent) │   │   Profiles    │
└───────┬───────┘   └───────────────┘   └────────┬────────┘   └───────────────┘
        │                                        │
        │                                        ▼
        │                              ┌───────────────────┐
        │                              │  Remote Access    │
        │                              │     Sessions      │
        │                              └───────────────────┘
        ▼
┌───────────────┐
│  Auth Tokens  │
│ (PBKDF2/HMAC) │
└───────────────┘
```

---

## 2. Asosiy Xavfsizlik Qoidalari (Security Invariants)

1. **Parollarni Xeshlash:**
   - Standart: **PBKDF2-HMAC-SHA256**.
   - Iteratsiyalar soni: **600,000** (OWASP 2024 tavsiyasi bo'yicha).
   - Tasodifiy Salt: `secrets.token_bytes(16)` (16 bayt).
   - Plaintext format hech qachon saqlanmaydi va loglarga yozilmaydi.
   - Format: `pbkdf2:sha256:600000$<salt_hex>$<hash_hex>`.
   - Tekshirish: `hmac.compare_digest` yordamida vaqt bo'yicha hujumlar (timing attacks) oldi olingan.

2. **Parol Murakkablik Talablari:**
   - Kamida 8 ta belgi (maksimal 128 ta).
   - Kamida 1 ta harf (`a-z, A-Z`) va kamida 1 ta raqam (`0-9`).
   - Tasdiq paroli (`confirm_password`) kiritilganda to'liq mos kelishi shart.

3. **Username & Email Validatsiyasi:**
   - Username: `^[a-zA-Z0-9_-]{3,32}$` (uzunligi 3-32, maxsus belgilar faqat `_` va `-`).
   - Email: Ixtiyoriy, ammo kiritilganda canonical kichik harflarga (`lowercase`) keltiriladi va RFC formati tekshiriladi.
   - Case-insensitive unikallik tekshiruvi.

4. **Sessiya va Token Boshqaruvi:**
   - `AccountSession`: Web/app autentifikatsiyasi uchun (TTL = 7 kun / 604800 soniya).
   - `RemoteAuthSession` (Phase 40 kompyuterni masofaviy boshqarish sessiyasi) dan to'liq ajratilgan.
   - Sessiya tokeni SHA-256 bilan heshlanadi. Plaintext faqat foydalanuvchiga 1 marta qaytariladi, diskda faqat `token_hash` saqlanadi.
   - Har bir token autentifikatsiyasida `last_activity_at` yangilanadi.

5. **Rate Limiting & Anti-Brute-Force:**
   - Har bir hisob yoki IP uchun 5 marta ketma-ket muvaffaqiyatsiz login urinishidan so'ng **5 daqiqa (300 soniya) cooldown** joriy etiladi.
   - Muvaffaqiyatli login hisoblagichni avtomatik tozalaydi.
   - 1 ta IP dan 1 soatda ko'pi bilan 10 ta ro'yxatdan o'tishga ruxsat beriladi.

6. **Foydalanuvchi Mavjudligini Aniqlashdan Himoya (User Enumeration Defense):**
   - Parol noto'g'ri bo'lganda ham, foydalanuvchi mavjud bo'lmaganda ham bir xil generic xabar qaytariladi: `"Noto'g'ri username/email yoki parol"`.
   - Parolni tiklash so'rovida (`forgot_password`) foydalanuvchi bazada bormi yoki yo'qmi, bir xil xabar qaytariladi: `"If account exists, a reset message has been sent."`.

7. **Multi-Tenant Izolyatsiyasi:**
   - Foydalanuvchi A o'zining sessiya tokeni orqali faqat o'ziga tegishli qurilmalar, buyruqlar va sessiyalarni ko'ra oladi va boshqara oladi.
   - Foydalanuvchi B ning ma'lumotlarini o'zgartirish qat'iyan man etiladi va `PermissionDenied` qaytariladi.

---

## 3. Realizatsiya Qilingan Backend Komponentlari

| Fayl | Mas'uliyat |
|------|-----------|
| `core/v8/account_device.py` | `MikasaUser` modeliga `email`, `password_hash`, `is_verified`, `last_login_at` maydonlari qo'shildi. `get_user_by_username`, `get_user_by_email`, `create_user`, `update_user` metodlari bilan kengaytirildi. `to_dict` parolni hech qachon chiqarmaydi. |
| `core/v8/events.py` | Phase 41 hodisalari qo'shildi (`ACCOUNT_REGISTERED`, `ACCOUNT_LOGIN_SUCCESS`, `ACCOUNT_LOGIN_FAILED`, `ACCOUNT_LOGOUT`, `ACCOUNT_LOGOUT_ALL`, `PASSWORD_CHANGED`, `PASSWORD_RESET_REQUESTED`, `PASSWORD_RESET_COMPLETED`, `EMAIL_VERIFIED`, `SESSION_REVOKED`). Xavfsiz loglash maskalari yangilandi. |
| `core/v8/account_auth.py` | PBKDF2 `PasswordManager`, `AccountSession`, `VerificationToken`, `EmailVerificationProvider`, `MockEmailVerificationProvider`, `AuthRateLimiter`, `AccountAuthManager` (barcha autentifikatsiya logikasi, sessiyalar, email tasdiqlash, parolni tiklash). |
| `core/v8/__init__.py` | `PHASE = 41` ga oshirildi, barcha yangi klasslar export qilindi. |
| `core/api_server.py` | Yangi REST handlerlar: `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/logout-all`, `/api/auth/me`, `/api/auth/verify-email`, `/api/auth/forgot-password`, `/api/auth/reset-password`, `/api/auth/change-password`. Bearer token tekshiruvi. |

---

## 4. Frontend Integratsiyasi (`mikasa-7`)

- **`src/services/backendService.ts`:**
  - Token boshqaruvi: `setAuthToken`, `getAuthToken`, `getAuthHeaders`, `onAuthChange`.
  - Yangi metodlar: `register`, `login`, `logout`, `logoutAllAccounts`, `getMe`, `verifyEmail`, `forgotPassword`, `resetPassword`, `changePassword`.
  - Barcha so'rovlar avtomatik ravishda `Authorization: Bearer <token>` sarlavhasini biriktiradi.

- **`src/pages/AuthPage.tsx`:**
  - Glassmorphic cyberpunk interfeysi (`Login`, `Register`, `Forgot Password`, `Reset Password`, `Verify Email` tablari).
  - Parol tasdiqlash va xatoliklarni xavfsiz ko'rsatish.

- **`src/App.tsx`:**
  - **Auth Gate**: Dastur ishga tushganda `backendService.getMe()` tekshiriladi.
  - Agar foydalanuvchi tizimga kirmagan bo'lsa (`401` yoki token yo'q), avtomatik ravishda **AuthPage** ochiladi.
  - Tizimga muvaffaqiyatli kirilgach yoki ro'yxatdan o'tilgach, asosiy **Dashboard (AppShell)** ochiladi.
  - Chiqish (`handleLogout`) qilinganda token tozalanadi va qayta AuthPage ga o'tiladi.

- **`src/pages/AccountPage.tsx`:**
  - Mikasa hisob ma'lumotlari kartasi, tasdiqlanganlik belgisi (Verified Badge).
  - "Tizimdan chiqish" va "Barcha qurilmalardan chiqish" tugmalari.
  - "Parolni o'zgartirish" modali (eski parol va yangi parolni xavfsiz qabul qiladi).

---

## 5. Testlar va Verifikatsiya

- **Phase 41 Unit & Integration Test Suite (`tests/test_v8_phase41.py`):**
  - **30 ta test** (Scenarios 1–30): PBKDF2 xeshlash, timing-attack himoyasi, parol qoidalari, username/email qoidalari, ro'yxatdan o'tish, login, brute-force rate-limiting, sessiyalar boshqaruvi, email tasdiqlash, parolni tiklash, multi-tenant izolyatsiyasi, HTTP API endpointlari.
  - Natija: **30 ta test muvaffaqiyatli o'tdi (100% PASS)**.

- **Full Regression Suite (`tests/test_v8*.py`):**
  - Phases 35–41 barcha v8 testlari: **181 ta test muvaffaqiyatli o'tdi (181 passed in 42s, 0 failures, 0 regressions)**.

- **Statik Kod Sifati & Linter:**
  - `flake8`: 0 xatolik, 0 ogohlantirish.

- **Frontend Tekshiruvi:**
  - `npm run build`: 44 modullar muvaffaqiyatli kompilyatsiya qilindi (0 errors).
  - `npm test -- --run`: 15 ta test to'liq o'tdi (0 errors).
