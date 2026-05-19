# Implementation Plan: Reports Feature — Daily Report Fixes

**Branch**: `013-reports-feature-audit` | **Date**: 2026-05-19 | **Spec**: `specs/013-reports-feature-audit/spec.md`
**Input**: Feature specification from `/specs/013-reports-feature-audit/spec.md`

## Summary

Fix the daily report to produce accurate, non-empty business data. Five bugs found: attendance query filters for non-existent `late`/`excused` statuses, `paid_at`/`enrolled_at` NULL causes zero revenue/enrollment counts, 6 of 11 template variables computed but never rendered in email body, raw SQL in service layer (constitution violation), and no typed DTOs (constitution violation). Scope is daily-report-only; weekly/monthly/scheduler deferred.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI, SQLModel, PostgreSQL, SQLAlchemy, ReportLab, smtplib
**Storage**: PostgreSQL (existing `notification_templates`, `notification_logs`, `notification_additional_recipients` tables)
**Testing**: pytest (no existing tests for report notifications — test coverage to be added)
**Target Platform**: Linux server (Leapcell deployment via uvicorn)
**Project Type**: web-service (FastAPI backend, 11-module monolith)
**Performance Goals**: N/A — reports are async background tasks (non-blocking)
**Constraints**: statement_timeout=30000, pool_size=10+5 overflow, pool_recycle=240s
**Scale/Scope**: Single FastAPI app; daily report runs once/day for <10 recipients via email + PDF

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Rationale |
|------|--------|-----------|
| **I. Layer Separation** | ❌ **VIOLATED** | `report_notifications.py` executes raw SQL via `session.exec(text(...))` — repositories must own all queries |
| **II. Module Organization** | ✅ PASS | Reports live in existing `notifications.services` — no new module needed |
| **III. Typed Contracts** | ❌ **VIOLATED** | `_fetch_daily_aggregates()` returns bare `dict` instead of typed DTO |
| **IV. Response Envelope** | ✅ PASS | Not applicable — reports are background dispatch, not API responses |
| **V. Auth-Guarded Endpoints** | ✅ PASS | New HTTP trigger endpoints will use existing `require_admin` guard |
| **VI. Dead Code Discipline** | ❌ **VIOLATED** | Commented-out PARENT_CODE block preserved in `report_notifications.py:429-441` |
| **VII. Cross-Slice Service Import** | ✅ PASS | No services importing other services within module |

**Justification for violations** (to be resolved by this plan):
- **Layer Separation (I)**: The inline SQL will be extracted into a new `ReportsRepository` under `app/modules/notifications/repositories/`. The service will call typed repository methods.
- **Typed Contracts (III)**: A `DailyReportAggregateDTO` Pydantic model will replace the `dict` return.
- **Dead Code (VI)**: The commented-out PARENT_CODE block will be deleted.

## Project Structure

### Documentation (this feature)

```text
specs/013-reports-feature-audit/
├── spec.md              # Feature specification (this directory)
├── plan.md              # This file
├── research.md          # Phase 0 - implementation decisions
├── data-model.md        # Phase 1 - DTOs and entities
├── quickstart.md        # Phase 1 - agent bootstrap
├── contracts/           # Phase 1 - interface contracts
└── tasks.md             # Phase 2 - task breakdown
```

### Source Code (repository root)

```text
app/modules/notifications/
├── repositories/
│   ├── __init__.py
│   ├── notification_repository.py      # Existing
│   ├── admin_settings_repository.py    # Existing
│   └── reports_repository.py           # NEW — report aggregate queries
├── schemas/
│   ├── __init__.py
│   ├── notification_dto.py             # Existing
│   ├── template_dto.py                 # Existing
│   ├── admin_settings_dto.py           # Existing
│   ├── send_request.py                 # Existing
│   ├── fallback_dto.py                 # Existing
│   └── report_dto.py                   # NEW — DailyReportAggregateDTO
├── services/
│   ├── __init__.py
│   ├── base_notification_service.py    # Existing (modify _resolve_notification_recipients SQL safety)
│   ├── notification_service.py         # Existing (add HTTP trigger delegates)
│   ├── enrollment_notifications.py     # Existing
│   ├── payment_notifications.py        # Existing
│   ├── competition_notifications.py    # Existing
│   ├── report_notifications.py         # EXISTS — MODIFY (fix 5 bugs)
│   └── report_scheduler.py             # Existing (no changes this sprint)
├── pdf/
│   └── daily_report_pdf.py             # Existing (no changes — already uses dict, will receive DTO)
└── dispatchers/
    ├── __init__.py
    ├── i_dispatcher.py
    ├── email_dispatcher.py
    └── whatsapp_dispatcher.py
```

**Structure Decision**: Notifications module uses flat horizontal layout (Pattern A) — `reports_repository.py` as a new file under existing `repositories/`, `report_dto.py` under `schemas/`. No new sub-slices needed.

## Complexity Tracking

No constitution violations remain after this plan — all three violations are resolved by the planned changes.
