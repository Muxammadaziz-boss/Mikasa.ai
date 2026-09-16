# MIKASA AI v8.0.0 — Phase 35: Remote PC Control & Telegram Gateway

## 1. Umumiy Maqsad va Arxitektura

Mikasa AI 8-versiyasining 35-bosqichida masofadan boshqarish, qurilma holatini monitoring qilish, Telegram transporti orqali buyruqlar qabul qilish va Wake-on-LAN (WoL) protokoli orqali kompyuterni yoqish arxitekturasi yaratildi.

Barcha yangi modullar to'liq izolyatsiyalangan holda `core/v8/` paketida joylashgan bo'lib, eski 7.x modullari bilan qat'iy interfeyslar orqali bog'lanadi.

```
+-------------------------------------------------------------+
|               Telegram Foydalanuvchisi / Admin              |
+-------------------------------------------------------------+
                              |
                              v (HTTPS / Telegram Bot API)
+-------------------------------------------------------------+
|             TelegramRemoteGateway (core.v8)                 |
| - Admin Auth (Whitelisting)                                 |
| - Uzbek & English NLP Intent Parsing                        |
| - Inline Keyboard & Confirmation Prompt                     |
+-------------------------------------------------------------+
         |                                           |
         v (Wake-on-LAN)                             v (Signed Envelope)
+-------------------------+             +-------------------------------+
| WakeOnLanManager        |             | EnvelopeManager               |
| - Magic Packet (UDP)    |             | - Nonce Replay Defense        |
| - WakeRelay Adapter     |             | - TTL / Expiration Check      |
+-------------------------+             +-------------------------------+
                                                     |
                                                     v
+-------------------------------------------------------------+
|                 MikasaPCAgent (core.v8)                     |
| - Deterministic Device Identity & Hardware Fingerprint      |
| - HeartbeatManager (ONLINE / OFFLINE / WAKING FSM)          |
| - Exponential Backoff Reconnection                          |
| - PermissionEngine (High/Medium/Low Risk Evaluation)        |
| - Tool System 2.0 Runner Integration                        |
+-------------------------------------------------------------+
```

---

## 2. Modullar va Komponentlar

### 2.1. Qurilma Identifikatsiyasi (`core/v8/device.py`)
- `DeviceIdentity`: Qurilmaning doimiy va deterministik pasporti (`device_id = f"{username}@{hostname}"`).
- `DeviceIdentityManager`: Qurilmaning apparat ma'lumotlari (MAC manzil, platforma, operatsion tizim versiyasi, protsessor arxitekturasi) asosida SHA-256 xesh yaratadi.

### 2.2. Heartbeat & Holat Boshqaruvi (`core/v8/heartbeat.py`)
- `DeviceState`: Qurilmaning chekli holatlar mashinasi (`OFFLINE`, `WAKING`, `ONLINE`, `BUSY`, `ERROR`).
- `HeartbeatManager`: Qurilmalardan davriy "tiriklik" signallarini qabul qiladi. `stale_timeout` oshganda qurilma avtomatik `OFFLINE` deb belgilanadi va holat tinglovchilari ogohlantiriladi.

### 2.3. Wake-on-LAN Menejeri (`core/v8/wol.py`)
- `create_magic_packet(mac)`: 102 baytlik standart WoL Magic Packet generatsiyasi.
- `WakeRelay` interfeysi: Mock va haqiqiy UDP broadcast (`LocalBroadcastRelay`) adapterlari.

### 2.4. Buyruq Envelopi va Replay Himoyasi (`core/v8/envelope.py`)
- `RemoteCommandEnvelope`: Buyruq konverti.
- `EnvelopeManager`: Nonce replay himoyasi, TTL muddati tekshiruvi, Admin foydalanuvchi tekshiruvi.

### 2.5. PC Agent Xizmati (`core/v8/pc_agent.py`)
- Kompyuter fonida ishlovchi agent, eksponensial kechikishli qayta ulanish (`backoff`), `PermissionEngine` va `Tool System 2.0` integratsiyasi.

### 2.6. Telegram Gateway (`core/v8/telegram_gateway.py`)
- Admin whitelisting, O'zbek va ingliz tili buyruqlarini tanish, inline tugmalar, yuqori xavfli amallarni tasdiqlash dialogi.

### 2.7. Masofaviy Rejalashtirish DAG (`core/v8/planning_remote.py`)
- `create_remote_wake_and_verify_dag`: Directed Acyclic Graph (DAG) ko'p bosqichli rejasi.

---

## 3. Xavfsizlik Kafolatlari

1. **Arbitrary Code Execution Taqiqlangan**: `eval()`, `exec()` yoki `os.system()` yo'q.
2. **Kredensial O'g'irlash Taqiqlangan**: Parol yoki cookie o'g'irlash kabi zararli amallar mutlaqo yo'q.
3. **Admin Autentifikatsiyasi**: Begona foydalanuvchilar qat'iy bloklanadi.
4. **Tasdiqlash Zanjiri (Confirmation Flow)**: Yuqori xavfli buyruqlar alohida tasdiqlash talab qiladi.
