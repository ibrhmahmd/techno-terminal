---

description: "Task list for Phase 2: rich detail tables — Reports Feature Audit"
---

# Tasks: Reports Feature — Rich Detail Tables (Phase 2)

**Input**: Design documents from `specs/013-reports-feature-audit/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Scope**: Phase 2 only — add per-session attendance table, payment grouping by type, and instructor summary table to daily report. Phase 1 (bug fixes) is already complete.

**User Stories**:
- **US1**: Daily report has accurate attendance metrics with per-session breakdown (P1) — includes instructor summary table
- **US8**: Payment breakdown grouped by type with subtotals (P1)

---

## Phase 1: Foundational — DTO Update

**Purpose**: Add 3 new DTOs to `report_dto.py` before repository and service changes.

**⚠️ CRITICAL**: T001 must be complete before all other tasks.

- [ ] T001 [P] Add `SessionDetailItem`, `PaymentTypeGroup`, and `InstructorSummaryItem` DTOs + corresponding fields to `DailyReportAggregateDTO` in `app/modules/notifications/schemas/report_dto.py`

**Checkpoint**: Foundation ready — US1 and US8 can now begin.

---

## Phase 2: User Story 1 — Per-Session Attendance Table (P1)

**Goal**: Daily report includes a per-session attendance table with instructor name, time slot, present/absent/cancelled counts, and comma-separated student names. Also includes a separate instructor summary table. Both appear in email body and PDF.

**Independent Test**: After implementation, inspect daily report email body or PDF — should show one row per completed session with attendance counts and student name lists.

### Implementation for User Story 1

- [ ] T002 [P] [US1] Add `_fetch_session_details(target_date)` to `ReportsRepository` in `app/modules/notifications/repositories/reports_repository.py` — query each completed session with its attendance, join to students for names, return `list[SessionDetailItem]`
- [ ] T003 [P] [US1] Add `_fetch_instructor_summary(target_date)` to `ReportsRepository` in `app/modules/notifications/repositories/reports_repository.py` — query session count per instructor for today, return `list[InstructorSummaryItem]`
- [ ] T004 [US1] Wire `session_details` and `instructor_summary` into `get_daily_aggregates()` in `app/modules/notifications/repositories/reports_repository.py` — populate the new DTO fields
- [ ] T005 [US1] Build per-session attendance HTML table in `send_daily_report()` in `app/modules/notifications/services/report_notifications.py` — render session time, instructor, counts, student names
- [ ] T006 [US1] Build instructor summary HTML table in `send_daily_report()` in `app/modules/notifications/services/report_notifications.py` — render instructor name + session count
- [ ] T007 [US1] Add per-session attendance table section to PDF in `app/modules/notifications/pdf/daily_report_pdf.py` — ReportLab table with same columns
- [ ] T008 [US1] Add instructor summary table section to PDF in `app/modules/notifications/pdf/daily_report_pdf.py` — ReportLab table with instructor name + session count

**Checkpoint**: US1 complete — per-session attendance and instructor summary tables render in both email and PDF.

---

## Phase 3: User Story 8 — Payment Grouping by Type (P1)

**Goal**: Daily report payment section groups transactions by payment type (cash, card, transfer, etc.) with subtotals per type, in both email body and PDF.

**Independent Test**: After implementation, inspect daily report — payments should be organized into sub-tables per type, each with a subtotal EGP header and student/group/amount rows.

### Implementation for User Story 8

- [ ] T009 [US8] Group payments by `payment_type` in `ReportsRepository._fetch_payments()` in `app/modules/notifications/repositories/reports_repository.py` — use the existing payment data, build `list[PaymentTypeGroup]` with subtotals
- [ ] T010 [US8] Build payment type sub-tables with subtotals in `send_daily_report()` in `app/modules/notifications/services/report_notifications.py` — one sub-table per type, header row with type name + subtotal, then student/group/amount rows
- [ ] T011 [US8] Add payments-by-type sub-tables section to PDF in `app/modules/notifications/pdf/daily_report_pdf.py` — ReportLab sub-tables per type with subtotals

**Checkpoint**: US8 complete — payments grouped by type with subtotals in both email and PDF.

---

## Phase 4: Polish & Cross-Cutting

**Purpose**: Update template variables to match the enriched report.

- [ ] T012 Create migration SQL `db/migrations/056_update_daily_report_template.sql` — UPDATE `daily_report` template body to include `{{session_details}}`, `{{instructor_summary}}`, `{{payments_by_type}}` variables, update the `variables` array

**Checkpoint**: All Phase 2 tasks complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: T001 (DTO update) — blocks all user stories
- **US1 (Phase 2)**: Depends on T001 (DTO fields exist), T002–T003 can run in parallel
- **US8 (Phase 3)**: Depends on T001 (DTO fields exist) — can run in parallel with US1 after T001
- **Polish (Phase 4)**: T012 depends on all phases being complete (template must reference all variables)

### User Story Dependencies

- **US1 (P1)**: Depends on T001 — no dependency on US8
- **US8 (P1)**: Depends on T001 — no dependency on US1
- **Polish**: Depends on both stories complete

### Within Each Phase

- DTO before repository before service before PDF
- Repository methods before wiring into `get_daily_aggregates()`
- HTML table before PDF table (same data, different renderers)

### Parallel Opportunities

- T002 and T003 in Phase 2 can run in parallel (different repository methods)
- T005 and T006 in Phase 2 can run in parallel (different HTML table builders in same file — sequential recommended)
- US1 (Phase 2) and US8 (Phase 3) can run in parallel after T001
- T007 and T008 can run in parallel (different PDF sections)

---

## Parallel Example: Phase 2

```bash
# Launch both repository query methods together:
Task: "Add _fetch_session_details() to ReportsRepository"
Task: "Add _fetch_instructor_summary() to ReportsRepository"
```

## Parallel Example: Phase 2 + Phase 3

```bash
# US1 and US8 can run in parallel after T001:
# Developer A:
Task: "US1 — session details query + HTML + PDF"
# Developer B:
Task: "US8 — payment grouping + sub-tables + PDF"
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2 Only)

1. Complete Phase 1: T001 (DTO update)
2. Complete Phase 2: US1 — per-session attendance + instructor summary tables
3. **STOP and VALIDATE**: Inspect email/PDF output
4. Deploy/demo if ready

### Incremental Delivery

1. Phase 1 (DTO) → Types ready
2. Phase 2 (US1) → Session + instructor tables → **MVP complete**
3. Phase 3 (US8) → Payment grouping tables
4. Phase 4 (Polish) → Template migration

### Parallel Strategy

With multiple developers:
- Developer A: Phase 1 → Phase 2 (US1)
- Developer B: Phase 3 (US8) — starts after Phase 1
- Developer A or B: Phase 4 after both stories done
