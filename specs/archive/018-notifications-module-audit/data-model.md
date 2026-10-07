# Data Model: Notifications Module Audit

## No New Entities

All fixes are code-only — no new tables, columns, or migrations.

## Key Changes

| File | Change | Rationale |
|------|--------|-----------|
| `app/core/config.py` | Add `fallback_email: str = "ibrahim.ahmd.net@gmail.com"` | Move from `os.getenv()` to Pydantic settings pattern |
| `base_notification_service.py` | Remove module-level `FALLBACK_EMAIL` | Replaced by `settings.fallback_email` |

## Methods Removed

| Method | Reason |
|--------|--------|
| `NotificationRepository.get_template_by_code()` | References non-existent `code` field; zero callers |
| `NotificationService.notify_enrollment()` | Deprecated shim — use `.enrollment.notify_enrollment_created()` |
| `NotificationService.notify_payment_receipt()` | Deprecated shim — use `.payment.notify_payment_receipt()` |
| `NotificationService.notify_level_progression()` | Deprecated shim — use `.enrollment.notify_level_progression()` |
| `NotificationService.notify_enrollment_completed()` | Deprecated shim — use `.enrollment.notify_enrollment_completed()` |
| `NotificationService.notify_enrollment_dropped()` | Deprecated shim — use `.enrollment.notify_enrollment_dropped()` |
| `NotificationService.notify_enrollment_transferred()` | Deprecated shim — use `.enrollment.notify_enrollment_transferred()` |
| `AdminSettingsRepository.get_enabled_admins_for_notification()` | Always returns `[]`; intentionally unused |

## Methods Moved

| Method | From | To |
|--------|------|----|
| `_get_student_name()` | `EnrollmentNotificationService` | `BaseNotificationService` |
| `_get_group_name()` | `EnrollmentNotificationService` | `BaseNotificationService` |
| `_get_instructor_name()` | `EnrollmentNotificationService` | `BaseNotificationService` |

## Methods Added (to NotificationService facade)

| Method | Delegates To |
|--------|-------------|
| `get_all_templates()` | `self._repo.get_all_templates()` |
| `get_template_by_id()` | `self._repo.get_template_by_id()` |
| `create_template()` | `self._repo.create_template()` |
| `update_template()` | `self._repo.update_template()` |
| `delete_template()` | `self._repo.delete_template()` |
