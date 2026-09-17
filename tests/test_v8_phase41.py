# ========== tests/test_v8_phase41.py ==========
# Phase 41 — Account Registration & Authentication System
# Comprehensive Test Suite covering all 30 specification scenarios

import os
import shutil
import tempfile
import unittest
import asyncio
import json
import time

from core.v8.account_device import AccountDeviceManager
from core.v8.account_auth import (
    PasswordManager,
    validate_username,
    validate_email,
    VerificationToken,
    MockEmailVerificationProvider,
    AccountAuthManager
)
from core.api_server import (
    handle_auth_register,
    handle_auth_login,
    handle_auth_me,
    handle_auth_forgot_password,
    handle_auth_reset_password,
    _get_request_user_id
)


class MockRequest:
    """Mock aiohttp request for endpoint testing."""
    def __init__(self, method="GET", query=None, headers=None, body=None, match_info=None, remote="127.0.0.1"):
        self.method = method
        self.query = query or {}
        self.headers = headers or {}
        self._body = body or {}
        self.match_info = match_info or {}
        self.remote = remote

    async def json(self):
        return self._body


class TestPasswordManagerAndValidation(unittest.TestCase):
    """Scenarios 1-5: Password Manager & Input Validation Rules"""

    def test_01_password_hashing_pbkdf2(self):
        """Scenario 1: PBKDF2-HMAC-SHA256 hashing format and verification."""
        pwd = "SecurePassword123!"
        hashed = PasswordManager.hash_password(pwd)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$600000$"))
        parts = hashed.split("$")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "pbkdf2_sha256")
        self.assertEqual(parts[1], "600000")

        # Verify correct password
        self.assertTrue(PasswordManager.verify_password(pwd, hashed))
        # Verify incorrect password
        self.assertFalse(PasswordManager.verify_password("WrongPassword999", hashed))

    def test_02_password_constant_time_comparison(self):
        """Scenario 2: Constant-time comparison rejects malformed or altered hashes safely."""
        hashed = PasswordManager.hash_password("Valid12345")
        # Tampered hash
        tampered = hashed[:-4] + "abcd"
        self.assertFalse(PasswordManager.verify_password("Valid12345", tampered))
        # Invalid format
        self.assertFalse(PasswordManager.verify_password("Valid12345", "plaintext_password"))
        self.assertFalse(PasswordManager.verify_password("Valid12345", ""))

    def test_03_password_validation_rules(self):
        """Scenario 3: Password strength validation (min 8 chars, letter + number)."""
        # Strong password
        valid, msg = PasswordManager.validate_strength("Secret99")
        self.assertTrue(valid)

        # Too short (< 8)
        valid, msg = PasswordManager.validate_strength("Sec1")
        self.assertFalse(valid)
        self.assertIn("kamida 8", msg)

        # Only letters
        valid, msg = PasswordManager.validate_strength("SecretOnlyLetters")
        self.assertFalse(valid)
        self.assertIn("raqam", msg)

        # Only numbers
        valid, msg = PasswordManager.validate_strength("1234567890")
        self.assertFalse(valid)
        self.assertIn("harf", msg)

        # With confirmation mismatch
        valid, msg = PasswordManager.validate_strength("Secret99", confirm_password="SecretDifferent99")
        self.assertFalse(valid)
        self.assertIn("mos kelmadi", msg)

    def test_04_validate_username_rules(self):
        """Scenario 4: Username validation rules (3-32 chars, alphanumeric, _ and -)."""
        self.assertTrue(validate_username("alisher")[0])
        self.assertTrue(validate_username("user_123")[0])
        self.assertTrue(validate_username("john-doe")[0])

        # Too short (< 3)
        self.assertFalse(validate_username("ab")[0])
        # Too long (> 32)
        self.assertFalse(validate_username("a" * 33)[0])
        # Invalid characters
        self.assertFalse(validate_username("user@name")[0])
        self.assertFalse(validate_username("user name")[0])
        self.assertFalse(validate_username("user!name")[0])

    def test_05_validate_email_rules(self):
        """Scenario 5: Email validation rules and canonical lowercase conversion."""
        valid, email = validate_email("User.Name@Example.Com")
        self.assertTrue(valid)
        self.assertEqual(email, "user.name@example.com")

        # Optional empty email
        self.assertTrue(validate_email(None)[0])
        self.assertTrue(validate_email("")[0])

        # Invalid emails
        self.assertFalse(validate_email("invalid_email")[0])
        self.assertFalse(validate_email("@missinguser.com")[0])
        self.assertFalse(validate_email("user@.com")[0])


class TestAccountRegistration(unittest.TestCase):
    """Scenarios 6-9: User Registration Workflows"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_test_auth_reg_")
        self.auth_file = os.path.join(self.test_dir, "auth.json")
        self.device_file = os.path.join(self.test_dir, "device.json")
        self.account_mgr = AccountDeviceManager(storage_path=self.device_file)
        self.auth_mgr = AccountAuthManager(
            account_device_mgr=self.account_mgr,
            storage_path=self.auth_file,
            email_provider=MockEmailVerificationProvider()
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_06_register_new_user_success(self):
        """Scenario 6: Registering a new valid user creates MikasaUser and AccountSession."""
        ok, msg, user, session = self.auth_mgr.register(
            username="sardor_dev",
            password="StrongPassword123!",
            email="sardor@example.com",
            client_ip="192.168.1.10",
            user_agent="MikasaApp/8.0.0"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(user)
        self.assertIsNotNone(session)
        self.assertEqual(user.username, "sardor_dev")
        self.assertEqual(user.email, "sardor@example.com")
        self.assertFalse(user.is_verified)
        self.assertTrue(session.is_active)
        self.assertTrue(len(session.token) >= 32)

        # Verify user persisted in AccountDeviceManager
        found = self.account_mgr.get_user(user.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.username, "sardor_dev")

    def test_07_register_duplicate_username_fails(self):
        """Scenario 7: Duplicate username registration is rejected."""
        self.auth_mgr.register(username="duplicate_user", password="Password123!")
        ok, msg, user, session = self.auth_mgr.register(
            username="duplicate_user",
            password="Password456!"
        )
        self.assertFalse(ok)
        self.assertIsNone(user)
        self.assertIn("mavjud", msg.lower())

    def test_08_register_duplicate_email_fails(self):
        """Scenario 8: Duplicate email address is rejected."""
        self.auth_mgr.register(username="user1", email="shared@example.com", password="Password123!")
        ok, msg, user, session = self.auth_mgr.register(
            username="user2",
            email="shared@example.com",
            password="Password123!"
        )
        self.assertFalse(ok)
        self.assertIsNone(user)
        self.assertIn("email", msg.lower())

    def test_09_register_weak_password_fails(self):
        """Scenario 9: Registering with a weak password is rejected."""
        ok, msg, user, session = self.auth_mgr.register(
            username="weak_pwd_user",
            password="123"
        )
        self.assertFalse(ok)
        self.assertIsNone(user)
        self.assertIn("kamida 8", msg.lower())


class TestAccountLoginAndRateLimiting(unittest.TestCase):
    """Scenarios 10-14: Login, Verification & Rate Limiting"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_test_auth_login_")
        self.auth_file = os.path.join(self.test_dir, "auth.json")
        self.device_file = os.path.join(self.test_dir, "device.json")
        self.account_mgr = AccountDeviceManager(storage_path=self.device_file)
        self.auth_mgr = AccountAuthManager(
            account_device_mgr=self.account_mgr,
            storage_path=self.auth_file
        )
        # Seed test user
        self.auth_mgr.register(
            username="alisher_test",
            email="alisher@example.com",
            password="CorrectPassword123!"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_10_login_with_username_success(self):
        """Scenario 10: Successful login using username returns user and active session."""
        ok, msg, user, session = self.auth_mgr.login(
            username_or_email="alisher_test",
            password="CorrectPassword123!",
            client_ip="10.0.0.1"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(user)
        self.assertIsNotNone(session)
        self.assertEqual(user.username, "alisher_test")
        self.assertIsNotNone(user.last_login_at)

    def test_11_login_with_email_success(self):
        """Scenario 11: Successful login using email address returns user and session."""
        ok, msg, user, session = self.auth_mgr.login(
            username_or_email="alisher@example.com",
            password="CorrectPassword123!",
            client_ip="10.0.0.1"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "alisher_test")

    def test_12_login_invalid_credentials_fails(self):
        """Scenario 12: Invalid username or password returns generic error message."""
        ok, msg, user, session = self.auth_mgr.login(
            username_or_email="alisher_test",
            password="WrongPassword123!"
        )
        self.assertFalse(ok)
        self.assertIsNone(user)
        self.assertIn("noto'g'ri", msg.lower())

        # Unknown user returns the same generic message (user enumeration defense)
        ok2, msg2, user2, session2 = self.auth_mgr.login(
            username_or_email="non_existent_user",
            password="SomePassword123!"
        )
        self.assertFalse(ok2)
        self.assertEqual(msg, msg2)

    def test_13_login_rate_limiting_cooldown(self):
        """Scenario 13: 5 consecutive failed attempts trigger a 5-minute cooldown."""
        ip = "192.168.100.5"
        for i in range(5):
            ok, msg, user, session = self.auth_mgr.login(
                username_or_email="alisher_test",
                password="WrongPassword!",
                client_ip=ip
            )
            self.assertFalse(ok)

        # 6th attempt should be blocked by rate limiter
        ok, msg, user, session = self.auth_mgr.login(
            username_or_email="alisher_test",
            password="CorrectPassword123!",
            client_ip=ip
        )
        self.assertFalse(ok)
        self.assertIn("urinish", msg.lower())

    def test_14_login_successful_resets_rate_limit(self):
        """Scenario 14: A successful login resets the failed attempts counter."""
        ip = "192.168.100.10"
        # 3 failed attempts
        for _ in range(3):
            self.auth_mgr.login(username_or_email="alisher_test", password="WrongPassword!", client_ip=ip)

        # Successful login
        ok, msg, user, session = self.auth_mgr.login(
            username_or_email="alisher_test",
            password="CorrectPassword123!",
            client_ip=ip
        )
        self.assertTrue(ok)

        # Can fail again without immediate block
        ok2, _, _, _ = self.auth_mgr.login(
            username_or_email="alisher_test",
            password="WrongPassword!",
            client_ip=ip
        )
        self.assertFalse(ok2)


class TestAccountSessionsAndTokens(unittest.TestCase):
    """Scenarios 15-19: Session Lifecycle, Hashing & Revocation"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_test_auth_sess_")
        self.auth_file = os.path.join(self.test_dir, "auth.json")
        self.device_file = os.path.join(self.test_dir, "device.json")
        self.account_mgr = AccountDeviceManager(storage_path=self.device_file)
        self.auth_mgr = AccountAuthManager(
            account_device_mgr=self.account_mgr,
            storage_path=self.auth_file
        )
        _, _, self.user, self.session = self.auth_mgr.register(
            username="sess_user",
            password="SessionPassword123!"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_15_session_token_hashing_and_ttl(self):
        """Scenario 15: Session tokens are stored hashed; 7-day default TTL."""
        self.assertTrue(self.session.token)
        self.assertGreater(self.session.expires_at, time.time() + 6 * 86400)

        # Authenticate via plaintext token
        sess, user = self.auth_mgr.authenticate_token(self.session.token)
        self.assertIsNotNone(sess)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user.id)

    def test_16_session_activity_tracking(self):
        """Scenario 16: Authenticating with a token updates last_activity_at."""
        old_act = self.session.last_activity_at
        # Advance time slightly
        time.sleep(0.02)
        sess, _ = self.auth_mgr.authenticate_token(self.session.token)
        self.assertGreater(sess.last_activity_at, old_act)

    def test_17_session_expiration(self):
        """Scenario 17: Expired sessions are rejected upon authentication."""
        # Artificially expire session
        self.session.expires_at = time.time() - 100
        sess, user = self.auth_mgr.authenticate_token(self.session.token)
        self.assertIsNone(sess)
        self.assertIsNone(user)

    def test_18_logout_single_session(self):
        """Scenario 18: Logging out a single session invalidates only that session."""
        # Create second session for same user
        _, _, _, session2 = self.auth_mgr.login(username_or_email="sess_user", password="SessionPassword123!")

        # Logout first session
        logged_out = self.auth_mgr.logout(self.session.token)
        self.assertTrue(logged_out)

        # First session invalid
        sess1, _ = self.auth_mgr.authenticate_token(self.session.token)
        self.assertIsNone(sess1)

        # Second session still valid
        sess2, _ = self.auth_mgr.authenticate_token(session2.token)
        self.assertIsNotNone(sess2)

    def test_19_logout_all_sessions(self):
        """Scenario 19: logout_all revokes all sessions for that user."""
        self.auth_mgr.login(username_or_email="sess_user", password="SessionPassword123!")
        self.auth_mgr.login(username_or_email="sess_user", password="SessionPassword123!")

        active_before = self.auth_mgr.get_active_sessions_for_user(self.user.id)
        self.assertEqual(len(active_before), 3)

        count = self.auth_mgr.logout_all(self.user.id)
        self.assertEqual(count, 3)

        active_after = self.auth_mgr.get_active_sessions_for_user(self.user.id)
        self.assertEqual(len(active_after), 0)


class TestEmailVerificationAndPasswordReset(unittest.TestCase):
    """Scenarios 20-26: Email Verification & Password Reset Workflows"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_test_auth_reset_")
        self.auth_file = os.path.join(self.test_dir, "auth.json")
        self.device_file = os.path.join(self.test_dir, "device.json")
        self.mock_email = MockEmailVerificationProvider()
        self.account_mgr = AccountDeviceManager(storage_path=self.device_file)
        self.auth_mgr = AccountAuthManager(
            account_device_mgr=self.account_mgr,
            storage_path=self.auth_file,
            email_provider=self.mock_email
        )
        _, _, self.user, self.session = self.auth_mgr.register(
            username="reset_user",
            email="reset@example.com",
            password="OriginalPassword123!"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_20_email_verification_token_generation_and_consumption(self):
        """Scenario 20: Email verification token sets is_verified=True and cannot be reused."""
        self.assertEqual(len(self.mock_email.sent_emails), 1)
        sent = self.mock_email.sent_emails[0]
        token = sent["token"]

        self.assertFalse(self.user.is_verified)
        ok, msg = self.auth_mgr.verify_email(token)
        self.assertTrue(ok)
        self.assertTrue(self.user.is_verified)

        # Re-using the same token should fail (single-use)
        ok2, msg2 = self.auth_mgr.verify_email(token)
        self.assertFalse(ok2)
        self.assertIn("ishlatilgan", msg2.lower())

    def test_21_email_verification_expired_token_fails(self):
        """Scenario 21: Expired verification tokens are rejected."""
        token_obj = VerificationToken(
            token="exp_token",
            user_id=self.user.id,
            token_type="email_verification",
            expires_at=time.time() - 10
        )
        self.auth_mgr._tokens["exp_token"] = token_obj
        ok, msg = self.auth_mgr.verify_email("exp_token")
        self.assertFalse(ok)
        self.assertIn("muddati", msg.lower())

    def test_22_request_password_reset_user_enumeration_defense(self):
        """Scenario 22: Password reset request returns identical success message for valid/invalid users."""
        ok1, msg1, token1 = self.auth_mgr.request_password_reset("reset@example.com")
        self.assertTrue(ok1)
        self.assertIsNotNone(token1)

        ok2, msg2, token2 = self.auth_mgr.request_password_reset("unknown_user@example.com")
        self.assertTrue(ok2)
        self.assertIsNone(token2)
        self.assertEqual(msg1, msg2)

    def test_23_reset_password_with_valid_token(self):
        """Scenario 23: Valid password reset token changes password and terminates all existing sessions."""
        _, _, token = self.auth_mgr.request_password_reset("reset@example.com")
        self.assertIsNotNone(token)

        # Reset password
        ok, msg = self.auth_mgr.reset_password(token, "BrandNewPassword123!")
        self.assertTrue(ok)

        # Old session should now be invalidated
        sess, _ = self.auth_mgr.authenticate_token(self.session.token)
        self.assertIsNone(sess)

        # Login with old password fails
        ok_old, _, _, _ = self.auth_mgr.login(username_or_email="reset_user", password="OriginalPassword123!")
        self.assertFalse(ok_old)

        # Login with new password succeeds
        ok_new, _, user_new, sess_new = self.auth_mgr.login(username_or_email="reset_user", password="BrandNewPassword123!")
        self.assertTrue(ok_new)
        self.assertIsNotNone(sess_new)

    def test_24_reset_password_with_expired_or_invalid_token_fails(self):
        """Scenario 24: Expired or invalid reset tokens fail."""
        ok, msg = self.auth_mgr.reset_password("invalid_token_xyz", "NewPassword123!")
        self.assertFalse(ok)
        self.assertIn("topilmadi", msg.lower())

    def test_25_change_password_authenticated(self):
        """Scenario 25: Authenticated user can change their password with valid old password."""
        ok, msg = self.auth_mgr.change_password(
            user_id=self.user.id,
            old_password="OriginalPassword123!",
            new_password="UpdatedPassword123!"
        )
        self.assertTrue(ok)

        # Login with updated password succeeds
        ok_login, _, _, _ = self.auth_mgr.login(username_or_email="reset_user", password="UpdatedPassword123!")
        self.assertTrue(ok_login)

    def test_26_change_password_wrong_old_password_fails(self):
        """Scenario 26: Changing password with wrong old password is rejected."""
        ok, msg = self.auth_mgr.change_password(
            user_id=self.user.id,
            old_password="IncorrectOldPassword!",
            new_password="UpdatedPassword123!"
        )
        self.assertFalse(ok)
        self.assertIn("noto'g'ri", msg.lower())


class TestTenantIsolationAndAPIEndpoints(unittest.TestCase):
    """Scenarios 27-30: Multi-Tenant Isolation & HTTP Endpoints"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_test_auth_api_")
        self.auth_file = os.path.join(self.test_dir, "auth.json")
        self.device_file = os.path.join(self.test_dir, "device.json")
        self.account_mgr = AccountDeviceManager(storage_path=self.device_file)
        self.auth_mgr = AccountAuthManager(
            account_device_mgr=self.account_mgr,
            storage_path=self.auth_file,
            email_provider=MockEmailVerificationProvider()
        )
        AccountDeviceManager._instance = self.account_mgr
        AccountDeviceManager._default_instance = self.account_mgr
        AccountAuthManager._instance = self.auth_mgr
        AccountAuthManager._default_instance = self.auth_mgr

    def tearDown(self):
        AccountDeviceManager._instance = None
        AccountDeviceManager._default_instance = None
        AccountAuthManager._instance = None
        AccountAuthManager._default_instance = None
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_27_multi_tenant_isolation(self):
        """Scenario 27: User A's session cannot access User B's resources or devices."""
        _, _, user_a, sess_a = self.auth_mgr.register(username="user_a", password="PasswordA123!")
        _, _, user_b, sess_b = self.auth_mgr.register(username="user_b", password="PasswordB123!")

        # User A registers a device
        self.account_mgr.register_device(user_id=user_a.id, device_id="pc_a", name="Laptop A")
        # User B registers a device
        dev_b = self.account_mgr.register_device(user_id=user_b.id, device_id="pc_b", name="Laptop B")

        # User A requests devices using their Bearer token
        req_a = MockRequest(headers={"Authorization": f"Bearer {sess_a.token}"})
        uid_extracted = _get_request_user_id(req_a)
        self.assertEqual(uid_extracted, user_a.id)

        # User A should only see Laptop A
        devices_a = self.account_mgr.get_devices_for_user(uid_extracted)
        self.assertEqual(len(devices_a), 1)
        self.assertEqual(devices_a[0].device_id, "pc_a")

        # User A cannot rename User B's device
        ok, msg, dev = self.account_mgr.rename_device(device_id_or_uuid="pc_b", user_id=uid_extracted, new_name="Hacked")
        self.assertFalse(ok)
        self.assertEqual(dev_b.name, "Laptop B")

    def test_28_api_auth_register_and_login_flow(self):
        """Scenario 28: End-to-end API registration and login via HTTP handlers."""
        async def _run():
            # 1. Register via API
            reg_req = MockRequest(body={
                "username": "api_user_1",
                "password": "ApiPassword123!",
                "confirm_password": "ApiPassword123!",
                "email": "api1@example.com"
            })
            resp = await handle_auth_register(reg_req)
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.text)
            self.assertTrue(data["ok"])
            self.assertEqual(data["user"]["username"], "api_user_1")
            token = data["session_token"]
            self.assertTrue(len(token) >= 32)

            # 2. Login via API
            login_req = MockRequest(body={
                "username": "api_user_1",
                "password": "ApiPassword123!"
            })
            login_resp = await handle_auth_login(login_req)
            self.assertEqual(login_resp.status, 200)
            login_data = json.loads(login_resp.text)
            self.assertTrue(login_data["ok"])
            self.assertEqual(login_data["user"]["username"], "api_user_1")

        asyncio.run(_run())

    def test_29_api_auth_me_authenticated_and_unauthenticated(self):
        """Scenario 29: GET /api/auth/me returns user data when authenticated, 401 when not."""
        async def _run():
            _, _, user, sess = self.auth_mgr.register(username="me_user", password="Password123!")

            # Authenticated request
            auth_req = MockRequest(headers={"Authorization": f"Bearer {sess.token}"})
            resp = await handle_auth_me(auth_req)
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.text)
            self.assertTrue(data["ok"])
            self.assertTrue(data["authenticated"])
            self.assertEqual(data["user"]["username"], "me_user")

            # Unauthenticated request
            unauth_req = MockRequest()
            resp_unauth = await handle_auth_me(unauth_req)
            self.assertEqual(resp_unauth.status, 401)
            data_unauth = json.loads(resp_unauth.text)
            self.assertFalse(data_unauth["authenticated"])

        asyncio.run(_run())

    def test_30_api_auth_password_reset_flow(self):
        """Scenario 30: Forgot password -> reset password -> login with new password via API."""
        async def _run():
            _, _, user, _ = self.auth_mgr.register(
                username="reset_api_user",
                email="reset_api@example.com",
                password="OldPassword123!"
            )

            # 1. Forgot password
            forgot_req = MockRequest(body={"email": "reset_api@example.com"})
            resp_forgot = await handle_auth_forgot_password(forgot_req)
            self.assertEqual(resp_forgot.status, 200)
            forgot_data = json.loads(resp_forgot.text)
            self.assertTrue(forgot_data["ok"])
            reset_token = forgot_data.get("token")
            self.assertIsNotNone(reset_token)

            # 2. Reset password with token
            reset_req = MockRequest(body={
                "token": reset_token,
                "new_password": "BrandNewPassword456!",
                "confirm_password": "BrandNewPassword456!"
            })
            resp_reset = await handle_auth_reset_password(reset_req)
            self.assertEqual(resp_reset.status, 200)
            reset_data = json.loads(resp_reset.text)
            self.assertTrue(reset_data["ok"])

            # 3. Login with new password
            login_req = MockRequest(body={
                "username": "reset_api_user",
                "password": "BrandNewPassword456!"
            })
            resp_login = await handle_auth_login(login_req)
            self.assertEqual(resp_login.status, 200)
            login_data = json.loads(resp_login.text)
            self.assertTrue(login_data["ok"])

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
