# Implementation Plan: Daily Report Redesign & Debtors Data

**Branch**: `019-daily-report-redesign` | **Date**: 2026-05-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-daily-report-redesign/spec.md`

## Summary

Redesign the daily report email from generic Arial/border-based layout to the Precision Engine design system (Space Grotesk/Inter, tonal layering, teal/deep slate palette, Power Gradient KPIs, status chips). Add debtors data: today's unpaid attendees, top 5 debtors, outstanding by group, and tomorrow's unpaid attendee preview. Deliver a CLI test script for visual validation before production rollout. PDF stays black & white (unchanged).

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: FastAPI, SQLModel, ReportLab, Gmail SMTP (all project standard)  
**Storage**: PostgreSQL via SQLModel (no new migrations except template body UPDATE)  
**Testing**: pytest  
**Target Platform**: Linux server (Leapcell deployment)  
**Project Type**: Web service (FastAPI backend)  
**Performance Goals**: Email generation within 5 seconds, PDF generation within 10 seconds  
**Constraints**: Gmail 102KB email clip limit, no new DB schema migrations, no new API endpoints  
**Scale/Scope**: Single center, ~500 students, ~50 daily sessions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| **I. Layer Separation** | ✅ PASS | No new routers. CLI script calls service directly (by spec). Service calls repo for tomorrow query. All existing patterns preserved. |
| **II. Module Organization** | ✅ PASS | All changes within existing notifications module. No slice changes needed. |
| **III. Typed Contracts** | ✅ PASS | All new DTOs are typed Pydantic models with `ConfigDict(from_attributes=True)`. No `dict`/`list[dict]` returns. |
| **IV. Response Envelope** | ✅ PASS | No new API endpoints. Existing endpoints unchanged. |
| **V. Auth-Guarded Endpoints** | ✅ PASS | CLI script is unauthenticated per spec clarification — not an API endpoint, no security concern. |

**No violations found.** Design is constitution-compliant.

## Project Structure

### Documentation (this feature)

```text
specs/019-daily-report-redesign/
├── plan.md              # This file
├── research.md          # Phase 0 — design decisions
├── data-model.md        # Phase 1 — DTO definitions
├── quickstart.md        # Phase 1 — execution order
├── contracts/           # Phase 1 — no external interfaces
└── tasks.md             # Phase 2 — (created by /speckit.tasks)
```

### Source Code Changes

```text
app/modules/notifications/schemas/
├── report_dto.py                          # MODIFY: add 4 new DTOs, extend DailyReportAggregateDTO

app/modules/notifications/repositories/
├── reports_repository.py                  # MODIFY: add _fetch_tomorrow_preview()

app/modules/notifications/services/
├── report_notifications.py                # MODIFY: fetch debtors data, render new HTML sections

scripts/
├── test_report_email.py                   # CREATE: CLI test email script

db/migrations/
├── 058_update_daily_report_precision_engine.sql   # CREATE: template body update
```

## Complexity Tracking

No constitution violations found. No complexity justification needed.
