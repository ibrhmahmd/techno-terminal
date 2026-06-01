---

description: "Task list for daily report redesign & debtors data"
---

# Tasks: Daily Report Redesign & Debtors Data

**Input**: Design documents from `/specs/019-daily-report-redesign/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not requested — skip test generation.

**Organization**: Tasks grouped by user story. Each story is independently verifiable even though US1-3 share `_build_variables()`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed — all work is within existing codebase

No tasks. Branch `019-daily-report-redesign` exists. All tools/patterns are established.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DTOs that MUST be in place before any user story can be implemented

- [x] T001 [P] Create `UnpaidAttendeeItem` DTO in `app/modules/notifications/schemas/report_dto.py`
- [x] T002 [P] Create `TopDebtorItem` DTO in `app/modules/notifications/schemas/report_dto.py`
- [x] T003 [P] Create `OutstandingByGroupItem` DTO in `app/modules/notifications/schemas/report_dto.py`
- [x] T004 [P] Create `TomorrowPreviewDTO` in `app/modules/notifications/schemas/report_dto.py`
- [x] T005 Extend `DailyReportAggregateDTO` with 6 new fields: `total_outstanding_debt`, `debtor_count`, `top_debtors`, `outstanding_by_group`, `today_unpaid_attendees`, `tomorrow_preview` in `app/modules/notifications/schemas/report_dto.py`

**Checkpoint**: All DTOs defined and importable. `from app.modules.notifications.schemas.report_dto import DailyReportAggregateDTO` picks up new fields.

---

## Phase 3: User Story 1 — Precision Engine Redesign (Priority: P1) 🎯 MVP

**Goal**: Admin receives daily report email redesigned with Space Grotesk/Inter, tonal layering, teal/deep slate palette, Power Gradient KPIs, status chips, and B&W print styles.

**Independent Test**: Generate a daily report and inspect the email HTML — confirm Space Grotesk `@import`, zero CSS borders for sectioning, Power Gradient on KPI cards, teal/amber status chips, `@media print` Black-on-white.

- [x] T006 [P] [US1] Write Precision Engine HTML template body — full email layout with Space Grotesk/Inter `@import`, tonal background shifts, Power Gradient, status chips, `@media print` in `db/migrations/058_update_daily_report_precision_engine.sql`
- [x] T007 [P] [US1] Create the migration SQL file that updates `notification_templates` body for `daily_report` in `db/migrations/058_update_daily_report_precision_engine.sql`
- [x] T008 [P] [US1] Update template variables list in migration to include new placeholder names (`total_outstanding_debt`, `debtor_count`, `debtors_section`, `tomorrow_preview_section`) in `db/migrations/058_update_daily_report_precision_engine.sql`
- [x] T009 [US1] Redesign `_build_variables()` in `app/modules/notifications/services/report_notifications.py` — replace inline table styles with Precision Engine tonal HTML (background-color shifts instead of borders, Space Grotesk headings, Inter body, Power Gradient KPIs, teal/amber chips, `@media print` styles)
- [x] T010 [US1] Add empty-state rendering: "No outstanding debt" when debtor_count=0, "No sessions scheduled tomorrow" when TomorrowPreviewDTO.has_sessions=False, "No payments recorded today" when payment_count=0 in `app/modules/notifications/services/report_notifications.py`

**Checkpoint**: Daily report email uses Precision Engine design. All content tables and sections use tonal layering. Print styles are B&W. Empty states render gracefully.

---

## Phase 4: User Story 2 — Debtors Data (Priority: P1)

**Goal**: Admin sees Debtors Alert section with total outstanding debt, top 5 debtors, outstanding by group, and today's unpaid attendees.

**Independent Test**: Generate a report for a day with known unpaid attendees and debtors — confirm their names, amounts, and group breakdowns appear in the email HTML.

- [x] T011 [US2] Add `fetch_tomorrow_preview()` to `ReportsRepository` in `app/modules/notifications/repositories/reports_repository.py` — parameterized SQL query joining tomorrow's `sessions` with `v_enrollment_balance` where balance < 0
- [x] T012 [US2] Update `ReportNotificationService._fetch_daily_aggregates()` in `app/modules/notifications/services/report_notifications.py` — call `get_top_debtors(limit=5)`, `get_outstanding_by_group()`, `get_today_unpaid_attendees(target_date)`, and `fetch_tomorrow_preview()` via module root imports; populate new `DailyReportAggregateDTO` fields
- [x] T013 [US2] Add debtors HTML rendering to `_build_variables()` in `app/modules/notifications/services/report_notifications.py` — Debtors Alert section: total outstanding (EGP), debtor count, top 5 debtors table, outstanding by group table, today's unpaid attendees with teal/amber chips
- [x] T014 [US2] Update `_has_data()` in `app/modules/notifications/services/report_notifications.py` to also check `debtor_count > 0` or `total_outstanding_debt > 0` when determining if report has content

**Checkpoint**: Daily report email includes Debtors Alert section showing all debtors data. Top 5 debtors, group breakdown, and today's unpaid attendees are listed.

---

## Phase 5: User Story 3 — Tomorrow's Preview (Priority: P2)

**Goal**: Admin sees Tomorrow's Preview section with session count, expected student count, and tomorrow's unpaid attendees.

**Independent Test**: Generate a report when sessions exist for tomorrow and some enrolled students have negative balance — confirm they appear in the tomorrow preview section.

- [x] T015 [US3] Add tomorrow preview HTML rendering to `_build_variables()` in `app/modules/notifications/services/report_notifications.py` — Tomorrow's Preview section: session count, expected students, unpaid attendees list with session time, group, and amount owed

**Checkpoint**: Daily report email includes Tomorrow's Preview section. Shows "No sessions scheduled tomorrow" when empty.

---

## Phase 6: User Story 4 — CLI Test Script (Priority: P1)

**Goal**: Developer can run `python scripts/test_report_email.py --to <email>` to send a test email with the new design using real data for 2026-05-24.

**Independent Test**: Run the CLI script with a valid email address and confirm the Precision Engine HTML email arrives with all sections populated.

- [x] T016 [P] [US4] Create `scripts/test_report_email.py` — argparse for `--to` (recipient email), imports `ReportNotificationService`, creates own session, calls `send_daily_report(target_date=date(2026, 5, 24))`, dispatches to provided email
- [x] T017 [P] [US4] Add `--save-pdf` flag to `scripts/test_report_email.py` — saves generated PDF to disk for visual B&W inspection
- [x] T018 [P] [US4] Add `--date` optional override flag to `scripts/test_report_email.py` — allows testing with different dates instead of hardcoded 2026-05-24 (useful for ongoing visual validation)

**Checkpoint**: CLI script runs end-to-end. Email arrives with Precision Engine design, PDF attachment, and all data sections.

---

## Phase 7: Polish & Verification

**Purpose**: Final verification and cleanup

- [ ] T019 Verify all 15 existing notification tests still pass: `pytest tests/test_notifications.py -v` (requires DB — run manually)
- [ ] T020 Run CLI test script against a real email: `py scripts/test_report_email.py --to <your-email>` and visually verify in Gmail/Outlook/Apple Mail
- [ ] T021 Cross-check: confirm the `notification_templates` migration applies cleanly against the dev database
- [x] T022 Remove any dead code or debugging artifacts from modified files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: None needed — project already initialized
- **Foundational (Phase 2)**: BLOCKS all user stories (DTOs required by everything)
- **US1 (Phase 3)**: Depends on Phase 2 — template + `_build_variables` redesign
- **US2 (Phase 4)**: Depends on Phase 2 + Phase 3 (adds debtors sections to `_build_variables`)
- **US3 (Phase 5)**: Depends on Phase 2 + Phase 3 (adds tomorrow section to `_build_variables`)
- **US4 (Phase 6)**: Depends on Phase 2 + Phase 3 (CLI script calls `send_daily_report()`)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — can be started first
- **US2 (P1)**: Modifies same `_build_variables()` as US1 — sequence recommended (US1 → US2)
- **US3 (P2)**: Modifies same `_build_variables()` as US1 — sequence recommended (US1 → US3)
- **US4 (P1)**: Depends on US1 being functional (CLI script calls `send_daily_report()`) — sequence required (US1 → US4)

### Parallel Opportunities

- T001-T004 (all DTOs) can run in parallel
- T006-T008 (template + migration files) can run in parallel
- T016-T018 (CLI script features) can run in parallel

---

## Parallel Example: Phase 2 (Foundational DTOs)

```bash
# Launch all 4 DTOs together:
Task: "Create UnpaidAttendeeItem DTO in app/modules/notifications/schemas/report_dto.py"
Task: "Create TopDebtorItem DTO in app/modules/notifications/schemas/report_dto.py"
Task: "Create OutstandingByGroupItem DTO in app/modules/notifications/schemas/report_dto.py"
Task: "Create TomorrowPreviewDTO in app/modules/notifications/schemas/report_dto.py"
```

## Parallel Example: Phase 3 (Template + Migration)

```bash
# Write template HTML and migration SQL together:
Task: "Write Precision Engine HTML template body in db/migrations/058_update_daily_report_precision_engine.sql"
Task: "Update template variables list in migration"
```

---

## Implementation Strategy

### MVP First (Phase 3 Only)

1. Complete Phase 2: Foundational DTOs
2. Complete Phase 3: US1 — Precision Engine redesign with existing data
3. **STOP**: Run test via existing `send_daily_report()` — verify visual design in email
4. Deploy/demo if visual design alone is acceptable

### Full Delivery

1. Phase 2: DTOs → Foundational ready
2. Phase 3: US1 → New design deployed (MVP!)
3. Phase 4: US2 → Debtors data added
4. Phase 5: US3 → Tomorrow preview added
5. Phase 6: US4 → CLI test script
6. Phase 7: Polish → Verify all tests pass

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US4 share no file conflicts — can proceed concurrently if needed
- US2 and US3 both modify `_build_variables()` — sequence US2 before US3 or merge into one pass
- The migration (`058_*.sql`) must be applied to dev DB to test — or template can be updated directly for testing
- Verify tests pass after each phase before moving on
