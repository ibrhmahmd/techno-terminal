# Phase 0 Research: 027 Test Failure Cleanup

## Auth Bypass Pattern

**Decision:** Use `override_auth` / `override_system_admin_auth` fixtures to replace real Supabase JWT.

**Rationale:** Tests using `system_admin_headers` hit real Supabase's `auth.get_user()` API, which rejects tokens with 403 → mapped to 401 by the auth pipeline. The `override_auth` fixture (conftest.py:74) replaces `get_current_user` with a hardcoded `User` ORM model — no JWT validation, no network calls, no expiry.

**Pattern:**
```python
# Before (broken):
def test_something(client, db_session, system_admin_headers):
    response = client.get("/endpoint", headers=system_admin_headers)

# After (fixed):
def test_something(client, db_session, override_system_admin_auth, system_admin_headers):
    response = client.get("/endpoint", headers=system_admin_headers)
```

**Files affected:** B3 (test_academics_groups.py), C3 (test_academics_sessions.py), F-auth (test_analytics_competition.py), G2 (test_attendance.py), H (test_competitions.py), I3 (test_notifications.py)

**Note for `test_competitions.py`:** Has its own `auto_override_auth` autouse fixture (line 16) that already overrides auth — the issue there may be a different conflict.

---

## 422 Root Cause Analysis

**General finding:** Tests getting 422 instead of expected status codes have request bodies/query params that don't match current Pydantic schema validation. Each case needs individual correction against the actual endpoint definition.

**Notable patterns:**
- `POST /groups/{id}/progress-level` — path param `id` type, request body field names may differ
- `GET /sessions/daily-schedule` — query param `target_date` format/requirement changed
- `POST /attendance/session/{id}/mark` — `StudentAttendanceItem` schema changed (student_id type, status enum values)
- `GET /groups/{id}/levels/{level_number}` — path param `level_number` vs query param

---

## Notification Template Body

**Current template (migration 059):** 9 variables, full HTML with 3 KPI cards, `@media print` CSS, placeholders for debtors/tomorrow/sessions/instructors/payments sections.

**Test fixtures use** simple `<p>` bodies with fewer variables. The enrollment notification tests mock the service directly — they use `MockNotificationRepository` with test-specific template fixtures. These tests don't hit the real DB, so they don't need migration 059's body. The only test that checks the real DB body is `test_daily_report_template_exists_and_active` (requires `>= 11` variables, but migration 059 has 9).

**Fix:** Update the `test_daily_report_template_exists_and_active` assertion to accept 9 variables.

---

## Per-File Inventory

### DELETE (21 tests)

| File | Test | Line | Reason |
|------|------|------|--------|
| `test_academics_groups.py` | `TestGroupsRead.test_search_groups_success` | 157 | Search endpoint never implemented |
| `test_academics_groups.py` | `TestGroupsRead.test_search_groups_short_query` | 173 | Same |
| `test_academics_groups.py` | `TestGroupsRead.test_list_groups_by_type_success` | 181 | by-type endpoint never implemented |
| `test_academics_groups.py` | `TestGroupsRead.test_list_groups_by_course_success` | 197 | by-course endpoint never implemented |
| `test_academics_groups.py` | `TestGroupsEdgeCases.test_search_groups_no_results` | 397 | Search endpoint never implemented |
| `test_analytics_dashboard.py` | `TestDashboardSummary.test_dashboard_summary_success` | 24 | Endpoint never existed at that path |
| `test_analytics_dashboard.py` | `TestDashboardSummary.test_dashboard_summary_requires_admin` | 52 | Same |
| `test_analytics_dashboard.py` | `TestDashboardAuth.test_all_dashboard_endpoints_require_admin` | 195 | References removed endpoint |
| `test_analytics.py` | `TestAnalyticsDashboard.test_dashboard_summary_success` | 363 | Endpoint never existed |
| `test_analytics.py` | `TestAnalyticsDashboard.test_dashboard_summary_requires_admin` | 379 | Same |
| `test_analytics.py` | `TestAcademicAnalytics.test_group_roster_success` | 53 | Roster endpoint not in analytics |
| `test_analytics.py` | `TestAcademicAnalytics.test_group_roster_missing_level` | 67 | Same |
| `test_analytics_academic.py` | `TestDashboardSummary.test_dashboard_summary_success` | 20 | Endpoint never existed |
| `test_analytics_academic.py` | `TestDashboardSummary.test_dashboard_summary_unauthorized` | 40 | Same |
| `test_analytics_academic.py` | `TestDashboardSummary.test_dashboard_summary_forbidden` | 45 | Same |
| `test_analytics_academic.py` | `TestGroupRoster.test_group_roster_success` | 99 | Roster endpoint not in analytics |
| `test_analytics_academic.py` | `TestGroupRoster.test_group_roster_missing_level` | 116 | Same |
| `test_analytics_academic.py` | `TestGroupRoster.test_group_roster_invalid_level` | 137 | Same |
| `test_analytics_academic.py` | `TestGroupRoster.test_group_roster_unauthorized` | 145 | Same |
| *(plus 2 more from test_analytics_academic.py TestGroupRoster)* | | | |

### UPDATE (33 tests)

See data-model.md for full list with specific changes per method.

### INFRA_FIX (12 tests)

See data-model.md for full list with specific fix per test.

---

## Key Design Decisions

1. **Mock auth vs real auth:** Prefer `override_auth` for business logic tests. Use `override_system_admin_auth` + `system_admin_headers` for admin role tests. No test should hit real Supabase during unit testing.
2. **Endpoint existence check:** Before writing any test for an analytics/dashboard endpoint, verify it exists in `app/api/routers/` with `@router.get(...)` decorator.
3. **Template body assertions:** For notification tests using mocks, keep simple body assertions. For integration tests checking the real DB, align with migration 059 values.
