# 5-Bosqich: Xavfli Buyruqlar va App-First Logika (2026-03-18)

## 1. Xavfli buyruq tasdiqlash — sabrsiz edi
* **Oldingi holat:** User "kompyuterni o'chir" desa, Mikasa "Kompyuter o'chirilmoqda. Tasdiqlaysizmi?" deb so'rar edi. Lekin foydalanuvchi gapirishga ulgurmasa yoki mic tinglolmasa — darhol "Buyruq bekor qilindi" deb berar edi. Ya'ni user nima desa ham — bekor qiladi. Hech qachon bajarilmasdi.
* **Sabab:** `tingla()` faqat 1 marta chaqirilardi. Agar javob `None` bo'lsa (yoki "ha" topilmasa) — darrov bekor.
* **Yangi holat:** Endi **2 marta** so'raladi. Birinchi javob tushunarsiz bo'lsa, ikkinchi marta "Tushunmadim. 'Ha' bajaraman, 'Yo'q' bekor qilaman" deb tushunarli tarzda qaytadan so'raydi. Qo'shimcha tasdiq so'zlari ham qo'shildi: `"bo'pti"`, `"ok"`, `"davom"`. Rad etish uchun ham maxsus so'zlar: `"yo'q"`, `"bekor"`, `"kerak emas"`.

## 2. Musiqa qidirish — desktop app tekshirish
* **Oldingi holat:** `musiqa_qidir()` DOIMO brauzerni ochardi — Yandex Music da ham, Spotify da ham. Agar foydalanuvchi allaqachon Yandex Music desktop ilovasini ishlatayotgan bo'lsa ham, Mikasa brauzerda ikkinchi oyna ochardi.
* **Sabab:** `webbrowser.open(url)` yagona yo'l edi, hech qanday desktop ilova qidirish yo'q edi.
* **Yangi holat:** 3 bosqichli aqlli logika:
  1. **Jarayon tekshirish:** `psutil.process_iter()` orqali kompyuterda Yandex Music yoki Spotify jarayoni allaqachon ishlamoqdami tekshiriladi. Agar ochiq bo'lsa — oynani oldinga olib keladi va keyboard shortcut bilan ilova ichidagi qidiruvga yozadi.
  2. **O'rnatilgan ilova:** Agar jarayon yo'q, lekin `.exe` fayl qattiq diskda mavjud bo'lsa — ilovani ochib beradi.
  3. **Browser fallback:** Faqat ilova umuman o'rnatilmagan bo'lgandagina brauzer ochiladi.
