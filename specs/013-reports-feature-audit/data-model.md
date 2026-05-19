# Data Model: Daily Report Aggregates

## New DTOs

### `DailyReportAggregateDTO`
**File**: `app/modules/notifications/schemas/report_dto.py`
**Purpose**: Typed return for `_fetch_daily_aggregates()`. Replaces bare `dict`.

| Field | Type | Source |
|-------|------|--------|
| `date` | `str` | `target_date.isoformat()` |
| `total_revenue` | `float` | `FinancialAnalyticsService.get_revenue_by_date().sum(net_revenue)` |
| `new_enrollments` | `int` | `COUNT(enrollments) WHERE COALESCE(enrolled_at, created_at) = target_date` |
| `sessions_held` | `int` | `COUNT(sessions) WHERE session_date = target_date AND status = 'completed'` |
| `absent_count` | `int` | `COUNT(attendance) WHERE status = 'absent' AND session in target_date sessions` |
| `present_count` | `int` | `COUNT(attendance) WHERE status = 'present' AND session in target_date sessions` |
| `attendance_rate` | `float` | `present_count / (present_count + absent_count + cancelled_count)` |
| `payment_count` | `int` | `COUNT(payments) JOIN receipts ON COALESCE(paid_at, created_at) = target_date` |
| `payment_methods` | `dict[str, int]` | `payments grouped by payment_type` |
| `payment_details` | `list[PaymentDetailItem]` | Per-payment: student, group, amount, type |
| `instructors_list` | `list[str]` | `DISTINCT instructors from sessions on target_date` |
| `unpaid_count` | `int` | `COUNT(enrollments) WHERE balance > 0 (via v_enrollment_balance)` |

### `PaymentDetailItem`
**File**: `app/modules/notifications/schemas/report_dto.py`

| Field | Type | Source |
|-------|------|--------|
| `student_name` | `str` | `students.full_name` |
| `group_name` | `str` | `groups.name` |
| `amount` | `float` | `payments.amount` |
| `payment_type` | `str` | `payments.payment_type` |

## Existing Entities (no changes)

| Entity | Table | File |
|--------|-------|------|
| `NotificationTemplate` | `notification_templates` | `app/modules/notifications/models/notification_template.py` |
| `NotificationLog` | `notification_logs` | `app/modules/notifications/models/notification_log.py` |
| `Receipt` | `receipts` | `app/modules/finance/models/receipt.py` |
| `Payment` | `payments` | `app/modules/finance/models/payment.py` |
| `Enrollment` | `enrollments` | `app/modules/enrollments/models/enrollment_models.py` |
| `CourseSession` | `sessions` | `app/modules/academics/models/session_models.py` |
| `Attendance` | `attendance` | `app/modules/attendance/models/attendance_models.py` |
| `Student` | `students` | `app/modules/crm/models/student_models.py` |
| `Group` | `groups` | `app/modules/academics/models/group_models.py` |
| `Employee` | `employees` | `app/modules/hr/models/employee_models.py` |

## State Transitions

None. Report aggregates are read-only queries — no state changes in the report flow. The only write is the `NotificationLog` entry created by `_dispatch()` after the email is sent.
