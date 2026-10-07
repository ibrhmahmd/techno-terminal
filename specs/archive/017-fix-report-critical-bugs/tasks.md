# Tasks: Fix Daily Report Critical Bugs

## T1: Fix enrollment date-boundary type mismatch (FR-001) [reports_repository.py]

- Wrap `func.coalesce(Enrollment.enrolled_at, Enrollment.created_at)` with `func.date()`
- Verify the DATE equality comparison against `report_date` parameter

## T2: Fix instructor status filter (FR-002) [reports_repository.py]

- Add `SessionAttendance.status == 'completed'` filter to `_fetch_instructor_summary`
- Verify instructor counts match per-session completed counts

## T3: Fix exec() with text() in base service (FR-003) [base_notification_service.py]

- Change `self._repo._session.exec(stmt, params=...)` to `self._repo._session.execute(stmt, params=...)` on line 115
- Verify the raw SQL SELECT executes without hanging

## T4: Handle invalid status in notification_logs (FR-004) [report_notifications.py]

- Ensure recipient_type values in create_log calls use `EMPLOYEE` (not `FALLBACK`/`ADDITIONAL`)
- Confirm DB CHECK constraint is satisfied

## T5: Narrow bare except Exception (FR-005) [report_notifications.py + reports_repository.py]

- Replace `except Exception` with `except SQLAlchemyError` in `_fetch_daily_aggregates` and `send_daily_report`
- Keep broader except only for truly unknown errors; let unexpected exceptions propagate

## T6: Eliminate payments N+1 queries (FR-006) [reports_repository.py]

- Replace per-receipt `session.get(Student)`, `session.get(Enrollment)`, `session.get(Group)` with a single JOIN query
- Return all needed fields (student_name, enrollment_id, group_name) in one round-trip

## T7: Eliminate session details N+1 queries (FR-007) [reports_repository.py]

- Replace per-attendance `session.get(Employee)` with a JOIN to `Employee`
- Replace per-attendance `session.get(Student)` with a JOIN to `Student`
- Return employee name + comma-separated student names in one query each

## T8: Combine three count queries into one (FR-008) [reports_repository.py]

- Replace separate `_fetch_present_students`, `_fetch_late_students`, `_fetch_excused_students` with single query using `COUNT(*) FILTER(WHERE ...)` or `SUM(CASE WHEN ...)`
- Note: Since late/excused are no longer valid statuses, this may reduce to just a present count

## T9: Add present_count to PDF (FR-009) [daily_report_pdf.py]

- Add a row in the summary table for "Present Students" showing `aggregates.present_count`

## T10: Add future-date validation (FR-010) [notifications_router.py]

- Add guard in both `POST /daily` and `GET /data` endpoints:
  ```python
  if report_date > date.today():
      raise HTTPException(status_code=400, detail="Report date cannot be in the future")
  ```

## T11: Truncate student names in PDF (FR-011) [daily_report_pdf.py]

- Truncate combined student names string to 80 characters with "..." suffix
- Apply in the session detail table where student names are displayed

## T12: Remove dead code _build_daily_report_body (FR-012) [report_notifications.py]

- Delete the `_build_daily_report_body` method entirely
- Verify no callers exist (grep for references)

## T13: Fix PDF loose type hint (FR-013) [daily_report_pdf.py]

- Change `aggregates: "DailyReportAggregateDTO"` to `aggregates: DailyReportAggregateDTO`
- Add proper import at top of file

## T14: Remove unused imports (FR-014) [reports_repository.py]

- After FR-006/FR-007 refactoring, remove any unused imports (e.g., `Student`, `Group`, `Employee`)
- Run tests to confirm no ImportErrors

## T15: Fix _has_data to check attendance (research note FR-015) [report_notifications.py]

- Add `aggregates.present_count > 0` to the return condition in `_has_data()`

## T16: Run full test suite

```bash
pytest tests/test_notifications.py -v
pytest tests/ -v
```
