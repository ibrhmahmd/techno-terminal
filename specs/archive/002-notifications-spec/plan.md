# Implementation Plan: Notifications Module

**Branch**: `002-notifications-spec` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-notifications-spec/spec.md`

## Summary

Deliver a robust email notification system covering enrollment lifecycle, payment events, scheduled business reports, and competition notifications. Admins manage recipients, templates, and per-type channel configuration. Failed sends auto-retry up to 3 times with manual retry from the audit log.

## Technical Context

**Language/Version**: Python 3.11+ (existing codebase)  
**Primary Dependencies**: FastAPI, SQLModel, SQLAlchemy, python-jose, supabase (existing — no new dependencies for core logic). Twilio SDK (existing) kept for future WhatsApp expansion but disabled.  
**Storage**: PostgreSQL 15+ via SQLModel ORM. Existing tables: `notification_templates`, `notification_logs`, `admin_notification_settings`, `notification_additional_recipients`.  
**Testing**: pytest (existing). No notification tests exist — must be created. Mock email dispatcher needed.  
**Target Platform**: Linux server (Leapcell / Docker)  
**Project Type**: Web service (FastAPI REST API)  
**Performance Goals**: Notifications delivered within 5 minutes of triggering event (from spec SC-001). Automatic retry within 1min/5min/30min windows.  
**Constraints**: Notification service opens its own DB session (independent from request session — intentional). Email-only channel for now; channel system must be extensible for WhatsApp later. Admin settings repository currently uses raw SQL with f-string interpolation — must be refactored to parameterized queries.  
**Scale/Scope**: Small center management system (tens of staff recipients, tens to low hundreds of notification events per day).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layer Separation (Router → Service → Repository) | ✅ PASS | Existing notifications module follows this pattern. Routers in `app/api/routers/notifications/`, services in `app/modules/notifications/services/`, repositories in `app/modules/notifications/repositories/`. |
| I. Services MUST NOT import from `app.api.*` | ✅ PASS | No violations found in existing code. |
| I. Repositories MUST NOT contain business logic | ❌ FAIL | `AdminSettingsRepository` uses raw SQL with f-string interpolation (`f"WHERE admin_id = {admin_id}"`) — SQL injection risk AND business rule leak (the interpolation itself is a security concern). Must refactor to parameterized queries. |
| I. Two-Layer Schema Rule | ✅ PASS | DTOs in `app/modules/notifications/schemas/`, router schemas in `app/api/schemas/` — no cross-import issues. |
| II. Module Organization | ✅ PASS | Notifications is a flat module (≤2 entities per slice pattern). Models horizontal in `models/`. |
| III. Typed Contracts — No Loose Return Types | ❌ FAIL | `AdminSettingsRepository` returns `list[dict]` from `get_admin_settings()`, `get_recipient()`, `get_additional_recipients()`, etc. These must return typed Pydantic DTOs. |
| IV. Response Envelope | ✅ PASS | All endpoints use `ApiResponse` wrapper. |
| V. Auth-Guarded Endpoints | ✅ PASS | All notification endpoints use `require_admin`. |
| Session Lifecycle (Notifications own session) | ✅ PASS | `get_notification_service()` opens independent session — matches constitutional rule. |
| Dead Code Discipline | ⚠️ WARN | Bulk notification router (`bulk_router.py`) exists but feature is deferred. WhatsApp dispatcher code exists but is disabled. Comented-out parent WhatsApp code in enrollment/payment services. These need removal per constitutional dead code rule. |

**Gate Decision**: ⚠️ **CONDITIONAL PASS** — Two constitution violations exist (raw SQL injection risk in admin_settings_repository, and loose return types). These will be addressed in the implementation plan as explicit refactoring tasks. Dead code removal (bulk router, WhatsApp dispatcher) flagged as warning — recommend removing or explicitly marking as deferred.

**Post-Phase 1 Re-evaluation**: ✅ **GATE MAINTAINED** — All violations are explicitly addressed by concrete steps in [quickstart.md](./quickstart.md):
- Step 1: Dead code removal (bulk_router.py, WhatsApp dispatcher)  
- Step 2: Parameterized queries in AdminSettingsRepository  
- Step 3: Typed DTOs for repository returns

## Project Structure

### Documentation (this feature)

```text
specs/002-notifications-spec/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
app/
├── api/
│   └── routers/
│       └── notifications/
│           ├── notifications_router.py    # Core notification endpoints
│           ├── templates_router.py         # Template CRUD
│           ├── admin_settings_router.py    # Admin settings + recipients
│           └── bulk_router.py              # [DECOMMISSION] Deferred feature
└── modules/
    └── notifications/
        ├── models/
        │   ├── notification_log.py
        │   └── notification_template.py
        ├── interfaces/
        │   └── i_notification_repository.py
        ├── dispatchers/
        │   ├── i_dispatcher.py
        │   ├── email_dispatcher.py
        │   └── whatsapp_dispatcher.py      # [DECOMMISSION] Deferred channel
        ├── repositories/
        │   ├── notification_repository.py
        │   └── admin_settings_repository.py # [REFACTOR] Raw SQL → parameterized
        ├── schemas/
        │   ├── admin_settings_dto.py
        │   ├── fallback_dto.py
        │   ├── notification_dto.py
        │   ├── send_request.py
        │   └── template_dto.py
        ├── services/
        │   ├── base_notification_service.py
        │   ├── competition_notifications.py
        │   ├── enrollment_notifications.py
        │   ├── notification_service.py
        │   ├── payment_notifications.py
        │   ├── report_notifications.py
        │   └── report_scheduler.py
        └── pdf/
            └── daily_report_pdf.py

tests/
└── test_notifications.py                   # [CREATE] New test module
```

**Structure Decision**: Follow existing project conventions — FastAPI routers in `app/api/routers/notifications/`, module logic in `app/modules/notifications/` with flat horizontal layer (models, repositories, services, schemas, dispatchers). No new directory structure needed; work is primarily refactoring existing code and adding tests.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Raw SQL in `AdminSettingsRepository` | Exists in codebase; will be refactored to use SQLModel ORM or parameterized SQLAlchemy `text()` queries | Direct ORM queries are safer and align with constitution rules |
| `list[dict]` return types in `AdminSettingsRepository` | Legacy code; will be replaced with typed DTOs | Typed DTOs catch structural changes at compile time per constitution §III |
