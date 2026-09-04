# 3-Bosqich: Arxitektura va GUI Qulayliklari

## 1. Agent Multi-turn History (Agent xotirasi chatni yodda tutadi)
* **Oldingi holat:** Foydalanuvchi bilan yozishayotganda, Agent (Gemini) har bitta yangi savolni alohida birinchi suhbatdek o'qir edi. Agar kishi "buni qanday qilamiz?", keyin "u nima edi o'zi" desa aloqa uzilib qolardi (suhbat tarixi `ai_engine` gacha yuborilmay qolib ketgan edi). Qolaversa, turli bosqichlarda topgan natijalarini ikkinchi savolda unutib qolardi.
* **Sabab:** `agent_ai_call` funksiyasining ichida qabul qilingan `history` argumenti hecham Google yoki OpenRouter API siga ulanib o'tmagandi.
* **Yangi holat:** Butun chatning eng so'nggi 10 ta yozishmalari Gemini o'ziga tushunadigan JSON formatga (`gemini_contents`) formatlanib API'ga ulanuvchi uzatmaga joylashtirildi. OpenRouter API ham ushbu xususiyat bilan jihozlandi. Tizim ancha **aqlli tarzda o'tgan gaplarni eslab fikrlaydi**.

## 2. O'z Bilimidan Javob berish (Web Search o'rniga ChatGPT usuli)
* **Oldingi holat:** "O'zbekiston poytaxti qayer?" deyilsa darrov Web Search qilar, topolmasa Google da qidiruv ochib tashlab, "Kechirasiz internetda yo'q ekan" derdi.
* **Sabab:** System promptda AI ga "Menda tool (internet) bor va uni har dam ishlata olaman" deb noto'g'ri topshiriq va prioritet berilgandi.
* **Yangi holat:** System Prompt to'lig'icha "Brainwash" qilinib qayta yozildi. Unga "Sen juda aqllisan. Tool bilan qidirmasdan oldin miyang izoh bersin! Oddiy savollarga o'z bilimlaringdan javob ber. Web Search faqat Yangilik yoki Valyuta kurslari kabi tez o'zgaruvchan ma'lumotlar uchun," degan ko'rsatmalar taqdim etildi.

## 3. CPU Resurslarini tejash (Smart Algorithms Guard)
* **Oldingi holat:** Dastur UI orqali ishga tushganda orqadagi `Smart Algorithms` deyilgan qismi "122 ta buyruq"ni ikkiga ajratib takror ikki marotaba yuklab olardi. Bunda ayniqsa og'ir bo'lgan AI matn tahlili (TF-IDF model fitting) kompyuter miyasini ikki bora ishga tushirar edi.
* **Yangi holat:** Python xotirasiga `_already_initialized` yoki `tayyor` flag (qorovul) o'rnatildi. Birinchi marta tayyor etilgach, ikkinchi jarayon qo'rqa-qo'rqa ko'chat etsak u shunchaki "Rahmat, bu qilingan" (Return) orqali vaqt (150-200ms) hamda operativ xotirani tejaydi.

## 4. GUI oynasidagi kamchiliklar (Visual Bugs)
* **Hardcoded raqamlar:** `Settings` sahifasida versiya har safar faqat "3.0.0" turardi (hozir "3.1.0"), "Dashboard" dagi Vositalar soni statik ravishda "14 ta" deya qotib qolgandi. Ular qattiq koddan yulib olinib, System fayllardan Avto chaqiriluvchi **dinamik ma'lumotlarga** o'tkazildi. Endi Mikasaning version yoki vositasi kengaysa o'z-o'zidan raqami yangilanadi.
* **Quick Action Tugmalar:** Asosiy oyna (Dashboard) da turadigan Oynali tugmachalar (Musiqa, Valyuta, Ob-havo, Ekran Tahlil) yuzaki `command=None` edi. Shu sababli ko'rinishidangina ishlardi, bossangiz hech ish qilmasdi. Endilikda barchasi to'g'ridan-to'g'ri Agent Bridge ga signal yuboradi.
* **Voice xotirasining o'chishi:** Ovozli oynada gapirilganda bir eski "Oxirgi buyruq" qo'shilsa, avvalgilari yo'q bo'lardi. Bu ro'yxatni buzib, ko'rinishga yomon aloqasi bor edi. Hozir u oxirgi 10 muloqotni chizib yig'ib boradi.
* **Sozlamalar tasdig'i:** Settings bo'limida "Saqlash" tugmasini bossangiz ham hech qanday miltillash va "Tasdiq" ko'rsatilmas edi ("TODO" bo'lib qolgan ekan). Endilikda u Yashil "✅ Saqlandi!" rejimiga soniyaga vizual tarzda kiradi!
