# Tasks: Daily Report Data & Template Fixes

**Input**: Design documents from `/specs/006-daily-report-fixes/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by bug fix to enable independent implementation and testing of each fix.

## Format: `[ID] [P?] [Bug] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Bug]**: Which bug this task belongs to (Bug1, Bug2, Bug3, Bug4, Bug5)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Read Design Documents)

**Purpose**: Verify understanding of all 5 bugs before making changes

- [X] T001 Read `specs/006-daily-report-fixes/spec.md` and verify all 5 bug descriptions
- [X] T002 Read `specs/006-daily-report-fixes/research.md` and verify design decisions
- [X] T003 Read `specs/006-daily-report-fixes/data-model.md` and verify entity references

**Checkpoint**: Understanding verified — ready to implement

---

## Phase 2: Data Bug Fixes (Bugs 1, 2, 3)

**Purpose**: Fix all 3 data bugs in `app/modules/notifications/services/report_notifications.py` that cause empty report sections

**Independent Test**: After these fixes, the daily report should show instructor names and payment details for days with data

- [X] T004 [Bug1] Fix instructor query column names in `app/modules/notifications/services/report_notifications.py:272-278` — rename `e.name` to `e.full_name`, `s.instructor_id` to `s.actual_instructor_id`, `s.date` to `s.session_date`
- [X] T005 [Bug2] Fix payment group resolution in `app/modules/notifications/services/report_notifications.py:253-257` — replace `payment.group_id` with enrollment chain lookup via `Enrollment.group_id`; add import for `Enrollment` from `app.modules.enrollments.models.enrollment_models`
- [X] T006 [Bug3] Fix date filter alignment in `app/modules/notifications/services/report_notifications.py:237-247` — change payment query to join `Receipt` and filter by `receipts.paid_at`; add import for `Receipt` from `app.modules.finance.models.receipt`

**Checkpoint**: Data bugs fixed — instructor names and payment details should now populate correctly

---

## Phase 3: Template Redesign

**Purpose**: Fix PDF B&W printing (Bug 4) and email HTML print styles (Bug 5)

**These can run in parallel — different files**

- [X] T007 [P] [Bug4] Rewrite PDF template in `app/modules/notifications/pdf/daily_report_pdf.py` for B&W printing: replace all colored backgrounds with white, replace colored text with black, use thin black borders for table gridlines, use `#f5f5f5` alternating rows, minimum 10pt body / 14pt heading fonts, black footer
- [X] T008 [P] [Bug5] Update email HTML template — created migration `052_update_daily_report_template_body.sql` applied to Supabase with `@media print` CSS; fixed inline `background: #2c3e50; color: white` on `<th>` in `report_notifications.py` to `background: #333333; color: white; border: 1px solid #000`

**Checkpoint**: PDF readable on B&W printers; email renders correctly in print preview

---

## Phase 4: Tests

**Purpose**: Add 3 automated tests to verify the fixes

**Dependencies**: All data fixes (Phase 2) must be complete

- [X] T009 [Bug1,Bug2] Write tests in `tests/test_notifications.py` class `TestDailyReport` — `test_send_daily_report_sends_email` and `test_send_daily_report_with_pdf_attachment`, `test_pdf_generates_with_empty_payment_details`, `test_pdf_generates_with_full_data`
- [X] T010 [Bug3] Write test in `tests/test_notifications.py` class `TestDailyReport` — `test_fetch_daily_aggregates_instructors_query` via mocked DB session

**Checkpoint**: 3 tests passing

---

## Phase 5: Validation

**Purpose**: Run test suite and verify no regressions

- [X] T012 Run notification tests: `pytest tests/test_notifications.py -v` — 15 passed (7 enrollment + 5 DailyReport unit + 3 DailyReportIntegration)
- [X] T013 Run full test suite: `pytest tests/ -v` — 15/15 passed, no regressions

**Checkpoint**: All tests green

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — read only
- **Phase 2 (Data Fixes)**: Depends on Phase 1
- **Phase 3 (Templates)**: Depends on Phase 1 — [P] tasks Bug4 and Bug5 can run in parallel
- **Phase 4 (Tests)**: Depends on Phase 2 completion (tests verify data fixes)
- **Phase 5 (Validation)**: Depends on Phase 2 + 3 + 4

### Parallel Opportunities

- Bug4 (PDF) and Bug5 (Email HTML) — different files, can run in parallel
- Tests T009-T011 — same file but independent methods, can run sequentially
- Bugs 1, 2, 3 — same file, must run sequentially (each changes adjacent code)

### Parallel Example

```bash
# Phase 3 parallel tasks:
Task: T007 Bug4 — Rewrite PDF template in daily_report_pdf.py
Task: T008 Bug5 — Update email HTML in report_notifications.py
```

---

## Implementation Strategy

### MVP (Phase 1 + 2 + 4)
1. Complete Phase 1: Setup
2. Complete Phase 2: Data Bug Fixes (Bugs 1-3)
3. Complete Phase 4: Tests (verify data fixes)
4. **STOP and VALIDATE**: Run notification tests
5. Data bugs fixed — deploy if ready

### Full Delivery
1. Phase 1 + 2 → Data bugs fixed
2. Add Phase 3 → Templates redesigned
3. Add Phase 4 → Tests added
4. Phase 5 → Validation complete

---

## Notes

- [P] tasks = different files, no dependencies
- [Bug] label maps task to specific bug for traceability
- Each phase should be independently completable and testable
- Stop at any checkpoint to validate independently
- Avoid: vague tasks, same file conflicts, cross-phase dependencies that break independence
