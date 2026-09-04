# ========== smart_algorithms.py ==========
# Aqlli algoritmlar moduli — Mikasa AI uchun
# Levenshtein, TF-IDF, LRU Cache, Rate Limiter, Markov Chain, Priority Queue

import time
import json
import os
import math
import logging
import re
from collections import OrderedDict, defaultdict
from threading import RLock

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Loyiha ildizi

# ========================================================
# 1. LEVENSHTEIN DISTANCE — Noto'g'ri so'zlarni tuzatish
# ========================================================

def levenshtein(s1, s2):
    """Ikki string orasidagi Levenshtein masofasini hisoblash.
    Qancha kichik bo'lsa — shuncha o'xshash.
    
    Masalan:
        levenshtein("yutuq", "yutub") → 1
        levenshtein("telegram", "telegra") → 1
        levenshtein("musiqa", "muzika") → 2
    """
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    # Dynamic Programming — O(n*m) vaqt, O(n) xotira
    oldingi_qator = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        joriy_qator = [i + 1]
        for j, c2 in enumerate(s2):
            # Qo'shish, o'chirish yoki almashtirish
            qoshish = oldingi_qator[j + 1] + 1
            ochirish = joriy_qator[j] + 1
            almashtirish = oldingi_qator[j] + (c1 != c2)
            joriy_qator.append(min(qoshish, ochirish, almashtirish))
        oldingi_qator = joriy_qator
    
    return oldingi_qator[-1]


def eng_yaqin_buyruq(matn, buyruqlar_dict, chegara=3):
    """Foydalanuvchi matni asosida eng yaqin buyruqni topish.
    
    Args:
        matn: Foydalanuvchi kiritgan matn (masalan: "yutuq")
        buyruqlar_dict: Buyruqlar lug'ati {"youtube": "open_youtube", ...}
        chegara: Maksimal qabul qilinadigan masofa (default: 3)
    
    Returns:
        (buyruq_nomi, intent, masofa) yoki None
    """
    matn_lower = matn.lower().strip()
    eng_yaqin = None
    eng_kichik_masofa = float('inf')
    
    def _mos_keladi(soz, buyruq, masofa):
        """Levenshtein natijasi ishonchli ekanligini tekshirish"""
        # Qisqa so'zlar uchun Levenshtein ishlamaydi (false positive ko'p)
        if len(soz) < 4 or len(buyruq) < 4:
            return False
        # Birinchi harf mos kelishi kerak (yana→sana kabi xatolarni oldini oladi)
        if soz[0] != buyruq[0]:
            return False
        # Qisqa so'zlar (4-5 harf) uchun faqat 1 ta xatoga ruxsat
        if max(len(soz), len(buyruq)) <= 5:
            return masofa <= 1
        # Uzunroq so'zlar uchun — 30% dan oshmasligi kerak
        max_masofa = max(len(soz), len(buyruq)) * 0.3
        return masofa <= max_masofa and masofa <= chegara
    
    for buyruq_nomi, intent in buyruqlar_dict.items():
        buyruq_lower = buyruq_nomi.lower()
        
        # To'liq so'z bilan solishtirish
        masofa = levenshtein(matn_lower, buyruq_lower)
        if masofa < eng_kichik_masofa and _mos_keladi(matn_lower, buyruq_lower, masofa):
            eng_kichik_masofa = masofa
            eng_yaqin = (buyruq_nomi, intent, masofa)
        
        # Matn ichidan har bir so'zni tekshirish
        for soz in matn_lower.split():
            masofa = levenshtein(soz, buyruq_lower)
            if masofa < eng_kichik_masofa and _mos_keladi(soz, buyruq_lower, masofa):
                eng_kichik_masofa = masofa
                eng_yaqin = (buyruq_nomi, intent, masofa)
    
    if eng_yaqin and eng_kichik_masofa <= chegara:
        logger.debug(f"Levenshtein: '{matn}' → '{eng_yaqin[0]}' (masofa={eng_kichik_masofa})")
        return eng_yaqin
    
    return None


# ========================================================
# 2. TF-IDF + COSINE SIMILARITY — Aqlli buyruq aniqlash
# ========================================================

class TFIDFMatcher:
    """TF-IDF asosida buyruqlarni aniqlash.
    scikit-learn kerak bo'lmaydi — o'zimiz yozdik!
    
    Ishlash tartibi:
    1. Buyruqlar bazasini o'rgatish (fit)
    2. Foydalanuvchi matnini vektorlashtirish
    3. Cosine Similarity orqali eng mos buyruqni topish
    """
    
    def __init__(self):
        self._lock = RLock()
        self.buyruqlar = {}        # {"youtube och": "open_youtube", ...}
        self.idf = {}              # Inverse Document Frequency
        self.tfidf_vektorlar = {}  # har bir buyruq uchun TF-IDF vektori
        self.tayyor = False
    
    def fit(self, buyruqlar_dict):
        """Buyruqlar bazasini o'rgatish.
        
        Args:
            buyruqlar_dict: {"youtube": "open_youtube", "musiqa": "music_search", ...}
        """
        with self._lock:
            self.buyruqlar = buyruqlar_dict.copy()
            
            # Barcha hujjatlar (har bir buyruq bir hujjat)
            hujjatlar = {}
            for buyruq_nomi, intent in buyruqlar_dict.items():
                sozlar = self._tokenize(buyruq_nomi)
                hujjatlar[buyruq_nomi] = sozlar
            
            # IDF hisoblash
            N = len(hujjatlar)
            soz_hujjat_soni = defaultdict(int)
            for sozlar in hujjatlar.values():
                for soz in set(sozlar):
                    soz_hujjat_soni[soz] += 1
            
            self.idf = {}
            for soz, soni in soz_hujjat_soni.items():
                self.idf[soz] = math.log((N + 1) / (soni + 1)) + 1  # Smooth IDF
            
            # TF-IDF vektorlarini hisoblash
            self.tfidf_vektorlar = {}
            for buyruq_nomi, sozlar in hujjatlar.items():
                self.tfidf_vektorlar[buyruq_nomi] = self._tfidf_vektor(sozlar)
            
            self.tayyor = True
            logger.debug(f"TF-IDF: {len(buyruqlar_dict)} ta buyruq o'rgatildi")
    
    def predict(self, matn, min_score=0.15):
        """Eng mos buyruqni aniqlash.
        
        Args:
            matn: Foydalanuvchi matni
            min_score: Minimal cosine similarity (0-1)
        
        Returns:
            (intent, score) yoki None
        """
        if not self.tayyor:
            return None
        
        with self._lock:
            matn_sozlar = self._tokenize(matn)
            matn_vektor = self._tfidf_vektor(matn_sozlar)
            
            if not matn_vektor:
                return None
            
            eng_yaxshi = None
            eng_yaxshi_score = 0
            
            for buyruq_nomi, buyruq_vektor in self.tfidf_vektorlar.items():
                score = self._cosine_similarity(matn_vektor, buyruq_vektor)
                if score > eng_yaxshi_score:
                    eng_yaxshi_score = score
                    eng_yaxshi = buyruq_nomi
            
            if eng_yaxshi and eng_yaxshi_score >= min_score:
                intent = self.buyruqlar[eng_yaxshi]
                logger.debug(f"TF-IDF: '{matn}' → '{eng_yaxshi}' ({intent}) score={eng_yaxshi_score:.3f}")
                return (intent, eng_yaxshi_score)
            
            return None
    
    def _tokenize(self, matn):
        """Matnni so'zlarga bo'lish"""
        matn = matn.lower().strip()
        matn = re.sub(r"['\u2018\u2019\u02BB`]", "", matn)  # Apostroflarni olib tashlash
        return [s for s in matn.split() if len(s) >= 2]
    
    def _tfidf_vektor(self, sozlar):
        """So'zlar ro'yxati uchun TF-IDF vektori"""
        if not sozlar:
            return {}
        
        # TF hisoblash
        tf = defaultdict(float)
        for soz in sozlar:
            tf[soz] += 1.0 / len(sozlar)
        
        # TF-IDF
        vektor = {}
        for soz, tf_val in tf.items():
            idf_val = self.idf.get(soz, 1.0)
            vektor[soz] = tf_val * idf_val
        
        return vektor
    
    def _cosine_similarity(self, v1, v2):
        """Ikki vektor orasidagi cosine similarity"""
        # Umumiy so'zlar
        umumiy = set(v1.keys()) & set(v2.keys())
        if not umumiy:
            return 0.0
        
        # Dot product
        dot = sum(v1[s] * v2[s] for s in umumiy)
        
        # Normalar
        norm1 = math.sqrt(sum(val ** 2 for val in v1.values()))
        norm2 = math.sqrt(sum(val ** 2 for val in v2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)


# ========================================================
# 3. LRU CACHE — Tez-tez buyruqlarni keshlash
# ========================================================

class BuyruqCache:
    """LRU (Least Recently Used) kesh — tez-tez ishlatiladigan
    buyruqlarni xotirada saqlash.
    
    Qanday ishlaydi:
    - Birinchi marta → algoritmlar ishlaydi → natija keshga yoziladi
    - Ikkinchi marta → keshdan olinadi (tez!)
    - Kesh to'lsa → eng eski (kam ishlatilgan) element o'chiriladi
    """
    
    def __init__(self, maxsize=200):
        self._lock = RLock()
        self._cache = OrderedDict()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0
    
    def get(self, key):
        """Keshdan qiymat olish. Topilmasa None qaytaradi."""
        with self._lock:
            key = key.lower().strip()
            if key in self._cache:
                # LRU: oxiriga ko'chirish (eng yangi)
                self._cache.move_to_end(key)
                self._hits += 1
                logger.debug(f"Cache HIT: '{key}' (hits={self._hits})")
                return self._cache[key]
            self._misses += 1
            return None
    
    def put(self, key, value):
        """Keshga qiymat yozish."""
        with self._lock:
            key = key.lower().strip()
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            
            # Kesh to'lsa — eng eskisini o'chirish
            while len(self._cache) > self._maxsize:
                eng_eski = self._cache.popitem(last=False)
                logger.debug(f"Cache EVICT: '{eng_eski[0]}'")
    
    def clear(self):
        """Keshni tozalash."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    @property
    def statistika(self):
        """Kesh statistikasi."""
        with self._lock:
            jami = self._hits + self._misses
            foiz = (self._hits / jami * 100) if jami > 0 else 0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "jami": jami,
                "foiz": round(foiz, 1),
                "hajm": len(self._cache),
                "max": self._maxsize
            }


# ========================================================
# 4. RATE LIMITER — API so'rovlarni cheklash
# ========================================================

class RateLimiter:
    """Token Bucket algoritmi — API so'rovlarni cheklash.
    
    Masalan: 
        limiter = RateLimiter(max_calls=15, period=60)
        # 60 soniya ichida maksimum 15 ta so'rov
    """
    
    def __init__(self, max_calls=15, period=60):
        self._lock = RLock()
        self.max_calls = max_calls
        self.period = period  # soniyada
        self._calls = []      # vaqt belgilari ro'yxati
        self._blocked_until = 0
    
    def is_allowed(self):
        """So'rov yuborish mumkinmi?
        
        Returns:
            (True, qoldiq_son) yoki (False, kutish_vaqti_soniya)
        """
        with self._lock:
            hozir = time.time()
            
            # Bloklangan bo'lsa
            if hozir < self._blocked_until:
                kutish = round(self._blocked_until - hozir, 1)
                return False, kutish
            
            # Eski so'rovlarni tozalash
            self._calls = [t for t in self._calls if hozir - t < self.period]
            
            if len(self._calls) < self.max_calls:
                self._calls.append(hozir)
                qoldiq = self.max_calls - len(self._calls)
                return True, qoldiq
            else:
                # Limit tugagan — qachon ochilishini hisoblash
                eng_eski = min(self._calls)
                kutish = round(self.period - (hozir - eng_eski), 1)
                return False, kutish
    
    def block(self, seconds=60):
        """Vaqtinchalik bloklash (masalan: 429 javob kelganda)."""
        with self._lock:
            self._blocked_until = time.time() + seconds
            logger.warning(f"RateLimiter: {seconds}s davomida bloklandi")
    
    @property
    def statistika(self):
        """Rate limiter holati."""
        with self._lock:
            hozir = time.time()
            faol = [t for t in self._calls if hozir - t < self.period]
            return {
                "ishlatilgan": len(faol),
                "max": self.max_calls,
                "qoldiq": self.max_calls - len(faol),
                "period": self.period
            }


# ========================================================
# 5. MARKOV CHAIN — Keyingi buyruqni bashorat qilish
# ========================================================

class BuyruqBashorat:
    """Markov Chain asosida keyingi buyruqni bashorat qilish.
    
    Ishlashi:
    1. Foydalanuvchi buyruqlar tarixidan o'rganadi
    2. "YouTube ochildi" → 70% "birinchi video", 20% "musiqa", 10% boshqa
    3. Bashorat natijasini GUI da ko'rsatish mumkin
    """
    
    def __init__(self):
        self._lock = RLock()
        # {oldingi_buyruq: {keyingi_buyruq: soni}}
        self._transitions = defaultdict(lambda: defaultdict(int))
        self._jami_soni = defaultdict(int)
        self._fayl = os.path.join(BASE_DIR, "data", "markov_data.json")
        self._yuklandi = False
        self._yukla()
    
    def qosh(self, oldingi, keyingi):
        """Yangi o'tishni qo'shish.
        
        Args:
            oldingi: Oldingi buyruq intent (masalan: "open_youtube")
            keyingi: Keyingi buyruq intent (masalan: "youtube_first_video")
        """
        with self._lock:
            self._transitions[oldingi][keyingi] += 1
            self._jami_soni[oldingi] += 1
            
            # Har 10 ta yangi o'tishda faylga saqlash
            if sum(self._jami_soni.values()) % 10 == 0:
                self._saqlash()
    
    def bashorat(self, oxirgi_buyruq, top_n=3):
        """Keyingi ehtimoliy buyruqlarni bashorat qilish.
        
        Args:
            oxirgi_buyruq: Oxirgi bajarilgan buyruq intent
            top_n: Nechta bashorat qaytarish
        
        Returns:
            [(intent, ehtimol), ...] — ehtimol bo'yicha tartiblangan
        """
        with self._lock:
            if oxirgi_buyruq not in self._transitions:
                return []
            
            jami = self._jami_soni[oxirgi_buyruq]
            if jami == 0:
                return []
            
            natijalar = []
            for keyingi, soni in self._transitions[oxirgi_buyruq].items():
                ehtimol = round(soni / jami, 3)
                natijalar.append((keyingi, ehtimol))
            
            # Ehtimol bo'yicha tartiblash (kattadan kichikka)
            natijalar.sort(key=lambda x: x[1], reverse=True)
            return natijalar[:top_n]
    
    def _yukla(self):
        """Fayldan yuklash."""
        try:
            if os.path.exists(self._fayl):
                with open(self._fayl, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for oldingi, keyingilar in data.get("transitions", {}).items():
                    for keyingi, soni in keyingilar.items():
                        self._transitions[oldingi][keyingi] = soni
                        self._jami_soni[oldingi] += soni
                
                self._yuklandi = True
                logger.debug(f"Markov: {len(self._transitions)} ta o'tish yuklandi")
        except Exception as e:
            logger.warning(f"Markov yuklash xatolik: {e}")
    
    def _saqlash(self):
        """Faylga saqlash."""
        try:
            data = {
                "transitions": {
                    k: dict(v) for k, v in self._transitions.items()
                }
            }
            with open(self._fayl, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("Markov: faylga saqlandi")
        except Exception as e:
            logger.warning(f"Markov saqlash xatolik: {e}")
    
    def saqlash(self):
        """Tashqaridan chaqiriluvchi saqlash."""
        with self._lock:
            self._saqlash()


# ========================================================
# 6. PRIORITY QUEUE — Buyruqlarga ustuvorlik
# ========================================================

# Buyruq prioritetlari: 1 = eng muhim (xavfli), 5 = oddiy
BUYRUQ_PRIORITETLARI = {
    # Xavfli — tasdiqlash kerak
    "shutdown": 1,
    "restart": 1,
    "lock": 2,
    "close_window": 2,
    
    # Tizim — tez bajarilishi kerak
    "volume_set": 3,
    "volume_up": 3,
    "volume_down": 3,
    "volume_mute": 3,
    "volume_unmute": 3,
    
    # Media — oddiy ustuvorlik
    "music_play": 4,
    "music_pause": 4,
    "music_restart": 4,
    "play_video": 4,
    "pause_video": 4,
    "next_video": 4,
    "prev_video": 4,
    
    # Ilova ochish — past ustuvorlik
    "open_youtube": 5,
    "open_telegram": 5,
    "open_chrome": 5,
    "open_brave": 5,
    "open_discord": 5,
    "open_code": 5,
    "open_explorer": 5,
    "open_cmd": 5,
    
    # Ma'lumot — past ustuvorlik
    "time": 5,
    "date": 5,
    "weather": 5,
    "search": 5,
    "greet": 5,
    "reminder": 5,
    "reminders": 5,
}

# Tasdiqlash kerak bo'lgan xavfli buyruqlar
XAVFLI_BUYRUQLAR = {"shutdown", "restart", "lock", "close_window"}


def buyruq_prioriteti(intent):
    """Buyruq prioritetini qaytarish (1-5)."""
    return BUYRUQ_PRIORITETLARI.get(intent, 5)


def xavfli_buyruqmi(intent):
    """Buyruq xavflimi (tasdiqlash kerakmi)?"""
    return intent in XAVFLI_BUYRUQLAR


# ========================================================
# 7. AQLLI BUYRUQ ANIQLASH — Barcha algoritmlarni birlashtirish
# ========================================================

# Global singleton'lar
_cache = BuyruqCache(maxsize=200)
_tfidf = TFIDFMatcher()
_bashorat = BuyruqBashorat()
_gemini_limiter = RateLimiter(max_calls=15, period=60)
_openrouter_limiter = RateLimiter(max_calls=20, period=60)
_oxirgi_intent = None


def algoritmlarni_tayyorla(buyruqlar_dict):
    """Barcha algoritmlarni buyruqlar bazasi bilan tayyorlash.
    Dastur ishga tushganda bir marta chaqiriladi.
    """
    # Guard — qayta yuklamaslik
    if _tfidf.tayyor:
        return
    _tfidf.fit(buyruqlar_dict)
    logger.info(f"Smart Algorithms: {len(buyruqlar_dict)} ta buyruq bilan tayyor")


def aqlli_buyruq_aniqla(matn, buyruqlar_dict, regex_fallback_func=None):
    """Barcha algoritmlarni ketma-ket ishlatib, buyruqni aniqlash.
    
    Tartib:
    1. Cache (eng tez) → agar keshda bo'lsa, darhol qaytaradi
    2. Levenshtein (fuzzy) → noto'g'ri yozilgan so'zlarni tuzatadi
    3. TF-IDF (semantic) → mazmuniy o'xshashlik bo'yicha topadi
    4. Regex fallback → mavjud buyruqni_aniqla() funksiyasi
    
    Args:
        matn: Foydalanuvchi kiritgan matn
        buyruqlar_dict: Buyruqlar lug'ati
        regex_fallback_func: Mavjud regex-based aniqlash funksiyasi
    
    Returns:
        intent string yoki tuple (buyruq, qiymat)
    """
    global _oxirgi_intent
    
    matn_toza = matn.lower().strip()
    
    # 1. CACHE — tez tekshirish
    cached = _cache.get(matn_toza)
    if cached is not None:
        logger.debug(f"[CACHE] '{matn_toza}' → {cached}")
        return cached
    
    # 2. REGEX FALLBACK — avval regex tekshirish (ovoz buyruqlari uchun)
    # Ovoz va raqamli buyruqlar regex da aniqroq ishlaydi
    if regex_fallback_func:
        regex_natija = regex_fallback_func(matn)
        if regex_natija != "unknown":
            _cache.put(matn_toza, regex_natija)
            _intent_saqlash(regex_natija)
            return regex_natija
    
    # 3. LEVENSHTEIN — noto'g'ri yozilgan so'zlarni tuzatish
    lev_natija = eng_yaqin_buyruq(matn_toza, buyruqlar_dict, chegara=2)
    if lev_natija:
        buyruq_nomi, intent, masofa = lev_natija
        if masofa <= 2:  # Juda yaqin bo'lsa — ishonchli
            _cache.put(matn_toza, intent)
            _intent_saqlash(intent)
            logger.info(f"[LEVENSHTEIN] '{matn}' → '{buyruq_nomi}' (masofa={masofa})")
            return intent
    
    # 4. TF-IDF — semantic o'xshashlik
    tfidf_natija = _tfidf.predict(matn_toza, min_score=0.40)  # Min score ni pasaytiramiz
    if tfidf_natija:
        intent, score = tfidf_natija
        if score >= 0.55:  # Yuqori ishonch — aniq buyruq
            _cache.put(matn_toza, intent)
            _intent_saqlash(intent)
            logger.info(f"[TF-IDF] '{matn}' → '{intent}' (score={score:.3f})")
            return intent
        elif score >= 0.40:
            # O'rtacha ishonch — tasdiqlash so'raladi
            logger.info(f"[TF-IDF] '{matn}' → '{intent}' TASDIQLASH KERAK (score={score:.3f})")
            return ("confirm", intent, score)
        else:
            logger.info(f"[TF-IDF] '{matn}' → '{intent}' PAST ISHONCH (score={score:.3f}), Agent ga yo'naltiriladi")
    
    # 5. Hech narsa topilmadi
    return "unknown"


def _intent_saqlash(intent):
    """Bashorat uchun intent ni saqlash."""
    global _oxirgi_intent
    if isinstance(intent, tuple):
        intent_str = intent[0]
    else:
        intent_str = intent
    
    if _oxirgi_intent and intent_str != "unknown":
        _bashorat.qosh(_oxirgi_intent, intent_str)
    _oxirgi_intent = intent_str


def keyingi_bashorat():
    """Keyingi buyruq bashoratini qaytarish."""
    if _oxirgi_intent:
        return _bashorat.bashorat(_oxirgi_intent)
    return []


def get_cache():
    """Cache obyektini qaytarish."""
    return _cache


def get_bashorat():
    """Bashorat obyektini qaytarish."""
    return _bashorat


def get_gemini_limiter():
    """Gemini rate limiter."""
    return _gemini_limiter


def get_openrouter_limiter():
    """OpenRouter rate limiter."""
    return _openrouter_limiter


def statistika():
    """Barcha algoritmlar statistikasi."""
    return {
        "cache": _cache.statistika,
        "gemini_limit": _gemini_limiter.statistika,
        "openrouter_limit": _openrouter_limiter.statistika,
        "bashorat_oxirgi": _oxirgi_intent,
    }
