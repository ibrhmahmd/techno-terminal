# Data Model: Daily Report Redesign & Debtors Data

## Existing DTOs — Extended

### DailyReportAggregateDTO (extended)
*File: `app/modules/notifications/schemas/report_dto.py`*

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| (existing fields) | — | — | Unchanged |
| total_outstanding_debt | float | `FinancialAnalyticsService.get_top_debtors()` → sum | Total EGP owed across all students |
| debtor_count | int | Count of entries with balance < 0 | Number of students with outstanding debt |
| top_debtors | list[TopDebtorItem] | `get_top_debtors(limit=5)` | Name + amount for top 5 |
| outstanding_by_group | list[OutstandingByGroupItem] | `get_outstanding_by_group()` | Per-group debt summary |
| today_unpaid_attendees | list[UnpaidAttendeeItem] | `get_today_unpaid_attendees(target_date)` | Students who attended today + owe |
| tomorrow_preview | TomorrowPreviewDTO | New query in ReportsRepository | Tomorrow's sessions + unpaid alerts |

### UnpaidAttendeeItem (new — adapted from analytics schemas)
*File: `app/modules/notifications/schemas/report_dto.py`*

| Field | Type | Notes |
|-------|------|-------|
| student_name | str | Full name |
| group_name | str | Current group |
| amount_owed | float | Positive EGP amount owed |
| payment_status | str | `not_paid` or `partially_paid` |

### TopDebtorItem (new)
*File: `app/modules/notifications/schemas/report_dto.py`*

| Field | Type | Notes |
|-------|------|-------|
| student_name | str | Full name |
| amount_owed | float | Total outstanding EGP |

### OutstandingByGroupItem (new)
*File: `app/modules/notifications/schemas/report_dto.py`*

| Field | Type | Notes |
|-------|------|-------|
| group_name | str | Group name |
| course_name | str | Course name |
| debtor_count | int | Students with balance in this group |
| total_outstanding | float | Total EGP owed in this group |

### TomorrowPreviewDTO (new)
*File: `app/modules/notifications/schemas/report_dto.py`*

| Field | Type | Notes |
|-------|------|-------|
| session_count | int | Sessions scheduled for tomorrow |
| expected_student_count | int | Total enrolled students across those sessions |
| unpaid_attendees | list[UnpaidAttendeeItem] | Tomorrow's expected attendees who owe |
| has_sessions | bool | False when no sessions tomorrow |

## Existing DTOs — Reused (no changes)

These already exist in `app/modules/analytics/schemas/` and are used as query sources:

- **UnpaidAttendeeDTO** (`academic_schemas.py`): student_id, student_name, parent_name, phone_primary, total_balance
- **TopDebtorDTO** (`financial_schemas.py`): student_id, student_name, parent_name, phone_primary, total_outstanding
- **OutstandingByGroupDTO** (`financial_schemas.py`): group_id, group_name, course_name, students_with_balance, total_outstanding

## New SQL Query — Tomorrow's Unpaid Attendees

```sql
SELECT DISTINCT
    st.id AS student_id,
    st.full_name AS student_name,
    COALESCE(g.name, 'N/A') AS group_name,
    SUM(CASE WHEN vb.balance < 0 THEN -vb.balance ELSE 0 END)
        OVER (PARTITION BY st.id) AS amount_owed,
    s.id AS session_id,
    s.start_time
FROM sessions s
JOIN enrollments e ON e.group_id = s.group_id AND e.level_number = s.level_number
JOIN students st ON e.student_id = st.id
JOIN v_enrollment_balance vb ON vb.student_id = st.id
LEFT JOIN groups g ON e.group_id = g.id
WHERE s.session_date = :tomorrow_date
  AND s.status = 'scheduled'
  AND vb.balance < 0
ORDER BY amount_owed DESC
```

## Validation Rules

- Empty states: All list fields default to `[]` (never None)
- `total_outstanding_debt` defaults to `0.0`
- `debtor_count` defaults to `0`
- `TomorrowPreviewDTO.has_sessions` = False when session_count == 0
- All DTOs use `model_config = ConfigDict(from_attributes=True)`
