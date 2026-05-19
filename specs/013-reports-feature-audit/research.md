# Research: Daily Report Fixes

## 1. Attendance Status Values

**Decision**: Remove `late` and `excused` from query filters. Use only `present`, `absent`, `cancelled`.
**Rationale**: The DB CHECK constraint and domain `AttendanceStatus` type alias both restrict to `present`, `absent`, `cancelled`. Adding `late`/`excused` would require a migration and business process change — out of scope.
**Alternatives considered**: Add `late` and `excused` to the model and schema (requires migration, not needed now).

**Implementation**:
- In `_fetch_daily_aggregates()`: Replace `Attendance.status.in_(["present", "late"])` with `Attendance.status == "present".`
- Remove the `excused` count filter entirely.
- Rename the `present` label to just `present_count`.
- The attendance rate formula stays: `present / (present + absent + cancelled)`.

## 2. Receipt `paid_at` NULL Handling

**Decision**: Use `COALESCE(Receipt.paid_at, Receipt.created_at)` in all report date filters.
**Rationale**: `paid_at` is `TIMESTAMPTZ` with no NOT NULL constraint. The receipt creation flow doesn't always set it. `created_at` is always set at creation time and reflects the actual payment processing moment.
**Alternatives considered**: Fix receipt creation flow to always set `paid_at` (larger scope, touches other modules).

**Implementation**:
- Analytics repository `get_revenue_by_date()`: Change the SQL from `WHERE DATE(r.paid_at) BETWEEN :start AND :end` to `WHERE DATE(COALESCE(r.paid_at, r.created_at)) BETWEEN :start AND :end`.
- Inline payment query in `_fetch_daily_aggregates()`: Change `Receipt.paid_at >= target_date` to `func.coalesce(Receipt.paid_at, Receipt.created_at) >= target_date`.

## 3. Enrollment `enrolled_at` NULL Handling

**Decision**: Use `COALESCE(Enrollment.enrolled_at, Enrollment.created_at)` in enrollment count queries.
**Rationale**: Same pattern as receipts — `enrolled_at` can be NULL, `created_at` is always set.
**Implementation**: Change `Enrollment.enrolled_at >= target_date` to `func.coalesce(Enrollment.enrolled_at, Enrollment.created_at) >= target_date`.

## 4. Repository Layer Extraction

**Decision**: Create `app/modules/notifications/repositories/reports_repository.py` with typed query methods.
**Rationale**: Constitution requires all queries in repositories. The existing `financial_repository.py` is in the analytics module and isn't the right home for report-specific DTO mappings. A dedicated reports repository keeps things cohesive.
**Alternatives considered**: Extend `financial_repository.py` (different module boundary), extend `notification_repository.py` (already handles templates/logs, mixing concerns).

**Interface**:
```python
class ReportsRepository:
    def get_daily_aggregates(self, session: Session, target_date: date) -> DailyReportAggregateDTO: ...
```

Single method that encapsulates all 7 aggregate queries (revenue, sessions, attendance, enrollments, payments, instructors, unpaid). Returns a single DTO.

## 5. Typed DTO Design

**Decision**: Create `DailyReportAggregateDTO` in `app/modules/notifications/schemas/report_dto.py`.
**Rationale**: Constitution §III forbids bare `dict` returns. The DTO matches the 11 variables currently passed to template + PDF.
**Alternatives considered**: Multiple fine-grained DTOs (over-engineered for a single-use report).

**Shape**:
```python
class DailyReportAggregateDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: str
    total_revenue: float
    new_enrollments: int
    sessions_held: int
    absent_count: int
    present_count: int
    attendance_rate: float
    payment_count: int
    payment_methods: dict[str, int]  # method -> count
    payment_details: list[PaymentDetailItem]
    instructors_list: list[str]
    unpaid_count: int

class PaymentDetailItem(BaseModel):
    student_name: str
    group_name: str
    amount: float
    payment_type: str
```

## 6. Email Template Update

**Decision**: Update the `daily_report` template body in the database to use the rich HTML table already built in `send_daily_report()` as `payment_details_html`.
**Rationale**: The code already constructs a rich HTML table with student/group/amount/type columns. The email template just doesn't use it. Rather than a migration, update the template body via the existing `PUT /templates/{id}` endpoint or a one-time data migration.
**Alternatives considered**: Add new template variables without changing the template (would still be unused), create a new template version (unnecessary indirection).

**Implementation approach**: Use a new migration SQL file (`056_update_daily_report_template.sql`) that `UPDATE`s the `daily_report` template's `body` and `variables` columns to include all 11 metrics with the full HTML table.

## 7. HTTP Trigger Endpoint

**Decision**: Add `POST /api/v1/notifications/reports/daily` as a new router or add to existing `notifications_router.py`.
**Rationale**: FR-006 requires manual trigger. The endpoint delegates to `svc.report.send_daily_report()` with `BackgroundTasks`.

**Implementation**: Add a single endpoint to `app/api/routers/notifications/notifications_router.py`. No new router file needed.

## 8. SQL Injection in Base Service

**Decision**: Replace f-string interpolation in `_resolve_notification_recipients()` with parameterized query.
**Rationale**: NFR-002. The `notification_type` value comes from app code currently, but the pattern is unsafe.

**Implementation**: Change:
```sql
f"""...'{notification_type}' = ANY(notification_types)"""
```
to:
```sql
"""...:notification_type = ANY(notification_types)"""
```
with `params={"notification_type": notification_type}`.

## 9. Dead Code Removal

**Decision**: Delete the commented-out PARENT_CODE block (`report_notifications.py:429-441`).
**Rationale**: Constitution §VI — zero tolerance for commented-out code.
