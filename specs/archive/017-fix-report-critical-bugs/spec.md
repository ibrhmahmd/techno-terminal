# Feature Specification: Fix Daily Report Critical Bugs

**Feature Branch**: `017-fix-report-critical-bugs`  
**Created**: 2026-05-22  
**Status**: Draft  
**Input**: User description: "Fix the problems found in the daily report feature code review"

## User Scenarios & Testing

### User Story 1 - Ensure Daily Report Data Is Accurate (Priority: P1)

Daily report consumers (admin staff) receive reports with correct enrollment counts, consistent session statistics, and properly filtered instructor data. The enrollment count accurately reflects the target date, and the session detail table numbers match the instructor summary.

**Why this priority**: Data accuracy is the core value of the report. Wrong enrollment counts and inconsistent session/instructor numbers erode trust in the system.

**Independent Test**: Can be tested by comparing the enrollment count from the report against a manual SQL query for the same date, and verifying session detail row count equals instructor summary session count.

**Acceptance Scenarios**:

1. **Given** a daily report run for a date where enrollments have `enrolled_at` as NULL and `created_at` as a non-midnight timestamp, **When** the report is generated, **Then** the enrollment count includes those enrollments in the correct date boundary.
2. **Given** a daily report run for a date with both completed and non-completed sessions, **When** the report is generated, **Then** the instructor summary session count matches the number of session detail rows.
3. **Given** the notification module sends any notification type, **When** `_resolve_notification_recipients` is called, **Then** it uses the correct `execute()` method and does not hang.

---

### User Story 2 - Prevent Silent Report Failures (Priority: P2)

When the database is unavailable or a query fails, the report either surfaces the error clearly or gracefully degrades with a visible warning — instead of silently returning all zeros with no alert.

**Why this priority**: Silent data loss is hard to detect in production. Staff may act on incorrect information for days before realizing the report has been showing zeros due to a connection failure.

**Independent Test**: Can be tested by temporarily making the database unreachable and verifying that the report endpoint returns an error instead of all zeros.

**Acceptance Scenarios**:

1. **Given** the database is unreachable, **When** a daily report is requested, **Then** the system returns an error instead of a report with all zero values.
2. **Given** the database is unreachable, **When** a daily report is requested via the HTTP endpoint, **Then** a 500-level error is returned with a descriptive message.

---

### User Story 3 - Access Attendance-Only Report Data (Priority: P2)

Report consumers can retrieve daily report data for dates that have attendance records but no completed sessions, no payments, and no enrollments. The 404 response is reserved for truly empty dates.

**Why this priority**: Attendance tracking is a primary function; hiding it from reports when other metrics are zero creates a blind spot.

**Independent Test**: Can be tested by requesting a report for a date that has attendance records but no sessions or payments — the endpoint returns the attendance data.

**Acceptance Scenarios**:

1. **Given** a date with attendance records but zero sessions, zero payments, and zero enrollments, **When** the report endpoint is called, **Then** it returns the attendance data with success.
2. **Given** a completely empty date (no data of any kind), **When** the report endpoint is called, **Then** it returns a 404 error.

---

### User Story 4 - Quick Report Generation for Heavy Days (Priority: P3)

Daily reports for dates with many sessions (10+) and payments (50+) generate within a reasonable time. The report does not issue hundreds of individual database queries.

**Why this priority**: As the center grows, session and payment volume increases. N+1 queries that work with 1 session will become unusably slow with 20.

**Independent Test**: Can be tested by running the report for a date with 20+ sessions and 100+ payments and measuring response time.

**Acceptance Scenarios**:

1. **Given** a date with 20 completed sessions, each with 15 attendance records, **When** the daily report is generated, **Then** the total number of database queries is proportional to the number of session/entity types, not the number of individual rows.
2. **Given** a date with 100 payments, **When** the daily report is generated, **Then** student names and group names are fetched via JOINs rather than individual lookups.

---

### User Story 5 - PDF Report Shows Attendance and Future-Date Validation (Priority: P3)

The PDF daily report includes the present count in its summary cards. The API endpoints reject requests for future dates.

**Why this priority**: Present count is the most important attendance metric. Future-date protection prevents confusing empty reports.

**Independent Test**: Can be tested by requesting a PDF for a date with attendance data and verifying present count appears in the summary. Future dates error with 400.

**Acceptance Scenarios**:

1. **Given** the PDF report is generated for a date with attendance data, **When** the PDF is opened, **Then** the summary cards include both "Present Students" and "Absent Students" counts.
2. **Given** the POST or GET endpoint is called with a date in the future, **When** the request is processed, **Then** a 400 Bad Request error is returned.
3. **Given** a session has 15+ student names, **When** the PDF is generated, **Then** long names are truncated or wrapped legibly rather than overflowing the cell.

---

### Edge Cases

- **Enrollment with only `created_at` (NULL `enrolled_at`)**: The date boundary calculation must correctly round to the day, not include partial time components.
- **Date with mixed completed/non-completed sessions**: Instructor summary and session detail counts must be consistent.
- **Date with attendance-only data**: Must return 200, not 404.
- **Future date**: Must return 400 with clear error.
- **Empty database**: Must return 500-level error, not a report of zeros.
- **Long student name lists (15+ names)**: Must not overflow PDF column or render illegibly.
- **`_resolve_notification_recipients` with `exec()`**: Must not hang or behave unexpectedly with any notification type.

## Requirements

### Functional Requirements

- **FR-001**: Enrollment date boundary query MUST use `DATE(COALESCE(...))` to strip time components from timestamps, matching the revenue query pattern.
- **FR-002**: The instructor summary query MUST filter by the same session status as the session details query (both "completed" only, or both all statuses — must be consistent).
- **FR-003**: All calls to `self._repo._session.exec()` with `text()` SQL MUST be changed to `self._repo._session.execute()` to match the correct SQLAlchemy/SQLModel API.
- **FR-004**: The `_has_data()` check MUST include `present_count > 0` as a valid data signal alongside sessions, payments, and enrollments.
- **FR-005**: Repository methods MUST NOT catch bare `except Exception`. Each try/except MUST specify the expected exception types (e.g., `except SQLAlchemyError`). Unexpected exceptions MUST propagate to the caller.
- **FR-006**: The `_fetch_payments` return value MUST remove the unused `List[Payment]` first element.
- **FR-007**: The `_fetch_session_details` and `_fetch_payments` methods MUST replace per-row `session.get()` lookups with JOINed queries to eliminate N+1 patterns.
- **FR-008**: The `_fetch_attendance` method MUST use a single `GROUP BY status` query instead of three separate count queries.
- **FR-009**: The PDF summary cards MUST include a `Present Students` row alongside `Absent Students`.
- **FR-010**: The POST and GET daily report endpoints MUST reject `target_date` values greater than today with a 400 error.
- **FR-011**: Long student name lists in the PDF session detail table MUST be truncated or wrapped to fit within the column width.
- **FR-012**: The unused `_build_daily_report_body` method MUST be removed.
- **FR-013**: The PDF `generate_daily_report_pdf` function MUST accept the typed `DailyReportAggregateDTO` instead of `Dict[str, Any]`.
- **FR-014**: The unused `Payment` import in `reports_repository.py` MUST be removed if confirmed unused after other changes.

### Key Entities

- **DailyReportAggregateDTO**: Typed output data transfer object containing all daily report metrics and sub-tables.
- **Enrollment**: Student enrollment record with nullable `enrolled_at` DATE and non-null `created_at` TIMESTAMP.
- **CourseSession**: Session record with `status` field (`completed`, `scheduled`, `cancelled`).
- **NotificationLog**: Audit log per notification dispatch — recipient_type must be valid (`PARENT` or `EMPLOYEE`).

## Success Criteria

### Measurable Outcomes

- **SC-001**: Enrollment counts in reports match manual SQL queries for the same date with ±0 error margin.
- **SC-002**: Instructor summary session count matches the number of session detail rows for every report generated.
- **SC-003**: No `session.exec(text(...))` or `session.exec(stmt, params=...)` calls remain in the codebase — all use `session.execute()`.
- **SC-004: The `_has_data()` check returns true for dates with attendance records only — no false 404s.
- **SC-005**: Report generation for 20+ sessions with 100+ payments completes in under 5 seconds (was previously unbounded due to N+1).
- **SC-006**: Future-date requests return 400 Bad Request — not 200 with empty data or 404.
- **SC-007**: PDF summary cards display "Present Students" count and "Absent Students" count side by side.
- **SC-008**: All specification tests pass (15 notification tests) after changes.

## Assumptions

- The `daily_report` template exists and is active in the database.
- The existing attendance status values (`present`, `absent`, `cancelled`) are sufficient — no new statuses are needed.
- The business considers attendance data independently valuable even without accompanying session/payment data.
- N+1 optimization targets are acceptable at service level — no Redis/memcache layer is assumed.
- Database connection failures are expected to be rare; the primary concern is catching them visibly rather than silently returning zeros.
