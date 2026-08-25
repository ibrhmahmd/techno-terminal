# Feature Specification: Fix Scheduled Weekly & Monthly Report Zero-Metrics & Data Accuracy

**Feature Branch**: `041-fix-scheduled-report-date-range`
**Created**: 2026-08-24
**Status**: Clarified
**Input**: User description: "Fix the weekly report scheduled email — it sends zeros for all metrics (the date range bug we were debugging). Scope: weekly + monthly reports, missing weekly metrics, soft delete filters, and test fixes."

---

## Root Cause Analysis

A thorough code audit revealed six interrelated issues:

### Cause 1 — Scheduler passes no `target_date` to weekly/monthly reports
In `report_scheduler.py:50, 54`:
```python
await svc.send_weekly_report()      # defaults to target_date = None -> date.today() (Monday)
await svc.send_monthly_report()     # defaults to target_date = None -> date.today() (1st of month)
```
When running on Monday at 01:27, `date.today()` is Monday. This computes `week_start = Monday`, `week_end = Monday`, querying only seconds of Monday morning data (zeros). The intended period is **Mon–Sun of the previous week** (`target_date = yesterday`). Similarly, for monthly reports firing on the 1st, the intended period is the **full previous month** (`target_date = yesterday`).

### Cause 2 — `send_weekly_report` / `send_monthly_report` always use `target_date` as `week_end` / `month_end`
In `report_notifications.py:107-109`:
```python
today      = target_date or date.today()
week_start = today - timedelta(days=today.weekday())
week_end   = today   # always capped at target_date, never the true Sunday of completed weeks
```
For a completed past week (e.g. user selects "Last Week" in the UI), this clips the period at Monday instead of extending to Sunday.

### Cause 3 — Missing `new_students` & `dropped_enrollments` queries in `_fetch_weekly_aggregates`
`_fetch_weekly_aggregates` in `report_notifications.py` completely omitted the SQL query for `dto.new_students` and `dto.dropped_enrollments`. As a result, `new_students` was hardcoded to `0` in all weekly email reports and weekly UI summaries, even when students enrolled during the week.

### Cause 4 — Missing `p.deleted_at IS NULL` in aggregate revenue & group queries
In `_fetch_weekly_aggregates` and `_fetch_monthly_aggregates`, queries for `total_revenue`, `top_groups`, and `revenue_by_course` did not filter `p.deleted_at IS NULL`, allowing voided/cancelled payments to count toward revenue.

### Cause 5 — Router endpoints date-range logic mismatch
In `notifications_router.py`, `/reports/weekly/data` and `/reports/monthly/data` calculated their own date boundaries independently with `week_end = report_date`, resulting in the UI showing truncated single-day or partial-week data for past periods.

### Cause 6 — Test FK violation: `SYSTEM_ADMIN_ID = 1` not in test DB
`admin_settings_router.py` hardcodes `SYSTEM_ADMIN_ID = 1`. In tests, `override_auth` does not ensure a user with `id = 1` exists, causing foreign key violations on `notification_additional_recipients.admin_id` across 6 tests.

---

## User Scenarios & Testing

### User Story 1 — Scheduler sends full previous-week report on Monday (P1)
Admins receive an email every Monday morning covering Mon–Sun of the week that just ended.
**Independent Test**: Invoke `send_weekly_report(target_date=yesterday)` where `yesterday` is Sunday, and verify the email shows real revenue, attendance, new students, and sessions for the 7-day period.

**Acceptance Scenarios**:
1. **Given** the scheduler fires on Monday at 01:27, **When** `send_weekly_report(target_date=yesterday)` runs, **Then** the report covers Mon–Sun of the prior week.
2. **Given** 3 new students enrolled in the prior week, **When** the weekly report is generated, **Then** `new_students` reflects 3 (not 0).
3. **Given** a payment voided during the week (`deleted_at IS NOT NULL`), **When** `total_revenue` is calculated, **Then** the voided payment is excluded.

---

### User Story 2 — Scheduler sends full previous-month report on the 1st (P1)
Admins receive an email on the 1st of the month covering the entire previous calendar month.
**Acceptance Scenarios**:
1. **Given** the scheduler fires on 2026-09-01, **When** `send_monthly_report(target_date=yesterday)` runs, **Then** it covers 2026-08-01 through 2026-08-31.
2. **Given** voided payments in August, **When** monthly revenue is calculated, **Then** voided payments are excluded.

---

### User Story 3 — UI-triggered reports show full past periods or partial current periods (P2)
Selecting "Last Week" in the Reports UI displays the full 7-day Mon–Sun period; selecting "This Week" displays Mon up to today.
**Acceptance Scenarios**:
1. **Given** a date in a past completed week (`week_start + 6 < date.today()`), **When** `/reports/weekly/data` is queried, **Then** `week_end = week_start + 6` (Sunday).
2. **Given** a date in the current week, **When** `/reports/weekly/data` is queried, **Then** `week_end = date.today()`.
3. **Given** a date in a past month (`date(y, m, last_day) < date.today()`), **When** `/reports/monthly/data` is queried, **Then** `month_end = date(y, m, last_day)`.
4. **Given** a date in the current month, **When** `/reports/monthly/data` is queried, **Then** `month_end = date.today()`.

---

### User Story 4 — All notification integration tests pass (P2)
**Acceptance Scenarios**:
1. **Given** `override_auth` fixture runs, **When** notification settings endpoints are accessed, **Then** a user with `id = 1` exists in the DB.
2. **Given** `pytest tests/test_notifications_full.py -v`, **Then** 30/30 tests pass with 0 failures.

---

## Requirements

### Functional Requirements
- **FR-001**: `report_scheduler.py` MUST pass `target_date = yesterday` to `send_weekly_report` on Mondays.
- **FR-002**: `report_scheduler.py` MUST pass `target_date = yesterday` to `send_monthly_report` on the 1st of each month.
- **FR-003**: `send_weekly_report(target_date)` and `get_weekly_report_data` MUST compute:
  - `week_start = target_date - timedelta(days=target_date.weekday())`
  - `week_end = week_start + timedelta(days=6)` IF `week_start + timedelta(days=6) < date.today()` (fully completed)
  - `week_end = date.today()` OTHERWISE (current in-progress week)
- **FR-004**: `send_monthly_report(target_date)` and `get_monthly_report_data` MUST compute:
  - `month_start = target_date.replace(day=1)`
  - `last_day = calendar.monthrange(month_start.year, month_start.month)[1]`
  - `month_end = date(month_start.year, month_start.month, last_day)` IF `date(month_start.year, month_start.month, last_day) < date.today()` (fully completed)
  - `month_end = date.today()` OTHERWISE (current in-progress month)
- **FR-005**: `_fetch_weekly_aggregates` MUST query `new_students` (distinct students whose first enrollment date falls within `[week_start, week_end]`) and `dropped_enrollments`.
- **FR-006**: All revenue, top groups, and revenue by course queries in `_fetch_weekly_aggregates` and `_fetch_monthly_aggregates` MUST include `AND p.deleted_at IS NULL`.
- **FR-007**: `tests/conftest.py` (`override_auth` and `override_system_admin_auth`) MUST ensure a placeholder user with `id = 1` exists in the database if not already present.

---

## Success Criteria
- **SC-001**: Weekly scheduler email shows accurate, non-zero values for revenue, sessions, and new students for any week with activity.
- **SC-002**: Monthly scheduler email covers the complete previous calendar month.
- **SC-003**: UI Reports page displays full Mon–Sun for past weeks and full month for past months.
- **SC-004**: `pytest tests/test_notifications_full.py -v` passes completely (30/30 passed).
- **SC-005**: Full pytest test suite passes without regressions.
