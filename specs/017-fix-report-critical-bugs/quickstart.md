# Quickstart: Fix Daily Report Critical Bugs

## No New Setup

This feature is purely bug fixes — no new environment variables, no new database migrations, no new dependencies.

## Verification

```bash
# Run just the notification tests
pytest tests/test_notifications.py -v

# Run full test suite
pytest tests/ -v
```

## Key Files to Modify

| File | Changes |
|------|---------|
| `app/modules/notifications/repositories/reports_repository.py` | FR-001, FR-002, FR-006, FR-007, FR-008, FR-014 |
| `app/modules/notifications/services/report_notifications.py` | FR-004, FR-012, FR-015, FR-016 |
| `app/modules/notifications/services/base_notification_service.py` | FR-003 |
| `app/modules/notifications/pdf/daily_report_pdf.py` | FR-009, FR-011, FR-013 |
| `app/api/routers/notifications/notifications_router.py` | FR-010 |
| `tests/test_notifications.py` | Updated assertions |
