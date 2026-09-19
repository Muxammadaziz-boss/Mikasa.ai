# ========== provider.py ==========
# Mikasa AI 7.x — AI Provider Base Interface & Provider Manager
# Provider Abstraction & Deterministic Fallback Mechanism

import abc
import logging
from typing import List, Optional, Dict, Any
from core.intelligence.types import AIRequest, AIResponse

logger = logging.getLogger(__name__)


class AIProvider(abc.ABC):
    """Barcha AI provayderlari (Gemini, OpenRouter, va h.k.) uchun yagona baza interfeys"""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provayder nomi (masalan: 'gemini', 'openrouter')"""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Provayder konfiguratsiya qilingan va tayyor ekanligini tekshirish"""
        pass

    @abc.abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Sinxron so'rov yuborish va normalizatsiya qilingan AIResponse qaytarish"""
        pass


class ProviderManager:
    """AI provayderlarini boshqarish va deterministik fallback mexanizmi"""

    def __init__(self, providers: Optional[List[AIProvider]] = None):
        self._providers: List[AIProvider] = providers or []

    def register_provider(self, provider: AIProvider):
        """Yangi provayder ro'yxatdan o'tkazish"""
        self._providers.append(provider)

    def get_available_providers(self) -> List[str]:
        """Faol va kalitlari sozlangan provayderlar ro'yxati"""
        return [p.name for p in self._providers if p.is_available()]

    def is_any_available(self) -> bool:
        """Kamida bitta provayder mavjudligini tekshirish"""
        return any(p.is_available() for p in self._providers)

    def generate_with_fallback(self, request: AIRequest) -> AIResponse:
        """
        Deterministik zanjir orqali javob olish:
        Provayder 1 (Gemini) -> xatolik? -> Provayder 2 (OpenRouter) -> xatolik? -> AI_PROVIDER_UNAVAILABLE
        """
        available_providers = [p for p in self._providers if p.is_available()]
        
        if not available_providers:
            logger.warning("Hech qanday AI provayder sozlanmagan (API kalitlar mavjud emas). Mahalliy offline rejim ishga tushadi.")
            query_str = getattr(request, "message", None) or getattr(request, "query", "") or ""
            query_lower = str(query_str).lower().strip()

            if any(w in query_lower for w in ["salom", "qodir", "nima", "qila ol", "kim", "yordam", "imkon"]):
                resp_text = (
                    "Assalomu alaykum! Men Mikasa — sizning shaxsiy sun'iy intellekt yordamchingizman.\n\n"
                    "Men quyidagi asosiy vazifalarni bajara olaman:\n"
                    "• 💻 Kompyuterni boshqarish (dasturlarni ochish, oynalar va skrinshot)\n"
                    "• 📊 Tizim holati (CPU, RAM va real vaqtdagi harorat monitoringi)\n"
                    "• ⏰ Vazifalar va eslatmalarni rejalashtirish\n"
                    "• 🎵 Musiqa va videolarni boshqarish\n\n"
                    "💡 Kengaytirilgan chuqur muloqot va erkin suhbat uchun Sozlamalar bo'limidan Google Gemini API kalitini kiritishingiz mumkin."
                )
            else:
                resp_text = (
                    "Mikasa mahalliy yordamchi rejimida ishlamoqda. Buyruqlaringizni bajarishga tayyorman!\n\n"
                    "Erkin tahlil va suhbatlar uchun Hisob sozlamalaridan Gemini API kalitini sozlashingiz mumkin."
                )

            return AIResponse(
                provider="local",
                model="mikasa-offline-core",
                type="answer",
                content=resp_text,
                success=True,
                error_code=None,
                metadata={"offline_mode": True}
            )

        last_error = ""
        for provider in available_providers:
            try:
                logger.info(f"AI so'rovi yuborilmoqda: provayder='{provider.name}'")
                response = provider.generate(request)
                if response and response.success:
                    logger.info(f"AI muvaffaqiyatli javob berdi: provayder='{provider.name}', model='{response.model}', type='{response.type}'")
                    return response
                
                # Agar muvaffaqiyatsiz bo'lsa, keyingi provayderga o'tish
                last_error = response.content if response else "Bo'sh javob"
                logger.warning(f"Provayder '{provider.name}' muvaffaqiyatsiz bo'ldi ({last_error}), keyingi provayderga o'tilmoqda...")
            except Exception as e:
                last_error = str(e)
                logger.error(f"Provayder '{provider.name}' ijrosida istisno: {e}", exc_info=True)

        # Barcha provayderlar ishlamadi
        logger.error(f"Barcha AI provayderlar zanjiri muvaffaqiyatsiz tugadi. Oxirgi xatolik: {last_error}")
        return AIResponse(
            provider="none",
            model="none",
            type="error",
            content="Barcha AI provayderlar bilan bog'lanishda vaqtinchalik xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
            success=False,
            error_code="AI_PROVIDER_UNAVAILABLE",
            metadata={"last_error": last_error}
        )
