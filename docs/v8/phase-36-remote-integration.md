# MIKASA AI v8.0.0 — PHASE 36: REMOTE INTEGRATION DOCUMENTATION
## Real Telegram ↔ Mikasa ↔ Windows PC Agent Integration

---

## 1. Architecture

Phase 36 introduces a production-ready, highly secure, and resilient integration architecture bridging Telegram Bot API, the Mikasa Central Intelligence System, and the local Windows PC Agent.

```
                    ┌─────────────────────────┐
                    │      TELEGRAM USER      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Telegram Bot API Server │
                    └────────────┬────────────┘
                                 │ Long Polling / Webhook
                                 ▼
                 ┌───────────────────────────────┐
                 │  core/v8/telegram_gateway.py  │
                 │  - Async Polling & Transport  │
                 │  - Uzbek NLP & Slash Commands │
                 │  - Inline Keyboards & Callback│
                 │  - Progress Indicators        │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │ core/v8/remote_orchestrator.py│
                 │ - Authentication Verification │
                 │ - Device Registry Resolution  │
                 │ - Planning 2.0 DAG Dispatch   │
                 │ - Confirmation Flow Manager   │
                 └──────┬─────────────────┬──────┘
                        │                 │
            [PC OFFLINE]│                 │[PC ONLINE]
                        ▼                 ▼
          ┌─────────────────────┐  ┌───────────────────────────┐
          │  core/v8/wol.py     │  │ core/intelligence/        │
          │  - WakeOnLanManager │  │ - PermissionEngine        │
          │  - Magic Packet     │  │ - AgentLoop (PLAN-ACT)    │
          │  - WakeRelay (UDP)  │  │ - Tool System 2.0         │
          └──────────┬──────────┘  └─────────────┬─────────────┘
                     │                           │
                     ▼                           ▼
          ┌─────────────────────┐  ┌───────────────────────────┐
          │     WINDOWS PC      │◄─┤   core/v8/pc_agent.py     │
          │  - Hardware NIC     │  │   - Heartbeat & Metrics   │
          │  - Bios WoL Power   │  │   - Idempotent Execution  │
          └─────────────────────┘  └───────────────────────────┘
```

---

## 2. Telegram Setup

1. **Bot yaratish**:
   - Telegramda `@BotFather` orqali `/newbot` buyrug'ini bering.
   - Bot nomini va unikal username tanlang (masalan, `MyMikasaBot`).
   - Berilgan bot tokenini oling (`123456789:ABCdef...`).

2. **Admin Telegram ID ni aniqlash**:
   - Telegramda `@userinfobot` yoki `@myidbot` ga `/start` yuborib o'zingizning raqamli ID raqamingizni oling (masalan, `987654321`).

3. **Konfiguratsiya**:
   - `.env.example` faylidan nusxa olib `.env` yarating:
     ```bash
     cp .env.example .env
     ```
   - `.env` ichiga olingan qiymatlarni yozing:
     ```env
     TELEGRAM_BOT_TOKEN=123456789:ABCdef...
     TELEGRAM_ADMIN_ID=987654321
     TELEGRAM_ALLOWED_USERS=987654321
     ```

---

## 3. Environment Variables

| O'zgaruvchi | Tavsif | Default qiymat |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API maxfiy tokeni | - |
| `TELEGRAM_ADMIN_ID` | Bosh administratorning Telegram raqamli IDsi | - |
| `TELEGRAM_ALLOWED_USERS` | Ruxsat berilgan qo'shimcha foydalanuvchilar (vergul bilan) | - |
| `WOL_ENABLED` | Wake-on-LAN faolligi | `true` |
| `WOL_BROADCAST_IP` | UDP broadcast IP manzili | `255.255.255.255` |
| `WOL_PORT` | UDP port | `9` |
| `WOL_RETRY_COUNT` | WoL urinishlar soni | `3` |
| `WOL_TIMEOUT` | WoL uyg'onish kutish chegarasi (soniya) | `10.0` |
| `TARGET_PC_MAC` | Nishon kompyuterning jismoniy MAC manzili | `00:11:22:33:44:55` |
| `AGENT_HEARTBEAT_INTERVAL`| Heartbeat yuborish oraliq vaqti (soniya) | `10.0` |
| `AGENT_MAX_BACKOFF` | Qayta ulanish maksimal kutish vaqti | `30.0` |
| `HEARTBEAT_STALE_TIMEOUT` | Offline deb hisoblash vaqti | `60.0` |
| `ENVELOPE_TTL_SECONDS` | Buyruq konvertining amal qilish muddati | `300` |
| `CONFIRMATION_TTL_SECONDS`| Xavfli amalni tasdiqlash muddati | `60` |

---

## 4. Device Pairing

Har bir kompyuter agenti va Telegram hisob o'rtasida ishonchli kriptografik bog'lanish o'rnatiladi:
1. **Apparat Fingerprint**:
   - `DeviceIdentityManager.compute_fingerprint()` orqali kompyuterning apparat xarakteristikalari (hostname, arxitektura, MAC) asosida 64 belgili SHA-256 xesh hisoblanadi.
   - Boshqa qurilma bir xil `device_id` bilan o'zini tanitmoqchi bo'lsa (impersonation), `DeviceRegistry` buni aniqlab, darhol bloklaydi (`DEVICE_AUTH_FAILED`).
2. **Pairing Token**:
   - Administrator `/pair <token>` buyrug'i orqali yoki avtomatik generatsiya qilingan kriptografik token bilan kompyuterni o'z hisobiga bog'laydi (`DevicePairingRecord`).
   - Pairing ma'lumotlari persistent xotirada (`devices.json`) xavfsiz saqlanadi.

---

## 5. PC Agent

`MikasaPCAgent` xizmati:
- Kompyuter yuklanganda fonda (background daemon/service) ishga tushadi.
- Holat o'tishlari: `INITIALIZING` → `REGISTERING` → `AUTHENTICATING` → `ONLINE`.
- Gateway bilan aloqa uzilsa, eksponensial backoff (`1s → 2s → 4s → ... → 30s`) bilan avtomatik qayta ulanadi (`reconnect`).
- Hech qanday ixtiyoriy shell kod (`eval`, `exec`, `subprocess`) qabul qilmaydi. Barcha amallar Mikasa `Tool System 2.0` va `PermissionEngine` orqali tekshirilib, xavfsiz chaqiriladi.

---

## 6. Heartbeat

- **Interval**: Har 10 soniyada agent Gatewayga `HeartbeatPayload` yuboradi.
- **Payload tarkibi**: `device_id`, `timestamp`, `agent_version`, `state`, `metrics` (CPU, RAM, Uptime).
- **Offline aniqlash**: Agar 60 soniya ichida (yoki testlarda sozlangan `stale_timeout`) heartbeat kelmasa, `HeartbeatManager` qurilmani avtomatik `DeviceState.OFFLINE` holatiga o'tkazadi va hodisa audit jurnaliga yoziladi.

---

## 7. Wake-on-LAN (WoL)

- **Standart Magic Packet**: 6 ta `0xFF` bayti ketidan nishon MAC manzilining 16 marta takrorlanishi (jami 102 bayt).
- **Abstraksiya**:
  - `WakeRelay`: Tarmoq orqali paket yetkazib beruvchi abstrakt interfeys.
  - `LocalBroadcastRelay`: Mahalliy tarmoqda to'g'ridan-to'g'ri UDP broadcast (port 9 yoki 7) orqali paket uzatuvchi.
  - `MockWakeRelay`: Tarmoqqa murojaatsiz, mustaqil test sinovlari uchun.
- **Retry**: Tarmoq xatosi yuz berganda avtomatik qayta urinish.

---

## 8. Remote Commands & UX

Telegram orqali quyidagi buyruqlar va o'zbek tilidagi tabiiy jumlalar qo'llab-quvvatlanadi:

1. **Holatni tekshirish**:
   - Buyruqlar: `/pc`, `/status`, `🟢 PC Status`, `kompyuterim yoqilganmi?`, `kompyuter holati`.
   - Javob: Qurilma holati, tizim, IP/MAC, oxirgi faollik va interaktiv inline tugmalar.

2. **Kompyuterni yoqish (Uyg'otish)**:
   - Buyruqlar: `/wake`, `⚡ Wake PC`, `kompyuterni yoq`, `kompyuterni uyg'ot`.
   - Javob: 5 bosqichli vizual progress bar:
     - `[1/5] Device holati tekshirilmoqda...`
     - `[2/5] Wake-on-LAN yuborilmoqda...`
     - `[3/5] Heartbeat kutilmoqda...`
     - `[4/5] Device online tasdiqlanmoqda...`
     - `[5/5] Status olinmoqda...`
     - `🟢 Kompyuter online bo'ldi. 🤖 Mikasa Agent: READY`

3. **Yuqori xavfli amallar**:
   - Buyruqlar: `/restart`, `/shutdown`, `kompyuterni o'chir`.
   - Javob: `⚠️ DIQQAT! Yuqori xavfli amal...` xabari va tasdiqlash tugmalari (`✅ Ha, bajarilsin`, `❌ Bekor qilish`).

---

## 9. Permissions & Confirmation Flow

- Har bir buyruq `core/intelligence/permission.py` orqali baholanadi.
- Xavfli amallar (`shutdown`, `restart`, `system_control`) uchun `confirmation_required: True` belgilanadi.
- Tasdiqlash so'rovi 60 soniya (`CONFIRMATION_TTL_SECONDS`) amal qiladi.
- Muddati o'tgan yoki bekor qilingan tasdiqlashlar ikkinchi marta bajarilmaydi.

---

## 10. Security & Threat Mitigation

| Hujum turi | Himoya mexanizmi |
| :--- | :--- |
| **Unauthorized Access** | Allowlist va raqamli Telegram ID tekshiruvi. Begona so'rovlar rad etilib, audit qilinadi. |
| **Replay Attack** | Har bir konvertda kriptografik 16-belgili `nonce` va `expires_at` (TTL). Takrorlangan nonce to'siladi. |
| **Duplicate Requests** | Idempotency Engine: Bajarilgan buyruqlar keshlanadi, qayta kelganda ikkinchi marta bajarilmaydi. |
| **Device Impersonation** | SHA-256 apparat fingerprint tekshiruvi. |
| **Command Injection** | Arbitrary shell, `eval()`, `exec()` qat'iyan taqiqlangan. Faqat Tool Registry orqali chaqiriladi. |
| **Credential Leakage** | Telegram tokenlar, parollar va API kalitlar loglarda avtomatik niqoblanadi (`***MASKED***`). |
| **Denial of Service** | Sliding-window `RateLimiter` (default: daqiqasiga 30 ta so'rov). |

---

## 11. Troubleshooting

- **Kompyuter uyg'onmayapti (`WAKE_TIMEOUT`)**:
  1. BIOS/UEFI sozlamalarida "Wake on LAN" yoki "PCI-E Power On" yoqilganligini tekshiring.
  2. Windows Device Manager ichida tarmoq kartasi sozlamalarida "Allow this device to wake the computer" va "Only allow a magic packet to wake the computer" belgilanganligini ko'ring.
  3. `.env` dagi `TARGET_PC_MAC` to'g'riligini tekshiring.
- **Telegram bot javob bermayapti**:
  1. `TELEGRAM_BOT_TOKEN` to'g'ri kiritilganligini va bot `@BotFather`da faolligini tekshiring.
  2. Sizning Telegram ID `TELEGRAM_ADMIN_ID` ga to'g'ri yozilganligini tekshiring.
- **Agent offline holatda turibdi**:
  1. Agent servisi ishlayotganligini tekshiring: `python main.py` yoki servis holati.
  2. Mahalliy tarmoq yoki xavfsizlik devori (firewall) portlarini tekshiring.

---

## 12. Testing

Barcha testlar hech qanday haqiqiy Telegram tokeni yoki jonli tarmoq talab qilmaydi (100% izolyatsiyalangan mocklar):

```bash
# 1. Phase 36 to'liq integratsiya testlari (40 ta test)
python -m unittest tests/test_v8_phase36.py

# 2. Phase 35 testlari (20 ta test)
python -m unittest tests/test_v8_remote.py

# 3. Backend to'liq regressiya (126 ta test)
python -m unittest tests/test_intelligence_core.py tests/test_e2e_lifecycle.py tests/test_windows_qa.py tests/test_stress.py tests/test_logging.py tests/test_security_api.py tests/test_account_api.py tests/test_plugins_api.py tests/test_scheduler_api.py tests/test_memory_api.py tests/test_commands_api.py tests/test_v8_remote.py tests/test_v8_phase36.py

# 4. Frontend testlari (15 ta test)
cd mikasa-7 && npm test

# 5. Flake8 statik tahlili (0 ta xatolik)
flake8 core/v8 tests/test_v8_remote.py tests/test_v8_phase36.py --max-line-length=150
```

---

## 13. Deployment

1. Repositoryni `dev-v8.0.0` branchida klonlang yoki yangilang.
2. Python virtual muhitini faollashtiring:
   ```powershell
   .venv\Scripts\activate
   ```
3. `.env` faylini to'ldiring:
   ```powershell
   cp .env.example .env
   # .env faylini tahrirlang
   ```
4. Frontend kutubxonalarini o'rnatish va qurish:
   ```powershell
   cd mikasa-7
   npm install
   npm run build
   cd ..
   ```
5. Xizmatni ishga tushirish:
   ```powershell
   python main.py
   ```

---

## 14. Rollback Plan

Agar favqulodda nosozlik aniqlansa:
1. `git log` orqali oxirgi barqaror commitni aniqlang (`b05d9d3` - Phase 35).
2. O'zgarishlarni bekor qilish:
   ```bash
   git checkout b05d9d3 -- core/v8/
   ```
3. Testlar yordamida Phase 35 holati barqarorligini tekshiring:
   ```bash
   python -m unittest tests/test_v8_remote.py
   ```
