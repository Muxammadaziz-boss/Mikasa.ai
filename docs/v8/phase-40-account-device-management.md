# MIKASA AI v8.0.0 — PHASE 40
# Universal Account & Device Management 2.0
# Multi-User Identity → Account → Multi-Device Architecture

**Versiya:** v8.0.0  
**Faza:** Phase 40  
**Filial:** `dev-v8.0.0`  
**Holat:** Tayyor va to'liq tasdiqlangan (151/151 backend testlar, 15/15 frontend testlar, 0 flake8 ogohlantirishlari)

---

## 1. Tizim Arxitekturasi va Topologiya

Phase 40 — Mikasa AI arxitekturasini universal ko'p foydalanuvchili va ko'p qurilmali boshqaruv darajasiga ko'taradi.
Ushbu faza Telegram foydalanuvchilari, Mikasa hisoblari va kompyuter apparat vositalari o'rtasidagi to'liq egalik zanjirini kafolatlaydi:

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
            v                                           v
+-----------------------+                   +-----------------------+
|    Mikasa User A      |                   |    Mikasa User B      |
|    (id: "user_a")     |                   |    (id: "user_b")     |
+-----------------------+                   +-----------------------+
       |         |                                      |
       v         v                                      v
+-----------+ +-----------+                        +-----------+
| Device A1 | | Device A2 |                        | Device B1 |
| (Uy PC)   | | (Ofis PC) |                        | (MacBook) |
+-----------+ +-----------+                        +-----------+
       |            |                                    |
+---------------+ +---------------+                +---------------+
| Session &     | | Session &     |                | Session &     |
| Permissions   | | Permissions   |                | Permissions   |
+---------------+ +---------------+                +---------------+
```

### To'liq Egalik Zanjiri (Core Ownership Chain):
$$\text{TelegramIdentity} \longrightarrow \text{MikasaUser} \longrightarrow \text{Device} \longrightarrow \text{UserPermissionProfile} \longrightarrow \text{RemoteAuthSession}$$

> [!IMPORTANT]
> **No Global State Principle**: Tizimda global `CURRENT_USER` yoki `CURRENT_DEVICE` tushunchasi mavjud emas. Har bir foydalanuvchining tanlangan kompyuteri (`UserDeviceContext`) va sessiyalari mustaqil saqlanadi. Foydalanuvchi A o'z qurilmasini o'zgartirishi Foydalanuvchi B ning faol kontekstiga mutlaqo ta'sir qilmaydi.

---

## 2. Asosiy Ma'lumotlar Modellari (`core/v8/account_device.py`)

### 1. `MikasaUser`
- **Tavsif:** Foydalanuvchi hisobi. Barcha qurilmalar, Telegram bog'lanishlari va ruxsatlarning ildiz egasi.
- **Maydonlar:** `id` (str), `username` (str), `created_at` (float), `updated_at` (float), `status` ("ACTIVE", "DISABLED", "REVOKED"), `metadata` (dict).

### 2. `Device`
- **Tavsif:** Foydalanuvchiga tegishli apparat kompyuter qurilmasi. Apparat identifikatori (`device_id`) va inson tushunadigan do'stona nom (`name`) qat'iy ajratilgan.
- **Maydonlar:** `id` (UUID str), `mikasa_user_id` (str), `device_id` (apparat HW ID), `name` (do'stona nom, 1–64 belgi), `hostname` (str), `platform` (str), `agent_version` (str), `status` ("online", "offline", "standby", "revoked"), `created_at`, `last_seen_at`, `last_heartbeat_at`, `metadata`.
- **Konversiyalar:** `to_device_identity()` va `from_device_identity()` orqali Phase 35 `DeviceIdentity` bilan 100% orqaga qaytuvchanlik ta'minlangan.

### 3. `UserDeviceLink`
- **Tavsif:** Foydalanuvchi hisobi va apparat qurilmasi o'rtasidagi doimiy egalik bog'lanishi.
- **Maydonlar:** `id` (UUID), `mikasa_user_id`, `device_id`, `linked_at`, `status` ("ACTIVE", "REVOKED"), `metadata`.

### 4. `UserDeviceContext`
- **Tavsif:** Foydalanuvchining ayni damda faol tanlangan kompyuter konteksti. Har bir foydalanuvchi uchun alohida boshqariladi.
- **Maydonlar:** `user_id`, `device_id`, `selected_at`, `expires_at`.

---

## 3. AccountDeviceManager Imkoniyatlari

### 1. Do'stona Nom Berish va Validatsiya (Friendly Renaming)
- Har bir qurilmaga foydalanuvchi tomonidan qulay nom berilishi mumkin (masalan, "Uy Noutbuki", "Ofis Ish Stoli").
- Nom uzunligi: 1–64 belgi orasida bo'lishi shart, bosh va oxiridagi ortiqcha bo'shliqlar avtomatik tozalanadi.
- Bo'sh satrlar yoki begona foydalanuvchiga tegishli qurilmani qayta nomlash so'rovlari qat'iy rad etiladi.

### 2. Kaskadli Qurilmani Bekor Qilish (Cascading Revocation)
Qurilma o'chirib tashlanganda yoki bekor qilinganda (`revoke_device`):
1. **Device:** `status = "revoked"`, `is_revoked = True` belgilanadi.
2. **UserDeviceLink:** `status = "REVOKED"` ga o'tkaziladi.
3. **SessionManager:** Ushbu qurilma bo'yicha barcha faol autentifikatsiya sessiyalari zudlik bilan to'xtatiladi (`terminate_device_sessions`).
4. **PermissionStore:** Qurilmaning ruxsatlar profili tozalanadi / bekor qilinadi (`revoke_device_permissions`).
5. **UserDeviceContext:** Agar foydalanuvchida ushbu qurilma faol tanlangan bo'lsa, tanlov konteksti xavfsiz tozalanadi.

### 3. Aqlli Qidiruv va Qurilma Tanlash (`select_device_by_query`)
Telegram boti yoki CLI orqali qulay boshqarish uchun foydalanuvchi quyidagi usullar bilan qurilmani tanlay oladi:
- **Aniq Apparat ID yoki UUID bo'yicha:** masalan, `/select hw-pc-001`
- **Aniq Do'stona Nom bo'yicha:** masalan, `/select Ofis Kompyuteri`
- **Qisman / Substring bo'yicha:** masalan, `/select ofis`
- **Noaniqlikni Aniqlash (Ambiguity Detection):** Agar so'rov bir nechta qurilmaga mos kelsa (masalan, "Ofis PC 1" va "Ofis PC 2"), xatolik berilib, foydalanuvchidan aniqroq nom yoki ID so'raladi.

---

## 4. Universal Telegram Bot Integratsiyasi (`core/v8/universal_bot.py`)

Universal Telegram Bot (@MikasaUniversalBot) Phase 40 buyruqlari bilan boyitildi:

| Buyruq | Tavsif | Foydalanish |
|---|---|---|
| `/devices` | Foydalanuvchiga tegishli kompyuterlar ro'yxati va holatlarini ko'rsatish | `/devices` |
| `/select <nom_yoki_id>` | Boshqaruv uchun faol kompyuterni tanlash | `/select Ofis` yoki `/select dev-001` |
| `/account` | Hisob ma'lumotlari, ulangan kompyuterlar soni va faol tanlangan kompyuter | `/account` |
| `/status` | Tizim holati (Phase 39 / Phase 40) | `/status` |

---

## 5. REST API Endpoints (`core/api_server.py`)

Backend serveriga quyidagi 10 ta yangi va kengaytirilgan API marshrutlari kiritildi:

1. `GET /api/account` — Foydalanuvchi hisobi va qurilmalar xulosasi (`devices_count`, `active_sessions_count`, `selected_device`).
2. `GET /api/devices` va `GET /api/account/devices` — Foydalanuvchining faol qurilmalari ro'yxati va `selected_device_id`.
3. `GET /api/devices/{device_id}` — Muayyan qurilma tafsilotlari.
4. `PATCH /api/devices/{device_id}` — Qurilma do'stona nomini o'zgartirish (`{"name": "Yangi nom"}`).
5. `DELETE /api/devices/{device_id}` — Qurilmani kaskadli bekor qilish (Revoke).
6. `POST /api/devices/{device_id}/select` — Qurilmani faol tanlash.
7. `GET /api/devices/{device_id}/permissions` — Qurilmaning foydalanuvchiga tegishli ruxsatlar profili.
8. `GET /api/account/sessions` — Foydalanuvchining barcha faol masofaviy sessiyalari.
9. `POST /api/account/sessions/logout-all` — Foydalanuvchining barcha faol sessiyalarini darhol to'xtatish.

---

## 6. Frontend Dasturi (`mikasa-7`)

1. **`DevicesPage.tsx`:** Qurilmalarni ko'rish, holatini tekshirish, nomini o'zgartirish va bekor qilish uchun maxsus boshqaruv paneli.
2. **`DeviceSelector.tsx`:** Ilovaning har qanday joyidan turib kompyuterni bir bosishda almashtirish dropdown komponenti.
3. **`AccountPage.tsx`:** Kompyuterlar umumiy kartasi, Telegram bot holati va faol sessiyalarni to'xtatish tugmasi ("Barcha sessiyalardan chiqish").
4. **`Sidebar.tsx` va `App.tsx`:** `/devices` ("Qurilmalar") sahifasi marshrutga va navigatsiyaga ulandi.
5. **`backendService.ts`:** WebSocket voqealariga jonli obuna (`subscribe`), Phase 40 qurilma va sessiya metodlari.

---

## 7. Test va Verifikatsiya Xulosasi

- **Phase 40 Unit & Integration Testlar (`tests/test_v8_phase40.py`):** 30/30 testlar muvaffaqiyatli o'tdi.
- **Barcha v8 Regressiya Testlari (`test_v8*.py`):** 151/151 testlar muvaffaqiyatli o'tdi (0 xato).
- **Frontend Testlar (`mikasa-7`):** 15/15 testlar muvaffaqiyatli o'tdi.
- **Frontend Build (`npm run build`):** 0 xatolik bilan muvaffaqiyatli yig'ildi.
- **Kod Sifati va Linter (`flake8`):** 0 ogohlantirish, 0 xato.
