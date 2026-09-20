# Phase 47: Full Agent Access & User Consent

> Mikasa AI v8.0.0 — Production-Grade User-Controlled Agent Authority

## 1. Umumiy Ko'rinish (Overview)

Phase 47 Mikasa AI agentiga **TO'LIQ VAKOLAT** (Full Agent Access) berish
uchun xavfsiz, foydalanuvchi tomonidan boshqariladigan tizimni amalga oshiradi.
Bu tizim foydalanuvchiga o'z qurilmasidagi agentga to'liq yoki cheklangan
vakolat berishni 4 bosqichli xavfsizlik pipeline orqali amalga oshiradi.

## 2. Arxitektura (Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (React)                        │
│  AccountPage.tsx → AgentAccessSecuritySection.tsx        │
│  backendService.ts (8 API methods)                       │
├─────────────────────────────────────────────────────────┤
│                  REST API (aiohttp)                       │
│  8 endpoints: /agent-access/*                            │
│  api_server.py: handle_agent_access_*                    │
├─────────────────────────────────────────────────────────┤
│                  CORE LOGIC                               │
│  AgentAccessManager (Singleton, RLock)                   │
│  ├── initiate_activation()                               │
│  ├── acknowledge_warning()                               │
│  ├── verify_reauthentication()                           │
│  ├── confirm_activation()                                │
│  ├── disable_full_access()                               │
│  ├── emergency_revoke()                                  │
│  └── set_permission_override()                           │
├─────────────────────────────────────────────────────────┤
│                  INTEGRATIONS                             │
│  PermissionCenter → access_level check                   │
│  CommandQueue → cancel_pending_for_device()              │
│  Events → 10 audit event types                           │
│  UniversalBot → /access, /permissions, /revoke           │
│  Supabase → agent_access_grants table + RLS              │
└─────────────────────────────────────────────────────────┘
```

## 3. 4-Bosqichli Faollashtirish Pipeline

```
User Request → [Step 1: Warning] → [Step 2: Acknowledge]
            → [Step 3: Re-Auth] → [Step 4: Confirm]
            → FULL ACCESS GRANTED ✅
```

1. **initiate_activation()** — Warning ko'rsatish, ActivationChallenge yaratish
2. **acknowledge_warning()** — Foydalanuvchi ogohlantirishni tasdiqlash
3. **verify_reauthentication()** — Parol/JWT bilan qayta autentifikatsiya
4. **confirm_activation()** — Yakuniy tasdiqlash, FULL access grant yaratish

## 4. Data Models

### AccessLevel (Enum)
- `LIMITED` — Standart cheklangan access (default)
- `FULL` — To'liq vakolat, barcha ruxsatlar berilgan
- `CUSTOM` — FULL dan ba'zi ruxsatlar o'chirilgan

### AgentAccessGrant (Dataclass)
```python
@dataclass
class AgentAccessGrant:
    user_id: str
    device_id: str
    access_level: str = "LIMITED"
    policy_version: str = "1.0.0"
    warning_acknowledged: bool = False
    reauthenticated_at: Optional[float] = None
    confirmation_id: Optional[str] = None
    enabled_at: Optional[float] = None
    overrides: Dict[str, bool] = field(default_factory=dict)
```

### ActivationChallenge (Dataclass)
- TTL: 5 daqiqa (300 soniya)
- `warning_token` — Warning bosqichi uchun
- `confirmation_token` — Yakuniy tasdiqlash uchun

## 5. Xavfsizlik Modeli (Security Model)

### Device Ownership Verification
- Faqat qurilma egasi full access bera oladi
- Cross-tenant activation bloklangan

### Rate Limiting
- 5 urinish / 60 soniya (user+device scope)

### Challenge TTL
- 5 daqiqa ichida barcha bosqichlar yakunlanishi kerak

### Thread Safety
- `threading.RLock` barcha operatsiyalar uchun
- Singleton pattern bilan global holat boshqaruvi

### AST Security
- 0 eval, 0 exec, 0 os.system, 0 shell=True

## 6. REST API Endpoints

| Method | Path | Handler |
|--------|------|---------|
| GET | `/api/devices/{id}/agent-access` | `handle_agent_access_get` |
| POST | `/api/devices/{id}/agent-access/warning` | `handle_agent_access_warning` |
| POST | `/api/devices/{id}/agent-access/acknowledge` | `handle_agent_access_acknowledge` |
| POST | `/api/devices/{id}/agent-access/reauth` | `handle_agent_access_reauth` |
| POST | `/api/devices/{id}/agent-access/confirm` | `handle_agent_access_confirm` |
| POST | `/api/devices/{id}/agent-access/disable` | `handle_agent_access_disable` |
| POST | `/api/devices/{id}/agent-access/revoke` | `handle_agent_access_revoke` |
| POST | `/api/devices/{id}/agent-access/override` | `handle_agent_access_override` |

## 7. Telegram Bot Buyruqlari

| Buyruq | Vazifasi |
|--------|----------|
| `/access` | Agent vakolat darajasi (LIMITED/FULL/CUSTOM) |
| `/permissions` | Barcha 15 ruxsat ro'yxati ✅/❌ |
| `/revoke` | 🚨 Favqulodda barcha vakolatlarni bekor qilish |

## 8. Frontend Components

### AgentAccessSecuritySection.tsx
- Device selector dropdown
- Access Level card (🟢 FULL / 🟡 LIMITED)
- "Enable Full Agent Access" button → 3-modal flow
- Warning Modal → Re-Auth Modal → Confirmation Modal
- Permissions Panel (15 tools, ON/OFF toggle)
- Danger Zone: Emergency Revoke (requires typing "REVOKE")

### AccountPage.tsx Integration
- "Xavfsizlik & Agent" tab qo'shildi
- ShieldIcon bilan navigatsiya
- AgentAccessSecuritySection komponenti render qilinadi

## 9. Permission Center Integration

`UserPermissionProfile.is_granted()` yangilandi:
1. Explicit permission check (set qilingan ruxsatlar)
2. **Phase 47:** FULL/CUSTOM access_level check — True qaytaradi
3. Default fallback (STANDARD_PERMISSIONS dan)

## 10. Command Queue Integration

Yangi metodlar:
- `cancel_pending_for_device(device_id, reason)` — Pending/awaiting buyruqlarni bekor qilish
- `invalidate_confirmations_for_device(device_id)` — Confirmation tokenlarni bekor qilish

Emergency revoke paytida avtomatik chaqiriladi.

## 11. Supabase Migration

`agent_access_grants` table:
- RLS: Har bir foydalanuvchi faqat o'z grantlarini ko'radi/o'zgartiradi
- Service role: to'liq access
- Unique constraint: (user_id, device_id)
- Auto-update trigger: `updated_at`

## 12. Audit Events (10 ta)

| Event | Tavsifi |
|-------|---------|
| FULL_ACCESS_WARNING_SHOWN | Warning ko'rsatildi |
| FULL_ACCESS_WARNING_ACKNOWLEDGED | Warning tasdiqlandi |
| FULL_ACCESS_REAUTH_PASSED | Qayta autentifikatsiya muvaffaqiyatli |
| FULL_ACCESS_REAUTH_FAILED | Qayta autentifikatsiya muvaffaqiyatsiz |
| FULL_ACCESS_ENABLED | Full access faollashtirildi |
| FULL_ACCESS_DISABLED | Full access o'chirildi |
| FULL_ACCESS_CROSS_TENANT_BLOCKED | Boshqa tenant bloklandi |
| FULL_ACCESS_PERMISSION_OVERRIDE | Individual ruxsat o'zgartirildi |
| FULL_ACCESS_EMERGENCY_REVOKE | Favqulodda bekor qilish |
| FULL_ACCESS_DEVICE_SCOPE_VIOLATION | Device scope buzilishi |

## 13. O'zgartirilgan Fayllar

### Backend (Python)
| Fayl | O'zgarish |
|------|-----------|
| `core/v8/agent_access.py` | **YANGI** — 450+ qator, core model & manager |
| `core/v8/events.py` | 10 yangi event type + 3 sensitive key |
| `core/v8/permission_center.py` | access_level, FULL check, from_dict safety |
| `core/v8/command_queue.py` | cancel_pending_for_device, invalidate_confirmations |
| `core/v8/__init__.py` | Phase 47 exports, PHASE = 47 |
| `core/v8/universal_bot.py` | /access, /permissions, /revoke + handlers |
| `core/api_server.py` | 8 API handlers + 8 route registrations |
| `supabase/migrations/20260920_phase47_agent_access.sql` | **YANGI** — RLS table |

### Frontend (TypeScript/React)
| Fayl | O'zgarish |
|------|-----------|
| `src/services/backendService.ts` | 2 interface + 8 API methods + access_count fix |
| `src/components/AgentAccessSecuritySection.tsx` | **YANGI** — 900+ qator UI |
| `src/pages/AccountPage.tsx` | Security tab + render block |

### Tests
| Fayl | O'zgarish |
|------|-----------|
| `tests/test_v8_phase47.py` | **YANGI** — 45 test, 14 kategoriya |

## 14. Existing Phase Compatibility

Phase 47 quyidagi komponentlarga **TO'G'RI INTEGRATSIYA** qilingan:
- Phase 38: PermissionStore — access_level check qo'shildi
- Phase 39: UniversalBot — 3 yangi command
- Phase 40: AccountDeviceManager — device ownership verification
- Phase 41: SupabaseAuth — reauth JWT verification
- Phase 46: CommandQueue — cancel_pending + invalidate_confirmations

**BUZILGAN NARSA YO'Q** — barcha mavjud testlar PASS qilishi kerak.
