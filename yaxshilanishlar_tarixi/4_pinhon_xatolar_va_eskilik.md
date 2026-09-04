# 4-Bosqich: Pinhon Xatolar va Eskilik Tozalash (2026-03-18)

## 1. 🔴 CRITICAL: Agent suhbat tarixini HALI HAM yubormayotgan edi!
* **Oldingi holat:** Biz `ai_engine.py` da `history` parametrini qo'shgandik. LEKIN `agent_planner.py` dan `_ai_call_with_retry` chaqirganda `history=history` ni UMUMAN YUBORMAGAN EKAN. Ya'ni Gemini har bir qadamda suhbat tarixini ko'rmasdi — bitta qadamdan keyingi qadamni unutardi.
* **Sabab:** `agent_ai_call(prompt, system_prompt)` — `history` argumenti yo'q edi.
* **Yangi holat:** `agent_planner.py:314` ga `history=history` qo'shildi. Endi Agent haqiqatan ham **multi-turn** ishlaydi.

## 2. Tool retry noto'g'ri logika
* **Oldingi holat:** `_tool_call_with_retry` faqat `result.get("success")` ni tekshirardi. Ammo ko'pchilik tool'lar `success` kalit qaytarmaydi — faqat `message` qaytaradi. Natijada muvaffaqiyatli natija ham "xato" deb qayta-qayta urinilardi.
* **Yangi holat:** `not result.get("error")` — xato kaliti yo'q bo'lsa muvaffaqiyat.

## 3. Duplikat comment (main.py:283-284)
* **Oldingi holat:** `# ========== Ovozli javob berish ==========` ikki marta yozilgan.
* **Yangi holat:** Bittasi olib tashlandi.

## 4. Legacy txt fayllardan config.json ga migratsiya
* **Oldingi holat:** Foydalanuvchi ismi `data/foydalanuvchi_ismi.txt` da, ovoz turi `data/ovoz_turi.txt` da saqlangan. Bu juda eski yondashuv — har bir sozlama uchun alohida txt fayl.
* **Yangi holat:** Endi `config.json` dan `user.name` va `user.voice_type` sifatida o'qiladi/saqlanadi. Agar eski txt fayllar mavjud bo'lsa, ulardan bir martalik migratsiya qilinadi.

## 5-6. Voice.py sozlamalari backend ga ulandi
* **Oldingi holat:** Voice sahifasidagi "Ovoz turi", "Tezlik" va "TTS Engine" sozlamalari chiroyli ko'rinar edi, lekin o'zgartiring — hech narsa bo'lmasdi. Ular backend ga ulanmagan edi.
* **Yangi holat:** 
  - **Ovoz turi** o'zgartirsa → `config.json` ga saqlanadi + `global_state.ovoz_turi_global` yangilanadi
  - **Tezlik** o'zgartirsa → `config.json` ga saqlanadi
  - **TTS Engine** o'zgartirsa → `config.json` ga saqlanadi
  - **Sahifa ochilganda** → config dan joriy qiymatlar yuklanadi
