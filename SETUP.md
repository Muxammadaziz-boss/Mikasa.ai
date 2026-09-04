# 🛠️ O'rnatish Bo'yicha Qo'llanma

## 1. Talablar

### Sistema talablari:

- **Python**: 3.11 yoki undan yuqori
- **Windows**: 10/11 (Audio API uchun)
- **Internet**: Google Speech API uchun
- **RAM**: kamida 4GB
- **Xotira**: 1GB bo'sh joy

### Dasturiy talablar:

- Python 3.11 venv
- Windows Audio xizmatlari
- Mikrofon ruxsati

## 2. Python 3.11 va Virtual Muhit

### Windows uchun:

```bash
# 1. Python 3.11 ni o'rnatish
# https://www.python.org/downloads/windows/

# 2. Virtual muhit yaratish
py -3.11 -m venv .venv

# 3. Faollashtirish
.venv\Scripts\activate

# 4. Tekshirish
python --version  # 3.11.x bo'lishi kerak
```

### PowerShell muammolari:

```bash
# Agar scriptlarni ishga tushirish taqiqlangan bo'lsa:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Yoki CMD dan foydalaning
```

## 3. Kutubxonalarni o'rnatish

### Avtomatik o'rnatish:

```bash
pip install -r requirements.txt
```

### Qo'lda o'rnatish (agar kerak bo'lsa):

```bash
pip install sounddevice==0.4.6
pip install soundfile==0.12.1
pip install edge-tts==6.1.10
pip install pycaw==20230407
pip install customtkinter==5.2.1
pip install pygame==2.6.1
pip install numpy
```

## 4. Konfiguratsiya

### .env faylini sozlash:

```env
# AI uchun
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# Musiqa platformalari
DEFAULT_MUSIC_PLATFORM=youtube  # youtube, yandex, spotify

# Debug
DEBUG=false
```

### config.json avtomatik yaratiladi:

```json
{
  "app": {
    "version": "2.2.5",
    "name": "Ovozli Yordamchi Pro",
    "debug": false
  },
  "audio": {
    "sample_rate": 16000,
    "duration": 5,
    "tts_voice_male": "uz-UZ-SardarNeural",
    "tts_voice_female": "uz-UZ-MadinaNeural"
  },
  "gui": {
    "theme": "dark",
    "color_scheme": "blue",
    "window_size": "1100x800"
  }
}
```

## 5. Dasturni ishga tushirish

### Oddiy ishga tushirish:

```bash
python main.py
```

### Debug rejimida:

```bash
python -c "import config; config.set('app.debug', True)"
python main.py
```

## 6. Birinchi ishga tushirish

Dastur birinchi marta ishga tushirilganda:

1. **Ismni so'rash**: O'zbekcha ism kiriting
2. **Ovoz turini tanlash**: "erkak" yoki "ayol"
3. **Mikrofon ruxsati**: Ruxsat bering tugmasini bosing
4. **GUI ochiladi**: Zamonaviy qorong'u interfeys

## 7. Muammolarni Hal Qilish

### 🎤 Mikrofon ishlamayapti:

```bash
# 1. Windows ruxsatlar
Windows Settings → Privacy & Security → Microphone
→ "Let apps access your microphone" - ON

# 2. Audio xizmati
Services → Windows Audio Service - Start

# 3. Driverlar
Device Manager → Sound controllers → Update driver
```

### 🔊 Ovoz chiqmaydi:

```bash
# 1. Internet ulanish
ping google.com

# 2. Windows Audio
Sound Settings → Output device → Test

# 3. edge-tts ishlashi
python -c "import edge_tts; print('OK')"
```

### 🖥️ GUI ochilmaydi:

```bash
# 1. CustomTkinter
python -c "import customtkinter; print('OK')"

# 2. Tkinter
python -c "import tkinter; print('OK')"

# 3. Venv tekshirish
which python
# .venv/Scripts/python.exe bo'lishi kerak
```

### 🔧 Umumiy xatolar:

```bash
# 1. Qayta o'rnatish
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# 2. Cache tozalash
pip cache purge

# 3. Python qayta o'rnatish
# Control Panel → Programs → Python 3.11 → Repair
```

## 8. Testlash

### Unit testlar:

```bash
python test_main.py
```

### Integratsion test:

```bash
# Dasturni ishga tushiring va quyidagilarni sinab ko'ring:
# 1. "youtube" - YouTube ochishi kerak
# 2. "ovozni 50 qil" - Ovoz 50% bo'lishi kerak
# 3. "vaqt" - Vaqtni ko'rsatishi kerak
```

## 9. Loglar va Debug

### Log fayllari:

```
logs/
├── yordamchi.log      # Asosiy log
├── yordamchi.log.1    # Avvalgi kun
├── yordamchi.log.2    # 2 kun avval
└── ...
```

### Debug qilish:

```python
# Log darajasini o'zgartirish
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Yoki config orqali
from config import set_config
set_config('app.debug', True)
```

## 10. Ishlab chiqarish uchun

### Development sozlamalari:

```bash
# 1. Development dependencies
pip install pytest pytest-cov black flake8

# 2. Code formatting
black *.py

# 3. Linting
flake8 *.py

# 4. Test coverage
pytest --cov=. test_main.py
```

### GitHub ishlashi:

```bash
# 1. Fork qiling
# 2. Clone qiling
git clone https://github.com/your-username/vozli-yordamchi.git

# 3. Branch yaratish
git checkout -b development

# 4. O'zgarishlar
# ... coding ...

# 5. Test va commit
python test_main.py
git add .
git commit -m "Yangilik qo'shildi"

# 6. Push
git push origin development
```

## 11. Performance optimizatsiya

### Tavsiyalar:

- **SSD**: Dastur SSD da tezroq ishlaydi
- **RAM**: 8GB yuqori yaxshi
- **CPU**: Multi-core yordam beradi
- **Internet**: Barqaror ulanish muhim

### Resource monitoring:

```bash
# CPU va RAM monitoring
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%'); print(f'RAM: {psutil.virtual_memory().percent}%')"
```

---

**🎯 Muvaffaqiyat**: O'zbek tilida ishlaydigan zamonaviy ovozli yordamchi!
