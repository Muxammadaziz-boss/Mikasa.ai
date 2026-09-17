# MIKASA AI v8.0.0 — PHASE 39
# Universal Telegram Bot ↔ Mikasa User App
# Multi-User Telegram Identity & OTP Account Linking

**Versiya:** v8.0.0  
**Faza:** Phase 39  
**Filial:** `dev-v8.0.0`  
**Holat:** Tayyor va to'liq tasdiqlangan (121/121 backend testlar, 15/15 frontend testlar, 0 flake8 xatolari)

---

## 1. Tizim Arxitekturasi va Topology

Phase 39 — Mikasa tizimida universal Telegram identifikatsiyasi va ko'p foydalanuvchili hisoblarni bog'lash (Multi-User Telegram Identity & OTP Account Linking) qatlamini yaratadi.

Bitta universal Telegram bot bir nechta Telegram foydalanuvchilariga xizmat ko'rsatadi va ularni o'zlarining tegishli Mikasa hisoblariga xavfsiz bog'laydi:

```
                  +--------------------------------+
                  |     Universal Telegram Bot     |
                  +--------------------------------+
                                  |
            +---------------------+---------------------+
            |                                           |
            v                                           v
+-----------------------+                   +-----------------------+
|  Telegram Identity A  |                   |  Telegram Identity B  |
|  (tg_user_id: 10101)  |                   |  (tg_user_id: 20202)  |
+-----------------------+                   +-----------------------+
            |                                           |
    Salted OTP / Token                          Salted OTP / Token
            |                                           |
            v                                           v
+-----------------------+                   +-----------------------+
|    Mikasa User A      |                   |    Mikasa User B      |
|   (User App UI /      |                   |   (User App UI /      |
|    Desktop Client)    |                   |    Desktop Client)    |
+-----------------------+                   +-----------------------+
```

> [!IMPORTANT]
> **Strict Isolation Principle**: Ushbu bosqichda FAQAT **Mikasa User App ↔ Universal Telegram Bot** ulanishi amalga oshirildi. PC Agentlar va apparat vositalari Phase 39 da bog'lanmaydi (PC masofaviy boshqaruvi keyingi fazalarda birlashtiriladi).

---

## 2. Kanonik Identifikatsiya (Canonical Telegram Identity)

- **Asosiy kalit:** Telegram raqamli identifikatori (`telegram_user_id`) qat'iy musbat butun son bo'lishi shart.
- **Foydalanuvchi nomlaridan voz kechish:** Telegram `username` doimiy emas va o'zgarishi yoki bo'sh bo'lishi mumkin. Shuning uchun `username` faqat yordamchi metadata sifatida saqlanadi, hech qachon birlamchi identifikator sifatida ishlatilmaydi.
- **Validatsiya:** Manfiy sonlar, 0, bo'sh satrlar, matnli belgilar va boolean qiymatlar qat'iy rad etiladi.

---

## 3. Xavfsiz Salted OTP va Bog'lash Oqimi (Account Linking Flow)

```
[Mikasa User App]                       [TelegramIdentityManager]                   [Telegram Bot]
       |                                           |                                      |
       |-- POST /api/telegram/link/start --------->|                                      |
       |   (mikasa_user_id: "admin")               |                                      |
       |                                           |-- 6-xonali tasodifiy OTP generatsiya |
       |                                           |-- 16-bayt kriptografik salt yaratish |
       |                                           |-- SHA-256(salt:otp) xeshini hisoblash|
       |                                           |-- link_token & deep-link yaratish    |
       |<-- {otp: "583921", deep_link, ...} -------|                                      |
       |                                                                                  |
       |-- [Variant A: Foydalanuvchi OTP kodni botga yuboradi] -------------------------->|
       |-- [Variant B: t.me/bot?start=<link_token> havolasini bosadi] ------------------->|
       |                                                                                  |
       |                                           |<-- verify_otp / verify_token --------|
       |                                           |-- hmac.compare_digest()              |
       |                                           |-- Single-use: is_used = True         |
       |                                           |-- Max 5 attempts & 300s TTL check    |
       |<-- WS: PAIRING_VERIFIED & CONNECTED ------|                                      |
       |                                           |-- OK: Bog'landi -------------------->|
```

### Xavfsizlik Kafolatlari:
1. **Ochiq matndagi OTP saqlanmaydi:** Ochiq matndagi 6 xonali OTP faqatgina API javobida mijozga qaytariladi. Diskda, bazada va xotiradagi doimiy yozuvlarda faqat `otp_hash` va 16-baytli `salt` saqlanadi.
2. **Replay Himoyasi (Single-Use):** Tasdiqlash kodi yoki havola bir marta muvaffaqiyatli ishlatilgandan so'ng holati `VERIFIED` ga o'tadi va ikkinchi marta foydalanish taqiqlanadi.
3. **Muddati (TTL):** Har bir so'rov yaratilgandan boshlab aniq 300 soniya (5 daqiqa) amal qiladi.
4. **Blokirovka (Max 5 attempts):** Noto'g'ri kod kiritilganda `attempt_count` oshirib boriladi. 5 ta ketma-ket xato urinishdan so'ng so'rov `FAILED` holatiga o'tadi va to'liq bloklanadi.
5. **Rate Limiting:** Har bir Mikasa hisobi uchun 10 daqiqa ichida maksimal 3 ta OTP generatsiya qilish mumkin (`TELEGRAM_LINK_RATE_LIMITED`).
6. **Constant-time taqqoslash:** Timing attack (vaqt bo'yicha hujumlar) ning oldini olish uchun xeshlarni tekshirishda `hmac.compare_digest` ishlatiladi.
7. **Audit Log Sanitsiyalash:** Barcha loglar va audit hodisalarida `otp`, `otp_hash`, `link_token` qiymatlari avtomatik ravishda `***REDACTED***` bilan niqoblanadi.

---

## 4. Universal Telegram Bot Buyruqlari

Universal bot foydalanuvchilarni ularning `telegram_user_id` si bo'yicha qat'iy ajratilgan holatda (isolated state) boshqaradi:

| Buyruq | Tavsif |
|---|---|
| `/start` | Botni ishga tushirish, xush kelibsiz xabari va bosqichma-bosqich qo'llanma |
| `/start <link_token>` | Deep-link orqali hisobni bir zumda avtomatik bog'lash |
| `/link <kod>` | Mikasa ilovasidagi 6 xonali OTP orqali hisobni bog'lash |
| `<6 xonali raqam>` (masalan: `583921`) | To'g'ridan-to'g'ri OTP kiritishni avtomatik aniqlash va bog'lash |
| `/unlink` | Telegram hisobini Mikasadan uzish (decouple) |
| `/account` | Bog'langan Mikasa hisobi, Telegram ID, username va sanani ko'rsatish |
| `/status` | Botning tarmoqdagi holati, faol foydalanuvchilar soni va versiyasi |
| `/help` | Botdagi barcha buyruqlar va ulanish yo'riqnomasi |

---

## 5. REST & WebSocket API Marshrutlari

### 1. `POST /api/telegram/link/start`
Yangi bir martalik OTP va Telegram deep-link generatsiya qilish.
- **So'rov:** `{"mikasa_user_id": "admin"}`
- **Javob:**
  ```json
  {
    "ok": true,
    "request_id": "c1b0d22f-2aff-48e7-a5db-39e823709a5c",
    "otp": "583921",
    "link_token": "qTz9_X...k3",
    "deep_link": "https://t.me/MikasaUniversalBot?start=qTz9_X...k3",
    "expires_at": 1726615200.0,
    "ttl_seconds": 300,
    "bot_username": "MikasaUniversalBot"
  }
  ```

### 2. `POST /api/telegram/link/verify`
OTP kodni tasdiqlash va Telegram ID bilan bog'lash.
- **So'rov:** `{"otp": "583921", "telegram_user_id": 123456789, "username": "ali_dev", "first_name": "Ali"}`
- **Javob:** `{"ok": true, "message": "OK: ...", "link": {...}}`

### 3. `GET /api/telegram/link/status`
Kutilayotgan so'rov yoki faol hisob holatini tekshirish.
- **So'rov parametrlar:** `?request_id=...&mikasa_user_id=admin`
- **Javob:** `{"ok": true, "status": "CONNECTED", "is_linked": true, "telegram_user_id": 123456789}`

### 4. `POST /api/telegram/unlink`
Telegram va Mikasa bog'lanishini bekor qilish.
- **So'rov:** `{"mikasa_user_id": "admin"}`
- **Javob:** `{"ok": true, "message": "Telegram hisobi muvaffaqiyatli uzildi"}`

### 5. `GET /api/telegram/account`
Foydalanuvchining ulangan Telegram profili va tafsilotlari.
- **So'rov parametrlar:** `?mikasa_user_id=admin`

### 6. `GET /api/telegram/status`
Universal botning konfiguratsiyasi va tizim statistikasi.

### WebSocket Tadbirlari (`broadcast_ws`):
- `PAIRING_CREATED` — Yangi pairing so'rovi va taymer boshlanganda
- `PAIRING_WAITING` — Foydalanuvchi kodni kiritishi kutilayotganda
- `PAIRING_VERIFIED` — Kod muvaffaqiyatli tekshirilganda
- `PAIRING_FAILED` — Noto'g'ri urinish yoki xatolik yuz berganda
- `PAIRING_EXPIRED` — 300 soniyalik vaqt tugaganda
- `TELEGRAM_CONNECTED` — Telegram hisobi tizimga to'liq ulanganda
- `TELEGRAM_DISCONNECTED` — Telegram hisobi uzilganda

---

## 6. Frontend Foydalanuvchi Interfeysi (`mikasa-7`)

`TelegramIntegrationPage.tsx` quyidagi holat mashinasini (State Machine) to'liq qo'llab-quvvatlaydi:
- `NOT_CONNECTED` — Chiroyli taklif kartasi, imkoniyatlar sharhi va "Bog'lanish Kodini Olish" tugmasi.
- `PAIRING` & `WAITING_FOR_OTP` — 300 soniyalik jonli taymer, katta monospaced shriftda ko'rsatilgan 6 xonali OTP, "Nusxa olish" tugmasi va "Telegram orqali ochish" deep-link tugmasi.
- `CONNECTED` — Yashil rangdagi xavfsizlik qalqoni, Telegram ID, foydalanuvchi nomi, ulangan vaqt va "Bog'lanishni uzish" amali.
- `EXPIRED` & `FAILED` — Vaqt tugaganda yoki xato bo'lganda ogohlantirish va bir tugma bilan yangi kod olish.
- `Sidebar` navigatsiyasida "Telegram Bot" bo'limi va `/telegram` yo'nalishi.

---

## 7. Testlash va Sifat Kafolati (Test Matrix)

| Test Nomi | Tavsif | Natija |
|---|---|---|
| `test_01_telegram_identity_canonical_numeric_id` | Faqat musbat butun son qabul qilinishi, string/salbiy qiymatlar rad etilishi | PASS |
| `test_02_telegram_identity_serialization` | `to_dict` va `from_dict` to'liq ma'lumot saqlanishi | PASS |
| `test_03_otp_generation_format_and_entropy` | 6 xonali [100000, 999999] diapazon va yuqori entropiya | PASS |
| `test_04_plaintext_otp_not_persisted` | Ochiq OTP diskda/bazada saqlanmasligi, faqat xesh saqlanishi | PASS |
| `test_05_link_token_generation` | Kriptografik xavfsiz URL-safe token va deep-link formati | PASS |
| `test_06_otp_verification_success` | To'g'ri OTP va musbat TG ID bilan faol `UserTelegramLink` yaratilishi | PASS |
| `test_07_constant_time_comparison` | `hmac.compare_digest` orqali doimiy vaqtli xesh tekshiruvi | PASS |
| `test_08_single_use_otp_replay_protection` | Kod ikkinchi marta ishlatilganda rad etilishi (`CODE_ALREADY_USED`) | PASS |
| `test_09_expired_otp_rejection` | 300 soniyadan so'ng kod rad etilishi (`CODE_EXPIRED`) | PASS |
| `test_10_invalid_otp_attempt_counter` | Noto'g'ri kiritilganda hisoblagich oshishi va qolgan urinishlar ko'rsatilishi | PASS |
| `test_11_max_attempts_lockout` | 5 ta xato urinishdan so'ng so'rov `FAILED` ga o'tishi va bloklanishi | PASS |
| `test_12_rate_limiting_otp_generation` | 10 daqiqa ichida maksimal 3 ta kod so'rash cheklovi | PASS |
| `test_13_deep_link_token_verification` | Deep-link token orqali to'g'ridan-to'g'ri ulanish | PASS |
| `test_14_single_use_link_token` | Deep-link tokenini takroriy ishlatish blokirovkasi | PASS |
| `test_15_unlink_flow` | Bog'lanishni uzish va holatni `REVOKED` ga o'tkazish | PASS |
| `test_16_pending_requests_cancelled_on_unlink` | Hisob uzilganda kutilayotgan so'rovlar bekor qilinishi | PASS |
| `test_17_multi_user_isolation` | Bir nechta foydalanuvchilarning ma'lumotlari bir-biriga aralashmasligi | PASS |
| `test_18_bot_start_without_token` | `/start` buyrug'ida o'zbek tilida yo'riqnoma berilishi | PASS |
| `test_19_bot_start_with_token` | `/start <token>` orqali avtomatik bog'lanish | PASS |
| `test_20_bot_link_command_with_code` | `/link <otp>` orqali hisobni bog'lash | PASS |
| `test_21_bot_link_command_prompt` | `/link` bo'sh kiritilganda kod so'ralishi | PASS |
| `test_22_bot_raw_otp_message` | 6 xonali raqam yuborilganda OTP deb qabul qilinishi | PASS |
| `test_23_bot_account_command` | `/account` buyrug'ida ulangan/ulanmagan holat tafsilotlari | PASS |
| `test_24_bot_unlink_command` | `/unlink` buyrug'i orqali hisobni botdan uzish | PASS |
| `test_25_bot_status_and_help` | `/status` va `/help` buyruqlari chiqishi | PASS |
| `test_26_audit_logging_secret_redaction` | Loglarda `otp`, `otp_hash`, `link_token` yashirilishi | PASS |
| `test_27_full_e2e_otp_linking_lifecycle` | To'liq E2E hayot davri (Start -> OTP -> Bot -> Linked -> Check -> Unlink) | PASS |
