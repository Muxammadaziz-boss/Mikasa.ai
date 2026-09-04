# ========== agent_planner.py ==========
# ReAct (Reason + Act) Agent Planner
# Murakkab vazifalarni bosqichlarga bo'lib bajarish

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ========================================================
# AGENT SYSTEM PROMPT — Tool'lar bilan ishlash uchun
# ========================================================

def agent_system_prompt(tools_description: str, user_knowledge: str = "") -> str:
    """Agent uchun system prompt yaratish"""
    knowledge_section = ""
    if user_knowledge:
        knowledge_section = f"""
FOYDALANUVCHI HAQIDA bilimlar:
{user_knowledge}
Bu ma'lumotlarni suhbatda ishlatib, shaxsiylashtirilgan javoblar ber.
"""
    
    return f"""Sen — "Mikasa AI Agent", aqlli va MUSTAQIL kompyuter yordamchisi.
Sen haqiqiy AI agent san — o'zing FIKRLAB, REJALASHTIR, qaror qilib, vositalarni (tool) ishlatib, ISTALGAN vazifani bajarasan.

ASOSIY QOIDALAR:
1. Har doim O'ZBEK tilida javob ber
2. Samimiy va do'stona bo'l
3. Chala so'zlarni tushun (nutq tanish xatolari)
4. BIRINCHI O'Z BILIMINGDAN JAVOB BER! Sen Gemini AI san — dunyodagi ko'p narsalarni BILASAN.
5. Tool'larni FAQAT kerak bo'lganda ishlat (ilova ochish, ob-havo, valyuta kursi, ekran boshqarish)

⚠️ BILIM SAVOLLARIGA TOOL KERAK EMAS:
Agar foydalanuvchi SAVOL so'rasa (kim, nima, qayerda, qachon, nima uchun, qanday):
→ web_search ISHLATMA! To'g'ridan-to'g'ri final_answer ber!
→ Sen AI san — javobni BILASAN!

MISOL:
Savol: "Elon Musk kim?" → final_answer("Elon Musk — Tesla va SpaceX asoschisi...")
Savol: "Python nima?" → final_answer("Python — dasturlash tili...")
Savol: "O'zbekiston poytaxti?" → final_answer("Toshkent!")
Savol: "Mir va Mira kim?" → final_answer("Bu haqida bilimim yo'q, tushuntirsangiz yordam beraman")

web_search FAQAT real-time ma'lumot uchun: bugungi yangiliklar, joriy narxlar, hozirgi ob-havo.

{knowledge_section}

MAVJUD TOOL'LAR (vositalar):
{tools_description}

JAVOB FORMATI:
Sen har bir qadamda JSON formatda javob berasan. 3 xil javob bor:

1) TOOL CHAQIRISH (biror narsa qilish kerak bo'lsa):
{{"action": "tool_call", "tool": "<tool_nomi>", "params": {{...}}, "thought": "<nima uchun bu tool kerak>"}}

2) YAKUNIY JAVOB (vazifa tugagan bo'lsa):
{{"action": "final_answer", "response": "<foydalanuvchiga javob>", "tools_used": ["<ishlatilgan tool'lar>"]}}

3) BILIM SAQLASH (foydalanuvchi haqida muhim narsa bilsang):
{{"action": "tool_call", "tool": "knowledge", "params": {{"action": "save", "key": "<kalit>", "value": "<qiymat>"}}, "thought": "Foydalanuvchi haqida yangi ma'lumot"}}

========== MUSTAQIL VAZIFA BAJARISH ==========

Sen MURAKKAB vazifalarni va DESKTOP ilovalarni mustaqil boshqarasan. QOIDALAR:

1) TEKSHIR: Ilova ishlayaptimi? `app_check` bilan tekshir
2) OCH/FOKUS: `system_control` qilib och yoki mavjud bo'lsa fokusga ol
3) KO'R: Ekranda nima borligini ko'rish uchun `screen_analyze("Ekranda nimalar bor?")` ishlat
4) BOS & YOZ: Ekranda ko'rgan koordinataga `screen_click` bilan bos, matnni `keyboard_type` bilan yoz
5) SO'RA: Noaniq bo'lsa `ask_user` bilan so'ra
6) KOD YOZ: Fayllarni yozish uchun `file_write` ishlat (YO'LNI SO'RA!)

MISOL 1 — "Login sahifa yoz":
Qadam 1: app_check(category="code_editor") → Cursor topildi
Qadam 2: ask_user("Qayerga va qaysi style'da yozaman?") → "Desktop/login ga, sof CSS"
Qadam 3: file_write("C:\\Users\\...\\Desktop\\login\\index.html", content="...")
Qadam 4: file_manager(action="open", path="C:\\...\\index.html")
Qadam 5: final_answer("Tayyor!")

MISOL 2 — "Telegramda Fergana guruhiga kirib hujjatni och":
Qadam 1: app_check(app_name="telegram") → "running": True
Qadam 2: system_control("open_telegram") → Oyna fokusga olindi
Qadam 3: keyboard_shortcut("ctrl+f") → Qidiruv ochildi
Qadam 4: keyboard_type("Fergana Startup") → Matn yozildi
Qadam 5: screen_analyze("Fergana guruhi qaysi koordinatada?") → "x=300, y=150"
Qadam 6: screen_click(x=300, y=150) → Guruh ochildi
Qadam 7: screen_analyze("docx fayl qayerda?") → "x=400, y=500"
Qadam 8: screen_click(x=400, y=500) → Fayl ochildi
Qadam 9: final_answer("Hujjat ochildi!")

========== MUHIM QOIDALAR ==========
- O'Z BILIMING: Agar web_search natija bermasa yoki "no_results" qaytarsa — O'Z BILIMINGDAN JAVOB BER! Sen aqlli AI san — ko'p narsani BILASAN. Foydalanuvchiga "topilmadi" DEMA, o'zing javob ber!
- ODDIY SAVOLLAR: Agar savol oddiy (kim, nima, qayerda), tool ishlatmasdan to'g'ridan-to'g'ri final_answer ber.
- KO'R VA BOS: Brauzer yoki ilovalarni boshlamoqchi bo'lsang faqat "ochildi" deb to'xtama. screen_analyze bilan tekshirib, screen_click va keyboard_type qilib ISHNI BAJAR.
- TEKSHIR: Ilova ochishdan oldin app_check qiling.
- SO'RA: file_write da fayl yo'li noaniq bo'lsa ask_user qiling.
- XATO: Xato bo'lsa, qayta urinib ko'r.
- JSON formatda qaytar!
"""


# ========================================================
# REACT AGENT — Asosiy Agent Loop
# ========================================================

class ReActAgent:
    """ReAct pattern bo'yicha ishlaydigan agent.
    
    Loop:
    1. Thought — nima qilish kerak?
    2. Action — tool tanlash va chaqirish
    3. Observation — natijani ko'rish
    4. Agar tayyor — Answer. Aks holda → 1 ga qaytish.
    """
    
    MAX_STEPS = 15      # Murakkab vazifalar uchun yetarli qadamlar
    MAX_RETRIES = 2     # Tool xato bo'lsa qayta urinish
    AI_TIMEOUT = 30     # AI javob kutish (soniya)
    
    def __init__(self, tool_registry, ai_call_func, memory=None):
        self.tools = tool_registry
        self.ai_call = ai_call_func
        self.memory = memory
        self._step_callbacks = []
        self._complete_callbacks = []
        self._is_running = False
    
    def on_step(self, callback):
        """Har bir qadam uchun callback (GUI yangilash)"""
        self._step_callbacks.append(callback)
    
    def on_complete(self, callback):
        """Agent tugaganda callback.
        Signature: callback(result: dict)
        """
        self._complete_callbacks.append(callback)
    
    @property
    def is_running(self):
        return self._is_running
    
    def _notify(self, step_num, step_type, data):
        for cb in self._step_callbacks:
            try:
                cb(step_num, step_type, data)
            except Exception as e:
                logger.error(f"Step callback xatolik: {e}")
    
    def _notify_complete(self, result):
        for cb in self._complete_callbacks:
            try:
                cb(result)
            except Exception as e:
                logger.error(f"Complete callback xatolik: {e}")
    
    # ========== ASYNC RUN ==========
    
    def run_async(self, user_input: str, conversation_history: list = None):
        """Agent ni background thread da ishga tushirish (GUI muzlamasligi).
        
        Natija on_complete callback orqali qaytariladi.
        """
        import threading
        
        if self._is_running:
            logger.warning("Agent allaqachon ishlamoqda")
            return
        
        def _worker():
            try:
                result = self.run(user_input, conversation_history)
                self._notify_complete(result)
            except Exception as e:
                logger.error(f"Agent async xatolik: {e}")
                self._notify_complete({
                    "response": "Agent xatolik yuz berdi.",
                    "tools_used": [], "steps": [], "success": False
                })
            finally:
                self._is_running = False
        
        self._is_running = True
        thread = threading.Thread(target=_worker, daemon=True, name="AgentWorker")
        thread.start()
    
    # ========== SYNC RUN ==========
    
    def run(self, user_input: str, conversation_history: list = None) -> dict:
        """Agent ni ishga tushirish (sinxron)."""
        self._is_running = True
        
        try:
            return self._run_internal(user_input, conversation_history)
        finally:
            self._is_running = False
    
    def _run_internal(self, user_input: str, conversation_history: list = None) -> dict:
        # System prompt yaratish
        user_knowledge = ""
        if self.memory:
            user_knowledge = self.memory.get_knowledge_summary()
        
        system_prompt = agent_system_prompt(
            self.tools.tools_prompt(),
            user_knowledge
        )
        
        history = conversation_history or []
        history.append({"role": "user", "content": user_input})
        
        steps = []
        tools_used = []
        final_response = None
        
        for step_num in range(1, self.MAX_STEPS + 1):
            logger.info(f"Agent qadam {step_num}/{self.MAX_STEPS}")
            
            # AI dan javob olish (retry bilan)
            ai_response = self._ai_call_with_retry(history, steps, system_prompt, step_num)
            if ai_response is None:
                return {
                    "response": "AI bilan aloqa bo'lmadi. Keyinroq urinib ko'ring.",
                    "tools_used": tools_used, "steps": steps, "success": False
                }
            
            # JSON ni parse qilish
            parsed = self._parse_response(ai_response)
            if not parsed:
                logger.warning(f"AI javob parse qilinmadi: {ai_response[:200]}")
                return {
                    "response": ai_response.strip() if ai_response else "Tushunmadim, qaytadan urinib ko'ring.",
                    "tools_used": tools_used, "steps": steps, "success": True
                }
            
            action = parsed.get("action", "")
            
            # ---- FINAL ANSWER ----
            if action == "final_answer":
                final_response = parsed.get("response", "Bajarildi!")
                used = parsed.get("tools_used", tools_used)
                steps.append({"step": step_num, "type": "final_answer", "response": final_response})
                self._notify(step_num, "final_answer", {"response": final_response})
                
                if self.memory:
                    self.memory.add_conversation(user_input, final_response)
                
                return {
                    "response": final_response,
                    "tools_used": used if used else tools_used,
                    "steps": steps, "success": True
                }
            
            # ---- TOOL CALL (retry bilan) ----
            elif action == "tool_call":
                tool_name = parsed.get("tool", "")
                params = parsed.get("params", {})
                thought = parsed.get("thought", "")
                
                self._notify(step_num, "thought", {"thought": thought, "tool": tool_name})
                
                # Tool ni chaqirish (RETRY LOGIC)
                result = self._tool_call_with_retry(tool_name, params, step_num)
                tools_used.append(tool_name)
                
                step_data = {
                    "step": step_num, "type": "tool_call",
                    "tool": tool_name, "params": params,
                    "thought": thought, "result": result
                }
                steps.append(step_data)
                self._notify(step_num, "tool_result", step_data)
                
                history.append({"role": "assistant", "content": json.dumps(parsed, ensure_ascii=False)})
                
                # Xato bo'lsa, Agent ga yaxshiroq kontekst berish
                if result.get("success") == False or result.get("error"):
                    error_msg = result.get("error", "Noma'lum xato")
                    available_tools = self.tools.list_names()
                    history.append({"role": "user", "content": (
                        f"XATOLIK: {error_msg}. "
                        f"Boshqa tool yoki usul bilan urinib ko'r. "
                        f"Mavjud tool'lar: {', '.join(available_tools)}"
                    )})
                else:
                    history.append({"role": "user", "content": f"Tool natijasi: {json.dumps(result, ensure_ascii=False)}"})
                
                logger.info(f"Tool '{tool_name}' natija: {result}")
            
            else:
                response_text = parsed.get("response", ai_response)
                return {
                    "response": response_text,
                    "tools_used": tools_used, "steps": steps, "success": True
                }
        
        # MAX_STEPS tugadi
        logger.warning("Agent maksimal qadamlar soniga yetdi")
        return {
            "response": final_response or "Vazifa murakkab ekan, keyinroq qaytadan urinib ko'ring.",
            "tools_used": tools_used, "steps": steps, "success": False
        }
    
    # ========== RETRY LOGIC ==========
    
    def _ai_call_with_retry(self, history, steps, system_prompt, step_num) -> Optional[str]:
        """AI ni chaqirish — 2 marta urinish"""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.ai_call(
                    prompt=self._build_prompt(history, steps),
                    system_prompt=system_prompt
                )
                if response:
                    return response
            except Exception as e:
                logger.warning(f"AI urinish {attempt + 1}/{self.MAX_RETRIES + 1} xatolik: {e}")
                if attempt < self.MAX_RETRIES:
                    self._notify(step_num, "error", {"error": f"AI javob bermadi, qayta urinilmoqda... ({attempt + 1})"})
                    import time
                    time.sleep(1)
        
        self._notify(step_num, "error", {"error": "AI bilan aloqa bo'lmadi"})
        return None
    
    def _tool_call_with_retry(self, tool_name: str, params: dict, step_num: int) -> dict:
        """Tool ni chaqirish — xato bo'lsa qayta urinish"""
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            result = self.tools.call(tool_name, **params)
            
            if result.get("success"):
                return result
            
            last_error = result.get("error", "Noma'lum xatolik")
            logger.warning(f"Tool '{tool_name}' urinish {attempt + 1} xatolik: {last_error}")
            
            if attempt < self.MAX_RETRIES:
                self._notify(step_num, "error", {"error": f"Tool '{tool_name}' xato, qayta urinilmoqda..."})
                import time
                time.sleep(0.5)
        
        return {"success": False, "error": f"Tool '{tool_name}' {self.MAX_RETRIES + 1} urinishda ham ishlamadi: {last_error}"}
    
    # ========== YORDAMCHI FUNKSIYALAR ==========
    
    def _build_prompt(self, history: list, steps: list) -> str:
        parts = []
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                parts.append(f"Foydalanuvchi: {content}")
            elif role == "assistant":
                parts.append(f"Agent: {content}")
        
        if steps:
            parts.append(f"\nHozircha {len(steps)} ta qadam bajarildi. Keyingi qadamni JSON formatda ber.")
        
        return "\n".join(parts)
    
    def _parse_response(self, text: str) -> Optional[dict]:
        if not text:
            return None
        
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        brace_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        
        start = text.find('{')
        if start >= 0:
            depth = 0
            for i, c in enumerate(text[start:], start):
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except json.JSONDecodeError:
                            break
        
        return None

