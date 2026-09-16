# 🔷 MIKASA AI v7.3.0 — Level 7 Autonomous Desktop Assistant & Intelligence Hub

> **O'zbek tilidagi birinchi professional avtonom AI desktop yordamchisi va aqlli orkestratori**  
> React 19 + Tauri 2.0 zamonaviy interfeysi, interaktiv Mikasa Orb, ko'p bosqichli intellektual boshqaruv (Agent Loop), Tool System 2.0, Secret Vault va to'liq avtonom desktop tizimi.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Tauri%202.0%20%7C%20React%2019-61DAFB?style=flat&logo=react&logoColor=black)](mikasa-7/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows)](https://microsoft.com/windows)
[![Release](https://img.shields.io/badge/Release-v7.3.0--final-success)](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v7.3.0)
[![Tests](https://img.shields.io/badge/Tests-86%2F86%20Backend%20%7C%2015%2F15%20Frontend-brightgreen)](tests/)

---

## 🌟 7-Versiyadagi Asosiy Yangiliklar

### 1. 🪐 Mikasa Orb & Zamonaviy Desktop UI (Tauri 2.0 + React 19)
* **Mikasa Orb**: Haqiqiy vaqt rejimida yordamchi holatini aks ettiruvchi interaktiv vizual yadro (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`).
* **Apple Dark Minimal & Glassmorphism**: Premium qora dizayn, silliq blur effektlar, dinamik fon rasmlari va qulay navigatsiya.
* **Raycast Uslubidagi Command Center**: 29+ dan ortiq tizim asboblarini klaviatura orqali bir lahzada chaqirish (`Ctrl+K`).
* **Interaktiv Vazifalar (Scheduler)**: Fon rejimida ishlovchi eslatmalar, davriy buyruqlar va vazifalar monitoringi.

### 2. 🧠 Agent Loop 2.0 & Rejalashtirish Dvigateli (Planner)
* **Deterministik Sikl**: Har bir murakkab so'rov `PLAN → ACT → OBSERVE → VERIFY → COMPLETE` zanjiri bo'yicha tartibli bajariladi.
* **Bog'liqliklar Grafigi (DAG)**: Ko'p bosqichli topshiriqlar uchun Directed Acyclic Graph va Kahn algoritmi asosidagi topologik saralash (`DependencyGraph`).
* **Avtomatik Verifikatsiya**: Har bir qadam natijasi tekshiriladi va xatolik yuz berganda xavfsiz replanning amalga oshiriladi.

### 3. 🛠️ Capability-Driven Tool System 2.0
* **29+ Rasmiy Asboblar**: Hisob-kitob, ob-havo, valyuta kurslari, xotira, fayllar boshqaruvi, tarjimon, tizim diagnostikasi, audio boshqaruvi va boshqalar.
* **Qat'iy Validatsiya**: `ParameterValidator` orqali noto'g'ri yoki xavfli parametrlar filtrlanadi.
* **Vaqt Chegarasi (Timeout Enforcement)** va **Salomatlik Holati (ToolHealth)**: Asboblar tizimni to'xtatib qo'ymasligi kafolatlanadi.

### 4. 🛡️ Xavfsizlik & Ruxsatlar Modeli (Permission & Risk Engine)
* **PermissionEngine**: Amallarni xavf darajasiga ko'ra baholash (`LOW`, `MEDIUM`, `HIGH`).
* **Foydalanuvchi Tasdig'i (Confirmation Flow)**: Kompyuterni o'chirish (`shutdown`), qayta yuklash (`restart`) yoki fayllarni o'chirish kabi muhim amallar foydalanuvchi roziligisiz bajarilmaydi.
* **SecretVault & Log Redaction**: API kalitlar shifrlanadi va jurnallarda (`sk-***MASKED_KEY***`) ko'rinishida avtomatik niqoblanadi.

### 5. 📦 Windows uchun Yig'ilgan Desktop Relizlar
* [Mikasa-AI-Setup-v7.3.0.exe](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v7.3.0) — NSIS qulay o'rnatuvchisi.
* [Mikasa-AI-v7.3.0.exe](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v7.3.0) — O'rnatish talab qilmaydigan Portable versiya.
* [Mikasa-AI-v7.3.0.msi](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v7.3.0) — Standart Windows MSI paketi.

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Tayyor Desktop Ilovani Ishlatish (Tavsiya etiladi)
[Releases Sahifasidan](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v7.3.0) `Mikasa-AI-Setup-v7.3.0.exe` yoki `Mikasa-AI-v7.3.0.exe` ni yuklab oling va to'g'ridan-to'g'ri ishga tushiring.

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
├── release/                    # Yig'ilgan desktop ilovalar arxivi (v7.0.0 ... v7.3.0)
│   └── v7.3.0/                 # v7.3.0 Setup, Portable va MSI ilovalari
├── tests/                      # 86 ta avtomatlashtirilgan backend testlari
├── docs/                       # Loyiha arxitekturasi va qo'llanmalar
├── main.py                     # Asosiy tizim boshqaruvchisi
├── requirements.txt            # Python bog'liqliklari
└── README.md                   # Loyiha bosh sahifasi
```

---

## 🧪 Sifat Kafolati va Testlar

Loyiha to'liq integratsion va birlik testlari bilan qamrab olingan:
```bash
# Backend testlarini ishga tushirish (86 ta test)
python -m unittest discover tests/ "test_*.py"

# Frontend testlarini ishga tushirish (15 ta test)
cd mikasa-7 && npm test
```
- **Backend**: `86 / 86 PASS` (100% barqaror)
- **Frontend**: `15 / 15 PASS` (100% barqaror)
- **Flake8**: `0 syntax/lint errors`

---

## 📄 Litsenziya va Muallif

* **Muallif:** Muxammadaziz ([@Muxammadaziz-boss](https://github.com/Muxammadaziz-boss))
* **Litsenziya:** MIT License
