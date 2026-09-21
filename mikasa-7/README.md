# Mikasa AI 8.0 — Desktop Foundation (Tauri 2.0 + React 19 + TypeScript)

Mikasa AI 8.0 uchun zamonaviy, xavfsiz va yuqori tezlikdagi native desktop interfeysi.

## 🚀 Texnologiyalar To'plami
- **Desktop Shell**: [Tauri 2.x](https://tauri.app/) (Rust)
- **Frontend**: React 19 + TypeScript 6 + Vite 8
- **Dizayn Tizimi**: Pure CSS Tokens (Near-black `#080C14`, Glassmorphism, Neon Cyan/Azure Glow)
- **Autentifikatsiya**: Supabase Auth SDK (`@supabase/supabase-js`)
- **Backend / AI Yadrosi**: Python 3.11 (`core/api_server.py`, `core/v8/`) REST + WebSocket (18420-port)

## 📁 Papkalar Tuzilmasi
```
mikasa-7/
├── src-tauri/               # Tauri Rust konfiguratsiyasi va desktop oyna sozlamalari
│   ├── Cargo.toml
│   ├── tauri.conf.json      # Frameless oyna (1280x800, min 1024x700)
│   └── src/
│       ├── lib.rs           # Rust mahalliy oyna funksiyalari
│       └── main.rs
├── src/
│   ├── assets/              # Statik resurslar va rasmlar
│   ├── components/          # Qayta ishlatiluvchi desktop komponentlar
│   │   ├── icons/Icons.tsx  # 26 ta SVG vektorli piktogrammalar
│   │   ├── MikasaOrb.tsx    # 10 ta holatli interaktiv AI Orb
│   │   ├── UpdateModal.tsx  # Phase 48: Avto-yangilanish holati va dialogi
│   │   ├── DevicePairingModal.tsx # Phase 42: 6-xonali kod bilan qurilma ulash
│   │   ├── WindowControls.tsx # Frameless oyna boshqaruv tugmalari
│   │   └── CommandCenter.tsx # Ctrl+K global buyruqlar palitrasi
│   ├── layout/              # Desktop Shell tartibi
│   │   ├── TopBar.tsx       # Sarlavha paneli (Drag region va oyna tugmalari)
│   │   ├── Sidebar.tsx      # Chap navigatsiya paneli
│   │   └── AppShell.tsx     # Barcha qismlarni birlashtiruvchi karkas
│   ├── pages/               # Asosiy sahifalar
│   │   ├── LandingPage.tsx  # Bosh sahifa (Orb, Telemetriya, Tezkor harakatlar)
│   │   ├── ChatPage.tsx     # Intellektual AI Suhbat
│   │   ├── VoicePage.tsx    # Ovozli jonli muloqot
│   │   ├── CommandsPage.tsx # 29+ Tizim asboblari
│   │   ├── MemoryPage.tsx   # Shaxsiy bilimlar bazasi
│   │   ├── SchedulerPage.tsx# Vazifalar va eslatmalar
│   │   ├── PluginsPage.tsx  # Plaginlar katalogi
│   │   └── AccountPage.tsx  # Supabase Auth, Qurilmalar va Auto-Update sozlamalari
│   ├── services/            # Aloqa xizmatlari
│   │   ├── backendService.ts# REST & WebSocket asinxron aloqasi
│   │   ├── supabaseAuth.ts  # Supabase mijoz va sessiya boshqaruvi
│   │   └── updateService.ts # Phase 48: Yangilanish tekshirish va o'rnatish
│   ├── styles/
│   │   ├── tokens.css       # Ranglar, shriftlar, radiuslar va shisha effektlari
│   │   └── globals.css      # Asosiy desktop stillari va skrollbar
│   ├── App.tsx              # Shell va marshrutlash
│   └── main.tsx             # React kirish nuqtasi
├── package.json
└── vite.config.ts
```

## 🛠 Ishga Tushirish Buyruqlari

### 1. Frontend-ni ishlab chiqish (Vite Dev Server)
```bash
npm install
npm run dev
```

### 2. Frontend-ni tekshirish va test qilish
```bash
npm test
npm run build
```

### 3. Tauri Desktop Ilovasini Ishga Tushirish (Native Dev)
```bash
npm run desktop
```

### 4. Ishlab Chiqarish (Release) uchun Yig'ish
```bash
npm run build:desktop
node scripts/package_release.cjs
```
*Natija `release/v8.0.0/` katalogida saqlanadi.*
