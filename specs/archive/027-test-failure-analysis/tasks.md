---

description: "Task list for 027 test failure analysis cleanup"
---

# Tasks: 027 — Test Failure Analysis & Cleanup

**Input:** Design documents from `specs/027-test-failure-analysis/`
**Prerequisites:** plan.md, spec.md, data-model.md, research.md, quickstart.md

**Organization:** Tasks grouped by workstream (DELETE / INFRA_FIX / UPDATE), not user stories — this is a test-only cleanup operation with no feature user stories.

## Format: `[ID] [P] Description`

- `[P]`: Can run in parallel with other `[P]` tasks in the same phase
- Include exact file paths in descriptions
- No `[Story]` labels — this spec has no user stories (it's a test cleanup, not a feature)

---

## Phase 1: Setup

**Purpose:** Capture baseline, verify environment

- [X] T001 Run baseline test suite and save output: **94 failed, 358 passed, 8 skipped, 2 errors** (baseline.txt)

---

## Phase 2: Foundational — Auth Fixture Infrastructure

**Purpose:** Unblock all INFRA_FIX auth-related tasks by creating the required fixture

- [X] T002 Add `override_system_admin_auth` fixture to `tests/conftest.py` — **already exists** (line 110) — no action needed

---

## Phase 3: DELETE — Remove Deprecated Tests

**Goal:** Remove all test methods that reference non-existent endpoints (dashboard summary, group roster, groups search/by-type/by-course). 19 tests across 4 files.

**Independent Test:** Run each affected file — deleted methods should no longer appear in test collection; remaining tests should still exist.

- [X] T003 [P] Delete 5 test methods from `tests/test_academics_groups.py`: `TestGroupsRead.test_search_groups_success`, `test_search_groups_short_query`, `test_list_groups_by_type_success`, `test_list_groups_by_course_success`, `TestGroupsEdgeCases.test_search_groups_no_results`
- [X] T004 [P] Delete 3 test methods from `tests/test_analytics_dashboard.py`: `TestDashboardSummary.test_dashboard_summary_success`, `test_dashboard_summary_requires_admin`, `TestDashboardAuth.test_all_dashboard_endpoints_require_admin`
- [X] T005 [P] Delete 4 test methods from `tests/test_analytics.py`: `TestAnalyticsDashboard.test_dashboard_summary_success`, `test_dashboard_summary_requires_admin`, `TestAcademicAnalytics.test_group_roster_success`, `test_group_roster_missing_level`
- [X] T006 [P] Delete 7 test methods from `tests/test_analytics_academic.py`: `TestDashboardSummary` (3 methods), `TestGroupRoster` (4 methods — `test_group_roster_success`, `test_group_roster_missing_level`, `test_group_roster_invalid_level`, `test_group_roster_unauthorized`)

**Checkpoint:** 19 deleted tests should no longer be collected by pytest. Run `python -m pytest tests/test_analytics_dashboard.py tests/test_analytics.py tests/test_analytics_academic.py tests/test_academics_groups.py --tb=short -v 2>&1 | Select-String "FAILED"` — only non-deleted failures should remain.

---

## Phase 4: INFRA_FIX — Fix Test Infrastructure

**Goal:** Fix auth fixtures and mock injection so tests no longer hit real Supabase. 10 tests across 5 files.

**Independent Test:** Each file should progress from 401/connection errors to the expected test outcome (may still fail due to assertion drift — acceptable at this stage).

- [X] T007 [P] Add `override_auth` fixture to `TestGroupsWrite` in `tests/test_academics_groups.py` — both `test_create_group_success` and `test_create_group_non_admin` need the fixture as parameter
- [X] T008 [P] Add `override_auth` fixture to `test_add_extra_session_non_admin` in `tests/test_academics_sessions.py`
- [X] T009 [P] Add `override_system_admin_auth` fixture to `TestCompetitionFeeSummary` in `tests/test_analytics_competition.py` — 3 methods need it: `test_competition_fee_summary_success`, `test_competition_fee_summary_structure`, `test_competition_fee_summary_empty`
- [X] T010 [P] Add `override_auth` fixture to `test_get_session_attendance_forbidden` and `test_mark_attendance_forbidden` in `tests/test_attendance.py`
- [ ] T011 [P] Fix auth fixture in `TestTeamRegistrationFeeInput` class in `tests/test_competitions.py` — **code bug (`Student.is_active`), auth already working**
- [X] T012 [P] Fix mock injection for `test_send_daily_report_sends_email` and `test_send_daily_report_with_pdf_attachment` in `tests/test_notifications.py` — **fixed async mark (`@pytest.mark.asyncio`→`anyio`)**

**Checkpoint:** Run `python -m pytest tests/test_academics_groups.py tests/test_academics_sessions.py tests/test_analytics_competition.py tests/test_attendance.py tests/test_notifications.py tests/test_competitions.py --tb=short -v 2>&1 | Select-String "FAILED"` — auth-related 401 failures should be gone. Remaining failures should be assertion/validation issues (handled in Phase 5).

---

## Phase 5: UPDATE — Update Drifted Assertions

**Goal:** Align test assertions with current endpoint behavior — status codes, response field names, request body formats, template variables. 37 tests across 7 files.

**Independent Test:** Each file should have fewer failures than baseline. Each update is a specific assertion fix.

- [ ] T013 [P] Update 5 assertions in `tests/test_academics_groups.py`:
  - `test_delete_group_success`: accept "deactivated" in message
  - `test_create_group_missing_required_fields`: verify current required fields
  - `test_update_group_no_changes`: check actual status behavior
  - `test_delete_already_inactive_group`: check actual status code
  - `test_list_group_sessions_with_level_filter`: fix query param name/format

- [ ] T014 [P] Update 7 assertions in `tests/test_academics_lifecycle.py`:
  - `test_get_group_level_details_success`: align request params with current endpoint
  - `test_get_group_level_not_found`: accept 422 if level_number is validated
  - `test_get_group_enrollment_analytics_success`: fix request params
  - `test_get_group_instructor_analytics_success`: fix request params
  - `test_get_enrollment_history_alias`: fix request params
  - `test_get_instructor_history_alias`: fix request params
  - `test_analytics_pagination`: fix pagination params

- [ ] T015 [P] Update 8 assertions in `tests/test_academics_sessions.py`:
  - `test_get_daily_schedule_success`: add required date param
  - `test_get_daily_schedule_with_date`: fix date format
  - `test_get_session_details_success`: fix session ID validation
  - `test_get_session_details_not_found`: check actual status code
  - `test_add_extra_session_success`: fix request body schema
  - `test_update_session_success`: fix request body schema
  - `test_update_session_not_found`: check actual status code
  - `test_delete_session_success`: align with current status code

- [ ] T016 [P] Update competition fee structure assertion in `tests/test_analytics_competition.py`:
  - `test_competition_fee_summary_structure`: replace `total_fees`, `participant_count`, `entry_fee`, `total_collected` with `fees_collected`, `fees_outstanding`, `member_count`

- [ ] T017 [P] Update 5 assertions in `tests/test_attendance.py`:
  - `test_mark_attendance_success`: fix request body format to match current schema
  - `test_mark_attendance_validation_duplicate_students`: check actual status code
  - `test_mark_attendance_all_valid_statuses`: fix status enum values
  - `test_mark_attendance_large_batch`: add `group_level_id` to session fixture
  - `test_mark_attendance_max_int_student_id`: create session in test instead of hardcoding

- [ ] T018 [P] Update 8 assertions in `tests/test_notifications.py`:
  - `TestEnrollmentNotifications.*` (7 methods, lines ~136–280): update template body assertions to match current rendering (9 variables, HTML template from migration 059)
  - `test_daily_report_template_exists_and_active`: change `>= 11` to `>= 9` variables count assertion

- [ ] T019 [P] Update 3 assertions in `tests/test_session_level_integrity.py`:
  - `test_get_levels_detailed_defaults_to_current_level`: accept `len == 2` (service intentionally returns all levels)
  - `test_create_group_sessions_have_group_level_id`: align with current lifecycle service
  - `test_progress_level_sessions_have_new_group_level_id`: align with current lifecycle service

---

## Phase 6: Polish & Verification

**Purpose:** Verify all changes work together, fix any issues

- [ ] T020 Run full verification suite: `python -m pytest tests/ --ignore=tests/test_hr.py -v --tb=short 2>&1 | Select-String "passed|failed|error"` — expect ~62 failures resolved, 14 remaining (12 HR phone + 1 G1 attendance + 1 I4 instructor query, all out of scope)
- [ ] T021 Commit all changes with descriptive message per file

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends On | Blocks |
|-------|-----------|--------|
| Phase 1: Setup | None | None |
| Phase 2: Auth Fixture | T001 | T007–T012 |
| Phase 3: DELETE | T001 | Phase 6 |
| Phase 4: INFRA_FIX | T002 | Phase 6 |
| Phase 5: UPDATE | T001 | Phase 6 |
| Phase 6: Polish | T003–T019 | None |

### Summary
- **T001** (baseline) completes first — standalone
- **T002** (auth fixture) completes before any INFRA_FIX task
- Phases 3, 4, 5 can proceed **in any order** after their prerequisites — no cross-phase ordering constraints
- Phase 6 is the final integration run

### Parallel Opportunities

- All tasks within each of Phases 3, 4, 5 are `[P]` — different files, no dependencies
- Phases 3, 4, and 5 can be worked on in parallel by different team members (different files, no overlap)

---

## Parallel Example: All Workstreams

```bash
# Phase 3: DELETE (all 4 files are independent)
Task: "Delete 5 methods from test_academics_groups.py"
Task: "Delete 3 methods from test_analytics_dashboard.py"
Task: "Delete 4 methods from test_analytics.py"
Task: "Delete 7 methods from test_analytics_academic.py"

# Phase 4: INFRA_FIX (all 5 files are independent)
Task: "Fix auth in test_academics_groups.py"
Task: "Fix auth in test_academics_sessions.py"
Task: "Fix auth in test_analytics_competition.py"
Task: "Fix auth in test_attendance.py"
Task: "Fix mock injection in test_notifications.py"
Task: "Fix fixture in test_competitions.py"

# Phase 5: UPDATE (all 7 files are independent)
Task: "Update assertions in test_academics_groups.py"
Task: "Update assertions in test_academics_lifecycle.py"
Task: "Update assertions in test_academics_sessions.py"
Task: "Update assertions in test_analytics_competition.py"
Task: "Update assertions in test_attendance.py"
Task: "Update assertions in test_notifications.py"
Task: "Update assertions in test_session_level_integrity.py"
```

---

## Implementation Strategy

### Recommended Order

1. **Phase 1–2**: Baseline + auth fixture (sequential, quick)
2. **Phase 3: DELETE**: Fast, low-risk — removes 19 dead tests
3. **Phase 4: INFRA_FIX**: Medium risk — requires understanding auth fixture injection
4. **Phase 5: UPDATE**: Highest effort — 37 assertions across 7 files, some require investigation of actual endpoint behavior
5. **Phase 6**: Final verification

### Risk Mitigation

- Run verification after each phase to catch regressions early
- DELETE first (safe, can't break anything)
- INFRA_FIX second (makes UPDATE easier to verify)
- UPDATE last (most complex, benefits from clean auth state)

---

## Notes

- [P] tasks = different files, no dependencies
- No [Story] labels — this is a test cleanup, not a feature with user stories
- Phase 6 verification confirms all in-scope failures resolved and out-of-scope failures remain
- Code fixes (HR phone, attendance session check, instructor query) are tracked separately — not in this plan
- Commit after each phase or logical group
