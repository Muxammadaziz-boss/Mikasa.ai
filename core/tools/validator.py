# ========== validator.py ==========
# Mikasa AI 7.x — Parameter Validation & Sanitization Engine
# Strict Type Checking, Required Field Enforcement & Injection Defense

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

from core.tools.contract import ToolContract2, ToolErrorCode

logger = logging.getLogger(__name__)

# Injection patterns to prevent arbitrary code or command execution
SUSPICIOUS_CODE_PATTERNS = [
    re.compile(r"\b(eval|exec)\s*\(", re.IGNORECASE),
    re.compile(r"\bos\.system\s*\(", re.IGNORECASE),
    re.compile(r"\b__import__\s*\(", re.IGNORECASE),
    re.compile(r"\bsubprocess\.(Popen|run|call|check_output)\s*\(", re.IGNORECASE),
]


class ParameterValidator:
    """
    Asbob parametrlarini ijro etishdan oldin qat'iy tekshirish dvigateli.
    Model tomonidan yaratilgan xato yoki xatarli parametrlarning asbobga o'tishiga yo'l qo'ymaydi.
    """

    @staticmethod
    def validate(
        tool: ToolContract2,
        params: Dict[str, Any],
        strict: bool = True,
        allow_code_input: bool = False
    ) -> Tuple[bool, Optional[str], Optional[ToolErrorCode], Dict[str, Any]]:
        """
        Parametrlarni tekshirish va xavfsiz tozalash.
        Qaytaradi: (is_valid, error_message, error_code, sanitized_params)
        """
        if params is None:
            params = {}

        if not isinstance(params, dict):
            return (
                False,
                f"Parametrlar lug'at (dict) ko'rinishida bo'lishi shart, olingan tur: {type(params).__name__}",
                ToolErrorCode.VALIDATION_ERROR,
                {}
            )

        declared_params = tool.parameters or {}
        required_params = tool.required_parameters or []

        # 1. Majburiy parametrlarni mavjudligini tekshirish
        for req_field in required_params:
            if req_field not in params or params[req_field] is None:
                msg = f"Asbob '{tool.name}' uchun majburiy parametr yetishmayapti: '{req_field}'"
                logger.warning(f"[ParameterValidator] {msg}")
                return False, msg, ToolErrorCode.VALIDATION_ERROR, {}
            # Agar satr bo'lsa va bo'sh bo'lsa
            if isinstance(params[req_field], str) and not params[req_field].strip():
                msg = f"Asbob '{tool.name}' majburiy parametri bo'sh bo'lishi mumkin emas: '{req_field}'"
                logger.warning(f"[ParameterValidator] {msg}")
                return False, msg, ToolErrorCode.VALIDATION_ERROR, {}

        # 2. Noma'lum parametrlarni aniqlash va rad etish (Strict mode)
        if strict and declared_params:
            unknown_keys = [k for k in params.keys() if k not in declared_params]
            if unknown_keys:
                msg = f"Asbob '{tool.name}' uchun noma'lum parametrlar aniqlandi: {unknown_keys}"
                logger.warning(f"[ParameterValidator] {msg}")
                return False, msg, ToolErrorCode.VALIDATION_ERROR, {}

        sanitized_params: Dict[str, Any] = {}

        # 3. Har bir parametrning turini va qiymatini tekshirish / xavfsiz konvertatsiya
        for key, value in params.items():
            schema = declared_params.get(key, {})
            expected_type = schema.get("type", "string").lower() if isinstance(schema, dict) else "string"

            # Maxsus: kod ijro etuvchi asboblardan tashqari boshqa joylarda xatarli kod injeksiyalarini bloklash
            is_code_field = (tool.name in ("sandbox_execute_python", "file_write") and key in ("code", "content"))
            if not is_code_field and not allow_code_input and isinstance(value, str):
                for pattern in SUSPICIOUS_CODE_PATTERNS:
                    if pattern.search(value):
                        msg = f"Xavfsizlik chegarasi buzildi: '{key}' parametrida ruxsatsiz kod inyeksiyasi aniqlandi"
                        logger.error(f"[ParameterValidator] {msg}: {value[:100]}")
                        return False, msg, ToolErrorCode.SECURITY_BLOCKED, {}

            # Tur tekshiruvi va xavfsiz konvertatsiya
            valid, coerced_val, err_msg = ParameterValidator._coerce_and_validate_type(key, value, expected_type)
            if not valid:
                logger.warning(f"[ParameterValidator] Asbob '{tool.name}' parametri '{key}' noto'g'ri: {err_msg}")
                return False, err_msg, ToolErrorCode.VALIDATION_ERROR, {}

            sanitized_params[key] = coerced_val

        return True, None, None, sanitized_params

    @staticmethod
    def _coerce_and_validate_type(field_name: str, value: Any, expected_type: str) -> Tuple[bool, Any, Optional[str]]:
        """Xavfsiz va aniq tur tekshiruvi hamda konvertatsiyasi"""
        if value is None:
            return True, None, None

        exp = expected_type.lower().strip()

        # String / text
        if exp in ("string", "str", "text"):
            if isinstance(value, str):
                return True, value, None
            # Raqamlar va bool larni satrga aylantirish xavfsiz
            if isinstance(value, (int, float, bool)):
                return True, str(value), None
            return False, None, f"'{field_name}' satr (string) bo'lishi kerak, lekin {type(value).__name__} berildi"

        # Integer / int
        elif exp in ("integer", "int"):
            if isinstance(value, bool):
                return False, None, f"'{field_name}' butun son bo'lishi kerak, boolean qabul qilinmaydi"
            if isinstance(value, int):
                return True, value, None
            if isinstance(value, str):
                val_str = value.strip()
                try:
                    return True, int(val_str), None
                except ValueError:
                    return False, None, f"'{field_name}' parametrini butun songa (int) aylantirib bo'lmadi: '{value}'"
            if isinstance(value, float):
                if value.is_integer():
                    return True, int(value), None
                return False, None, f"'{field_name}' butun son bo'lishi kerak, kasr son {value} berildi"
            return False, None, f"'{field_name}' butun son (int) bo'lishi kerak"

        # Float / number
        elif exp in ("float", "number", "numeric"):
            if isinstance(value, bool):
                return False, None, f"'{field_name}' son bo'lishi kerak, boolean qabul qilinmaydi"
            if isinstance(value, (int, float)):
                return True, float(value), None
            if isinstance(value, str):
                try:
                    return True, float(value.strip()), None
                except ValueError:
                    return False, None, f"'{field_name}' parametrini haqiqiy songa (float) aylantirib bo'lmadi: '{value}'"
            return False, None, f"'{field_name}' raqamli son (number) bo'lishi kerak"

        # Boolean / bool
        elif exp in ("boolean", "bool"):
            if isinstance(value, bool):
                return True, value, None
            if isinstance(value, str):
                clean_v = value.strip().lower()
                if clean_v in ("true", "1", "yes", "ha", "y"):
                    return True, True, None
                if clean_v in ("false", "0", "no", "yo'q", "n"):
                    return True, False, None
                return False, None, f"'{field_name}' mantiqiy (bool) qiymat bo'lishi kerak: 'true'/'false'"
            if isinstance(value, int):
                if value in (0, 1):
                    return True, bool(value), None
            return False, None, f"'{field_name}' mantiqiy (bool) qiymat bo'lishi kerak"

        # Dictionary / object
        elif exp in ("dict", "object", "mapping"):
            if isinstance(value, dict):
                return True, value, None
            return False, None, f"'{field_name}' obyekt (dict) bo'lishi kerak, olingan: {type(value).__name__}"

        # List / array
        elif exp in ("list", "array", "sequence"):
            if isinstance(value, (list, tuple)):
                return True, list(value), None
            return False, None, f"'{field_name}' ro'yxat (list) bo'lishi kerak, olingan: {type(value).__name__}"

        # Agar tur noma'lum bo'lsa, asl holicha o'tkazamiz
        return True, value, None
