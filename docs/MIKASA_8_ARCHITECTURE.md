# 🏛️ Mikasa AI v8.0.0 — Arxitektura Qo'llanmasi (Architecture Blueprint)

**Loyiha:** `Muxammadaziz-boss/Mikasa.ai`  
**Versiya:** `8.0.0 (Production Release)`  
**Tarmoq:** `dev-v8.0.0`  
**Sana:** 2026-09-21  

---

## 1. Umumiy Arxitektura Ko'rinishi

Mikasa AI v8.0.0 uchta mustaqil, ammo xavfsiz kanallar orqali bog'langan asosiy qatlamdan iborat:

```
┌─────────────────────────────────────────────────────────────────┐
│                       MIKASA AI v8.0.0                          │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  FRONTEND (UI)   │  │   PYTHON CORE    │  │  REMOTE / AGENT  │
│  Tauri 2.0 (Rust)│  │  API Server 18420│  │  Windows Agent   │
│  React 19 + Vite │  │  Agent Loop 2.0  │  │  Telegram Gateway│
│  Supabase Auth   │  │  Update Service  │  │  WoL & DPAPI     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 2. Asosiy Qismlar va Xavfsizlik Tamoyillari

### 1. 🪐 Foydalanuvchi Interfeysi (mikasa-7)
* **Tauri 2.0 + React 19**: Rust quvvatida ishlovchi yengil, tezkor va xavfsiz native desktop shell.
* **Mikasa Orb**: 10 ta holatli (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`, ...) vizual reaktiv audio sfera.
* **Quiet Intelligence UI**: Solid quyuq zamin, nozik aero-shisha (glassmorphism) va zumrad yorug'lik aksentlari.
* **Command Center (`Ctrl+K`)**: 29+ tizim vositalarini bir lahzada chaqirish va klaviaturadan to'liq boshqarish.

### 2. 🧠 Backend va Intellektual Yadro (core/)
* **`core/api_server.py`**: 127.0.0.1:18420 manzilida asinxron ishlovchi aiohttp REST va WebSocket serveri.
* **Agent Loop 2.0 & Planner DAG**: Kahn algoritmi asosida ko'p qadamli vazifalarni topologik rejalashtirish va xatoda replanning.
* **Tool System 2.0**: Qat'iy kontraktlar, parametrlar validatsiyasi va xavfsiz ijro nazoratchisi.

### 3. 🔐 Kriptografik Xavfsizlik va Autentifikatsiya (core/v8/)
* **Supabase Multi-Tenant Auth**: `auth.users.id` asosida xavfsiz email/parol, tokenlar va RLS ma'lumotlar bazasi izolyatsiyasi.
* **PC Agent Enrollment**: 6-xonali bir martalik kod (5 min TTL), bruteforce chegarasi (5 urinish), Ed25519 kalitlar juftligi.
* **Replay Himoyasi**: 32-bayt nonce challenge-response protokoli.
* **Windows DPAPI**: Shaxsiy kriptografik kalitlarni operatsion tizim darajasida shifrlab saqlash.

### 4. 🔄 Xavfsiz Avto-Yangilanish Tizimi (Phase 48)
* **`core/v8/update_service.py`**:
  * SemVer 2.0.0 qoidalariga asoslangan versiya tekshiruvi.
  * Ed25519 raqamli imzosi (`DEFAULT_TRUSTED_PUBLIC_KEY`) va SHA-256 xesh tekshiruvi (Fail-closed).
  * Atomik staging va avtomatik zaxiralash (backup).
  * Jarayonda nosozlik aniqlansa, darhol avvalgi versiyaga avtomatik rollback.

---

## 3. Sinov va Sifat Standartlari

* **Backend Unit & Integration**: 242/242 PASS
* **Secure Updater**: 31/31 PASS
* **Frontend Tests**: 15/15 PASS
* **Linting / Flake8**: 0 xatolik
