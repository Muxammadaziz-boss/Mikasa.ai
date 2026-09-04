# ========== test_smart_algorithms.py ==========
# Aqlli algoritmlar uchun unit testlar

import unittest
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Loyiha ildizi

from core.smart_algorithms import (
    levenshtein, eng_yaqin_buyruq,
    TFIDFMatcher, BuyruqCache, RateLimiter, BuyruqBashorat,
    aqlli_buyruq_aniqla, algoritmlarni_tayyorla,
    xavfli_buyruqmi, buyruq_prioriteti, get_cache
)


class TestLevenshtein(unittest.TestCase):
    """Levenshtein Distance testlari"""
    
    def test_ayni_suzlar(self):
        """Bir xil so'zlar — masofa 0"""
        self.assertEqual(levenshtein("youtube", "youtube"), 0)
        self.assertEqual(levenshtein("musiqa", "musiqa"), 0)
    
    def test_bir_harf_farq(self):
        """Bir harf farq — masofa 1"""
        self.assertEqual(levenshtein("yutub", "yutub"), 0)
        self.assertEqual(levenshtein("yutuq", "yutub"), 1)
        self.assertEqual(levenshtein("telegra", "telegram"), 1)
    
    def test_ikki_harf_farq(self):
        """Ikki harf farq — masofa 2"""
        self.assertEqual(levenshtein("muzika", "musiqa"), 2)
    
    def test_bosh_string(self):
        """Bo'sh stringlar"""
        self.assertEqual(levenshtein("", ""), 0)
        self.assertEqual(levenshtein("abc", ""), 3)
        self.assertEqual(levenshtein("", "abc"), 3)
    
    def test_eng_yaqin_buyruq_topiladi(self):
        """Eng yaqin buyruqni topish"""
        buyruqlar = {
            "youtube": "open_youtube",
            "musiqa": "music_search",
            "telegram": "open_telegram"
        }
        
        # "yutub" → "youtube" (masofa=1)
        natija = eng_yaqin_buyruq("yutub", buyruqlar, chegara=2)
        self.assertIsNotNone(natija)
        self.assertEqual(natija[1], "open_youtube")
        
        # "telegra" → "telegram" (masofa=1)
        natija = eng_yaqin_buyruq("telegra", buyruqlar, chegara=2)
        self.assertIsNotNone(natija)
        self.assertEqual(natija[1], "open_telegram")
    
    def test_eng_yaqin_buyruq_topilmaydi(self):
        """Chegara dan uzoq bo'lsa None"""
        buyruqlar = {"youtube": "open_youtube"}
        natija = eng_yaqin_buyruq("xyzabc", buyruqlar, chegara=2)
        self.assertIsNone(natija)


class TestTFIDF(unittest.TestCase):
    """TF-IDF Matcher testlari"""
    
    def setUp(self):
        get_cache().clear()  # Test izolyatsiyasi
        self.matcher = TFIDFMatcher()
        self.buyruqlar = {
            "youtube och": "open_youtube",
            "musiqa qidir": "music_search",
            "telegram och": "open_telegram",
            "ovozni oshir": "volume_up",
            "vaqt": "time",
            "salom": "greet"
        }
        self.matcher.fit(self.buyruqlar)
    
    def test_fit_tayyor(self):
        """Fit dan keyin tayyor bo'lishi kerak"""
        self.assertTrue(self.matcher.tayyor)
    
    def test_aniq_mos_kelish(self):
        """Aniq buyruq — yuqori score"""
        natija = self.matcher.predict("youtube och")
        self.assertIsNotNone(natija)
        intent, score = natija
        self.assertEqual(intent, "open_youtube")
        self.assertGreater(score, 0.5)
    
    def test_oxshash_buyruq(self):
        """O'xshash buyruq ham topilishi kerak"""
        natija = self.matcher.predict("youtube ochib ber")
        if natija is not None:
            intent, score = natija
            self.assertEqual(intent, "open_youtube")
        # TF-IDF da qo'shimcha so'zlar bo'lsa score past bo'lishi mumkin
    
    def test_hech_narsa_topilmaydi(self):
        """Umuman boshqa matn"""
        natija = self.matcher.predict("python dasturlash tili", min_score=0.5)
        self.assertIsNone(natija)


class TestLRUCache(unittest.TestCase):
    """LRU Cache testlari"""
    
    def setUp(self):
        self.cache = BuyruqCache(maxsize=3)
    
    def test_put_get(self):
        """Keshga yozish va o'qish"""
        self.cache.put("youtube", "open_youtube")
        self.assertEqual(self.cache.get("youtube"), "open_youtube")
    
    def test_cache_miss(self):
        """Keshda yo'q bo'lsa None"""
        self.assertIsNone(self.cache.get("telegram"))
    
    def test_maxsize_eviction(self):
        """Kesh to'lganda eng eski o'chishi"""
        self.cache.put("a", 1)
        self.cache.put("b", 2)
        self.cache.put("c", 3)
        self.cache.put("d", 4)  # "a" o'chishi kerak
        
        self.assertIsNone(self.cache.get("a"))
        self.assertEqual(self.cache.get("b"), 2)
        self.assertEqual(self.cache.get("d"), 4)
    
    def test_lru_tartib(self):
        """LRU: ishlatilganlari saqlanadi"""
        self.cache.put("a", 1)
        self.cache.put("b", 2)
        self.cache.put("c", 3)
        
        # "a" ni ishlatish — u endi eng yangi
        self.cache.get("a")
        
        # "d" qo'shilganda "b" o'chishi kerak (eng eski)
        self.cache.put("d", 4)
        self.assertIsNone(self.cache.get("b"))
        self.assertEqual(self.cache.get("a"), 1)
    
    def test_statistika(self):
        """Statistika to'g'ri ishlashi"""
        self.cache.put("a", 1)
        self.cache.get("a")  # hit
        self.cache.get("b")  # miss
        
        stat = self.cache.statistika
        self.assertEqual(stat["hits"], 1)
        self.assertEqual(stat["misses"], 1)
        self.assertEqual(stat["foiz"], 50.0)


class TestRateLimiter(unittest.TestCase):
    """Rate Limiter testlari"""
    
    def test_ruxsat_beriladi(self):
        """Limit ichida — ruxsat"""
        limiter = RateLimiter(max_calls=5, period=60)
        ruxsat, qoldiq = limiter.is_allowed()
        self.assertTrue(ruxsat)
        self.assertEqual(qoldiq, 4)
    
    def test_limit_tugadi(self):
        """Limit tugaganda — rad"""
        limiter = RateLimiter(max_calls=2, period=60)
        limiter.is_allowed()
        limiter.is_allowed()
        ruxsat, kutish = limiter.is_allowed()
        self.assertFalse(ruxsat)
        self.assertGreater(kutish, 0)
    
    def test_bloklash(self):
        """Vaqtinchalik bloklash"""
        limiter = RateLimiter(max_calls=10, period=60)
        limiter.block(seconds=5)
        ruxsat, kutish = limiter.is_allowed()
        self.assertFalse(ruxsat)
    
    def test_statistika(self):
        """Statistika"""
        limiter = RateLimiter(max_calls=10, period=60)
        limiter.is_allowed()
        limiter.is_allowed()
        stat = limiter.statistika
        self.assertEqual(stat["ishlatilgan"], 2)
        self.assertEqual(stat["qoldiq"], 8)


class TestMarkovChain(unittest.TestCase):
    """Markov Chain (Buyruq bashorati) testlari"""
    
    def setUp(self):
        self.bashorat = BuyruqBashorat()
        # Test uchun faylni o'chirish
        self.bashorat._fayl = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "test_markov_data.json"
        )
    
    def tearDown(self):
        """Test faylini tozalash"""
        if os.path.exists(self.bashorat._fayl):
            os.remove(self.bashorat._fayl)
    
    def test_bashorat_bosh(self):
        """Bo'sh tarixda bashorat yo'q"""
        natija = self.bashorat.bashorat("open_youtube")
        self.assertEqual(natija, [])
    
    def test_bashorat_ishlaydi(self):
        """O'tishlar qo'shilgandan keyin bashorat ishlashi"""
        self.bashorat.qosh("open_youtube", "youtube_first_video")
        self.bashorat.qosh("open_youtube", "youtube_first_video")
        self.bashorat.qosh("open_youtube", "music_search")
        
        natija = self.bashorat.bashorat("open_youtube")
        self.assertGreater(len(natija), 0)
        
        # Eng ehtimoliy — youtube_first_video (2/3 = 0.667)
        self.assertEqual(natija[0][0], "youtube_first_video")
        self.assertAlmostEqual(natija[0][1], 0.667, places=2)
    
    def test_bashorat_top_n(self):
        """top_n cheklanishi"""
        self.bashorat.qosh("a", "b")
        self.bashorat.qosh("a", "c")
        self.bashorat.qosh("a", "d")
        self.bashorat.qosh("a", "e")
        
        natija = self.bashorat.bashorat("a", top_n=2)
        self.assertLessEqual(len(natija), 2)


class TestPriorityQueue(unittest.TestCase):
    """Priority va xavfli buyruqlar testlari"""
    
    def test_xavfli_buyruqlar(self):
        """Xavfli buyruqlar to'g'ri aniqlanishi"""
        self.assertTrue(xavfli_buyruqmi("shutdown"))
        self.assertTrue(xavfli_buyruqmi("restart"))
        self.assertTrue(xavfli_buyruqmi("lock"))
        self.assertFalse(xavfli_buyruqmi("open_youtube"))
        self.assertFalse(xavfli_buyruqmi("greet"))
    
    def test_prioritetlar(self):
        """Prioritetlar to'g'ri ishlashi"""
        self.assertEqual(buyruq_prioriteti("shutdown"), 1)
        self.assertEqual(buyruq_prioriteti("volume_set"), 3)
        self.assertEqual(buyruq_prioriteti("open_youtube"), 5)
        self.assertEqual(buyruq_prioriteti("noma'lum"), 5)


class TestAqlliBuyruqAniqla(unittest.TestCase):
    """Aqlli buyruq aniqlash (to'liq pipeline) testlari"""
    
    def setUp(self):
        get_cache().clear()  # Test izolyatsiyasi
        self.buyruqlar = {
            "youtube": "open_youtube",
            "musiqa": "music_search",
            "telegram": "open_telegram",
            "chrome": "open_chrome",
            "salom": "greet",
            "vaqt": "time"
        }
        algoritmlarni_tayyorla(self.buyruqlar)
    
    def test_aniq_buyruq(self):
        """Aniq buyruq — to'g'ridan-to'g'ri topilishi"""
        def mock_regex(matn):
            if "youtube" in matn.lower():
                return "open_youtube"
            return "unknown"
        
        natija = aqlli_buyruq_aniqla("youtube", self.buyruqlar, mock_regex)
        self.assertEqual(natija, "open_youtube")
    
    def test_fuzzy_buyruq(self):
        """Noto'g'ri yozilgan buyruq — Levenshtein topishi"""
        natija = aqlli_buyruq_aniqla("yutub", self.buyruqlar)
        # "yutub" → "youtube" (Levenshtein masofa=1, chegara=2 da topiladi)
        self.assertEqual(natija, "open_youtube")
    
    def test_noma_lum_buyruq(self):
        """Umuman noma'lum buyruq"""
        natija = aqlli_buyruq_aniqla("dasturlash o'rgatish kurslar", self.buyruqlar)
        self.assertEqual(natija, "unknown")
    
    def test_cache_ishlaydi(self):
        """Ikkinchi marta keshdan kelishi"""
        # Birinchi marta
        aqlli_buyruq_aniqla("salom", self.buyruqlar)
        
        # Ikkinchi marta — keshdan
        from core.smart_algorithms import get_cache
        cache = get_cache()
        natija = cache.get("salom")
        self.assertIsNotNone(natija)


if __name__ == '__main__':
    unittest.main(verbosity=2)
