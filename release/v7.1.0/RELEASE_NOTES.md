# Mikasa AI v7.1.0 — Reliz Qaydlari (Release Notes)

🎉 **Mikasa AI 7.1.0 rasmiy relizi e'lon qilindi!**

Ushbu reliz dasturning eski prototipidan to'liq mustaqil, xavfsiz va tezkor Windows Desktop AI yordamchisiga aylanganligini bildiradi.

---

### 📦 Reliz Tarkibi va Yuklab Olish:

| Fayl nomi | Hajmi | Turi | Tavsif |
| :--- | :--- | :--- | :--- |
| **`Mikasa-AI-v7.1.0.exe`** | 4.29 MB | Portable Executable | O'rnatish talab qilmaydigan mustaqil ishga tushuvchi fayl |
| **`Mikasa-AI-Setup-v7.1.0.exe`** | 1.80 MB | NSIS Installer | Windows uchun rasmiy o'rnatuvchi dastur |
| **`Mikasa-AI-v7.1.0.msi`** | 2.55 MB | Windows MSI Package | Korporativ va standart Windows MSI paketi |
| **`run_portable.bat`** | 1.2 KB | Batch Launcher | Backend xizmatini avtomatik ko'taruvchi va dasturni ochuvchi fayl |
| **`version_manifest.json`** | 1.0 KB | Manifest & Hashes | Barcha binary fayllarning SHA256 nazorat yig'indilari |

---

### ⚡ Ishlash Samaradorligi Ko'rsatkichlari (Benchmarks):
- **O'tkazuvchanlik**: 1,730.1 so'rov / soniya (500 buyruq sinovida)
- **Mahalliy buyruqlar kechikishi**: o'rtacha 1.15 ms / so'rov
- **Qidiruv tezligi**: 1000 ta buyruq bo'yicha qidiruv 0.09 ms
- **Xotira sarfi**: 1000 ta takroriy so'rovdan so'ng RAM o'sishi atigi +0.23 MB
- **Dastur yuklanish vaqti**: < 280 ms (Vite production build)

---

### 🛡️ Xavfsizlik va Ishonchlilik:
- **CORS va IP himoyasi**: Faqat lokal `tauri://localhost` va `127.0.0.1` ulanishlariga ruxsat berilgan.
- **Path Traversal Guard**: Plaginlar o'rnatishda katalogdan chiqib ketish qat'iy to'xtatilgan.
- **Tauri CSP**: Xavfli tashqi skriptlar inyeksiyasiga qarshi Content Security Policy.
- **Maxfiy ma'lumotlar himoyasi**: Log fayllarida API kalitlari (`AIza...`, `sk-...`), bearer tokenlar va parollar avtomatik maskalanadi.
- **Global Error Boundary**: Kutilmagan qulashlarda oq ekran o'rniga qayta yuklash va bosh sahifaga qaytish imkonini beruvchi ekran.

---

### 🚀 Ishga Tushirish:
1. **Portativ rejimda**: `release/v7.1.0/run_portable.bat` faylini ikki marta bosing.
2. **O'rnatuvchi orqali**: `release/v7.1.0/Mikasa-AI-Setup-v7.1.0.exe` ni ishga tushirib o'rnating.
