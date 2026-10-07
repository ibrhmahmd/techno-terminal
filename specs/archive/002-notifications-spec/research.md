# Research: Notifications Module

## Decisions

### D1: Retry Strategy
- **Decision**: Automatic retry up to 3 times with delays of ~1min, ~5min, ~30min, then manual retry from log
- **Rationale**: Catches transient SMTP/Twilio failures without queue infrastructure. Manual retry gives admin control over persistent failures.
- **Implementation**: Add `retry_count INT DEFAULT 0` and `next_retry_at TIMESTAMP` to `notification_logs`. Background task (or scheduler integration) polls for due retries. Manual retry endpoint: `POST /api/v1/notifications/logs/{id}/retry`.
- **Alternatives considered**: Persistent queue (overkill for scale), no retry (loses notifications on transient error)

### D2: Channel Configuration
- **Decision**: Admin configures channel per notification type via admin settings API. Current: email only.
- **Rationale**: Matches existing `admin_notification_settings` table which already has a `channel` column. Keeps the door open for WhatsApp without complicating current delivery.
- **Implementation**: Existing `channel` field in `admin_notification_settings` is already stored; no DB migration needed. Default to `EMAIL` for all types.
- **Alternatives considered**: Per-recipient channel (adds complexity without current need)

### D3: Email Testing Strategy
- **Decision**: Mock email dispatcher for unit tests; integration test with a test Gmail account (optional, marked as manual).
- **Rationale**: SMTP calls are slow and unreliable in CI. Mock dispatcher captures sent emails in-memory for assertion.
- **Implementation**: Create `MockEmailDispatcher` that stores `(recipient, body, subject, attachments)` tuples in a list. Inject via dependency override in tests.
- **Alternatives considered**: `smtplib` mock, real test email account

### D4: AdminSettingsRepository Refactoring
- **Decision**: Convert all raw f-string SQL to SQLAlchemy `text()` with `:param` bind parameters. Long term: migrate to SQLModel ORM models.
- **Rationale**: Eliminates SQL injection risk immediately with minimal changes. Full ORM migration is higher effort and not required for this feature scope.
- **Implementation**: Replace `f"WHERE admin_id = {admin_id}"` with `text("WHERE admin_id = :admin_id").bindparams(admin_id=admin_id)`.
- **Alternatives considered**: Full ORM models (too much scope), keep raw SQL (security risk)

### D5: Return Type Refactoring
- **Decision**: Replace all `list[dict]` return types in `AdminSettingsRepository` with typed Pydantic DTOs.
- **Rationale**: Constitution §III prohibits loose return types. Typed DTOs catch structural changes at compile time.
- **Implementation**: Create `AdminSettingDTO`, `AdditionalRecipientDTO` in `app/modules/notifications/schemas/admin_settings_dto.py` (some already exist — verify and complete).
- **Alternatives considered**: NamedTuple (less flexible), dataclass (no validation)

### D6: Dead Code Handling
- **Decision**: Remove bulk_router.py entirely (deferred feature should not ship dead endpoints). WhatsApp dispatcher code kept but explicitly disabled with a clear comment and a configuration flag (`WHATSAPP_ENABLED=False`) rather than a silent skip.
- **Rationale**: Constitution §81 mandates zero tolerance for dead code. Bulk router exposes an API endpoint that does nothing. WhatsApp dispatcher silently marks sends as "success" which is misleading.
- **Implementation**: Delete `bulk_router.py` and its router registration. Add `WHATSAPP_ENABLED` env var check in `_dispatch()` instead of the current silent-skip pattern.
- **Alternatives considered**: Keep dead code with deprecation warnings (constitution prohibits this)

### D7: Notification Test Module
- **Decision**: Create `tests/test_notifications.py` with unit tests for each notification service method, using `MockEmailDispatcher` and `MockNotificationRepository`.
- **Rationale**: Existing notification code has zero test coverage. The retry logic, template rendering, recipient resolution, and fallback mechanism all need verification.
- **Implementation**: One test class per service (Enrollment, Payment, Report, Competition, Base). Test fixtures for mock repo and mock dispatcher.
- **Alternatives considered**: Integration tests only (too slow, require DB)

## Existing Infrastructure Inventory

| Component | Status | Action |
|-----------|--------|--------|
| `GmailEmailDispatcher` | Working | Keep as-is |
| `TwilioWhatsAppDispatcher` | Disabled (silent skip) | Add explicit `WHATSAPP_ENABLED` flag |
| `NotificationRepository` | Working (SQLModel) | Keep as-is |
| `AdminSettingsRepository` | Raw SQL, loose returns | Refactor to parameterized queries + typed DTOs |
| `BaseNotificationService._dispatch()` | Working | Add retry integration |
| `NotificationService` (facade) | Working | Keep as-is |
| Enrollment/Payment/Report/Competition services | Working | Keep as-is |
| `report_scheduler.py` | Working | Keep as-is |
| `daily_report_pdf.py` | Working | Keep as-is |
| `bulk_router.py` | Exists for deferred feature | Remove |
| `notification_logs` table | Has columns for status, error | Add `retry_count`, `next_retry_at` columns |
| `admin_notification_settings` table | Has `channel` column | Keep as-is |
| `notification_additional_recipients` table | Working | Keep as-is |
| Notification tests | None | Create `tests/test_notifications.py` |
