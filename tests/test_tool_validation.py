# ========== test_tool_validation.py ==========
# Phase 32 — Parameter Validation & Sanitization Engine Unit Tests
# Strict Types, Required Fields, Safe Coercion & Injection Defense

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.tools.contract import ToolContract2, ToolErrorCode
from core.tools.validator import ParameterValidator


class TestToolValidation(unittest.TestCase):
    """Asbob parametrlarini qat'iy tekshirish va tozalash testlari"""

    def setUp(self):
        self.sample_tool = ToolContract2(
            name="user_profile_tool",
            description="Updates user profile",
            parameters={
                "username": {"type": "string", "description": "Username", "required": True},
                "age": {"type": "integer", "description": "Age", "required": False},
                "score": {"type": "float", "description": "Rating score", "required": False},
                "is_active": {"type": "boolean", "description": "Active flag", "required": False},
                "metadata": {"type": "dict", "description": "Extra info", "required": False},
                "tags": {"type": "list", "description": "Tags", "required": False},
            },
            function=lambda **kwargs: kwargs,
        )

    def test_required_parameter_missing(self):
        """Majburiy parametr berilmaganda VALIDATION_ERROR qaytishi"""
        valid, err_msg, code, clean = ParameterValidator.validate(
            tool=self.sample_tool,
            params={"age": 25}  # username missing
        )
        self.assertFalse(valid)
        self.assertEqual(code, ToolErrorCode.VALIDATION_ERROR)
        self.assertIn("majburiy parametr yetishmayapti", err_msg)
        self.assertIn("username", err_msg)

    def test_required_parameter_empty_string(self):
        """Majburiy parametr bo'sh satr bo'lsa VALIDATION_ERROR qaytishi"""
        valid, err_msg, code, clean = ParameterValidator.validate(
            tool=self.sample_tool,
            params={"username": "   "}
        )
        self.assertFalse(valid)
        self.assertEqual(code, ToolErrorCode.VALIDATION_ERROR)
        self.assertIn("bo'sh bo'lishi mumkin emas", err_msg)

    def test_unknown_parameter_strict_rejection(self):
        """Strict rejimda e'lon qilinmagan parametrlar rad etilishi"""
        valid, err_msg, code, clean = ParameterValidator.validate(
            tool=self.sample_tool,
            params={"username": "ali", "unknown_field": "test"},
            strict=True
        )
        self.assertFalse(valid)
        self.assertEqual(code, ToolErrorCode.VALIDATION_ERROR)
        self.assertIn("noma'lum parametrlar", err_msg)

    def test_type_coercion_string(self):
        """Raqamli qiymatlar string turiga xavfsiz aylantirilishi"""
        valid, err_msg, code, clean = ParameterValidator.validate(
            tool=self.sample_tool,
            params={"username": 12345}
        )
        self.assertTrue(valid)
        self.assertEqual(clean["username"], "12345")

    def test_type_coercion_integer(self):
        """Raqamli satrlar ("25") butun songa (25) xavfsiz aylantirilishi"""
        valid, err_msg, code, clean = ParameterValidator.validate(
            tool=self.sample_tool,
            params={"username": "vali", "age": "30"}
        )
        self.assertTrue(valid)
        self.assertEqual(clean["age"], 30)

        # Noto'g'ri string int ga aylanmaydi
        valid_bad, err_bad, code_bad, _ = ParameterValidator.validate(
            tool=self.sample_tool,
            params={"username": "vali", "age": "not_a_number"}
        )
        self.assertFalse(valid_bad)
        self.assertEqual(code_bad, ToolErrorCode.VALIDATION_ERROR)

    def test_type_coercion_float(self):
        """Kasr sonlar va ularning satr ko'rinishlari float turiga aylantirilishi"""
        valid, err_msg, code, clean = ParameterValidator.validate(
            tool=self.sample_tool,
            params={"username": "hasan", "score": "4.75"}
        )
        self.assertTrue(valid)
        self.assertEqual(clean["score"], 4.75)

    def test_type_coercion_boolean(self):
        """Mantiqiy ifodalar ('ha', 'yes', 'true', 'yo\'q', 'false') to'g'ri bool ga aylanishi"""
        # True variantlar
        for val in ("true", "ha", "yes", "1", True):
            valid, _, _, clean = ParameterValidator.validate(
                tool=self.sample_tool,
                params={"username": "user", "is_active": val}
            )
            self.assertTrue(valid, f"Failed for {val}")
            self.assertTrue(clean["is_active"])

        # False variantlar
        for val in ("false", "yo'q", "no", "0", False):
            valid, _, _, clean = ParameterValidator.validate(
                tool=self.sample_tool,
                params={"username": "user", "is_active": val}
            )
            self.assertTrue(valid, f"Failed for {val}")
            self.assertFalse(clean["is_active"])

    def test_type_validation_dict_and_list(self):
        """dict va list turlari qat'iy tekshirilishi"""
        valid, _, _, clean = ParameterValidator.validate(
            tool=self.sample_tool,
            params={
                "username": "admin",
                "metadata": {"role": "superadmin"},
                "tags": ["core", "security"]
            }
        )
        self.assertTrue(valid)
        self.assertEqual(clean["metadata"]["role"], "superadmin")
        self.assertEqual(clean["tags"], ["core", "security"])

        # Noto'g'ri dict turi
        valid_err, err, code, _ = ParameterValidator.validate(
            tool=self.sample_tool,
            params={"username": "admin", "metadata": "not_a_dict"}
        )
        self.assertFalse(valid_err)
        self.assertEqual(code, ToolErrorCode.VALIDATION_ERROR)

    def test_security_injection_blocking(self):
        """Oddiy parametrga xatarli kod inyeksiyasi kiritilganda SECURITY_BLOCKED qaytishi"""
        malicious_inputs = [
            "__import__('os').system('rm -rf /')",
            "eval('1+1')",
            "exec('import sys; sys.exit(0)')",
            "subprocess.Popen(['calc.exe'])",
        ]

        for mal_input in malicious_inputs:
            valid, err_msg, code, clean = ParameterValidator.validate(
                tool=self.sample_tool,
                params={"username": mal_input}
            )
            self.assertFalse(valid, f"Should have blocked: {mal_input}")
            self.assertEqual(code, ToolErrorCode.SECURITY_BLOCKED)
            self.assertIn("ruxsatsiz kod inyeksiyasi", err_msg)

    def test_code_tools_exempt_from_injection_blocks(self):
        """file_write va sandbox_execute_python vositalarida kod parametriga ruxsat berilishi"""
        file_write_tool = ToolContract2(
            name="file_write",
            description="Writes code",
            parameters={"path": {"type": "string", "required": True}, "content": {"type": "string", "required": True}},
            function=lambda **kwargs: kwargs,
        )

        valid, err_msg, code, clean = ParameterValidator.validate(
            tool=file_write_tool,
            params={"path": "main.py", "content": "import os\nprint(eval('2+2'))"}
        )
        self.assertTrue(valid)
        self.assertIsNone(code)

    def test_invalid_params_not_a_dict(self):
        """Parametrlar dict bo'lmaganda tizim qulamasligi va xato qaytarishi"""
        valid, err_msg, code, clean = ParameterValidator.validate(
            tool=self.sample_tool,
            params="string_not_dict"  # type: ignore
        )
        self.assertFalse(valid)
        self.assertEqual(code, ToolErrorCode.VALIDATION_ERROR)
        self.assertIn("lug'at (dict) ko'rinishida", err_msg)


if __name__ == "__main__":
    unittest.main()
