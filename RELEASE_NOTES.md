# Mikasa AI v8.0.0 — Reliz Qaydlari (Release Notes)

🎉 **Mikasa AI 8.0.0 rasmiy relizi e'lon qilindi!**

Mikasa AI 8.0.0 — to'liq avtonom, xavfsiz va tarmoqlangan shaxsiy AI desktop yordamchisi. Ushbu yirik reliz Supabase Auth autentifikatsiyasi, Ed25519 kriptografik PC Agent Enrollment & Pairing tizimi, universal Telegram masofaviy boshqaruvi va ko'p bosqichli intellektual orkestratsiyani birlashtiradi.

---

### 📦 Reliz Tarkibi va Yuklab Olish:

| Fayl nomi | Hajmi | Turi | Tavsif |
| :--- | :--- | :--- | :--- |
| **`Mikasa-AI-v8.0.0.exe`** | 4.3 MB | Portable Executable | O'rnatish talab qilmaydigan mustaqil ishga tushuvchi fayl |
| **`Mikasa-AI-Setup-v8.0.0.exe`** | 1.8 MB | NSIS Installer | Windows uchun rasmiy o'rnatuvchi dastur |
| **`Mikasa-AI-v8.0.0.msi`** | 2.6 MB | Windows MSI Package | Korporativ va standart Windows MSI paketi |
| **`run_portable.bat`** | 1.2 KB | Batch Launcher | Backend xizmatini avtomatik ko'taruvchi va dasturni ochuvchi fayl |
| **`version_manifest.json`** | 1.0 KB | Manifest & Hashes | Barcha binary fayllarning SHA256 nazorat yig'indilari |

---

### 🌟 Asosiy Yangiliklar (v8.0.0):
1. **🔐 Supabase Auth (Phase 41)**:
   - `auth.users.id` asosiy identity provider sifatida.
   - Email/parol, email tasdiqlash, parol tiklash va sessiya boshqaruvi.
   - Qat'iy Row Level Security (RLS) va ko'p foydalanuvchili izolyatsiya.
2. **💻 PC Agent Enrollment & Pairing (Phase 42)**:
   - 6-xonali bir martalik qisqa muddatli pairing kodlari (5 min TTL).
   - Ed25519 asimmetrik kalitlar juftligi va Windows DPAPI xavfsiz saqlash.
   - 32-bayt bir martalik nonce asosidagi challenge-response autentifikatsiyasi.
3. **🌐 Remote Control & Telegram Gateway (Phase 38–39)**:
   - Universal Telegram Bot orqali buyruqlar, status va bildirishnomalar.
   - Wake-on-LAN (WoL) orqali masofadan kompyuterni uyg'otish.
4. **🧠 Agent Loop 2.0 & Rejalashtirish Dvigateli**:
   - Directed Acyclic Graph (DAG) va Kahn algoritmi asosida ko'p bosqichli vazifalarni bajarish.
   - 29+ tizim vositalari (Tool System 2.0) va avtomatik replanning.

---

### ⚡ Sifat va Sinov Ko'rsatkichlari:
- **Backend Testlari**: 211 / 211 PASS (100% muvaffaqiyatli)
- **Frontend Testlari**: 15 / 15 PASS (100% muvaffaqiyatli)
- **Kriptografiya**: Ed25519, SHA256, DPAPI, constant-time verification.

---

### 🚀 Ishga Tushirish:
1. **Portativ rejimda**: `release/v8.0.0/run_portable.bat` faylini ikki marta bosing.
2. **O'rnatuvchi orqali**: `release/v8.0.0/Mikasa-AI-Setup-v8.0.0.exe` ni ishga tushirib o'rnating.
