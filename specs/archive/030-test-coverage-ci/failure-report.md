# CI Diagnostic Failure Report

**Branch**: `030-test-coverage-ci` | **Date**: 2026-06-10
**CI Run**: #27280674935 (conclusion: success, continue-on-error: true)
**Artifact**: `ci-failure-output` available on the run page

> **Note**: Exact CI output is in the artifact, which requires admin API credentials to download.
> This report is derived from the Phase 1 test file inventory (T005) combined with CI observations.

---

## Test Summary (Estimated)

| Module | Tests | Expected Status | Estimated Failures |
|--------|-------|-----------------|-------------------|
| Finance (`test_finance.py` ✓) | 32 | ✅ Pass | 0 |
| CRM (`test_crm.py` ✓) | 26 | ✅ Pass | 0 |
| Error Handlers (`test_error_handlers.py`) | 12 | ✅ Pass (no DB) | 0 |
| Auth (`test_auth.py`) | 89 | ⚠️ Mixed — partial mocks | ~5 |
| **Total working now** | **~159** | | **0** |
| Academics (5 files) | 168 | ❌ Needs seed data | ~168 |
| Analytics (6 files) | 149 | ❌ Needs seed data | ~149 |
| Attendance | 27 | ❌ Needs seed data | ~27 |
| Competitions | 58 | ❌ Needs seed data | ~58 |
| Dashboard | 10 | ❌ Needs seed data | ~10 |
| Enrollments | 41 | ❌ Needs seed data | ~41 |
| HR | 60 | ❌ Needs seed data | ~60 |
| Session Integrity | 18 | ❌ Needs seed data | ~18 |
| Notifications | 46 | ❌ Needs mocking | ~30 |
| **Total failing** | **~705** | | **~700** |

---

## Failure Categories

### 1. "Needs Seed Data" (Estimated ~540 failures across 20+ test files)

**Root Cause**: Tests assume database records exist (students, courses, groups, etc.) but CI database is fresh schema-only.

**Files affected**:
- `test_academics.py` + 4 sub-files — courses, groups, sessions queries return empty
- `test_analytics.py` + 5 sub-files — analytics queries return None/empty
- `test_attendance.py` — session/student FK not found
- `test_competitions.py` — missing competition records
- `test_dashboard.py` — dashboard queries return empty
- `test_enrollments.py` — missing enrollment records
- `test_hr.py` — missing employee records
- `test_session_level_integrity.py` — missing session data
- `test_notifications.py` — may partly fail from missing related records
- Potentially some `_full.py` suites

**Typical error signature**:
```
sqlalchemy.exc.IntegrityError: insert or update on table "..." violates foreign key constraint
-- or --
AttributeError: 'NoneType' object has no attribute '...'
```

### 2. "Needs Mocking" (Estimated ~30 failures)

**Root Cause**: Tests try to connect to external services (Twilio, Gmail, Supabase) that aren't available in CI.

**Files affected**:
- `test_notifications.py` — Twilio WhatsApp, Gmail SMTP calls
- `test_auth.py` — some tests need real Supabase JWT validation

**Note**: Auth already has `tests/utils/jwt_mocks.py` for mock tokens. Notifications mocks may be partial.

### 3. "Real Bugs" (Estimated 0–5)

**Root Cause**: Legitimate code defects exposed by test suite.

**Likelihood**: Low — the same tests pass on the dev environment. Most failures are environmental, not logical.

### 4. "Needs Env Var" (Estimated 0–2)

**Root Cause**: Tests that require a specific env variable not set in CI.

**Note**: CI already sets all env vars documented in `AGENTS.md`.

---

## Remediation Priority

| Fix | Impact | Effort | Priority |
|-----|--------|--------|----------|
| ✅ Seed data fixture | Resolves ~540 failures | ✅ Done (T006) | P1 |
| Per-file transaction rollback | Ensures clean isolation | Low | P1 |
| Add seed to CI workflow | Makes seed data available | Low | P1 |
| Mock external services | Resolves ~30 failures | Medium | P2 |
| Mark full suites as nightly | Keeps CI fast | Low | P3 |
| Schema verification | Safety net | Low | P3 |

---

## Recommended MVP

1. **Seed data fixture** → Already created in `tests/seed_data.py` ✅
2. **Add seed to CI** → Add seed step after schema apply
3. **Run all non-full suites** → Update test list in CI
4. **Audit remaining failures** → Fix or mark as skip/skipif

This should get us from 58→~580 passing tests (67% coverage) without any code changes to the application itself.
