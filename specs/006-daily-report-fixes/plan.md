# Implementation Plan: Daily Report Data & Template Fixes

**Branch**: `main` | **Date**: 2026-05-13 | **Spec**: `specs/006-daily-report-fixes/spec.md`
**Input**: Feature specification from `specs/006-daily-report-fixes/spec.md`

## Summary

Fix 5 bugs in the daily business report: 3 data bugs causing empty sections (wrong column names in instructor query, missing `group_id` on Payment model, date filter mismatch between revenue and payment queries), 1 PDF template redesign for B&W printer compatibility, and 1 email HTML template update with `@media print` rules.

## Technical Context

**Language/Version**: Python 3.13, FastAPI
**Primary Dependencies**: ReportLab (PDF generation), SQLModel/SQLAlchemy (database), SQLite testing (via MockNotificationRepository)
**Storage**: PostgreSQL (Supabase) via `report_notifications.py` `_fetch_*` methods using `get_session()`
**Testing**: pytest 9.0, pytest-asyncio 1.3
**Target Platform**: Linux server (Leapcell deployment)
**Project Type**: Web service (FastAPI backend)
**Performance Goals**: N/A — fixes existing functionality, no new performance requirements
**Constraints**: PDF must be readable on B&W printers; email must render correctly in print preview
**Scale/Scope**: 3 data fix locations in 1 service file + 1 PDF template rewrite + 1 email template update + 3 new tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| §I — Layer Separation | ✅ PASS | Only modifying existing service layer files. No layer violations. |
| §II — Module Organization | ✅ PASS | Changes stay within existing notifications module structure. |
| §III — Typed Contracts | ⚠️ ACCEPTABLE | `_fetch_daily_aggregates` returns `dict` (pre-existing). Fix is out of scope — `#TODO` comment already present on line 164. |
| §IV — Response Envelope | ✅ PASS | No API changes. |
| §V — Auth Guards | ✅ PASS | No new endpoints. |
| §VIII — Dead Code | ✅ PASS | No dead code involved. |

**Gate Result**: PASS — minor pre-existing `dict` return type documented with `#TODO`, no new violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/006-daily-report-fixes/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 — design decisions
├── data-model.md        # Phase 1 — no new entities
├── quickstart.md        # Phase 1 — implementation steps
└── contracts/           # Phase 1 — no new interfaces
```

### Source Code (repository root)

```text
app/modules/notifications/
├── services/
│   └── report_notifications.py   # Bugs 1, 2, 3, 5
├── pdf/
│   └── daily_report_pdf.py       # Bug 4

tests/
└── test_notifications.py         # New: TestReportNotifications class
```

**Structure Decision**: Single project (existing layout). No new files needed — only modifications to 2 existing source files and additions to 1 test file.

## Complexity Tracking

No constitution violations to justify.
