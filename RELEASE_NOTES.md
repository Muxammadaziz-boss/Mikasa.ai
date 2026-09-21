# 🚀 Mikasa AI v8.0.0 — Rasmiy Reliz Qaydlari (Release Notes)

🎉 **Mikasa AI 8.0.0 (Level 8 Autonomous Desktop Assistant & Intelligence Hub) rasmiy relizi e'lon qilindi!**

Mikasa AI 8.0.0 — to'liq avtonom, xavfsiz va tarmoqlangan shaxsiy AI desktop yordamchisi. Ushbu yirik reliz Supabase Auth autentifikatsiyasi, Ed25519 kriptografik PC Agent Enrollment & Pairing tizimi, universal Telegram masofaviy boshqaruvi, qat'iy sandboxlangan Windows Agent vositalari va Ed25519 bilan imzolangan xavfsiz Auto-Update tizimini birlashtiradi.

---

### 📦 Reliz Binar Fayllari (Cryptographically Verified):

| Fayl nomi | Hajmi | Turi | SHA-256 Nazorat Yig'indisi |
| :--- | :--- | :--- | :--- |
| **`Mikasa-AI-v8.0.0.exe`** | **4.87 MB** | Standalone Portable | `f8264cce30a004f93d602c193c0bab8ee8cadb2007b915331591f09f158e73c9` |
| **`Mikasa-AI-Setup-v8.0.0.exe`** | **2.01 MB** | NSIS Installer | `dbebb87f1869e47ef0014d45f791b4cee533918fb69a16c7117403603d06ca7e` |
| **`Mikasa-AI-v8.0.0.msi`** | **2.70 MB** | Windows MSI Package | `4d34c9ba60a676c560fbaba1c58193f4d6e0d065d951aaec26313d5919b8fff1` |
| **`WebView2Loader.dll`** | **0.15 MB** | Windows Native DLL | `8427b1fc58ec707813e5c0a51eb5d69397bb333250a7b891be4d3b123f1e0f1c` |
| **`run_portable.bat`** | **1 KB** | Batch Launcher | Avtomatik port va fon xizmati boshqaruvi |
| **`version_manifest.json`** | **2 KB** | Signed Manifest | Ed25519 raqamli imzolari bilan to'liq himoyalangan |

*Barcha reliz fayllari rasmiy [GitHub Releases Sahifasida](https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/tag/v8.0.0) joylashtirilgan.*

---

### 🌟 Asosiy Yangiliklar (v8.0.0 / Phases 35–48):

1. **🔐 Supabase Auth & Multi-Tenant Xavfsizlik (Phase 40–41)**:
   - `auth.users.id` asosiy identity provider sifatida tanlandi.
   - Email va parol bilan ro'yxatdan o'tish, sessiya boshqaruvi, parolni xavfsiz tiklash.
   - Qat'iy Row Level Security (RLS) orqali ko'p foydalanuvchili to'liq izolyatsiya.

2. **💻 Kriptografik PC Agent Enrollment & Pairing (Phase 42–44)**:
   - 6-xonali bir martalik qisqa muddatli pairing kodlari (5 min TTL).
   - Ed25519 asimmetrik kalitlar juftligi va Windows DPAPI xavfsiz kalit saqlash mexanizmi.
   - 32-bayt bir martalik nonce asosidagi challenge-response autentifikatsiyasi.

3. **🌐 Remote Control & Telegram Gateway (Phase 38–39)**:
   - Universal Telegram Bot orqali buyruqlar, status va bildirishnomalar.
   - Wake-on-LAN (WoL) orqali masofadan kompyuterni uyg'otish.
   - Xavfsizlik filtrlari va nozik amallarni tasdiqlash (Approval) tizimi.

4. **🛡️ Windows Agent & Real Tizim Vositalari (Phase 45–47)**:
   - `PathSecurityValidator` orqali tizim kataloglari va maxfiy ma'lumotlarni (`C:\Windows`, `.ssh`, `.env`) himoya qilish.
   - Skrinshot olish, ilovalarni xavfsiz ishga tushirish/yopish, klaviatura va sichqoncha harakatlari.

5. **🔄 Secure Auto-Update & Crash-Safe Rollback Engine (Phase 48)**:
   - SemVer 2.0.0 qoidalari bo'yicha versiya nazorati.
   - Har bir yangilanish fayli serverdan olinishi bilanoq Ed25519 raqamli imzosi va SHA-256 xeshi orqali tekshiriladi (Fail-closed).
   - Atomik staging va nosozlik yuz berganda avtomatik rollback himoyasi.

6. **🧠 Agent Loop 2.0 & Rejalashtirish Dvigateli**:
   - Directed Acyclic Graph (DAG) va Kahn algoritmi asosida ko'p bosqichli vazifalarni bajarish.
   - 29+ tizim vositalari (Tool System 2.0) va avtomatik replanning.

---

### 🔐 Ishonchli Ochiq Kalit (Trusted Ed25519 Public Key):
```
b4be839fd62657c0e786e1a2ad590c05c45c511371d041137c5ca9ac57c29829
```
*Ilova har qanday yangilanish paketini o'rnatishdan avval ushbu kalit orqali imzoning haqiqiyligini tekshiradi.*

---

### ⚡ Sifat va Sinov Ko'rsatkichlari:
- **Backend Testlari**: `242 / 242 PASS` (100% muvaffaqiyatli)
- **Secure Auto-Update Testlari**: `31 / 31 PASS` (100% muvaffaqiyatli)
- **Frontend Testlari**: `15 / 15 PASS` (100% muvaffaqiyatli)
- **Kriptografiya**: Ed25519, SHA-256, DPAPI, constant-time verification
