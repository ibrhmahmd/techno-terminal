# Contracts: Reports Feature

## Public Interfaces

### `ReportsRepository`
**File**: `app/modules/notifications/repositories/reports_repository.py`

```python
class ReportsRepository:
    """Report aggregate queries — single source of truth for daily report metrics."""

    def get_daily_aggregates(self, session: Session, target_date: date) -> DailyReportAggregateDTO:
        """Fetch all daily report metrics in a single method.
        
        Encapsulates:
        - Revenue (via COALESCE(paid_at, created_at))
        - Sessions held count
        - Attendance breakdown (present/absent/cancelled only)
        - New enrollments (via COALESCE(enrolled_at, created_at))
        - Payment details, methods, count
        - Instructor list
        - Unpaid enrollment count
        """
```

### `ReportNotificationService` (modified)
**File**: `app/modules/notifications/services/report_notifications.py`

```python
class ReportNotificationService(BaseNotificationService):
    async def send_daily_report(self) -> None:
        """Send daily business summary. Now uses ReportsRepository for typed aggregates."""
```

## API Contracts

### Manual Trigger Endpoint

```
POST /api/v1/notifications/reports/daily
Authorization: Bearer <admin-jwt>
```

Response: `{"success": true, "data": "Daily report queued", "message": "..."}`

## Database Migration Contract

**File**: `db/migrations/056_update_daily_report_template.sql`

Purpose: `UPDATE notification_templates SET body = '...rich HTML...', variables = ARRAY['all','11','variables'] WHERE name = 'daily_report'`

Must be idempotent (use `WHERE name = 'daily_report' AND is_standard = true`).
