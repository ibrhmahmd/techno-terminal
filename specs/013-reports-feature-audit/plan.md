# Implementation Plan: Reports Feature — Bug Fixes & Rich Tables

**Branch**: `013-reports-feature-audit` | **Date**: 2026-05-20 | **Spec**: `specs/013-reports-feature-audit/spec.md`
**Input**: Feature specification from `/specs/013-reports-feature-audit/spec.md`

## Summary

Two-phased scope: (1) Fix 5 daily report bugs — attendance status filters, COALESCE NULL fallbacks, raw SQL in service layer, untyped dict returns, SQL injection in recipient resolution, dead code. (2) Add 3 rich detail tables to daily report — per-session attendance breakdown with student names, payments grouped by type with subtotals, instructor summary. All tables appear in both email body and PDF attachment.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI, SQLModel, PostgreSQL, SQLAlchemy, ReportLab, smtplib
**Storage**: PostgreSQL (existing `notification_templates`, `notification_logs`, `notification_additional_recipients`, `sessions`, `attendance`, `payments`, `receipts` tables)
**Testing**: pytest (no existing tests for report notifications)
**Target Platform**: Linux server (Leapcell via uvicorn)
**Project Type**: web-service (FastAPI backend, 11-module monolith)
**Performance Goals**: Reports are async background tasks — no latency targets
**Constraints**: statement_timeout=30000, pool_size=10+5 overflow, pool_recycle=240s
**Scale/Scope**: Single FastAPI app; daily report runs once/day for <10 recipients via email + PDF

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Rationale |
|------|--------|-----------|
| **I. Layer Separation** | ✅ PASS | New queries in ReportsRepository, service delegates, router has no business logic |
| **II. Module Organization** | ✅ PASS | Flat horizontal layout — new DTOs under `notifications/schemas/`, new methods in existing `ReportsRepository` |
| **III. Typed Contracts** | ✅ PASS | 3 new DTOs: `SessionDetailItem`, `PaymentTypeGroup`, `InstructorSummaryItem` — no bare dicts |
| **IV. Response Envelope** | ✅ PASS | Not applicable — reports are background dispatch, not API responses |
| **V. Auth-Guarded Endpoints** | ✅ PASS | `POST /reports/daily` uses existing `require_admin` guard |
| **VI. Dead Code Discipline** | ✅ PASS | Already resolved in bug-fix phase — PARENT_CODE block deleted |
| **VII. Cross-Slice Service Import** | ✅ PASS | No services importing other services within module |

## Project Structure

### Documentation (this feature)

```text
specs/013-reports-feature-audit/
├── spec.md              # Feature specification (clarified)
├── plan.md              # This file
├── research.md          # Phase 0 — implementation decisions
├── data-model.md        # Phase 1 — DTOs and entities
├── quickstart.md        # Phase 1 — agent bootstrap
├── contracts/           # Phase 1 — interface contracts
└── tasks.md             # Phase 2 — task breakdown
```

### Source Code (repository root)

```text
app/modules/notifications/
├── repositories/
│   ├── __init__.py
│   ├── notification_repository.py      # Existing
│   ├── admin_settings_repository.py    # Existing
│   └── reports_repository.py           # EXISTS — add 3 new query methods
├── schemas/
│   ├── __init__.py
│   ├── report_dto.py                   # EXISTS — add 3 new DTOs
│   └── ...
├── services/
│   ├── base_notification_service.py    # EXISTS — fixed SQL injection
│   ├── report_notifications.py         # EXISTS — add table rendering in service
│   ├── notification_service.py         # Existing
│   └── report_scheduler.py             # Existing (no changes)
├── pdf/
│   └── daily_report_pdf.py             # EXISTS — add 3 new PDF sections
└── ...
```

**Structure Decision**: Notifications module uses flat horizontal layout (Pattern A). No new sub-slices needed. The three new tables are additions to existing `DailyReportAggregateDTO` and `ReportsRepository` — same patterns as the bug-fix phase.

## Complexity Tracking

No constitution violations. All gates pass.
