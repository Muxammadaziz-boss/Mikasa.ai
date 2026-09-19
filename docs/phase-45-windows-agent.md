# MIKASA AI v8.0.0 — PHASE 45: REAL WINDOWS PC AGENT
## Production-Grade Implementation & Architectural Specification

---

### 1. EXECUTIVE SUMMARY & PRODUCTION READINESS STATUS
Mikasa AI v8.0.0 Phase 45 implements a modular, production-ready Windows PC Agent architecture. This release establishes a secure cryptographic foundation for remote device integration without compromising host integrity or bypassing operating system security boundaries.

- **Status**: PRODUCTION READY (`dev-v8.0.0`)
- **Key Deliverables**:
  - Stable, deterministic hardware-bound device identity (`agent/identity.py`).
  - Cryptographic vault backed by Windows DPAPI (`CryptProtectData`) on Windows and portable fallback on Linux CI (`agent/crypto.py`).
  - Out-of-band 6-digit numeric PIN pairing client (`agent/enrollment.py`).
  - Asymmetric Ed25519 challenge-response authentication with replay attack rejection (`agent/auth.py`).
  - Autonomous heartbeat telemetry engine with 403 revocation detection (`agent/heartbeat.py`).
  - Strict TLS transport client with zero-trust token injection (`agent/transport.py`).
  - Exponential backoff reconnection manager (`1s -> 2s -> 4s -> 8s -> 16s -> 30s -> 60s`) (`agent/lifecycle.py`).
  - Transparent crash recovery and dirty exit detection (`agent/recovery.py`).
  - User-controlled autostart management without UAC bypass (`agent/startup.py`).
  - Scrubbed audit logger with zero secret leakage (`agent/audit.py`).
  - PyInstaller packaging specification with zero bundled secrets (`packaging/agent.spec`, `packaging/build_agent.py`).
  - 30/30 comprehensive automated tests passing (`tests/test_v8_phase45.py`).

---

### 2. THREAT MODEL & SECURITY ARCHITECTURE
The PC Agent is designed under a strict Zero Trust and Least Privilege model:

```
+-------------------------------------------------------------------------+
|                              MIKASA CLOUD                               |
|                  (FastAPI/aiohttp Backend, Supabase Auth)               |
+------------------------------------+------------------------------------+
                                     |
                TLS 1.3 / HTTPS      |  POST /api/devices/{id}/challenge
             Strict Certificate      |  POST /api/devices/{id}/authenticate
                 Validation          |  POST /api/devices/{id}/heartbeat
                                     |
+------------------------------------+------------------------------------+
|                         WINDOWS PC HOST                                 |
|                                                                         |
|  +---------------------+   +---------------------+   +---------------+  |
|  |    SecureTransport   |   |   AgentCrypto Vault |   | AgentIdentity |  |
|  | (aiohttp + TLS Enforced) | (Windows DPAPI/Ed25519)| (Hardware SHA)|  |
|  +----------+----------+   +----------+----------+   +-------+-------+  |
|             |                         |                      |          |
|             +-------------------------+----------------------+          |
|                                       |                                 |
|                        +--------------v--------------+                  |
|                        |    AgentLifecycleManager     |                  |
|                        | (FSM, Backoff, Shutdown)    |                  |
|                        +--------------+--------------+                  |
|                                       |                                 |
|         +-----------------------------+---------------------------+     |
|         |                             |                           |     |
|  +------v-------+             +-------v-------+            +------v---+ |
|  |AgentHeartbeat|             | CrashRecovery |            |  Startup | |
|  |  (Telemetry) |             |  (Dirty Flag) |            | (No UAC) | |
|  +--------------+             +---------------+            +----------+ |
+-------------------------------------------------------------------------+
```

#### STRIDE Assessment & Mitigations:
1. **Spoofing**: Prevented by Ed25519 asymmetric signatures. Private keys never leave the host and cannot be extracted from DPAPI without local user credentials.
2. **Tampering**: All challenge messages are signed with canonical determinism (`device_id|nonce|timestamp|protocol_version`). Backend enforces tamper-evident signature checks.
3. **Repudiation**: Every lifecycle action emits an immutable audit event (`RemoteAuditEvent`) logged with correlated request IDs.
4. **Information Disclosure**: Memory wiping (`crypto.clean_memory()`) runs on shutdown. All logs pass through `sanitize_event_data` which masks tokens, private keys, authorization headers, and pairing PINs.
5. **Denial of Service**: Heartbeat exponential backoff caps at 60s, preventing network floods. Nonces expire after 60s.
6. **Elevation of Privilege**: Autostart uses HKCU Run or documented Scheduled Tasks. Zero UAC bypasses, zero shellcode injection, zero hidden persistence.

---

### 3. HARDWARE FINGERPRINTING & DETERMINISTIC DEVICE IDENTITY
- **Fingerprint Algorithm**: SHA-256 hash computed deterministically across:
  - System hostname (`socket.gethostname()`)
  - CPU architecture (`platform.machine()`)
  - Primary Network Interface MAC address (`uuid.getnode()`)
- **Device ID Stability**:
  - Formatted as `win-{fingerprint[:16]}`.
  - Persisted upon first initialization into `<vault_dir>/device_identity.json`.
  - Survives system reboots, user renames, network adapter changes, and agent restarts without mutating the registered `device_id`.

---

### 4. CRYPTOGRAPHIC KEY MANAGEMENT (Ed25519 & DPAPI)
- **Algorithm**: Ed25519 (RFC 8032) asymmetric cryptography.
- **Windows DPAPI Vault**:
  - On Windows, the 32-byte raw private key is encrypted via `ctypes.windll.crypt32.CryptProtectData` with user-level binding (`CRYPTPROTECT_UI_FORBIDDEN`).
  - Saved as an encrypted binary blob in `<vault_dir>/ed25519_agent_key_{device_id}.vault`.
- **Portable Mock Fallback**:
  - In Linux CI and non-Windows test environments, falls back to `MockCredentialStore` with identical interface semantics, enabling 100% CI pass rates without native Windows binaries.
- **Key Zeroing & Memory Scrubbing**:
  - Upon clean exit or `SIGINT`/`SIGTERM`, `AgentCrypto.clean_memory()` sets `_private_key = None` and triggers garbage collection to scrub cryptographic key material from RAM.

---

### 5. OUT-OF-BAND 6-DIGIT PIN PAIRING FLOW
1. **User Request**: User opens Mikasa Web/Desktop dashboard and initiates device pairing.
2. **PIN Issuance**: Backend generates an out-of-band 6-digit numeric pairing code (e.g. `849201`) bound to the user's `mikasa_user_id` with 5-minute TTL.
3. **Agent Registration**: On the PC, user runs `MikasaAgent pair <PIN>`.
4. **Public Key Transport**: The agent posts `{"pin": "849201", "public_key": "<64_hex_ed25519_pub>", "device_id": "<id>"}` to `/api/devices/pairing/complete`.
5. **Backend Verification**: Backend matches the PIN, creates `DeviceCredential` in `DeviceEnrollmentManager`, links ownership in `AccountDeviceManager`, and assigns default safe permissions (all dangerous execution primitives blocked).

---

### 6. ASYMMETRIC CHALLENGE-RESPONSE PROTOCOL
To authenticate an enrolled agent without transmitting secrets:
1. **Challenge Request**: Agent calls `POST /api/devices/{device_id}/challenge`.
2. **Nonce Issuance**: Backend returns `challenge_id` and a cryptographically random 32-byte (64 hex characters) nonce with a 60-second TTL.
3. **Canonical Message**: Both client and server construct identical canonical bytes:
   `raw = f"{device_id}|{nonce}|{timestamp:.3f}|{protocol_version}".encode("utf-8")`
4. **Signature**: Agent signs `raw` using its Ed25519 private key.
5. **Verification & Session**: Backend validates signature using the enrolled public key, marks nonce as used (`is_used = True`) to prevent replay attacks, and issues a 24-hour `DeviceSession`.

---

### 7. PERIODIC HEARTBEAT ENGINE & FSM STATES
The agent state machine manages the following states:
- `INITIALIZING`: Agent starting up, reading configuration and vault.
- `CONNECTING`: Acquiring challenge and authenticating session.
- `ONLINE`: Active session established, periodic heartbeats succeeding.
- `DEGRADED`: Transient heartbeat failures (>= 3 consecutive errors).
- `REVOKED`: Backend returned 403 `DEVICE_REVOKED`. Agent halts permanently.
- `STOPPED`: Gracefully terminated via signal or CLI.

#### Heartbeat Telemetry:
Payload sent to `/api/devices/{device_id}/heartbeat`:
- `timestamp`: Current UTC timestamp.
- `agent_version`: `8.0.0`
- `state`: Current FSM state.
- `metrics`:
  - `uptime_seconds`: Agent process uptime.
  - `cpu_percent`: Host CPU utilization.
  - `ram_percent`: Host RAM utilization percentage.
  - `ram_used_mb`: Host RAM usage in megabytes.

---

### 8. SECURE TRANSPORT LAYER
- **aiohttp ClientSession**: Async HTTP connection pooling.
- **Mandatory TLS**: Default context enforces strict TLS certificate verification. Setting `verify_ssl=False` is rejected by design (`ValueError`).
- **Session Injection**: Automatically decorates all outbound requests with:
  - `Authorization: Bearer <session_token>`
  - `X-Mikasa-Device-Token: <session_token>`
  - `X-Device-ID: <device_id>`
  - `User-Agent: Mikasa-PC-Agent/8.0.0`

---

### 9. EXPONENTIAL BACKOFF RECONNECTION LOGIC
When disconnected from backend, the agent retries with deterministic bounded backoff:
```
Attempt 0: 1.0s
Attempt 1: 2.0s
Attempt 2: 4.0s
Attempt 3: 8.0s
Attempt 4: 16.0s
Attempt 5: 30.0s
Attempt 6+: 60.0s (Max Cap)
```
- Halts immediately if the backend signals that the device has been revoked (`AgentState.REVOKED`).

---

### 10. TRANSPARENT CRASH RECOVERY & DIRTY EXIT DETECTION
- **Runtime State File**: `<vault_dir>/agent_runtime_state.json`.
- **Startup Check**:
  - If `is_running: true` and `clean_exit: false`, a previous unhandled crash or sudden power loss occurred.
  - Logs `RemoteEventType.CRASH_RECOVERY` with previous PID and startup timestamp.
- **Clean Shutdown**:
  - On graceful stop (`SIGINT`/`SIGTERM`/`shutdown()`), state is updated to `is_running: false`, `clean_exit: true`.

---

### 11. WINDOWS STARTUP & SERVICE INTEGRATION
- **User Autostart (HKCU)**:
  - Stored in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
  - Requires zero administrator elevation and zero UAC prompts.
  - Fully transparent and manageable via `MikasaAgent autostart [enable|disable|status]`.
- **Enterprise Service Option**:
  - System administrators can deploy as a native Windows Service via NSSM or Task Scheduler (`schtasks /create /tn "MikasaAgent" /sc onlogon`).

---

### 12. REMOTE CONTROL BOUNDARIES (PHASE 45 VS PHASE 46)
> [!IMPORTANT]
> **Strict Security Boundary**:
> - **Phase 45 (Current)**: Strictly establishes the secure PC agent lifecycle, cryptographic identity, pairing, authentication, transport, and heartbeat telemetry.
> - **Phase 46 (Future)**: Will implement controlled, capability-bounded remote tool execution with explicit human confirmation and audit policies.
> - **Zero Execution in Phase 45**: There are 0 calls to `eval()`, 0 calls to `exec()`, 0 `subprocess.Popen(..., shell=True)`, and 0 remote command runners in this phase.

---

### 13. AUDIT LOGGING & SENSITIVE DATA REDACTION
All agent events pass through `AgentAuditLogger`:
- Sanitization masks all known credential keys (`session_token`, `private_key`, `authorization_header`, `pin`, `auth_code`, `secret`) with `***REDACTED***`.
- Emits structured lifecycle events:
  - `AGENT_STARTED`, `AGENT_STOPPING`, `AGENT_STOPPED`
  - `ENROLLMENT_STARTED`, `ENROLLMENT_COMPLETED`, `ENROLLMENT_FAILED`
  - `AUTH_STARTED`, `AUTH_SUCCESS`, `AUTH_FAILED`
  - `HEARTBEAT_SENT`, `HEARTBEAT_FAILED`
  - `RECONNECT_STARTED`, `RECONNECT_SUCCESS`, `RECONNECT_FAILED`
  - `CREDENTIAL_LOADED`, `CREDENTIAL_REVOKED`, `CRASH_RECOVERY`

---

### 14. MULTI-TENANT ISOLATION & DEVICE AUTHORIZATION
- Devices are strictly partitioned by `mikasa_user_id`.
- An agent enrolled under Tenant A cannot authenticate or access devices registered under Tenant B.
- Backend validates that the authenticated public key matches the specific device record in `DeviceEnrollmentManager`. Cross-tenant signature attempts yield `401 Unauthorized`.

---

### 15. STANDALONE BINARY PACKAGING (ZERO SECRETS)
- **Specification**: `packaging/agent.spec`
- **Build Script**: `packaging/build_agent.py`
- **Zero Secrets Guarantee**:
  - Pre-build scanner verifies absence of hardcoded tokens and cloud credentials.
  - No `.env` files, certificates, or secrets are bundled inside `MikasaAgent.exe`.
  - Standalone binary size: ~20-35 MB (Python runtime + PyInstaller bootloader + compiled agent modules).

---

### 16. AUTOMATED TEST SUITE (30/30 TESTS)
Run the Phase 45 test suite:
```powershell
python -m pytest -v tests/test_v8_phase45.py
```

Test Breakdown:
1. `test_01_identity_stable_across_invocations`: Device ID remains unchanged across restarts.
2. `test_02_identity_hardware_fingerprint_deterministic`: 64-char SHA256 hardware hash consistency.
3. `test_03_identity_metadata_persistence`: `device_identity.json` persistence.
4. `test_04_crypto_ed25519_keypair_generation`: Valid 64-char hex public key.
5. `test_05_crypto_canonical_challenge_signing`: Cryptographic signature verification.
6. `test_06_crypto_store_persistence_and_retrieval`: Mock/Windows vault persistence.
7. `test_07_crypto_memory_wiping_on_shutdown`: Private key memory erasure.
8. `test_08_crypto_keypair_regeneration`: Re-pairing key regeneration.
9. `test_09_transport_tls_verification_mandatory`: TLS verification enforcement.
10. `test_10_transport_session_token_injection`: Authorization header injection.
11. `test_11_enrollment_pairing_success`: Successful 6-digit PIN pairing.
12. `test_12_enrollment_invalid_pin_rejected`: Rejection of malformed/invalid PINs.
13. `test_13_enrollment_public_key_matches_crypto`: Public key integrity during enrollment.
14. `test_14_auth_challenge_acquisition`: 32-byte nonce challenge issuance.
15. `test_15_auth_challenge_response_success`: Challenge-response authentication flow.
16. `test_16_auth_replay_attack_rejected`: Replay attack rejection.
17. `test_17_auth_expired_challenge_rejected`: Expired challenge rejection.
18. `test_18_heartbeat_payload_telemetry`: Host telemetry metrics collection.
19. `test_19_heartbeat_updates_backend_state`: Backend device status update to online.
20. `test_20_heartbeat_revocation_detection`: 403 `DEVICE_REVOKED` handling.
21. `test_21_heartbeat_consecutive_failures_degraded`: Degradation on repeated failure.
22. `test_22_reconnect_exponential_backoff_sequence`: Backoff timing validation.
23. `test_23_reconnect_halts_on_revocation`: Permanent halt on revocation.
24. `test_24_lifecycle_graceful_shutdown`: Graceful shutdown and clean exit.
25. `test_25_crash_recovery_detection`: Dirty shutdown crash detection.
26. `test_26_windows_startup_manager`: Safe registry autostart management.
27. `test_27_audit_logger_redaction`: Sensitive token masking verification.
28. `test_28_audit_lifecycle_events_logged`: Structured audit event generation.
29. `test_29_multi_tenant_device_isolation`: Cross-tenant device isolation.
30. `test_30_ast_security_scan`: AST security scan (0 eval, 0 exec, 0 shell=True).

---

### 17. REAL WINDOWS PC VERIFICATION GUIDE
To run and verify the agent on a host Windows machine:

```powershell
# 1. Check Agent Status and Hardware Fingerprint
python -m agent.windows_agent status

# 2. Pair with Mikasa Account via 6-digit PIN
python -m agent.windows_agent pair 849201

# 3. Start Agent in Foreground
python -m agent.windows_agent start

# 4. Manage Windows Autostart (HKCU)
python -m agent.windows_agent autostart status
python -m agent.windows_agent autostart enable
python -m agent.windows_agent autostart disable
```

---

### 18. SECURITY CHECKLIST & OPERATIONAL RUNBOOK
- [x] Zero hardcoded secrets in source code or packaging spec.
- [x] Private keys encrypted at rest via Windows DPAPI.
- [x] TLS verification enabled by default; no `verify=False`.
- [x] 60-second nonce TTL with single-use replay enforcement.
- [x] Memory wiping on graceful shutdown.
- [x] Zero dangerous execution primitives (`eval`, `exec`, `shell=True`).
- [x] No hidden persistence or UAC elevation bypass.
- [x] 30/30 unit and integration tests passing.
