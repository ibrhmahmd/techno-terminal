# Research: Fix Daily Report Critical Bugs

## No [NEEDS CLARIFICATION]

All requirements in spec.md were clear. Research confirms the approach for each fix:

### FR-001 — Enrollment date-boundary type mismatch

**Finding**: `enrollments.enrolled_at` is `DATE` (nullable). `enrollments.created_at` is `TIMESTAMPTZ`. The current query:
```sql
func.coalesce(Enrollment.enrolled_at, Enrollment.created_at)
```
Promotes `DATE` to `TIMESTAMPTZ` implicitly, so `2026-05-22` at midnight compares correctly. However, the equality check `== report_date` fails for timestamps where `created_at` has a non-midnight time component.

**Fix**: Wrap with `func.date(...)`:
```sql
func.date(func.coalesce(Enrollment.enrolled_at, Enrollment.created_at))
```
Same pattern used in `_fetch_revenue`.

### FR-002 — Instructor summary counts all statuses

**Finding**: `_fetch_instructor_summary` counts `COUNT(*)` with no status filter. `_fetch_session_details` filters `status = 'completed'`. Discrepancy means instructor totals exceed session counts.

**Fix**: Add `where(SessionAttendance.status == 'completed')` to instructor summary query. Two sessions by one instructor on same date/time period: one `present`, one `absent` — instructor should only count the `present` one.

### FR-003 — exec() with text() in base_notification_service.py

**Finding**: Line 115 uses `self._repo._session.exec(smt, params=...)` which is SQLAlchemy 2.0 ORM API for `SELECT`. But the statement is constructed with `text()` — raw SQL. `exec()` is for ORM queries; `execute()` is the correct method for raw SQL text.

**Fix**: Change `exec()` to `execute()`.

### FR-005 — Bare except Exception

**Finding**: `_fetch_daily_aggregates`, `send_daily_report`, and `_build_daily_report_body` catch `Exception` broadly.

**Fix**: Change to `except SQLAlchemyError` for database operations. Network/dispatcher errors can remain `Exception` but should be more specific where possible.

### FR-006 — Payments N+1 queries

**Finding**: For each receipt, 3 individual `session.get()` calls to fetch student, enrollment, and group.

**Fix**: Replace with a single JOIN query returning student name, enrollment ID, group name.

### FR-007 — Session details N+1 queries

**Finding**: For each session attendance, lookup employee name; for each attendance, lookup student name.

**Fix**: Replace with JOIN queries returning employee name + student names in one query.

### FR-008 — Three separate count queries

**Finding**: `_fetch_present_students`, `_fetch_late_students`, `_fetch_excused_students` each do `COUNT(*)` separately.

**Fix**: Combine into a single query with `COUNT(*) FILTER(WHERE ...)` or `SUM(CASE WHEN ...)`.

### FR-009 — PDF missing present_count

**Finding**: PDF `_build_daily_report_pdf` receives `aggregates` but doesn't display `present_count`.

**Fix**: Add a row in the summary table for present students.

### FR-010 — No future-date validation

**Finding**: Both endpoints accept any date, even in the future.

**Fix**: Add guard at top of both endpoint functions: `if report_date > date.today(): raise HTTPException(400, ...)`.

### FR-011 — PDF student name overflow

**Finding**: Combined student names per session can exceed column width in PDF table.

**Fix**: Truncate combined names string to 80 chars with "..." suffix. Column is already small (session detail table).

### FR-012 — Dead code: _build_daily_report_body

**Finding**: `_build_daily_report_body` is defined but never called (HTML body built in `_dispatch`).

**Fix**: Delete the method.

### FR-013 — PDF loose type hint

**Finding**: `_build_daily_report_pdf` accepts `aggregates: "DailyReportAggregateDTO"` (string annotation).

**Fix**: Change to `aggregates: DailyReportAggregateDTO` with proper import.

### FR-014 — Unused import

**Finding**: `from app.modules.notifications.schemas.report_dto import ...` imports `PaymentDetailItem` and `DailyReportAggregateDTO` but one may be unused after FR-006/FR-007 refactor.

**Fix**: Remove unused imports after refactoring.

### FR-015 — _has_data ignores attendance

**Finding**: `_has_data()` only checks sessions_held, payment_count, new_enrollments — but not present_count.

**Fix**: Add `present_count > 0` to the condition.

### FR-016 — Unused return value

**Finding**: `_dispatch()` returns `bool` but callers ignore the return value.

**Fix**: Either make it return `None` and adjust all callers, or add `-> bool` typing. Since `_dispatch` is a Protocol, check the interface first.
