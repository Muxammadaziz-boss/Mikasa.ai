# 🔷 MIKASA AI v8.0.0 — Level 8 Autonomous Desktop Assistant & Intelligence Hub

> **O'zbek tilidagi birinchi professional avtonom AI desktop yordamchisi va aqlli orkestratori**  
> React 19 + Tauri 2.0 zamonaviy interfeysi, Supabase Auth xavfsiz autentifikatsiyasi, Ed25519 kriptografik PC Agent Enrollment & Pairing (Phase 42), Telegram masofaviy boshqaruvi, Wake-on-LAN, ko'p bosqichli intellektual boshqaruv (Agent Loop 2.0), Tool System 2.0 va to'liq avtonom desktop tizimi.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Tauri%202.0%20%7C%20React%2019-61DAFB?style=flat&logo=react&logoColor=black)](mikasa-7/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows)](https://microsoft.com/windows)
[![Release](https://img.shields.io/badge/Release-v8.0.0-success)](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v8.0.0)
[![Tests](https://img.shields.io/badge/Tests-211%2F211%20Backend%20%7C%2015%2F15%20Frontend-brightgreen)](tests/)

---

## 🌟 8-Versiyadagi Asosiy Yangiliklar (v8.0.0 / Phases 35–42)

### 1. 🔐 Supabase Auth & Multi-Tenant Account Architecture (Phase 40–41)
* **Supabase Auth Integratsiyasi**: `auth.users.id` asosiy identity provider sifatida, email/parol, email tasdiqlash va sessiya boshqaruvi.
* **RLS & Multi-Tenant Xavfsizlik**: Har bir foydalanuvchi ma'lumotlari (`profiles`, `devices`, `sessions`) qat'iy izolyatsiya qilingan.

### 2. 💻 Secure PC Agent Enrollment & Pairing System (Phase 42)
* **6-Xonali Qisqa Muddatli Pairing Kodlari**: 5 daqiqalik TTL, salt+hash himoyasi, bruteforce cheklovi (maksimal 5 urinish).
* **Ed25519 Asimmetrik Kriptografiya**: Agent o'zining shaxsiy kalitini OS darajasida (Windows DPAPI) shifrlab saqlaydi, serverga faqat ochiq kalit uzatiladi.
* **Challenge-Response Autentifikatsiyasi**: 32-bayt bir martalik nonce orqali replay hujumlaridan to'liq himoyalangan avtonom agent ulanishi.

### 3. 🌐 Remote Control & Universal Telegram Bot (Phase 38–39)
* **Telegram Gateway**: Masofadan buyruqlar yuborish, status olish, ekranni boshqarish va xavfsiz bildirishnomalar.
* **Wake-on-LAN (WoL)**: Magic packet va retry mexanizmi orqali uxlab yotgan kompyuterlarni masofadan uyg'otish.

### 4. 🪐 Mikasa Orb & Zamonaviy Desktop UI (Tauri 2.0 + React 19)
* **Mikasa Orb**: Haqiqiy vaqt rejimida yordamchi holatini aks ettiruvchi interaktiv vizual yadro (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`).
* **Apple Dark Minimal & Glassmorphism**: Premium qora dizayn, silliq blur effektlar, dinamik fon rasmlari va qulay navigatsiya.
* **Raycast Uslubidagi Command Center**: 29+ dan ortiq tizim asboblarini klaviatura orqali bir lahzada chaqirish (`Ctrl+K`).
* **Interaktiv Vazifalar (Scheduler)**: Fon rejimida ishlovchi eslatmalar, davriy buyruqlar va vazifalar monitoringi.

### 5. 🧠 Agent Loop 2.0 & Rejalashtirish Dvigateli (Planner)
* **Deterministik Sikl**: Har bir murakkab so'rov `PLAN → ACT → OBSERVE → VERIFY → COMPLETE` zanjiri bo'yicha tartibli bajariladi.
* **Bog'liqliklar Grafigi (DAG)**: Ko'p bosqichli topshiriqlar uchun Directed Acyclic Graph va Kahn algoritmi asosidagi topologik saralash (`DependencyGraph`).
* **Avtomatik Verifikatsiya**: Har bir qadam natijasi tekshiriladi va xatolik yuz berganda xavfsiz replanning amalga oshiriladi.

### 6. 📦 Windows uchun Yig'ilgan Desktop Relizlar
* [Mikasa-AI-v8.0.0.exe](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v8.0.0) — O'rnatish talab qilmaydigan Portable versiya.
* [Mikasa-AI-Setup-v8.0.0.exe](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v8.0.0) — NSIS qulay o'rnatuvchisi.
* [Mikasa-AI-v8.0.0.msi](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v8.0.0) — Standart Windows MSI paketi.

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Tayyor Desktop Ilovani Ishlatish (Tavsiya etiladi)
[Releases Sahifasidan](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v8.0.0) `Mikasa-AI-v8.0.0.exe` yoki `Mikasa-AI-Setup-v8.0.0.exe` ni yuklab oling va to'g'ridan-to'g'ri ishga tushiring.

### 2. Dasturchilar uchun (Source Code orqali)
```bash
# Repozitoriyani klonlash
git clone https://github.com/Muxammadaziz-boss/Mikasa.ai.git
cd Mikasa.ai

# Python virtual muhiti
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Frontend (mikasa-7)
cd mikasa-7
npm install
npm run build
cd ..

# Ishga tushirish
python main.py
```

---

## 📁 Loyiha Strukturasi

```
Mikasa.ai/
├── core/                       # Intellektual yadro va backend xizmatlari
│   ├── v8/                     # Phase 35–42: Supabase Auth, PC Agent, WoL, Telegram Gateway
│   ├── intelligence/           # Agent Loop, Planner DAG, Verifier, PermissionEngine
│   ├── tools/                  # Tool System 2.0 (Contract, Runner, Discovery, Validator)
│   ├── agent_tools.py          # 29+ tizim asboblari
│   ├── api_server.py           # Mahalliy REST API server
│   ├── audio_service.py        # VAD ovoz xizmati
│   └── smart_algorithms.py     # Mahalliy tezkor qidiruv va algoritmlar
├── mikasa-7/                   # Tauri 2.0 + React 19 Desktop UI
│   ├── src/                    # React frontend komponentlari (Orb, Dashboard, Chat)
│   ├── src-tauri/              # Rust Tauri qobig'i va tizim integratsiyasi
│   └── dist/                   # Ishlab chiqarish uchun yig'ilgan statik fayllar
├── release/                    # Yig'ilgan desktop ilovalar arxivi
│   └── v8.0.0/                 # v8.0.0 Setup, Portable va MSI ilovalari
├── tests/                      # 211 ta avtomatlashtirilgan backend testlari
├── docs/                       # Loyiha arxitekturasi va qo'llanmalar
├── main.py                     # Asosiy tizim boshqaruvchisi
├── requirements.txt            # Python bog'liqliklari
└── README.md                   # Loyiha bosh sahifasi
```

---

## 🧪 Sifat Kafolati va Testlar

Loyiha to'liq integratsion va birlik testlari bilan qamrab olingan:
```bash
# Backend testlarini ishga tushirish (211 ta test)
python -m unittest discover tests/ "test_*.py"

# Frontend testlarini ishga tushirish (15 ta test)
cd mikasa-7 && npm test
```
- **Backend**: `211 / 211 PASS` (100% barqaror)
- **Frontend**: `15 / 15 PASS` (100% barqaror)
- **Flake8**: `0 syntax/lint errors`

---

## 📄 Litsenziya va Muallif

* **Muallif:** Muxammadaziz ([@Muxammadaziz-boss](https://github.com/Muxammadaziz-boss))
* **Litsenziya:** MIT License
