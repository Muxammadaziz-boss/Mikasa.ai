# Phase 46 — Real Remote Tool Execution

## Overview

Phase 46 implements **production-grade secure remote command execution** for Mikasa AI v8.0.0.
The system enables authenticated users to remotely execute whitelisted tools on enrolled Windows
PC agents with full audit logging, path security, confirmation flows, and replay protection.

> **IMPORTANT**: This is NOT a remote shell or RAT. Only pre-registered tools with strict
> schemas can be executed. Arbitrary shell commands are **permanently blocked**.

## Architecture

```
User (Web/Telegram)
        │
        ▼
┌──────────────────┐
│  Backend API     │  6 new endpoints for command lifecycle
│  (api_server.py) │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│  CommandQueueManager │  Server-side command queue & confirmation tokens
│  (command_queue.py)  │  Thread-safe, in-memory with history
└────────┬─────────────┘
         │ Agent polls every 5s
         ▼
┌──────────────────────┐
│  RemoteCommandExecutor│  Agent-side validation pipeline
│  (agent/executor.py)  │  Idempotency → Expiry → Nonce → Tool → Confirm → Execute
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  AgentToolRegistry   │  15 real Windows tool handlers
│  (agent/tools.py)    │  Path security, app allowlists, protected processes
└──────────────────────┘
```

## Security Guarantees

### Zero Forbidden Calls
- **0 eval()** — Verified by AST scan
- **0 exec()** — Verified by AST scan
- **0 os.system()** — Verified by AST scan
- **0 subprocess(shell=True)** — All subprocess calls use explicit arg lists with `shell=False`

### Path Security (PathSecurityValidator)
| Check | Error Code |
|-------|-----------|
| `..` in path | PATH_TRAVERSAL |
| UNC paths (`\\server\share`) | UNC_PATH_BLOCKED |
| Windows device names (CON, NUL, COM1-9, LPT1-9) | DEVICE_NAME_BLOCKED |
| Sensitive dirs (C:\Windows, AppData, .ssh, .gnupg) | SENSITIVE_DIRECTORY |
| Credential files (.env, id_rsa, *.key, *.pem) | CREDENTIAL_FILE |
| Outside sandbox | PATH_OUTSIDE_SANDBOX |
| Default sandbox | `~/MikasaSandbox/` |

### App Security
- **Allowlisted apps only**: notepad, calc, explorer, paint, wordpad, snipping_tool, task_manager, chrome
- **Protected processes** cannot be terminated: csrss, wininit, services, lsass, smss, winlogon, system, svchost, dwm, explorer, registry, fontdrvhost, conhost, RuntimeBroker

### Command Validation Pipeline (agent/executor.py)
1. **Idempotency**: Same `command_id` returns cached result
2. **Expiry**: Commands expire after 5 minutes (300s TTL)
3. **Nonce replay**: Same nonce blocked
4. **Tool lookup**: Only registered tools accepted
5. **Confirmation**: HIGH risk tools require 2-step confirmation
6. **Timeout**: Each tool has enforced timeout (5-15s)
7. **Result sanitization**: Secrets redacted, size limited to 64KB
8. **Dangerous lock**: Only one HIGH risk operation per device at a time

## Registered Tools (15)

| Tool ID | Category | Risk | Confirmation | Description |
|---------|----------|------|-------------|-------------|
| system.status | system | LOW | No | CPU, RAM, uptime |
| system.info | system | LOW | No | Full system details |
| system.screenshot | system | LOW | No | Screen capture (PIL) |
| app.list | apps | LOW | No | Running processes |
| app.launch | apps | MEDIUM | No | Launch allowlisted app |
| app.close | apps | MEDIUM | Yes | Terminate process |
| file.list | files | LOW | No | List sandbox directory |
| file.read | files | MEDIUM | No | Read file (max 64KB) |
| file.write | files | HIGH | Yes | Write file (max 256KB) |
| file.delete | files | HIGH | Yes | Delete single file |
| network.info | network | LOW | No | IP, interfaces |
| power.restart | power | HIGH | Yes | Restart (5s delay) |
| power.shutdown | power | HIGH | Yes | Shutdown (5s delay) |
| power.sleep | power | HIGH | Yes | Sleep mode |
| power.wake | power | LOW | No | Wake-on-LAN |

## API Endpoints

### User-facing (authenticated via Bearer token)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/devices/{device_id}/commands` | Submit new command |
| POST | `/api/devices/{device_id}/commands/{command_id}/confirm` | Confirm dangerous command |
| POST | `/api/devices/{device_id}/commands/{command_id}/cancel` | Cancel pending command |
| GET | `/api/devices/{device_id}/commands/history` | View command history |

### Device-facing (authenticated via device session token)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices/{device_id}/commands/pending` | Poll for pending commands |
| POST | `/api/devices/{device_id}/commands/{command_id}/result` | Submit execution result |

## Command Lifecycle

```
SUBMIT → [PENDING | AWAITING_CONFIRMATION]
                    │
           CONFIRM  │  (token required)
                    ▼
              CONFIRMED → DISPATCHED → EXECUTING → SUCCEEDED/FAILED
                                                     │
                                                     ▼
                                                  HISTORY
```

- **PENDING**: Ready for agent to pick up
- **AWAITING_CONFIRMATION**: HIGH risk tool needs user to confirm with token
- **CONFIRMED**: User confirmed, ready for dispatch
- **DISPATCHED**: Sent to agent
- **SUCCEEDED/FAILED**: Terminal states, moved to history
- **EXPIRED**: TTL exceeded (5 minutes)
- **CANCELLED**: User cancelled before execution

## Audit Events (14 new)

| Event | Description |
|-------|-------------|
| REMOTE_COMMAND_SUBMITTED | New command submitted to queue |
| REMOTE_COMMAND_DISPATCHED | Command sent to agent |
| REMOTE_COMMAND_CONFIRMED | User confirmed dangerous command |
| REMOTE_COMMAND_REJECTED | Command rejected (auth/permission/validation) |
| REMOTE_COMMAND_SUCCEEDED | Command executed successfully |
| REMOTE_COMMAND_FAILED | Command execution failed |
| REMOTE_COMMAND_TIMEOUT | Command timed out |
| REMOTE_COMMAND_EXPIRED | Command TTL expired |
| REMOTE_COMMAND_CANCELLED | Command cancelled by user |
| REMOTE_COMMAND_REPLAY_BLOCKED | Nonce replay attempt blocked |
| REMOTE_CONFIRMATION_REQUESTED | Confirmation token generated |
| REMOTE_CONFIRMATION_ACCEPTED | Confirmation token accepted |
| REMOTE_CONFIRMATION_EXPIRED | Confirmation token expired |
| REMOTE_PERMISSION_DENIED | Permission check failed |

## Files Modified/Created

### New Files
| File | Description |
|------|-------------|
| `agent/tools.py` | 15 real Windows tool handlers with path/app security |
| `agent/executor.py` | RemoteCommandExecutor + CommandPoller |
| `core/v8/command_queue.py` | Server-side command queue manager |
| `tests/test_v8_phase46.py` | 35 security tests |
| `docs/phase-46-remote-tools.md` | This documentation |

### Modified Files
| File | Change |
|------|--------|
| `core/v8/events.py` | 14 new RemoteEventType entries |
| `core/v8/remote_tools.py` | Extended RemoteToolDefinition (5 new fields), file.write/file.delete executors and registrations |
| `core/api_server.py` | 6 new command queue API endpoints |
| `agent/__init__.py` | Phase 46 exports |

## Test Coverage

35 tests across 5 test classes:
- **TestPathSecurityValidator** (8): Path traversal, UNC, device names, sensitive dirs, credentials, sandbox
- **TestAgentToolRegistry** (7): Singleton, tool count, handlers, app allowlist
- **TestRemoteCommandExecutor** (8): Idempotency, expiry, replay, confirmation, execution
- **TestCommandQueueManager** (8): Submit, confirm, cancel, pending, result, history
- **TestPhase46Integration** (4): Registry count, event types, extended definition, AST security scan
