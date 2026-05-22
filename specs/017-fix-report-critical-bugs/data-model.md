# Data Model: Fix Daily Report Critical Bugs

## No New Entities

All changes are in-place query fixes within the existing notification module. No new tables, columns, or migrations.

## COALESCE Type Behavior (reference)

| Column | DB Type | Nullable | COALESCE fallback | COALESCE result type |
|--------|---------|----------|-------------------|----------------------|
| `enrollments.enrolled_at` | `DATE` | YES | `enrollments.created_at` (`TIMESTAMPTZ`) | `TIMESTAMPTZ` (implicit promotion) |
| `receipts.paid_at` | `TIMESTAMPTZ` | YES | `receipts.created_at` (`TIMESTAMPTZ`) | `TIMESTAMPTZ` |

**Key insight**: When COALESCE promotes `DATE` to `TIMESTAMPTZ`, the `DATE` value becomes `YYYY-MM-DD 00:00:00+00`. Equality comparison against a `date` object works correctly only if the TIMESTAMPTZ also falls at midnight. To guarantee correct date boundary matching, wrap with `func.date()`:

```python
func.date(func.coalesce(Enrollment.enrolled_at, Enrollment.created_at)) == report_date
```

## Query Pattern Changes

| FR | Before | After |
|----|--------|-------|
| FR-001 | `func.coalesce(Enrollment.enrolled_at, Enrollment.created_at) == report_date` | `func.date(func.coalesce(Enrollment.enrolled_at, Enrollment.created_at)) == report_date` |
| FR-002 | `COUNT(*)` on sessions with no status filter | `COUNT(*) FILTER(WHERE SessionAttendance.status == 'completed')` or `COUNT(*) WHERE status = 'completed'` |
| FR-006 | Per-receipt `session.get()` ×3 | Single JOIN: `Receipt → Enrollment → Student` + `Receipt → Enrollment → Group` |
| FR-007 | Per-attendance `session.get()` ×2 | Single JOIN: `SessionAttendance → Employee` + `SessionAttendance → Student` |
| FR-008 | 3 separate `COUNT(*)` queries | Single query with `COUNT(*) FILTER(WHERE ...)` ×3 |
