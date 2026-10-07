# Quickstart: Notifications Module Audit

## No New Setup

All changes are code-only — no new environment variables, no database migrations, no new dependencies.

## New Config Field

```python
# app/core/config.py (add to Settings class)
fallback_email: str = "ibrahim.ahmd.net@gmail.com"
```

## Verification

```bash
# Run notification tests
pytest tests/test_notifications.py -v -x

# Run full suite
pytest tests/ -v
```

## Key Files to Modify (grouped by Priority)

### P1 — Critical (6 files)
| File | US |
|------|----|
| `admin_settings_repository.py` | US-001 (SQL injection) |
| `competition_notifications.py` | US-002 (crashes) |
| `base_notification_service.py` | US-002, 008, 009, 012, 020 |
| `enrollment_notifications.py` | US-002 (move helpers) |
| `notification_repository.py` | US-003 (broken method) |
| `app/core/config.py` | US-008 (config field) |

### P2 — High+Medium (10 files)
| File | US |
|------|----|
| `notification_service.py` | US-004, 005, 007, 016 |
| `admin_settings_repository.py` | US-004, 007 |
| `templates_router.py` | US-005, 021 |
| `notifications_router.py` | US-005 |
| `report_scheduler.py` | US-005, 019, 015 |
| `email_dispatcher.py` | US-010, 017 |
| `whatsapp_dispatcher.py` | US-010, 018 |
| `notification_template.py`, `notification_log.py` | US-009 |

### P3 — Low (3 files)
| File | US |
|------|----|
| `report_notifications.py` | US-013 |
| `bulk_router.py` | US-014 |
| `payment_notifications.py` | US-004 |
