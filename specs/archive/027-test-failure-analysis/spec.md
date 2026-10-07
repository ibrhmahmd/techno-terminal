# Spec 027: Test Failure Analysis

**Status:** Draft  
**Date:** 2026-06-08  
**Total failures:** 77 (369 passed, 8 skipped)

## Failure Categories

### A. HR Phone Pattern Validation (12 failures)

**Tests:** `test_hr.py` — all `test_create_employee_*`, `test_update_employee_*`, and edge cases

**Root cause:** `CreateEmployeeDTO` and `UpdateEmployeeDTO` define `phone: str = Field(..., pattern=r"^\d{10,}$")` with a `clean_phone` field validator that strips non-digits. In Pydantic v2, `pattern` check runs BEFORE `@field_validator` (default mode=`'after'`). So the `+` prefix from test data (`+201000...`) fails pattern check before `clean_phone` can strip it.

**Files:**
- `app/modules/hr/schemas/employee_schemas.py:19,31-35,43,55-60`

**Fix:** Add `mode='before'` to both `clean_phone` validators so they run before pattern validation.

---

### B. Academics Groups — Missing Endpoints (15 failures)

**Tests:** `test_academics_groups.py` — `by_type`, `by_course`, `search`, `progress_level`, `create_group`, `delete_group`

**Root cause (B1 — 404s):** Three endpoints referenced by tests **do not exist** as route handlers:
| Test calls | Actual result |
|---|---|
| `GET /academics/groups/search?query=...` | **Not implemented** |
| `GET /academics/groups/by-type/{type}` | **Not implemented** |
| `GET /academics/groups/by-course/{id}` | **Not implemented** |

Closest equivalents exist at `GET /academics/groups/filter` (with `q` param) and `GET /academics/groups/grouped` (with `group_by` param).

**Files:**
- `tests/test_academics_groups.py:157,181,197,397`
- `app/api/routers/academics/group_directory_router.py` — has `/filter` and `/grouped` only

**Root cause (B2 — 422s):**
- `POST /groups/{id}/progress-level` returns 422 — likely path param type mismatch (test sends int but handler expects different)
- `GET /groups/search?query=...` returns 422 — endpoint doesn't exist, falls through to a different route that 422s

**Root cause (B3 — 401s):**
- `test_create_group_success`, `test_create_group_non_admin` — use `system_admin_headers` (real Supabase JWT) which gets rejected by Supabase. Auth bypass isn't working for these tests.

**Root cause (B4 — message mismatch):**
- `test_delete_group_success` expects "archived" or "deleted" in message but endpoint returns "group deactivated successfully"

---

### C. Academics Lifecycle/Sessions (15 failures)

**Tests:** `test_academics_lifecycle.py`, `test_academics_sessions.py`

**Root cause (C1 — 422s):**
- `GET /academics/sessions/daily-schedule` returns 422 — query param validation issue
- `POST /groups/{id}/sessions` returns 422 — request body validation mismatch
- `POST /groups/{id}/progress-level` returns 422 — path/query param type mismatch
- `GET /groups/{id}/levels/{level_number}` returns 422 — path param type issue

**Root cause (C2 — 404/200 mismatch):**
- `test_delete_session_not_found` expects 404 but gets 200 — session soft-delete returns success

**Root cause (C3 — 401 instead of 403):**
- `test_add_extra_session_non_admin` — real Supabase JWT rejected

---

### D. Analytics Dashboard — Path Mismatch (9 failures)

**Tests:** `test_analytics_dashboard.py`, `test_analytics.py::TestAnalyticsDashboard`, `test_analytics_academic.py::TestDashboardSummary`

**Root cause:** All tests call `GET /api/v1/analytics/dashboard/summary` which **does not exist**. The actual endpoint is `GET /api/v1/dashboard/daily-overview` (a completely different path and response shape).

**Files:**
- `app/api/routers/analytics/dashboard.py` — has `/dashboard/daily-overview`
- Test files expect `/analytics/dashboard/summary`

---

### E. Analytics Group Roster — Missing Endpoint (7 failures)

**Tests:** `test_analytics.py::TestAcademicAnalytics`, `test_analytics_academic.py::TestGroupRoster`

**Root cause:** `GET /analytics/academics/groups/{id}/roster` returns 404. No standalone roster endpoint exists in the analytics routers. Roster data is embedded within:
- `GET /attendance/session/{session_id}` (per-session roster)
- `GET /academics/groups/{group_id}/attendance?level_number=N` (per-level grid)
- `GET /dashboard/daily-overview` (embedded in scheduled groups)

**Files:**
- `tests/test_analytics.py:62`, `tests/test_analytics_academic.py:111`
- No corresponding `@router.get` for `/academics/groups/{id}/roster` in analytics routers

---

### F. Competition Fee Summary — Auth Failures (4 failures)

**Tests:** `test_analytics_competition.py`

**Root cause (F1):** `test_competition_fee_summary_success/structure/empty` — endpoint exists at `GET /api/v1/analytics/competitions/fee-summary` but requires `require_admin`. Test uses `system_admin_headers` (real Supabase JWT) which gets rejected → 401.

**Root cause (F2):** `test_competition_fee_summary_forbidden` — expects 200 or 403 but gets 401 (same real JWT issue).

**Secondary issue:** Even if auth worked, `test_competition_fee_summary_structure` asserts field keys (`total_fees`, `participant_count`, `entry_fee`, `total_collected`) that don't match the DTO fields (`fees_collected`, `fees_outstanding`, `member_count`, no `entry_fee`).

**Files:**
- `app/api/routers/analytics/competition.py`
- `app/modules/analytics/schemas/competition_schemas.py:CompetitionFeeSummaryDTO`
- `tests/test_analytics_competition.py`

---

### G. Attendance — Missing Session Check (8 failures)

**Tests:** `test_attendance.py`

**Root cause (G1 — 200 instead of 404):**
- `test_get_session_attendance_not_found` — `get_session_roster_with_attendance()` never checks if the session exists. It queries only the `attendance` table and returns `[]` for non-existent sessions → 200 with `{"data": []}`.

**Root cause (G2 — 401 instead of 403):**
- `test_get_session_attendance_forbidden`, `test_mark_attendance_forbidden` — real Supabase JWT rejected

**Root cause (G3 — validation issues):**
- `test_mark_attendance_success` — gets 422 (body validation, possibly student_id or status field mismatch)
- `test_mark_attendance_all_valid_statuses` — gets 422 (status enum values may not match test expectations)
- `test_mark_attendance_validation_duplicate_students` — gets 422

**Root cause (G4 — 404 for session not found in DB):**
- `test_mark_attendance_large_batch`, `test_mark_attendance_max_int_student_id` — session_id=1 doesn't exist in test DB → 404

**Files:**
- `app/api/routers/attendance_router.py`
- `app/modules/attendance/services/attendance_service.py` — missing session existence check in `get_session_roster_with_attendance`

---

### H. Competitions — Registration Fee Input (2 failures)

**Tests:** `test_competitions.py::TestTeamRegistrationFeeInput`

**Root cause:** Both `test_add_team_member_with_fee` and `test_add_team_member_without_fee` fail. Stack trace shows `concurrent.futures` exception — likely Supabase JWT rejection (401) or request body validation error.

---

### I. Notifications — Template Body Mismatch (11 failures)

**Tests:** `test_notifications.py`

**Root cause (I1 — template body):**
- `test_enrollment_created_sends_notification` and 6 similar enrollment notification tests — fail because the notification template body in DB doesn't match what the service expects. The templates were updated through migrations but the tests weren't updated.

**Root cause (I2 — variables count):**
- `test_daily_report_template_exists_and_active` — expects `assert len(template.variables) >= 11` but migration 059 reduced variables to 9.

**Root cause (I3 — email sending):**
- `test_send_daily_report_sends_email`, `test_send_daily_report_with_pdf_attachment` — email sending fails, likely due to mock/configuration issue.

**Root cause (I4 — instructor query):**
- `test_fetch_daily_aggregates_instructors_query` — aggregate query returns unexpected results.

**Files:**
- `tests/test_notifications.py`
- `db/migrations/059_update_daily_report_template_3kpi.sql` — reduced variables to 9

---

### J. Session Level Integrity — Returns All Levels (3 failures)

**Tests:** `test_session_level_integrity.py`

**Root cause (J1):**
- `test_get_levels_detailed_defaults_to_current_level` — service docstring says "return only current active level" but implementation returns **all levels** (`include_inactive=True`) because frontend needs full history for LevelSelector. Test still asserts `len == 1`.

**Root cause (J2):**
- `test_create_group_sessions_have_group_level_id`, `test_progress_level_sessions_have_new_group_level_id` — session creation/level progression test assertions fail, likely because the lifecycle service behavior changed.

**Files:**
- `app/modules/academics/group/details/service.py:123-138`
- `tests/test_session_level_integrity.py:193-215`

---

## Summary Table

| # | Category | Count | Root Cause Summary |
|---|----------|-------|-------------------|
| A | HR Phone Pattern | 12 | `mode='before'` missing on phone validator |
| B | Academics Groups | 15 | 3 missing endpoints + auth + validation mismatches |
| C | Lifecycle/Sessions | 15 | Validation + auth + 404/200 mismatches |
| D | Dashboard Summary | 9 | Wrong endpoint path in tests |
| E | Group Roster | 7 | Missing standalone analytics roster endpoint |
| F | Competition Fee | 4 | Auth + response field name mismatch |
| G | Attendance | 8 | Missing session check + auth + validation |
| H | Competitions | 2 | Auth/body validation |
| I | Notifications | 11 | Template body/variable mismatch |
| J | Session Integrity | 3 | Service returns all levels, test expects one |
| | **Total** | **77** | |

## Plan Scope

**In scope:** Test file changes only — deletion of deprecated tests, updating drifted assertions, fixing test infrastructure (auth fixtures, mocks).

**Out of scope:** Application code changes — HR phone validation fix (A), attendance session existence check (G1), instructor query investigation (I4). Code bugs tracked separately.

**Total tests in scope:** ~66 (21 delete + 33 update + 12 infra fix) of 77 total failures

## Clarifications

### Session 2026-06-08
- **Q1:** What criteria define a "non-logical/deprecated" test? → **A:** Three criteria: (B) test references non-existent endpoint → delete, (C) response shape/status drift → update test to match implementation, (E) implementation intentionally changed/test stale → update or delete old test.
- **Q2:** What scope for deletion? → **A:** Flexible per situation — (A) individual methods for isolated bad tests, (B) entire test class if all methods are deprecated, (C) entire test file if no valid tests remain.
- **Q3:** Should plan include code fixes for real bugs? → **A:** No — tests only. Code fixes (HR phone, session check) are separate work.
- **Q4:** Full scope of plan? → **A:** Full cleanup — delete deprecated tests + update drifted assertions + fix test infrastructure (auth, mocks).

## Classification Framework

| Disposition | Criterion | Action |
|---|---|---|
| **Delete test** | Test references non-existent endpoint (never implemented or removed) | Remove test method/class |
| **Update test** | Endpoint exists but returns different response shape, field names, or status code | Align test assertions with current implementation |
| **Update or delete** | Implementation intentionally changed (migration, refactor), test wasn't updated | Update test to match new behavior, or delete if test concept is obsolete |
| **Fix code** | Test correctly identifies a real bug in the implementation | Fix the application code |
| **Fix test infra** | Test fails due to test environment issue (e.g., real Supabase JWT rejected) | Fix auth fixture/test setup |

## Failure Disposition Mapping

| Category | Count | Disposition | Action |
|---|---|---|---|
| A — HR Phone Pattern | 12 | **Fix code** | Add `mode='before'` to `clean_phone` validators |
| B1 — Missing endpoints (search, by-type, by-course) | 5 | **Delete test** | Remove test methods for non-existent endpoints |
| B2 — 422 validation mismatches | 4 | **Update test** | Align request bodies with current schema |
| B3 — Auth (real Supabase JWT) | 2 | **Fix test infra** | Use `override_auth` fixture |
| B4 — Delete message mismatch | 1 | **Update test** | Accept "deactivated" wording |
| C1 — Lifecycle 422s | 9 | **Update test** | Align request params with current routes |
| C2 — 404/200 mismatches | 2 | **Update test** | Accept current status codes |
| C3 — Auth (real Supabase JWT) | 1 | **Fix test infra** | Use `override_auth` fixture |
| D — Dashboard path mismatch | 9 | **Delete test** | Endpoint never existed at that path |
| E — Group roster not in analytics | 7 | **Delete test** | No standalone roster endpoint in analytics |
| F — Competition fee auth | 3 | **Fix test infra** | Use `override_auth` fixture |
| F — Competition fee structure | 1 | **Update test** | Align field names with DTO |
| G1 — Missing session check | 1 | **Fix code** | Add existence check to `get_session_roster_with_attendance` |
| G2 — Auth (real Supabase JWT) | 2 | **Fix test infra** | Use `override_auth` fixture |
| G3 — 422 validation | 3 | **Update test** | Align request bodies with current schema |
| G4 — Session not in test DB | 2 | **Update test** | Use proper session fixture |
| H — Competition team fee | 2 | **Fix test infra** | Likely auth + body validation |
| I1 — Template body mismatch | 7 | **Update test** | Match current template body |
| I2 — Variables count | 1 | **Update test** | Accept 9 variables (migration 059) |
| I3 — Email sending | 2 | **Fix test infra** | Fix mock/configuration |
| I4 — Instructor query | 1 | **Fix code or update test** | Investigate aggregate query behavior |
| J1 — All levels returned | 1 | **Update test** | Accept intentional behavior (frontend needs all levels) |
| J2 — Lifecycle assertions | 2 | **Update test** | Align with current lifecycle service |

## Cross-Cutting Themes

1. **Real Supabase JWT** — ~25% of failures root-caused by real Supabase JWT rejection. Tests using `system_admin_headers` (not mock auth) hit real Supabase which returns 403 → mapped to 401. Fix: use `override_auth` fixture or mock tokens.

2. **Test/Implementation Drift** — Many tests reference endpoints or field names that no longer match the implementation (Dashboard summary, Group roster, Competition fee, Notification templates, Session level integrity).

3. **Missing `mode='before'`** — HR phone validation is a single-character Pydantic mode fix.
