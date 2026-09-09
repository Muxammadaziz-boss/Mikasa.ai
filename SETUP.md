# 🛠️ Mikasa AI v6.0.0 — O'rnatish va Sozlash Qo'llanmasi

## 1. Tizim Talablari
- **Operatsion tizim**: Windows 10 yoki Windows 11 (64-bit)
- **Python**: 3.11.x
- **RAM**: Kamida 4GB (8GB tavsiya etiladi)
- **Mikrofon va Dinamik**: Ovozli boshqaruv uchun
- **Internet**: Google Speech API va LLM API so'rovlari uchun

## 2. O'rnatish Bosqichlari

### 1-qadam: Repozitoriyani yuklab olish
```bash
git clone https://github.com/Muxammadaziz-boss/Mikasa.ai.git
cd Mikasa.ai
```

### 2-qadam: Python 3.11 Virtual Muhiti
```bash
# Virtual muhit yaratish
py -3.11 -m venv .venv

# Virtual muhitni faollashtirish (PowerShell)
.venv\Scripts\Activate.ps1

# Yoki CMD orqali:
# .venv\Scripts\activate.bat
```

### 3-qadam: Kerakli kutubxonalarni o'rnatish
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Konfiguratsiya (.env va data/config.json)

Loyiha ildizida `.env` faylini tekshiring:
```env
OPENROUTER_API_KEY=sk-or-v1-sizning_kalitingiz
OPENROUTER_MODEL=openai/gpt-3.5-turbo
DEFAULT_MUSIC_PLATFORM=youtube
DEBUG=false
```

## 4. Dasturni Ishga Tushirish

### Zamonaviy Grafika (GUI):
```bash
python run_gui.py
```

### Konsol / Terminal Rejimi:
```bash
python main.py
```

## 5. Sinov va Testlar
```bash
python -m unittest tests/test_v6_user_account.py tests/test_v6_window_chrome.py tests/test_v6_chat.py tests/test_v6_chat_ux.py tests/test_v6_surfaces.py tests/test_v6_final_qa.py
```
