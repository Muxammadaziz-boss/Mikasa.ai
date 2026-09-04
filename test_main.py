# ========== test_main.py ==========
# Asosiy funksiyalar uchun unit testlar

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
import sys

# Main modulni import qilish
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestMainFunctions(unittest.TestCase):
    """Asosiy funksiyalar uchun test klassi"""
    
    def setUp(self):
        """Testdan oldin tayyorgarlik"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = {
            "app": {"version": "2.2.5", "name": "Test"},
            "audio": {"sample_rate": 16000, "duration": 5},
            "paths": {
                "user_file": "test_user.txt",
                "voice_file": "test_voice.txt"
            }
        }
    
    def tearDown(self):
        """Testdan keyin tozalash"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('main.sd')
    @patch('main.sr')
    def test_tingla_success(self, mock_sr, mock_sd):
        """Mikrofon tinglash muvaffaqiyatli testi"""
        from main import tingla
        
        # Mock sozlash
        mock_sd.rec.return_value = MagicMock()
        mock_sd.wait.return_value = None
        mock_sr.Recognizer.return_value.recognize_google.return_value = "test matn"
        
        # Global state ni sozlash
        from main import global_state
        global_state.tinglash_faol = True
        
        # Test
        with patch('main.gui_ga_xabar_yuborish'):
            result = tingla()
            self.assertIsNotNone(result)
            self.assertEqual(result, "test matn")
    
    @patch('main.edge_tts')
    def test_ovoz_chiqar_tez_success(self, mock_edge_tts):
        """TTS ovoz chiqarish testi"""
        from main import ovoz_chiqar_tez
        
        # Mock sozlash
        mock_communicate = MagicMock()
        mock_edge_tts.Communicate.return_value = mock_communicate
        
        # Global state ni sozlash
        from main import global_state
        global_state.ovoz_turi_global = "erkak"
        
        # Test
        with patch('main.gui_ga_xabar_yuborish'):
            with patch('main.asyncio.new_event_loop'):
                with patch('main.asyncio.set_event_loop'):
                    with patch('tempfile.gettempdir', return_value=self.temp_dir):
                        ovoz_chiqar_tez("test matn")
    
    def test_buyruqni_aniqla_volume_commands(self):
        """Ovoz buyruqlarini aniqlash testi"""
        from main import buyruqni_aniqla
        
        # Test ovoz sozlash
        result = buyruqni_aniqla("ovozni 50 qil")
        self.assertEqual(result, ("volume_set", 50))
        
        # Test ovoz oshirish
        result = buyruqni_aniqla("ovozni oshir 10")
        self.assertEqual(result, ("volume_up", 10))
        
        # Test ovoz pasaytirish
        result = buyruqni_aniqla("ovozni pasaytir 5")
        self.assertEqual(result, ("volume_down", 5))
        
        # Test ovoz o'chirish
        result = buyruqni_aniqla("ovozni o'chir")
        self.assertEqual(result, "volume_mute")
    
    def test_buyruqni_aniqla_simple_commands(self):
        """Oddiy buyruqlarni aniqlash testi"""
        from main import buyruqni_aniqla
        
        # Test YouTube
        result = buyruqni_aniqla("youtube och")
        self.assertEqual(result, "open_youtube")
        
        # Test musiqa
        result = buyruqni_aniqla("musiqa qidir")
        self.assertEqual(result, "music_search")
        
        # Test vaqt
        result = buyruqni_aniqla("vaqt")
        self.assertEqual(result, "time")
    
    @patch('main.AudioUtilities')
    def test_get_audio_session_success(self, mock_audio_utils):
        """Audio sessiyasini olish testi"""
        from main import get_audio_session
        
        # Mock sozlash
        mock_devices = MagicMock()
        mock_interface = MagicMock()
        mock_volume = MagicMock()
        
        mock_audio_utils.GetSpeakers.return_value = mock_devices
        mock_devices.Activate.return_value = mock_interface
        
        # Test
        result = get_audio_session()
        self.assertIsNotNone(result)
    
    @patch('main.AudioUtilities')
    def test_get_audio_session_failure(self, mock_audio_utils):
        """Audio sessiyasini olish xatolik testi"""
        from main import get_audio_session
        
        # Mock sozlash - xatolik
        mock_audio_utils.GetSpeakers.side_effect = Exception("Test error")
        
        # Test
        result = get_audio_session()
        self.assertIsNone(result)
    
    def test_eslatma_qoshish_success(self):
        """Eslatma qo'shish testi"""
        from main import eslatma_qoshish
        
        # Test
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            with patch('main.gui_ga_xabar_yuborish'):
                with patch('main.ovoz_chiqar_tez'):
                    eslatma_qoshish("Test eslatma")
                    
                    # Fayl yozilganini tekshirish
                    mock_file.assert_called_once()
    
    def test_buyruqlar_json_ol_default(self):
        """Standart buyruqlarni yuklash testi"""
        from main import buyruqlar_json_ol
        
        # Test
        with patch('os.path.exists', return_value=False):
            with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
                with patch('json.dump') as mock_dump:
                    result = buyruqlar_json_ol()
                    
                    # Standart buyruqlar borligini tekshirish
                    self.assertIn("youtube", result)
                    self.assertIn("musiqa", result)
                    self.assertIn("vaqt", result)

class TestConfig(unittest.TestCase):
    """Konfiguratsiya testlari"""
    
    def setUp(self):
        """Testdan oldin tayyorgarlik"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
    
    def tearDown(self):
        """Testdan keyin tozalash"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_creation(self):
        """Konfiguratsiya yaratish testi"""
        from config import Config
        
        # Test
        with patch('config.Path.__div__', return_value=self.temp_dir):
            with patch('config.Path.exists', return_value=False):
                config = Config()
                
                # Standart qiymatlar borligini tekshirish
                self.assertEqual(config.get('app.version'), '2.2.5')
                self.assertEqual(config.get('audio.sample_rate'), 16000)
                self.assertEqual(config.get('gui.theme'), 'dark')
    
    def test_config_get_set(self):
        """Konfiguratsiya qiymatlarini olish/berish testi"""
        from config import Config
        
        # Test
        with patch('config.Path.__div__', return_value=self.temp_dir):
            config = Config()
            
            # Qiymat olish
            version = config.get('app.version')
            self.assertEqual(version, '2.2.5')
            
            # Qiymat berish
            config.set('app.version', '2.3.0')
            new_version = config.get('app.version')
            self.assertEqual(new_version, '2.3.0')
            
            # Mavjud bo'lmagan qiymat
            missing = config.get('app.missing', 'default')
            self.assertEqual(missing, 'default')

if __name__ == '__main__':
    # Testlarni ishga tushirish
    unittest.main(verbosity=2)
