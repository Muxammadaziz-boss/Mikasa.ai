# Phase 42 — Secure PC Agent Enrollment & Pairing System

## 1. Umumiy Arxitektura va Maqsad

Mikasa AI v8.0.0 loyihasining 42-bosqichida (Phase 42) foydalanuvchining shaxsiy Windows kompyuter agentini (PC Agent) o'zining Mikasa hisobiga asimmetrik kriptografiya (Ed25519) va qisqa muddatli juftlash kodlari (Pairing Codes) orqali xavfsiz tarzda biriktirish (Enrollment) va autentifikatsiya qilish tizimi to'liq ishlab chiqildi.

### Identity va Ruxsat Zanjiri
```
Supabase Auth (Cloud Identity Provider)
       │
       ▼
Supabase auth.users (UUID `sub`)
       │
       ▼
Mikasa public.profiles (Foydalanuvchi profili)
       │
       ├── Telegram Identity (Phase 39)
       │
       ├── Devices Enrollment (Phase 42 — Ed25519 Cryptographic Pairing)
       │         │
       │         ▼
       │   Device Credentials (public_key: 32-bayt Ed25519, OS DPAPI)
       │         │
       │         ▼
       │   Device Sessions (Agent ↔ Server xavfsiz aloqa kanali)
       │
       ├── Permission Profile (Phase 38 — RBAC va Safe Defaults)
       │
       ▼
RemoteAuthSession (Apparat darajasidagi masofaviy boshqaruv — Screen, Mouse, Terminal)
       │
       ▼
Windows PC Agent (Hardware Execution Node)
```

---

## 2. Asosiy Xavfsizlik Invariantlari (Security Invariants)

1. **Device Enrolled ≠ Remote Session Authorized (Qat'iy ajratilganlik qoidasi):**
   - Kompyuterni hisobga muvaffaqiyatli biriktirish (enrollment) faqat apparat identifikatsiyasini va Ed25519 ommaviy kalitini tasdiqlaydi.
   - Bu holat avtomatik ravishda kompyuterni masofaviy boshqarish (Remote Control) huquqini BERMAYDI.
   - Masofaviy amallarni bajarish uchun foydalanuvchi alohida Permission Center orqali ruxsat berishi va har bir masofaviy sessiya uchun RemoteAuth challenge-response orqali `RemoteAuthSession` hosil qilinishi shart.

2. **Nol Ochiq Matn Saqlash (Zero Plaintext Code & Private Key Storage):**
   - Juftlash uchun generatsiya qilingan 6-xonali tasodifiy kod server bazasida yoki fayl tizimida HECH QACHON ochiq matnda saqlanmaydi.
   - Serverda faqat tasodifiy tuzlangan (salted) SHA-256 xeshi saqlanadi: `SHA256(salt + ":" + code)`.
   - Agentning Ed25519 shaxsiy kaliti (`private_key`) hech qachon serverga yoki tarmoqqa uzatilmaydi. U Windows DPAPI orqali foydalanuvchi hisobining shaxsiy kaliti bilan shifrlanib, faqat lokal xotirada saqlanadi.

3. **Vaqt va Urinish Cheklovlari (TTL & Brute-force Lockout):**
   - Juftlash kodi 5 daqiqa (300 soniya) davomida amal qiladi.
   - Kodni noto'g'ri kiritish bo'yicha maksimal 5 ta urinishga ruxsat etiladi (`MAX_ATTEMPTS = 5`). 5-urinishdan so'ng sessiya `FAILED` holatiga o'tadi va bloklanadi.
   - Kod faqat bir marta ishlatilishi mumkin (Single-Use).

4. **Kriptografik Chaqiriq-Javob va Replay Hujumlaridan Himoya (Replay Protection):**
   - Agent autentifikatsiyasi uchun har safar 32-baytlik kriptografik tasodifiy chaqiriq (nonce) va 60 soniyalik TTL beriladi.
   - Chaqiriq tekshirilishi bilanoq darhol `is_used = True` qilinadi, bu esa takroriy (replay) hujumlarni mutlaqo istisno qiladi.
   - Imzo kanonik formatdagi deterministik xabar ustida tekshiriladi:
     `device_id|nonce|timestamp|protocol_version`

5. **Xavfsiz Boshlang'ich Ruxsatlar (Safe Default Permissions):**
   - Yangi ulangan kompyuter uchun sukut bo'yicha faqat xavfsiz o'qish va telemetriya buyruqlari ruxsat etiladi (`system.status`, `system.info`, `heartbeat`).
   - Xavfli destruktiv buyruqlar (`power.shutdown`, `power.restart`, `file.delete`, `terminal.execute`) sukut bo'yicha qat'iyan bloklanadi.

6. **Kaskadli Bekor Qilish (Cascading Revocation):**
   - Foydalanuvchi kompyuterni o'chirganda (revoke), unga tegishli barcha `DeviceCredential` bekor qilinadi, faol `DeviceSession`lar to'xtatiladi va kutilayotgan barcha pairing sessiyalari bekor qilinadi.

---

## 3. Komponentlar Arxitekturasi

### A. `core/v8/device_pairing.py`
- `DevicePairingSession`: Juftlash sessiyasi modeli.
- `DevicePairingManager`: 6-xonali raqamli kod yaratish, xesh hisoblash, vaqt va urinishlarni nazorat qilish, sessiyani tasdiqlash va bekor qilish.

### B. `core/v8/device_enrollment.py`
- `DeviceCredential`: Qurilmaning ommaviy kaliti (Ed25519 32-byte / 64-hex char) va metama'lumotlari.
- `SecureCredentialStore`, `WindowsCredentialStore`, `MockCredentialStore`: Windows DPAPI (`ctypes.windll.crypt32.CryptProtectData`) yordamida lokal shifrlash ombori.
- `DeviceEnrollmentManager`: Qurilmalarni `AccountDeviceManager`ga kiritish, xavfsiz standart ruxsatlarni belgilash va kaskadli revocation.

### C. `core/v8/device_auth.py`
- `DeviceAuthChallenge`: 32-baytlik bir martalik tasodifiy chaqiriq (nonce, TTL: 60s).
- `DeviceSession`: Autentifikatsiyadan o'tgan agent aloqa kanali sessiyasi (`token`, `expires_at`).
- `DeviceAuthManager`: Nonce generatsiyasi, kanonik formatlash, Ed25519 imzo verifikatsiyasi va replay protection.

### D. `core/v8/device_agent_crypto.py`
- `DeviceAgentCrypto`: PC Agent mijoz yordamchisi. Ed25519 kalitlarini hosil qiladi, lokal omborda saqlaydi va chaqiriqlarni imzolaydi.

---

## 4. REST API Endpointlari

| Metod | Endpoint | Tavsif | Autentifikatsiya |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/devices/pairing/start` | 6-xonali yangi juftlash kodini hosil qilish | Foydalanuvchi (Bearer / Header) |
| `GET` | `/api/devices/pairing/{id}` | Juftlash sessiyasi holatini tekshirish | Foydalanuvchi (Bearer / Header) |
| `POST` | `/api/devices/pairing/{id}/cancel` | Juftlash sessiyasini bekor qilish | Foydalanuvchi (Bearer / Header) |
| `POST` | `/api/devices/pairing/complete` | Agent tomonidan kod va Ed25519 public key yuborish | Ochiq (Pairing Code orqali) |
| `POST` | `/api/devices/{device_id}/challenge` | Agent uchun 32-baytlik bir martalik nonce olish | Ochiq (Enrolled Device) |
| `POST` | `/api/devices/{device_id}/authenticate` | Imzolangan chaqiriqni yuborib `DeviceSession` olish | Ed25519 Raqamli Imzo |

---

## 5. Web UI (Mikasa Frontend)

Foydalanuvchi uchun `DevicesPage.tsx` sahifasida 3 bosqichli interaktiv juftlash oynasi (Modal Wizard) taqdim etildi:
1. **1-qadam (Kod olish):** Foydalanuvchi "+ Kompyuter qo'shish" tugmasini bosadi, xavfsizlik kafolatlari ko'rsatiladi va kod generatsiya qilinadi.
2. **2-qadam (Kodni ko'rsatish & Taymer):** Monospace Cyberpunk uslubida 6 xonali kod (`123 456`), nusxalash tugmasi, faol `04:59` teskari taymer va polling indikatori namoyish etiladi.
3. **3-qadam (Tasdiqlash & Nom berish):** Windows agenti ulangach, aniqlangan kompyuter xususiyatlari (hostname, platform, ID) ko'rsatiladi, do'stona nom kiritiladi va ulanish yakunlanadi.
