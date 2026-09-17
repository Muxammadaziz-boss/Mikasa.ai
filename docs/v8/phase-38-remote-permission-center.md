# MIKASA AI v8.0.0 — PHASE 38
# Online Remote Control + User Permission Center Architecture

**Versiya:** v8.0.0  
**Faza:** Phase 38  
**Filial:** `dev-v8.0.0`  
**Holat:** Tayyor va to'liq tasdiqlangan (100% testlar muvaffaqiyatli o'tgan)

---

## 1. Tizim Arxitekturasi va Ishlash Prinsipi

Phase 38 — Telegram bot, Mikasa User App (Web Frontend) va Windows PC Agent'ni yagona, o'ta xavfsiz va granular ruxsatlar bilan boshqariladigan masofaviy boshqaruv tizimiga birlashtiradi.

```
+------------------+         +----------------------------+
|  Telegram User   | <-----> |   Telegram Bot Gateway     |
+------------------+         +----------------------------+
                                          |
                                          v
+------------------+         +----------------------------+
|  Mikasa User App | <-----> |     Mikasa Remote Gateway  |
|  (Frontend UI)   |         |    (User Linking & Token)  |
+------------------+         +----------------------------+
                                          |
                                          v
                             +----------------------------+
                             |   User Permission Center   |
                             |  (Profile & Observer Bus)  |
                             +----------------------------+
                                          |
                                          v
                             +----------------------------+
                             |   Remote Session Auth      |
                             |   (Phase 37 Challenge)     |
                             +----------------------------+
                                          |
                                          v
                             +----------------------------+
                             |   Tool System 2.0 /        |
                             |   RemoteToolRegistry       |
                             +----------------------------+
                                          |
                                          v
                             +----------------------------+
                             |    Windows PC Agent        |
                             +----------------------------+
                                          |
                                          v
                             +----------------------------+
                             |    Windows PC Hardware     |
                             +----------------------------+
```

---

## 2. Hisobni Ulash (Account Linking)

Foydalanuvchi o'zining Telegram hisobini Mikasa ilovasidagi kompyuteriga bir martalik maxfiy kod orqali ulaydi:

1. **Pairing Token Generatsiyasi:**
   - Format: `MK-XXXXXX` (masalan: `MK-A7F92B`).
   - Amal qilish muddati (TTL): 300 soniya (5 daqiqa).
   - Saqlash: `UserLinkingStore` orqali xotirada va diskda (`data/v8_user_links.json`).
   - Bir martalik foydalanish: Kod bir marta ishlatilgach, avtomatik ravishda yaroqsiz holga keltiriladi (`is_used = True`).

2. **Telegram orqali faollashtirish:**
   - Buyruq: `/pair MK-XXXXXX` yoki `/link MK-XXXXXX`.
   - Telegram identity musbat butun son ekanligi qat'iy tekshiriladi (`TelegramIdentity.is_valid()`).
   - Ulanish muvaffaqiyatli bo'lgach, foydalanuvchi ruxsat berilganlar ro'yxatiga (`allowed_user_ids`) kiritiladi va qurilma foydalanuvchiga biriktiriladi (`pair_device`).

3. **Bog'lanishni bekor qilish:**
   - Buyruq: `/unpair`.
   - Barcha faol sessiyalar yopiladi va bog'lanish faolsizlantiriladi.

---

## 3. Foydalanuvchi Ruxsatlar Markazi (User Permission Center)

Har bir `foydalanuvchi + qurilma` juftligi uchun alohida `UserPermissionProfile` yuritiladi.

### 6 ta Ruxsat Toifasi va 16 ta Granular Ruxsat:

| Toifa | Ruxsat ID | Tavsif | Birlamchi Holat | Xavf Darajasi | Tasdiqlash |
|---|---|---|---|---|---|
| **SYSTEM** | `system.status` | PC online/offline holati va qisqa telemetriya | Faol | LOW | Yo'q |
| **SYSTEM** | `system.info` | CPU, RAM, disk va operatsion tizim ma'lumotlari | Faol | LOW | Yo'q |
| **SYSTEM** | `system.screenshot` | Ishchi stol ekran tasvirini olish | Faol | LOW | Yo'q |
| **APPS** | `app.list` | Ishlayotgan jarayonlar va ilovalar ro'yxati | Faol | LOW | Yo'q |
| **APPS** | `app.launch` | Faqat ruxsat etilgan dasturlarni ochish | Faol | MEDIUM | Yo'q |
| **APPS** | `app.close` | Tanlangan jarayonni xavfsiz to'xtatish | O'chiq | MEDIUM | **HA** |
| **FILES** | `file.list` | Ruxsat etilgan papkalardagi fayllar ro'yxati | Faol | LOW | Yo'q |
| **FILES** | `file.read` | Matnli fayllar tarkibini o'qish (hajm <= 64KB) | Faol | MEDIUM | Yo'q |
| **FILES** | `file.write` | Yangi fayl yaratish yoki yozish | O'chiq | MEDIUM | Yo'q |
| **FILES** | `file.delete` | Faylni o'chirib yuborish | O'chiq | HIGH | **HA** |
| **NETWORK** | `network.info` | Tarmoq adapterlari va IP manzillarini olish | Faol | LOW | Yo'q |
| **POWER** | `power.wake` | Wake-on-LAN orqali kompyuterni yoqish | Faol | LOW | Yo'q |
| **POWER** | `power.restart` | Kompyuterni masofadan qayta yuklash | Faol | HIGH | **HA** |
| **POWER** | `power.shutdown` | Kompyuterni masofadan to'liq o'chirish | O'chiq | HIGH | **HA** |
| **POWER** | `power.sleep` | Kompyuterni uyqu rejimiga kiritish | O'chiq | HIGH | **HA** |
| **ADVANCED**| `admin.tool.access` | Maxsus ma'muriy asboblarga kirish | O'chiq | CRITICAL | **HA** |

### Zudlik Bilan Kuchga Kirish (Zero-Restart Propagation):
- Ruxsatlar o'zgartirilganda (`grant_permission`, `revoke_permission`), serverni qayta ishga tushirish talab qilinmaydi.
- `PermissionStore` ichidagi `_subscribers` hodisa shinasi orqali barcha faol modullar (Telegram Gateway, Orchestrator, Agent) darhol yangilanadi.
- Ruxsat bekor qilingan zahoti keyingi buyruq bloklanadi: `❌ Bu amal uchun ruxsat berilmagan.`

---

## 4. Xavfsizlik va Buyruqlar Bajarilishi

1. **Ixtiyoriy Shell va Kod Bajarilishini To'liq Taqiq:**
   - `eval()`, `exec()`, `os.system()`, `subprocess.Popen(shell=True)` mutlaqo taqiqlangan.
   - Barcha masofaviy amallar faqat `RemoteToolRegistry`da ro'yxatdan o'tgan qat'iy tekshirilgan asboblar orqali amalga oshiriladi.
   - Ro'yxatdan tashqari har qanday buyruq `TOOL_NOT_FOUND` xatosi bilan to'xtatiladi.

2. **Yuqori Xavfli Amallar va Tasdiqlash (Confirmation Flow):**
   - Amallar: `power.shutdown`, `power.restart`, `power.sleep`, `app.close`, `file.delete`.
   - Foydalanuvchiga Telegramda ogohlantirish yuboriladi va inline tasdiqlash tugmalari chiqariladi.
   - Tasdiqlash muddati (TTL): 60 soniya.
   - `/confirm` orqali tasdiqlanganda amal bajariladi, `/cancel` yuborilganda darhol bekor qilinadi.

3. **Replay Attack va Nonce Himoyasi:**
   - Har bir buyruq uchun yagona kriptografik `nonce` hosil qilinadi.
   - Takrorlangan nonce bilan kelgan soxta buyruqlar `REPLAY_ATTACK_DETECTED` bilan bloklanadi.

4. **Audit Loglarida Maxfiylikni Himoyalash:**
   - `sanitize_event_data` funksiyasi barcha maxfiy kalitlarni (`pairing_code`, `password`, `secret_hash`, `raw_file_content`) loglarda `***REDACTED***` ga almashtiradi.

---

## 5. REST API va WebSocket Xaritalash

| Metod | URL | Tavsif |
|---|---|---|
| `GET` | `/api/remote/devices` | Barcha ro'yxatdan o'tgan qurilmalar va ularning holati |
| `GET` | `/api/remote/permissions?deviceId={id}` | Tanlangan qurilma uchun ruxsatlar katalogi va holati |
| `PUT` | `/api/remote/permissions` | Ruxsatlarni yangilash (grant / revoke) |
| `POST` | `/api/remote/pair/generate` | 5 daqiqalik bir martalik `MK-XXXXXX` kodini yaratish |
| `POST` | `/api/remote/unpair` | Telegram foydalanuvchisini qurilmadan uzish |
| `POST` | `/api/remote/session/lock` | Faol masofaviy sessiyani zudlik bilan bloklash |
| `POST` | `/api/remote/session/logout` | Faol masofaviy sessiyani yopish |
| `GET` | `/api/remote/audit` | Masofaviy audit jurnali (so'nggi 50 ta voqea) |

---

## 6. Frontend Foydalanuvchi Interfeysi (`mikasa-7`)

- **Marshrut:** `/remote` ("Masofaviy Boshqaruv").
- **Dizayn:** Zamonaviy Glassmorphic qorong'i mavzu (Cyan/Indigo neon urg'ulari).
- **Telegram Ulash Kartasi:**
  - `MK-XXXXXX` kodini bir klikda generatsiya qilish.
  - Jonli sekundomer taymeri (5:00 dan 0:00 gacha hisoblash).
  - Nusxalash tugmasi va Telegram botga to'g'ridan-to'g'ri havolalar.
- **Granular Ruxsat Switchlari:**
  - 6 ta toifa bo'yicha guruhlangan switchlar.
  - Optimistik UI yangilanishi va xatolikda avtomatik qaytarish (rollback).
  - Yuqori xavfli ruxsatlar yonida qizil "Tasdiqlash talab etiladi" nishoni.
- **Sessiya Boshqaruvi:**
  - "Sessiyani qulflash" va "Chiqish" tezkor harakat tugmalari.
- **Jonli Audit Logi:**
  - Barcha buyruqlar, avtorizatsiyalar va rad etishlar vaqt tamg'asi bilan ko'rinadi.

---

## 7. Testlash va Sifat Kafolati (QA)

Phase 38 doirasida 20 ta yangi qat'iy test yozildi va barcha mavjud fazalar bilan to'liq regressiya tekshiruvi o'tkazildi:

1. `tests/test_v8_remote.py` (Phase 35): **20/20 PASS**
2. `tests/test_v8_phase36.py` (Phase 36): **40/40 PASS**
3. `tests/test_v8_phase37.py` (Phase 37): **14/14 PASS**
4. `tests/test_v8_phase38.py` (Phase 38): **20/20 PASS**
5. **Jami:** **94 ta backend integratsiya testi muvaffaqiyatli (0 ta xato, 0 ta uzilish)**.
6. **Frontend:** `vitest` orqali 15/15 testlar muvaffaqiyatli o'tdi, TypeScript kompilyatsiyasi 0 ta xato bilan yakunlandi.
7. **Flake8 Linter:** 0 ta xato, 0 ta ogohlantirish.
