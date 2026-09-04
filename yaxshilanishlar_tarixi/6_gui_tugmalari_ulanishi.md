# 6-Bosqich: GUI Barcha Tugmalari va Elementlarini Ulanishi (2026-03-21)

Ushbu bosqichda UI da vizual mavjud bo'lgan, ammo click/change eventlariga ega bo'lmagan (decorativ) yoki backend ga ulanmagan barcha 20+ ko'proq elementlar to'liq ishchi holatga keltirildi.

## 1. Xotira Markazi (`memory.py`)
- **Tuzatilganlar:**
  - `on_show` metodi orqali sahifa ochilganda barcha ma'lumotlar jonli yuklanadi.
  - **Profil qismi:** "Saqlash" tugmasi bosilganda ma'lumotlar `config.json` ga va `main.global_state` ga yoziladi.
  - **Bilimlar qismi:** Yangi bilim qo'shish formulasi backend (`AgentMemory`) ga yozadi. Barcha bilimlar ro'yxatda namoyon bo'ladi.
  - **Suhbat tarixi qismi:** Backend dan ohirgi suhbatlar chiroyli chat formatida o'qib kelinadi.
  - **Xotira statistikasi:** Yuqoridagi 4 ta karta (kontekst, suhbatlar, bilimlar) ro'stdan ham backenddagi raqamlarga moslashdi.
  - **Eksport:** Barcha AI bilim va tarixi `.json` fayl qilib yuklab olinishi ta'minlandi.

## 2. Buyruqlar Markazi (`commands.py`)
- **Tuzatilganlar:**
  - Tool kartalar endi statik 14 ta emas, balki `ToolRegistry` dan (backend dan) interaktiv o'qib olinadigan bo'ldi (20+).
  - Har bir toll kartasini bossa — avtomatik ravishda `chat.py` sahifasiga o'tib "shu tool ni ishlatib ko'rsat" deb input qilib beradi.
  - Yuqoridagi qidiruv input paneli (Search) endi tool larni jonli tarzda (live-filter) saralaydi.

## 3. Rejalashtiruvchi (`scheduler.py`)
- **Tuzatilganlar:**
  - "Yangi vazifa" formulasidan kiritilgan eslatmalar shunchaki UI ro'yxatga tushib qolmasdan, haqiqiy `agent_scheduler.py` tizimiga (multithreading) topshiriladi.
  - O'ng tomondagi ekranda bugungi sana va jonli ishlaydigan soat paydo bo'ldi. Timeline da kelgusi 5 ta vazifa ko'rinadi.

## 4. Chat Sahifasi (`chat.py`)
- **Tuzatilganlar:**
  - "Chat | Agent | Vision" degan switch paneliga callback ulanib, input qatori uchun to'g'ri maslahatlar chiqishi ta'minlandi.

## 5. Plaginlar (`plugins.py`)
- **Tuzatilganlar:**
  - `core/agent_plugins.py` dagi `PLUGINS_DIR` dan (dinamik) fayllar o'qiladi.
  - "Papkani ochish" tugmasi orqali Windows Explorer da to'g'ridan to'g'ri plaginlar turgan papka ochiladi.
  - Toggle switch orqali plaginlarni o'chirish/yoqish tizimi fayllar oldiga `_` belgisi qo'shish mexanizmi bilan ishga tushirildi.
  - "Shablon yaratish" tugmalari orqali avtomatik tarzda `my_website.json` kabi ishalydigan tool strukturasi hosil qilinadi.

## 6. Sozlamalar (`settings.py`)
- **Tuzatilganlar:**
  - Barcha input, switch, dropdown va rang/tema tanlovlari endi vizual emas, balki ro'stdan `config.py` funksiyalaridan foydalanib `config.json` ga saqlanadigan qilindi.
  - Dastur qayta ochilganda ushbu formlar faqat saqlangan sozlamalarni ko'rsatadi.
  - "Keshni tozalash" tugmasi barcha ichki `__pycache__` larni tozalaydi.
  - "Loglarni tozalash" barcha eski log rekordlarini tozalay oladi.
  - Tema (Light/Dark) ni "Saqlash" tugmasini bosganda real-time da almashish tizimi yoqildi.
