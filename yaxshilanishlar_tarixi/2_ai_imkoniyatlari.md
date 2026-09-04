# 2-Bosqich: AI Qobiliyatlari va Aqlli Agent

## 1. Haqiqiy Web Search xususiyati
* **Oldingi holat:** AI "falon narsani qidir" desa shunchaki kompyuterdagi brauzerni qidiruv sahifasi bilan ochib qo'yardi. "Qidirdim" deb jim turardi.
* **Sabab:** Qidiruv natijasini o'qib AI o'zlashtira olmasdi, faqat `webbrowser.open` yozilgandi.
* **Yangi holat:** DuckDuckGo Instant Answer API integratsiya qilindi. Endi Mikasa AI qidiruv natijalarining **abstrakt (qisqacha) javobini** o'zi o'qib, brauzer ochmasdan to'g'ridan to'g'ri gapirib bera oladi. Qachonki umuman javob topilmasa, keyingina ChatGPT singari **o'z bilimidan** javob berishga harakat qiladi.

## 2. Dynamic App Launcher (Istalgan dasturni ochish)
* **Oldingi holat:** AI ga "notepaddni och" desa ochar edi, lekin ba'zi noma'lum ilovalarni qayerdan ochishni bilmasdan qulab tushar edi yoki "Bunday ilova yo'q" deb qaytarardi.
* **Yangi holat:** `open_any_app` degan yangi yordamchi algoritm qo'shildi! Endi Windows muhitida o'zi maxsus qidiruv qilib ocha oladi. Shuningdek, ilovalarga qisqa laqablar (aliases) berildi (masalan "word" - "winword.exe", "steam" va hokazo).

## 3. Foydalanuvchi Xotirasini Inyektsiya (System prompt injection)
* **Oldingi holat:** User haqidagi yig'ilgan bilimlarni Mikasa AI o'z yodida (xotira modulida) saqlar, ammo API (Gemini/OpenRouter) orqali yuborilayotganda bu ma'lumotlar yuborilmas edi. Natijada chat paytida AI siz haqingizdagi bilimlarni unitib qo'ygandek aloqada bo'lardi.
* **Sabab:** AI promptlariga dinamik ravishda ma'lumot qisimi qo'shilmagan edi.
* **Yangi holat:** `ai_engine.py` dagi AI Prompt tizimiga o'zgartirish kiritildi. Qachonki suhbat yuzaga kelsa, xotiradagi bor bilim (fishing, musiqiy did va h.k.) AI qulog'iga shivirlanadi (Prompt Injection in System message) va Mikasa **sizni kimligingizni tanib qolgan holda** o'ziga xos munosabat bildiradi.

## 4. Agent Error Recovery (O'z xatosini anglashi)
* **Oldingi holat:** ReAct AI tool ishlatishda formatni buzsa yoki xato parametrlarni bersa, `Observation: ValueError` kabi python xatosi qaytarilib butun agent zanjiri to'xtab qolardi va mijoz "Tushunmadim" degan xato xabar olar edi.
* **Sabab:** Agent o'z xatosini "ko'rmas" va uni qanday tuzatishni bilmasdi.
* **Yangi holat:** Xato ro'y berganda dastur qulamaydi! Xato matni va mavjud muqobil vositalar ro'yxatini qayta Agent xotirasiga yuboriladi. Bunda AI asbobini ishlatishdagi xatoni o'qiydi ("Men qayerda xato qildim o'zi?") va to'g'ri instrument yordamida ikkinchi marta qayta ishlaydi. Bu haqiqiy aqlli agent xususiyati.
