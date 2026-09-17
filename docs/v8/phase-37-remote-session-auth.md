# MIKASA AI v8.0.0 — PHASE 37: SECURE REMOTE SESSION AUTHENTICATION
## Telegram → Wake-on-LAN → PC Agent → Authentication Challenge → Remote Session

---

## 1. Arxitektura va Ishlash Prinsipi

Phase 37 da masofaviy kompyuter boshqaruvi uchun ko'p pog'onali, xavfsizlik kafolatlangan sessiyaviy autentifikatsiya arxitekturasi joriy etildi.

```
                    ┌─────────────────────────┐
                    │      TELEGRAM USER      │
                    └────────────┬────────────┘
                                 │
                 1. "PCni uyg'ot" yoki /wake
                                 ▼
                    ┌─────────────────────────┐
                    │  Wake-on-LAN Pipeline   │
                    │  (Magic Packet -> WoL)  │
                    └────────────┬────────────┘
                                 │
                         2. PC Online bo'ldi
                                 ▼
                    ┌─────────────────────────┐
                    │  RemoteOrchestrator     │
                    │  + RemoteAuthEngine     │
                    └────────────┬────────────┘
                                 │
                 3. 🔐 "Parolni tasdiqlang!"
                                 ▼
                    ┌─────────────────────────┐
                    │      TELEGRAM USER      │
                    │  (Parol yoki PIN kod)   │
                    └────────────┬────────────┘
                                 │
                                 ▼
        ┌─────────────────────────────────────────────────┐
        │             RemoteAuthEngine                    │
        │ - 5-min Cooldown tekshiruvi                     │
        │ - PBKDF2-HMAC-SHA256 (100k rounds)              │
        │ - Constant-time comparison                      │
        │ - 3 ta xato urinish chegarasi                   │
        └──────────────┬──────────────────┬───────────────┘
          [XATO PAROL] │                  │ [TO'G'RI PAROL]
                       ▼                  ▼
        ┌────────────────────────┐  ┌───────────────────────────────────┐
        │ Qolgan urinish: (3->2->1│  │ SessionManager:                   │
        │ 3 xatoda: 5-MIN LOCKOUT│  │ - RemoteAuthSession ochiladi      │
        │ (AUTH_COOLDOWN_ACTIVE) │  │ - TTL: 15 daqiqa (900 soniya)     │
        │                        │  │ - Agent holati: READY             │
        └────────────────────────┘  └─────────────────┬─────────────────┘
                                                      │
                                    4. Masofaviy buyruqlar ruxsat etildi
                                                      ▼
                                            ┌───────────────────┐
                                            │ Mikasa PC Agent   │
                                            │ (Buyruq bajarish) │
                                            └───────────────────┘
```

---

## 2. Xavfsizlik Modeli va Mexanizmlar

### A. PBKDF2-HMAC-SHA256 Xeshlash
- Har bir maxfiy parol va PIN kod uchun `secrets.token_bytes(16)` orqali kriptografik tuz (salt) generatsiya qilinadi.
- NIST tavsiyasiga ko'ra **100,000 iteratsiya** bilan xeshlanadi:
  `pbkdf2:sha256:100000:<salt_hex>:<hash_hex>`

### B. Constant-Time Solishtirish (Timing Attack himoyasi)
- Parol va PIN kodlarni solishtirishda oddiy `==` operatori o'rniga `secrets.compare_digest()` dan foydalaniladi.
- Bu orqali vaqt bo'yicha tahlil (side-channel timing attack) hujumlari to'liq bartaraf etiladi.

### C. 3 Ta Urinish Chegarasi va 5 Daqiqalik Blokirovka (Cooldown Lockout)
- Har bir xato parol kiritilganda `AUTH_ATTEMPT_FAILED` hodisasi qayd etiladi va qolgan urinishlar soni kamayadi (3 -> 2 -> 1).
- Ketma-ket 3 ta xato urinish kiritilgach:
  - Tizim **5 daqiqaga (300 soniya)** qat'iy bloklanadi (`AUTH_COOLDOWN_ACTIVATED`).
  - Blokirovka davrida hatto to'g'ri parol kiritilsa ham darhol rad etiladi.
  - Cooldown muddati o'tgach, hisoblagich avtomatik 3 ga qaytadi.

### D. Zero-Exposure Maxfiylik va Audit Sanitizatsiyasi
- Telegram orqali parol yoki PIN kiritilayotganda loglarda `***PASSWORD_INPUT***` qayd etiladi.
- Barcha audit hodisalarida quyidagi kalitlar avtomatik `***REDACTED***` qilinadi:
  `password`, `pin`, `token`, `bot_token`, `secret`, `pairing_token`, `auth_header`, `auth_code`, `session_token`.
- Plain-text parollar hech qachon fayllarda yoki xotiradagi ochiq loglarda saqlanmaydi.

---

## 3. Sessiya Boshqaruvi (Session Lifecycle)

1. **Sessiya Davomiyligi (TTL)**:
   - Standart TTL: **15 daqiqa (900 soniya)**.
   - Har bir sessiya yagona UUID identifikatoriga (`session_id`) ega.
   - `is_valid()` metodi orqali muddat va faollik tekshiriladi.
2. **Buyruqlar**:
   - `/session` yoki `sessiya holati`: Faol sessiya mavjudligi, sessiya IDsi va qolgan soniyalarni ko'rsatadi.
   - `/logout` yoki `/lock` yoki `sessiyani yop`: Faol sessiyani darhol yopadi va masofaviy boshqaruvni qayta qulflaydi.
3. **Avtomatik Tozalash**:
   - Muddati o'tgan sessiyalar `SESSION_EXPIRED` hodisasini yozib avtomatik nofaol qilinadi.
   - `cleanup_expired_sessions()` orqali xotira tozalanadi.

---

## 4. Konfiguratsiya (.env)

Tizim sozlamalari `.env` fayli orqali boshqariladi:

```env
# ========== Remote Session Authentication (Phase 37) ==========
REMOTE_AUTH_PASSWORD=your_secure_remote_password_here
REMOTE_AUTH_PIN=1234
REMOTE_SESSION_TTL_SECONDS=900
AUTH_MAX_ATTEMPTS=3
AUTH_COOLDOWN_SECONDS=300
REQUIRE_SESSION_AUTH=true
```

---

## 5. Yangi Audit Hodisalari (RemoteEventType)

| Hodisa Turi | Tavsif |
|---|---|
| `AUTH_CHALLENGE_ISSUED` | Foydalanuvchiga parol/PIN tasdiqlash so'rovi yuborildi |
| `AUTH_ATTEMPT_SUCCESS` | Parol to'g'ri kiritildi va sessiya ochildi |
| `AUTH_ATTEMPT_FAILED` | Noto'g'ri parol kiritildi (urinish kamaydi) |
| `AUTH_COOLDOWN_ACTIVATED` | 3 marta xato sababli 5 daqiqalik blokirovka yoqildi |
| `SESSION_OPENED` | Yangi masofaviy boshqaruv sessiyasi ochildi |
| `SESSION_EXPIRED` | Sessiya TTL muddati o'tdi |
| `SESSION_CLOSED` | Foydalanuvchi `/logout` orqali sessiyani yopdi |

---

## 6. Test Qamrovi

Phase 37 uchun `tests/test_v8_phase37.py` test to'plamida 14 ta avtomatlashtirilgan test to'liq muvaffaqiyatli o'tadi:

1. `test_01_auth_engine_init`: Dastlabki sozlamalar va holat
2. `test_02_password_hashing`: PBKDF2 va constant-time solishtirish
3. `test_03_challenge_issued_on_wake`: Wake pipeline orqali challenge so'rovi
4. `test_04_correct_password_opens_session`: To'g'ri parol bilan sessiya ochish
5. `test_05_session_ttl_and_expiry`: Sessiya TTL va avtomatik yopilish
6. `test_06_wrong_password_decrement`: Urinishlar kamayishi (3 -> 2 -> 1)
7. `test_07_three_failures_triggers_cooldown`: 3 ta xatodan so'ng 5-min cooldown
8. `test_08_cooldown_blocks_attempts`: Cooldown davrida qat'iy blokirovka
9. `test_09_cooldown_expiry`: Cooldown muddati o'tgach qayta urinish
10. `test_10_session_command_authorization`: Sessiya talab qiluvchi buyruqlar nazorati
11. `test_11_logout_and_session_close`: `/logout` va `/session` buyruqlari
12. `test_12_password_sanitization_in_logs`: Audit loglarda maxfiy so'zlarni yashirish
13. `test_13_mocked_telegram_auth_e2e`: To'liq muvaffaqiyatli E2E jarayoni
14. `test_14_mocked_telegram_auth_failure_and_cooldown_e2e`: To'liq xato va lockout E2E jarayoni

Jami Mikasa v8 testlari: **74 ta test, 100% PASS.**
