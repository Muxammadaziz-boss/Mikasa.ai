# Mikasa AI 7.0 — Desktop Foundation (Tauri + React + TypeScript)

Mikasa AI 7.0 uchun zamonaviy, tezkor va xavfsiz desktop interfeysi.

## 🚀 Texnologiyalar to'plami
- **Desktop Shell**: [Tauri 2.x](https://tauri.app/) (Rust)
- **Frontend**: React 19 + TypeScript + Vite 8
- **Dizayn tizimi**: Pure CSS Tokens (Near-black, Glassmorphism, Neon Cyan/Azure Glow)
- **Backend / AI yadrosi**: Python 3.12 (Mavjud Mikasa AI 6.0 yadrosi to'liq saqlangan holda)

## 📁 Papkalar tuzilmasi
```
mikasa-7/
├── src-tauri/               # Tauri Rust konfiguratsiyasi va desktop oyna sozlamalari
│   ├── Cargo.toml
│   ├── tauri.conf.json      # Frameless oyna (1280x800, min 1024x700)
│   └── src/
│       ├── lib.rs
│       └── main.rs
├── src/
│   ├── assets/              # Statik resurslar
│   ├── components/          # Qayta ishlatiluvchi desktop komponentlar
│   │   ├── icons/Icons.tsx  # Desktop SVG ikonkalari
│   │   ├── Avatar.tsx       # Foydalanuvchi profili
│   │   ├── Button.tsx       # Birlamchi, ikkilamchi va glass tugmalar
│   │   ├── IconButton.tsx   # Tooltip bilan ta'minlangan ikonka tugmalari
│   │   ├── MikasaLogo.tsx   # Mikasa AI brend logosi
│   │   ├── MikasaOrb.tsx    # 7 holatli interaktiv AI Orb (idle, listening, thinking, ...)
│   │   ├── StatusIndicator.tsx # Tizim holati (Online/Offline)
│   │   └── WindowControls.tsx  # Frameless oyna boshqaruv tugmalari (Minimize, Maximize, Close)
│   ├── layout/              # Desktop Shell tartibi
│   │   ├── TopBar.tsx       # Sarlavha paneli (Drag region va oyna tugmalari)
│   │   ├── Sidebar.tsx      # Chap navigatsiya paneli (MIKASA va AGENT bo'limlari)
│   │   ├── AccountRow.tsx   # Foydalanuvchi hisobi (Pastki qism, Sozlamalar integratsiyalashgan)
│   │   └── AppShell.tsx     # Barcha qismlarni birlashtiruvchi desktop karkasi
│   ├── pages/               # Sahifalar
│   │   ├── LandingPlaceholder.tsx # Step 0 Bosh sahifa (AI Orb, Salomnoma, Voice CTA, Takliflar)
│   │   └── RoutePlaceholder.tsx   # Ovoz, Suhbat, Buyruqlar, Xotira uchun vaqtinchalik marshrutlar
│   ├── styles/
│   │   ├── tokens.css       # Ranglar, shriftlar, radiuslar va shisha effektlari
│   │   └── globals.css      # Asosiy desktop stillari va skrollbar
│   ├── App.tsx              # Shell va marshrutlash
│   └── main.tsx             # React kirish nuqtasi
├── package.json
└── vite.config.ts
```

## 🛠 Ishga tushirish buyruqlari

### 1. Frontend-ni brauzerda ishlab chiqish (Vite Dev Server)
```bash
cd mikasa-7
npm install
npm run dev
```

### 2. Frontend-ni tekshirish va yig'ish (TypeScript + Vite)
```bash
cd mikasa-7
npm run build
```

### 3. Tauri Desktop ilovasini ishga tushirish (Tauri Dev Mode)
```bash
cd mikasa-7
npm run tauri dev
```

### 4. Ishlab chiqarish (Production) uchun o'rnatuvchi paket yaratish
```bash
cd mikasa-7
npm run tauri build
```

## 🔗 Mikasa 6.0 Python yadrosi bilan bog'lanish
- Mikasa 7.0 Tauri ilovasi mavjud Mikasa Python backendiga IPC (Tauri Command / Local HTTP / WebSocket) orqali ulanadi.
- Mavjud `core/`, `tests/` va `main.py` fayllari o'zgarishsiz qolgan.

