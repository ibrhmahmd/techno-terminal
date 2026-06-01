# Contracts: Daily Report Redesign

This feature introduces no new external interfaces (API endpoints, CLI commands, library APIs, etc.).

**CLI script** (`scripts/test_report_email.py`) is an internal developer tool — no formal contract needed.

All changes are internal to the existing notifications module:
- New DTOs in `app/modules/notifications/schemas/`
- New repository method in `app/modules/notifications/repositories/`
- Updated service methods in `app/modules/notifications/services/`
- New migration in `db/migrations/`
