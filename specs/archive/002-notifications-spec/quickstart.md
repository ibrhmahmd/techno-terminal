# Quickstart: Notifications Module

Implementation order (8 steps, dependency-gated):

## Step 1: Dead Code Removal
- Delete `app/api/routers/notifications/bulk_router.py`
- Remove bulk_router registration from `app/api/routers/notifications/__init__.py`
- Add `WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"` to `base_notification_service.py`
- Replace silent WhatsApp skip with explicit check against `WHATSAPP_ENABLED`
- **Test**: Verify `/api/v1/notifications/bulk` returns 404

## Step 2: Refactor AdminSettingsRepository
- Convert all `text(f"...WHERE admin_id = {admin_id}")` to `text("...WHERE admin_id = :admin_id").bindparams(admin_id=admin_id)`
- Audit all 10+ methods in `admin_settings_repository.py`
- **Test**: Run existing tests to ensure no regression (no notification tests yet, but other modules shouldn't break)

## Step 3: Typed DTOs for Repository Returns
- Verify `AdminSettingDTO`, `AdditionalRecipientDTO` exist in `app/modules/notifications/schemas/admin_settings_dto.py`
- Update `AdminSettingsRepository` methods to return typed DTOs instead of `list[dict]`
- Update router code that destructures the dict returns
- **Test**: Verify all admin settings endpoints still return correct data

## Step 4: Add Retry Columns to DB
- Create migration `050_add_notification_retry_columns.sql`:
  ```sql
  ALTER TABLE notification_logs ADD COLUMN retry_count INT DEFAULT 0;
  ALTER TABLE notification_logs ADD COLUMN next_retry_at TIMESTAMP;
  ```
- **Test**: Verify columns exist via `\d notification_logs`

## Step 5: Implement Retry Logic in Base Service
- In `BaseNotificationService._dispatch()`:
  - On failure: increment `retry_count`, calculate `next_retry_at` (1min/5min/30min based on attempt), set status to `RETRYING`, update log
  - After final attempt (retry_count >= 3): set status to `FAILED`
- Add a retry polling method `_process_retry_queue()` that queries `notification_logs WHERE status = 'RETRYING' AND next_retry_at <= NOW()`
- Integrate with `report_scheduler.py` or create a lightweight background task
- **Test**: Unit test with mock dispatcher that fails first N attempts

## Step 6: Add Manual Retry Endpoint
- Add `POST /logs/{log_id}/retry` to `notifications_router.py`
- Accept log_id, validate status is FAILED, reset to PENDING and dispatch
- Return `RetryResult`
- **Test**: Test 404, 409 (non-failed status), 200 success

## Step 7: Create Notification Tests
Create `tests/test_notifications.py` with:
- `MockEmailDispatcher` fixture
- `MockNotificationRepository` fixture (or use real repo with test session)
- Test classes:
  - `TestEnrollmentNotifications` — verify correct templates selected, recipient resolution
  - `TestPaymentNotifications` — verify PDF attachment logic, template rendering
  - `TestReportNotifications` — verify data aggregation (mock analytics services)
  - `TestBaseService` — verify retry counts, fallback triggers, WhatsApp disabled behavior
  - `TestAdminSettingsRepository` — verify typed returns, parameterized queries
- Run: `pytest tests/test_notifications.py -v`

## Step 8: End-to-End Verification
- Run all existing tests: `pytest tests/ -v`
- Verify no regression from dead code removal or repository refactoring
- Manually test notification send via Swagger UI at `/api/v1/docs`
