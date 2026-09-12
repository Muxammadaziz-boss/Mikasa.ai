# Mikasa AI — Loyiha O'zgarishlar Tarixi (Changelog)

Barcha o'zgarishlar va relizlar Semantic Versioning (SemVer) qoidalariga muvofiq yuritiladi.

---

## [7.1.0] — 2026-09-13 (Production Native Desktop Release)

Mikasa AI 7.1.0 — loyihaning to'liq 27 bosqichli Master Rejasi asosida tubdan yangilangan, Windows 10/11 uchun moslashgan ishlab chiqarish (production) darajasidagi sun'iy intellektli shaxsiy yordamchisi.

### 🌟 Yangi Imkoniyatlar va Arxitektura:
- **Phase 0 — To'liq Loyiha Auditi**: Barcha mavjud kodlar, yo'llar va bog'liqliklar tahlil qilinib, portativ arxitektura poydevori yaratildi.
- **Phase 1 & 2 — Native Tauri 2.0 Desktop Shell**: Rust asosidagi xavfsiz va tezkor desktop qobiq, maxsus oynani boshqarish (minimize, toggle maximize, clean close) va frameless silliq oyna dizayni.
- **Phase 3 & 4 — Python Backend Lifecycle & Portability**: Zero hardcoded paths tamoyili, aiohttp asinxron REST & WebSocket serveri (`127.0.0.1:18420`), fondagi o'rnatilgan Python boshqaruvi va avtomatik resurs tozalash.
- **Phase 5 & 6 — Quiet Intelligence Dizayn Tizimi**: Matnli emojilardan butunlay voz kechildi; to'liq vektorli SVG piktogrammalar, `#0E1422` solid quyuq yuzalar, nozik shisha (glassmorphism) va `#10B981` zumrad yorug'lik effektlari.
- **Phase 7 — Responsive Desktop AppShell**: 1024x700 minimal o'lchamdan boshlab 4K gacha avtomatik moslashuvchi qatlam, tor ekranlarda 68px ixcham yon panel.
- **Phase 8 — Home / Landing**: Real apparat telemetriyasi (soxta ma'lumotlarsiz real CPU/RAM/Disk), tezkor AI harakatlari kartochkalari.
- **Phase 9 — AI Chat**: Fikrlovchi Gemini va universal modellar, ko'p qatorli avtomatik kattalashuvchi yozish maydoni, suhbat tozalash va to'liq kontekstli javoblar.
- **Phase 10 — Ovozli Muloqot & Mikasa Orb**: 7 xil jonli holatga ega (idle, listening, thinking, speaking, loading, offline, error) audio sfera, Edge-TTS Sardor va Madina ovozlari.
- **Phase 11 — Buyruqlar Markazi**: 29 ta haqiqiy ToolRegistry vositasi, tezkor qisqartmalar, parametrlarni interaktiv sozlash modali va natijalarni nusxalash.
- **Phase 12 — Xotira Maydoni**: Shaxsiy bilimlar bazasi (CRUD), suhbatlar konteksti va profil sozlamalari.
- **Phase 13 — Rejalashtiruvchi**: 5 ta holatli (active, repeating, completed, failed, cancelled) eslatmalar va vazifalar tizimi, fon oqimida 1ms da to'xtovchi signal mexanizmi.
- **Phase 14 — Plaginlar Markazi**: O'rnatilgan, mavjud, o'chirilgan va yangilanish holatidagi plaginlar katalogi, JSON shablonlar asosida yangi plagin qo'shish.
- **Phase 15 — Hisob va Sozlamalar**: 7 ta bo'lim (Profil, Ovoz, AI modeli, Ko'rinish, Bildirishnomalar, Maxfiylik, Dastur haqida), dinamik avatar va mavzular.
- **Phase 16 — Global Buyruqlar Palitrasi (`Ctrl+K`)**: WAI-ARIA 1.2 standartiga mos to'liq klaviatura orqali boshqariluvchi global qidiruv va navigatsiya.
- **Phase 17 — Responsive Desktop**: Grid kartochkalarining avtomatik to'lishi (`repeat(auto-fit, minmax(...))`) va tor ekranlarda tugmalar siqilishining oldini olish.
- **Phase 18 — Foydalanish Qulayligi (a11y)**: Yuqori kontrastli fokus halqalari (`:focus-visible`), harakatni kamaytirish (`prefers-reduced-motion`) va ekran o'quvchilari uchun maxsus belgilar.
- **Phase 19 — Ishlash Tezligi (Performance)**: `mountedRef` orqali eskirgan holatlarni tozalash, fonda xotira oqishini (memory leak) bartaraf etish.
- **Phase 20 — Xavfsizlik (Security)**: Qat'iy CORS oq ro'yxati (Tauri va localhost), begona veb-saytlar va tashqi tarmoq IP-laridan kelgan so'rovlarni bloklash (403), plagin nomlarida path traversal himoyasi va Tauri CSP direktivalari.
- **Phase 21 — Xatoliklarni Boshqarish (Error Handling)**: Global React `ErrorBoundary`, "Nima bo'ldi — Nega bo'ldi — Nima qilish kerak" 3 qismli intuitiv xatolik ko'rinishi va barcha sahifalarda qayta urinish mexanizmi.
- **Phase 22 — Ishlab Chiqarish Loglari (Logging)**: `logs/mikasa.log`, `logs/backend.log`, `logs/crash.log` fayllari, aylanuvchi (rotating) hajmlar va API kalitlari/parollarni avtomatik maskalash.
- **Phase 23 — Sinovlar (Testing)**: Frontend `node --test` birlik testlari va to'liq E2E hayotiy tsikl (Launch -> Chat -> Voice -> Commands -> Memory -> Scheduler -> Plugins -> Account) integratsiya testlari.
- **Phase 24 — Yuklama Sinovlari (Stress Testing)**: 100, 500 va 1000 ta buyruqlar yuklamasi (1,730 req/s, o'rtacha 1.15ms kechikish), 10,000 marshrut almashinuvi va barqaror RAM.
- **Phase 25 — Windows QA**: Windows 10 va 11 qo'llab-quvvatlovi, 100%-200% High-DPI masshtabi, jarayonlarni toza o'chirish.
- **Phase 26 — Production Build**: `Mikasa-AI-v7.1.0.exe`, MSI va NSIS o'rnatuvchilari, sha256 tekshiruv fayllari.
- **Phase 27 — Reliz Muhandisligi**: Portativ ishga tushiruvchi (`run_portable.bat`), to'liq hujjatlar va reliz qaydlari.

---

## [6.0.0] — Avvalgi Avlod
- CustomTkinter asosidagi ish stoli ko'rinishi (`gui/` katalogida to'liq zaxira sifatida saqlab qolingan).
