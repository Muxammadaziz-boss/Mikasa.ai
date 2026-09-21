# Mikasa AI v8.0.0 — Phase 48: Secure Auto Update & Release System

## 1. Overview
Phase 48 introduces a production-grade, fail-closed, cryptographically secured auto-update and release distribution architecture for the Mikasa AI Windows Desktop application. It enables the desktop app to discover new releases, verify binary integrity (SHA-256) and authenticity (Ed25519 digital signatures), stage files atomically, recover gracefully from sudden crashes/power outages, and allow deterministic rollback without risking system corruption.

---

## 2. Architecture
The update system follows a unidirectional, decoupled security flow:

```
┌────────────────────────────────────────────────────────┐
│               MIKASA DESKTOP APP (Tauri)               │
│                                                        │
│  User / Startup Trigger                                │
│    ↓                                                   │
│  GET /api/updates/check (HTTPS to GitHub / Manifest)   │
│    ↓                                                   │
│  SemVer Comparison (Target > Current)                  │
│    ↓                                                   │
│  Download Signed Binary to Staging                     │
│    ↓                                                   │
│  Dual Cryptographic Verification:                      │
│    1. SHA-256 Hash Digest Check                        │
│    2. Ed25519 Signature Verification                   │
│    ↓                                                   │
│  Atomic Staging & Rollback Backup                      │
│    ↓                                                   │
│  Restart & Post-Update Health Verification             │
└────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Boundary Isolation**: The update engine is strictly decoupled from arbitrary remote command execution, the Windows PC Agent background service, and the Universal Telegram Webhook gateway.

---

## 3. Versioning
- Adheres strictly to **Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH[-PRERELEASE]`).
- String comparisons (e.g. `"8.10.0" < "8.9.0"`) are disallowed; comparison uses integer tuple arithmetic:
  `SemVer(major, minor, patch)`.
- Pre-releases are deterministic: a final release (`8.1.0`) always has higher precedence than a pre-release (`8.1.0-beta.1`).

---

## 4. Manifest
Release metadata is distributed via `version_manifest.json`:
```json
{
  "app": "Mikasa AI",
  "version": "8.1.0",
  "version_name": "v8.1.0",
  "release_date": "2026-09-21T12:00:00Z",
  "channel": "stable",
  "mandatory": false,
  "minimum_supported_version": "8.0.0",
  "files": [
    {
      "name": "Mikasa-AI-v8.1.0.exe",
      "size_bytes": 5103616,
      "size_mb": 4.87,
      "sha256": "c6c652ad44f46c438c1440d39b2aed3e719c083f6130ce0188546c34ffa379cb",
      "signature": "0d9e90f4ae832baed3665020bedd8d866359ed900bb06cea98d1417004d45c8c..."
    }
  ],
  "release_notes": [
    "Secure Auto Update & Release System",
    "Enhanced Telegram Webhook Gateway",
    "Performance and memory optimisations"
  ]
}
```

---

## 5. Cryptographic Signing
- **Algorithm**: `Ed25519` (Edwards-curve Digital Signature Algorithm).
- **Private Key**: Kept exclusively in secure CI/CD build environments (`MIKASA_RELEASE_SIGNING_KEY`). **NEVER** stored in source code, committed to Git, or bundled into client binaries.
- **Signing Payload**: The canonical SHA-256 digest string (`expected_sha256.encode("utf-8")`) is signed by the private key.
- **Fail-Closed**: If a signature is missing, invalid, or truncated, the artifact is rejected immediately.

---

## 6. Client Verification
The desktop client holds the **Trusted Public Key**:
```
DEFAULT_TRUSTED_PUBLIC_KEY = "b4be839fd62657c0e786e1a2ad590c05c45c511371d041137c5ca9ac57c29829"
```
Verification procedure:
1. Stream file bytes and calculate SHA-256 digest.
2. Confirm computed SHA-256 matches manifest `sha256`.
3. Verify Ed25519 signature over SHA-256 digest using trusted public key.
4. **Purge on Mismatch**: If any step fails, the downloaded temporary binary is deleted immediately from disk (`temp_file.unlink()`).

---

## 7. Windows Installation
- Updates are staged in `%APPDATA%/Mikasa/updates/staging/`.
- Download writes to `.downloading` temporary files before atomic rename to target `.exe`.
- Current executable is never overwritten in place while active.
- When applying, current running binary is backed up to `%APPDATA%/Mikasa/updates/backups/`.

---

## 8. Rollback
- Automatic backup is created prior to any executable replacement:
  `%APPDATA%/Mikasa/updates/backups/<Name>.backup_<version>`
- If post-startup health check or version verification fails, the service executes `svc.rollback()`, restoring the original verified binary.
- Rollback events are persistently recorded in the audit log (`UPDATE_ROLLED_BACK`).

---

## 9. Release Pipeline
1. Developer bumps version across:
   - `core/v8/__init__.py`
   - `mikasa-7/package.json`
   - `mikasa-7/src-tauri/tauri.conf.json`
   - `mikasa-7/src-tauri/Cargo.toml`
2. Run automated test suites (`test_v8_secure_updater.py`).
3. Commit and push git tag: `git tag v8.1.0 && git push origin v8.1.0`.

---

## 10. GitHub Actions
The automated workflow `.github/workflows/release.yml`:
1. Triggers on tag push `v*.*.*`.
2. Compiles Python backend and runs unit tests.
3. Builds Tauri desktop app on `windows-latest`.
4. Runs `packaging/sign_release.py` with secret `MIKASA_RELEASE_SIGNING_KEY`.
5. Publishes release assets and `version_manifest.json` to GitHub Releases.

---

## 11. User Settings
- Located in **Account / Settings → Dastur Haqida (About App)**.
- Displays:
  - Current installed version: `v8.0.0`
  - Active update channel: `Barqaror (Stable)`
  - Action button: `[ Yangilanishlarni Tekshirish ]`
- State Machine:
  - `IDLE` ➔ `CHECKING` ➔ `UPDATE_AVAILABLE` / `UP_TO_DATE`
  - `DOWNLOADING` (0..100% progress) ➔ `VERIFYING` ➔ `STAGING` ➔ `INSTALLING` ➔ `SUCCESS`

---

## 12. Troubleshooting
| Symptom | Cause | Solution |
|---|---|---|
| "Insecure transport URL blocked" | Manifest URL starts with `http://` | Ensure HTTPS endpoint is configured |
| "Verification failed" | Tampered file or wrong signature | Staged file deleted automatically; check signing key |
| "Rate limited" | Checked within 6 hours | Pass `force=true` or click button in UI |
| "Invalid state transition" | Illegal state progression | State reset to IDLE upon reload |

---

## 13. Security Model
- **Fail-Closed Execution**: Zero unsigned executables can ever reach the staging or execution phase.
- **Zero Arbitrary Execution**: 0 `eval`, 0 `exec`, 0 `os.system`, 0 `shell=True` across the entire update module.
- **Path Traversal Protection**: Filenames from manifests are strictly sanitized via `sanitize_filename()` to reject `../` and directory separators.
- **XSS Prevention**: Release notes are stripped of HTML tags, `<script>`, and `javascript:` URIs via `sanitize_release_notes()`.

---

## 14. Threat Model
- **Man-in-the-Middle (MitM)**: Thwarted by mandatory TLS/HTTPS certificate validation and Ed25519 signature checks.
- **Compromised Mirror / CDN**: Even if binary content is altered, SHA-256 and Ed25519 signature verification fails closed.
- **Replay / Stale Attacks**: Protected by SemVer strictly requiring `target_version > current_version`.

---

## 15. Testing
The test suite in `tests/test_v8_secure_updater.py` covers 31 distinct scenarios:
- Valid update flow, no update, newer version, older version, pre-release.
- Invalid SemVer rejection.
- Invalid signature, wrong public key, SHA-256 mismatch, corrupted download cleanup.
- HTTP blocking, HTTPS allowance, channel filtering.
- Mandatory vs optional flags.
- Crash resumption, interrupted install, rollback on failure, health verification.
- Path traversal prevention, XSS notes sanitization, oversized metadata rejection.
- API endpoints: `/api/updates/status`, `/api/updates/check`, `/api/updates/download`, `/api/updates/apply`.

---

## 16. Release Procedure
```bash
# 1. Bump version in codebase
# 2. Run test suites
python -m unittest tests/test_v8_secure_updater.py

# 3. Build release binaries
cd mikasa-7 && npm run build:release

# 4. Sign release manifest (CI/CD or secure release machine)
python packaging/sign_release.py --manifest release/v8.1.0/version_manifest.json

# 5. Push git tag to trigger automated release
git tag v8.1.0
git push origin v8.1.0
```
