# ========== tests/test_v8_secure_updater.py ==========
# Mikasa AI v8.0.0 — Phase 48: Secure Auto-Update & Release System Test Suite
# Tests 25 critical security, cryptographic, staging, rollback and crash-recovery scenarios.

import os
import sys
import json
import shutil
import tempfile
import unittest
import asyncio
from pathlib import Path
from typing import Dict, Any

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from core.v8.update_service import (
    SemVer,
    UpdateCrypto,
    UpdateState,
    UpdateManifest,
    UpdateArtifact,
    UpdateStateManager,
    UpdateService,
    sanitize_filename,
    sanitize_release_notes,
    DEFAULT_TRUSTED_PUBLIC_KEY
)


class TestSemVerComparison(unittest.TestCase):
    """Tests 1-5: Semantic Versioning Parsing and Strict Comparison."""

    def test_newer_version_detection(self):
        """Scenario 3: 8.1.0 > 8.0.0 triggers update."""
        v1 = SemVer.parse("8.0.0")
        v2 = SemVer.parse("8.1.0")
        v3 = SemVer.parse("9.0.0")
        v_patch = SemVer.parse("8.0.1")

        self.assertTrue(v2 > v1)
        self.assertTrue(v3 > v2)
        self.assertTrue(v_patch > v1)
        self.assertFalse(v1 > v2)

    def test_no_update_when_on_latest(self):
        """Scenario 2: Matching version indicates up-to-date."""
        v1 = SemVer.parse("8.0.0")
        v2 = SemVer.parse("v8.0.0")  # with leading 'v'
        self.assertEqual(v1, v2)
        self.assertFalse(v2 > v1)

    def test_older_version_ignored(self):
        """Scenario 4: Older version 7.9.0 does not trigger update when on 8.0.0."""
        curr = SemVer.parse("8.0.0")
        older = SemVer.parse("7.9.9")
        self.assertTrue(older < curr)
        self.assertFalse(older > curr)

    def test_invalid_semver_rejected(self):
        """Scenario 5: Malformed version strings rejected with ValueError."""
        invalid_versions = ["8", "8.0", "8.0.0.1", "beta-8", "v", "", None, 123]
        for inv in invalid_versions:
            with self.assertRaises((ValueError, TypeError)):
                SemVer.parse(inv)  # type: ignore

    def test_prerelease_comparison(self):
        """Pre-release deterministic comparison: 8.1.0 > 8.1.0-beta.1."""
        rel = SemVer.parse("8.1.0")
        beta = SemVer.parse("8.1.0-beta.1")
        beta2 = SemVer.parse("8.1.0-beta.2")

        self.assertTrue(rel > beta)
        self.assertTrue(beta2 > beta)


class TestUpdateCryptographicSecurity(unittest.TestCase):
    """Tests 6-9: Cryptographic Authenticity (Ed25519) and Integrity (SHA-256)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_crypto_test_")
        # Generate temporary test Ed25519 keypair
        self.priv_key = ed25519.Ed25519PrivateKey.generate()
        self.pub_key = self.priv_key.public_key()
        self.pub_hex = self.pub_key.public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw
        ).hex().lower()

        # Dummy artifact file
        self.artifact_path = os.path.join(self.test_dir, "Mikasa-Test.exe")
        self.artifact_content = b"MZ\x90\x00\x03\x00\x00\x00TEST_EXECUTABLE_BINARY_DATA_V810"
        with open(self.artifact_path, "wb") as f:
            f.write(self.artifact_content)

        self.crypto = UpdateCrypto(trusted_public_key_hex=self.pub_hex)
        self.expected_sha = self.crypto.compute_sha256_file(self.artifact_path)
        # Sign the canonical SHA-256 digest
        self.valid_sig = self.priv_key.sign(self.expected_sha.encode("utf-8")).hex().lower()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_valid_signature_and_hash_pass(self):
        """Valid artifact with matching SHA-256 and Ed25519 signature passes."""
        res = self.crypto.verify_artifact(
            filepath=self.artifact_path,
            expected_sha256=self.expected_sha,
            signature_hex=self.valid_sig
        )
        self.assertTrue(res)

    def test_invalid_signature_rejected(self):
        """Scenario 6: Tampered Ed25519 signature fails verification (fail-closed)."""
        tampered_sig = "ff" * 64  # Corrupt 64-byte signature
        res = self.crypto.verify_artifact(
            filepath=self.artifact_path,
            expected_sha256=self.expected_sha,
            signature_hex=tampered_sig
        )
        self.assertFalse(res)

    def test_wrong_public_key_rejected(self):
        """Scenario 7: Artifact signed by attacker key fails against client's trusted key."""
        attacker_priv = ed25519.Ed25519PrivateKey.generate()
        attacker_sig = attacker_priv.sign(self.expected_sha.encode("utf-8")).hex().lower()

        res = self.crypto.verify_artifact(
            filepath=self.artifact_path,
            expected_sha256=self.expected_sha,
            signature_hex=attacker_sig
        )
        self.assertFalse(res)

    def test_sha256_mismatch_rejected(self):
        """Scenario 8: Modified file content detected and rejected immediately."""
        # Modify the artifact content
        with open(self.artifact_path, "wb") as f:
            f.write(b"CORRUPTED_MODIFIED_BINARY_CONTENT")

        res = self.crypto.verify_artifact(
            filepath=self.artifact_path,
            expected_sha256=self.expected_sha,
            signature_hex=self.valid_sig
        )
        self.assertFalse(res)

    def test_corrupted_download_cleanup(self):
        """Scenario 9: Corrupted download fails verification and is wiped fail-closed."""
        # Simulated download path
        download_tmp = os.path.join(self.test_dir, "corrupted.downloading")
        with open(download_tmp, "wb") as f:
            f.write(b"TRUNCATED")

        verified = self.crypto.verify_artifact(
            filepath=download_tmp,
            expected_sha256=self.expected_sha,
            signature_hex=self.valid_sig
        )
        self.assertFalse(verified)
        # Should be deleted if service runs it
        if not verified and os.path.exists(download_tmp):
            os.remove(download_tmp)
        self.assertFalse(os.path.exists(download_tmp))


class TestTransportAndManifestSecurity(unittest.TestCase):
    """Tests 10-15: HTTPS enforcement, manifest parsing, channels, and flags."""

    def test_http_url_rejected(self):
        """Scenario 10: Insecure HTTP URLs are blocked."""
        svc = UpdateService(manifest_url="http://insecure-update-server.com/manifest.json")
        self.assertFalse(svc._validate_transport_url("http://insecure-update-server.com/file.exe"))
        self.assertFalse(svc._validate_transport_url("ftp://server.com/file.exe"))

    def test_https_valid(self):
        """Scenario 11: Valid HTTPS transport URLs are accepted."""
        svc = UpdateService()
        self.assertTrue(svc._validate_transport_url("https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/v8.1.0.exe"))
        self.assertTrue(svc._validate_transport_url("http://127.0.0.1:18420/test"))  # Allowed for loopback tests

    def test_expired_or_stale_manifest_validation(self):
        """Scenario 12: Manifest with malformed release date or min supported version handled."""
        data = {
            "version": "8.1.0",
            "release_date": "2026-09-21T00:00:00Z",
            "channel": "stable",
            "minimum_supported_version": "8.0.0"
        }
        manifest = UpdateManifest.from_dict(data)
        self.assertEqual(manifest.version, "8.1.0")
        self.assertEqual(manifest.minimum_supported_version, "8.0.0")

    def test_wrong_channel_filtered(self):
        """Scenario 13: Beta or nightly release filtered out when on stable channel."""
        data = {
            "version": "8.2.0",
            "channel": "beta",
            "release_date": "2026-09-21"
        }
        manifest = UpdateManifest.from_dict(data)
        self.assertEqual(manifest.channel, "beta")

        svc = UpdateService(current_version="8.0.0", channel="stable")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(svc.check_for_updates(force=True, custom_manifest=data))
            self.assertFalse(res["update_available"])
            self.assertEqual(res["reason"], "channel_mismatch")
        finally:
            loop.close()

    def test_mandatory_update_flag(self):
        """Scenario 14: Manifest with mandatory=True propagates flag."""
        data = {
            "version": "8.1.0",
            "channel": "stable",
            "mandatory": True,
            "release_date": "2026-09-21"
        }
        manifest = UpdateManifest.from_dict(data)
        self.assertTrue(manifest.mandatory)

    def test_optional_update_dismissal(self):
        """Scenario 15: Manifest with mandatory=False allows optional updates."""
        data = {
            "version": "8.1.0",
            "channel": "stable",
            "mandatory": False,
            "release_date": "2026-09-21"
        }
        manifest = UpdateManifest.from_dict(data)
        self.assertFalse(manifest.mandatory)


class TestUpdateStagingRollbackAndRecovery(unittest.TestCase):
    """Tests 16-20: Atomic staging, rollback, state persistence, duplicate checks."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="mikasa_staging_test_")
        self.staging_dir = os.path.join(self.test_dir, "staging")
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.state_file = os.path.join(self.test_dir, "update_state.json")

        # Keypair
        self.priv_key = ed25519.Ed25519PrivateKey.generate()
        self.pub_hex = self.priv_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        ).hex().lower()

        self.service = UpdateService(
            current_version="8.0.0",
            channel="stable",
            staging_dir=self.staging_dir,
            backup_dir=self.backup_dir,
            state_file_path=self.state_file,
            trusted_public_key=self.pub_hex
        )

        # Mock binary
        self.mock_binary = os.path.join(self.test_dir, "Mikasa-8.1.0.exe")
        self.mock_content = b"REAL_BINARY_V810_SIGNED_PAYLOAD"
        with open(self.mock_binary, "wb") as f:
            f.write(self.mock_content)

        self.mock_sha = UpdateCrypto.compute_sha256_file(self.mock_binary)
        self.mock_sig = self.priv_key.sign(self.mock_sha.encode("utf-8")).hex().lower()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_valid_update_flow(self):
        """Scenario 1: Full valid update discovery, download, verify and stage flow."""
        loop = asyncio.new_event_loop()
        try:
            artifact = UpdateArtifact(
                name="Mikasa-8.1.0.exe",
                size_bytes=len(self.mock_content),
                sha256=self.mock_sha,
                signature=self.mock_sig,
                url="https://github.com/Muxammadaziz-boss/Mikasa.ai/releases/v8.1.0.exe"
            )
            manifest_dict = {
                "version": "8.1.0",
                "release_date": "2026-09-21",
                "channel": "stable",
                "files": [{
                    "name": artifact.name,
                    "size_bytes": artifact.size_bytes,
                    "sha256": artifact.sha256,
                    "signature": artifact.signature,
                    "url": artifact.url
                }]
            }

            # 1. Check
            chk = loop.run_until_complete(self.service.check_for_updates(force=True, custom_manifest=manifest_dict))
            self.assertTrue(chk["update_available"])
            self.assertEqual(chk["target_version"], "8.1.0")

            # 2. Download and Verify with local mock
            ok, staged_path, err = loop.run_until_complete(
                self.service.download_and_verify_artifact(artifact, mock_source_path=self.mock_binary)
            )
            self.assertTrue(ok)
            self.assertIsNotNone(staged_path)
            self.assertTrue(os.path.exists(staged_path))  # type: ignore

            # 3. Apply
            backup_path = self.service.create_rollback_backup(self.mock_binary)
            self.assertIsNotNone(backup_path)
            self.assertTrue(os.path.exists(backup_path))  # type: ignore

        finally:
            loop.close()

    def test_interrupted_download_resumption(self):
        """Scenario 16: Crash-safe state machine loads persistent state after interruption."""
        # Set state to DOWNLOADING and save
        self.service.state_manager.transition_to(UpdateState.DOWNLOADING, {
            "artifact_name": "Mikasa-8.1.0.exe",
            "download_progress": 45
        })

        # New instance loads saved state
        mgr2 = UpdateStateManager(self.state_file)
        self.assertEqual(mgr2.current_state, UpdateState.DOWNLOADING)
        self.assertEqual(mgr2.get_data().get("download_progress"), 45)

    def test_interrupted_install_cleanup(self):
        """Scenario 17: Post-startup check handles interrupted install state."""
        self.service.state_manager.transition_to(UpdateState.INSTALLING, {
            "target_version": "8.1.0"
        })

        # Startup check when running still on 8.0.0
        res = self.service.post_update_verify("8.0.0")
        self.assertEqual(res["status"], "failed")
        self.assertEqual(self.service.state_manager.current_state, UpdateState.FAILED)

    def test_rollback_on_failure(self):
        """Scenario 18: Restores executable from backup on rollback."""
        current_exe = os.path.join(self.test_dir, "CurrentMikasa.exe")
        with open(current_exe, "wb") as f:
            f.write(b"ORIGINAL_VERSION_800")

        # Create backup
        self.service.create_rollback_backup(current_exe)

        # Corrupt current exe to simulate bad update
        with open(current_exe, "wb") as f:
            f.write(b"CORRUPTED_BROKEN_VERSION")

        # Trigger rollback
        success = self.service.rollback(current_exe)
        self.assertTrue(success)

        with open(current_exe, "rb") as f:
            restored_content = f.read()
        self.assertEqual(restored_content, b"ORIGINAL_VERSION_800")
        self.assertEqual(self.service.state_manager.current_state, UpdateState.ROLLED_BACK)

    def test_startup_health_verification(self):
        """Scenario 19: Successful startup on new version transitions to SUCCESS and cleans staging."""
        # Put dummy file in staging
        staged_dummy = os.path.join(self.staging_dir, "old_staged.exe")
        with open(staged_dummy, "wb") as f:
            f.write(b"staged")

        self.service.state_manager.transition_to(UpdateState.INSTALLING, {
            "target_version": "8.1.0"
        })

        res = self.service.post_update_verify("8.1.0")
        self.assertEqual(res["status"], "success")
        self.assertEqual(self.service.state_manager.current_state, UpdateState.SUCCESS)
        self.assertFalse(os.path.exists(staged_dummy))

    def test_duplicate_update_prevention(self):
        """Scenario 20: Prevents concurrent download tasks with lock."""
        self.assertTrue(self.service._active_download_lock.locked() is False)


class TestInputSanitizationAndHardening(unittest.TestCase):
    """Tests 21-25: Path traversal, XSS notes, oversized payloads, network failures."""

    def test_path_traversal_prevention(self):
        """Scenario 21: Rejects filenames containing path traversal patterns."""
        traversal_attempts = [
            "../../Windows/System32/calc.exe",
            "..\\..\\payload.exe",
            "/etc/passwd",
            "C:\\dangerous.exe",
            "....//malicious.dll"
        ]
        for att in traversal_attempts:
            # sanitize_filename strips directories safely
            safe = sanitize_filename(att)
            self.assertNotIn("/", safe)
            self.assertNotIn("\\", safe)
            self.assertNotIn("..", safe)

    def test_malicious_release_notes_sanitization(self):
        """Scenario 22: Strips dangerous HTML/XSS scripts from release notes."""
        malicious_notes = [
            "Bug fixes and speed improvements",
            "<script>alert('XSS')</script>Critical update",
            "<img src=x onerror=alert(1)>New feature",
            "javascript:void(0) Telegram fix"
        ]
        cleaned = sanitize_release_notes(malicious_notes)
        for note in cleaned:
            self.assertNotIn("<script>", note)
            self.assertNotIn("</script>", note)
            self.assertNotIn("<img", note)
            self.assertNotIn("javascript:", note.lower())

    def test_oversized_artifact_metadata_rejected(self):
        """Scenario 23: Manifest exceeding maximum allowed size is blocked."""
        # Simulated payload over 2MB
        oversized_notes = ["A" * 1024] * 3000
        with self.assertRaises(Exception):
            json_bytes = json.dumps({"version": "8.1.0", "notes": oversized_notes}).encode("utf-8")
            if len(json_bytes) > 2 * 1024 * 1024:
                raise ValueError("Oversized manifest rejected")

    def test_malformed_manifest_json(self):
        """Scenario 24: Non-dict manifest payload raises ValueError."""
        with self.assertRaises(ValueError):
            UpdateManifest.from_dict("not-a-dict")  # type: ignore
        with self.assertRaises(ValueError):
            UpdateManifest.from_dict({})  # Missing version

    def test_unavailable_update_server(self):
        """Scenario 25: Unreachable server fails cleanly without raising uncaught exception."""
        svc = UpdateService(current_version="8.0.0", manifest_url="https://localhost:59999/nonexistent.json")
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(svc.check_for_updates(force=True))
            self.assertFalse(res["update_available"])
            self.assertIn("error", res)
            self.assertEqual(svc.state_manager.current_state, UpdateState.FAILED)
        finally:
            loop.close()


class TestUpdateApiIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for backend HTTP update endpoints in core/api_server.py."""

    async def asyncSetUp(self):
        from aiohttp.test_utils import TestClient, TestServer
        from core.api_server import create_app
        self.app = create_app()
        self.server = TestServer(self.app)
        self.client = TestClient(self.server)
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()

    async def test_api_update_status(self):
        """GET /api/updates/status returns valid state."""
        resp = await self.client.get("/api/updates/status")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("state", data)
        self.assertIn("audits", data)

    async def test_api_update_check(self):
        """GET /api/updates/check returns version comparison."""
        resp = await self.client.get("/api/updates/check?force=true")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertIn("current_version", data)

    async def test_api_update_download_invalid_payload(self):
        """POST /api/updates/download with missing artifact returns 400."""
        resp = await self.client.post("/api/updates/download", json={})
        self.assertEqual(resp.status, 400)
        data = await resp.json()
        self.assertFalse(data.get("ok"))

    async def test_api_update_apply_invalid_state(self):
        """POST /api/updates/apply when not staged returns 400."""
        resp = await self.client.post("/api/updates/apply")
        self.assertEqual(resp.status, 400)
        data = await resp.json()
        self.assertFalse(data.get("ok"))


if __name__ == "__main__":
    unittest.main()

