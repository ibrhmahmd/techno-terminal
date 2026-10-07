# Research: Notifications Module Audit

## No [NEEDS CLARIFICATION]

All 21 user stories in spec.md are clear. Technical decisions:

### US-003: get_template_by_code — Remove, not fix
The `code` field does not exist on `NotificationTemplate` model. Adding it would require a migration. The method has zero callers outside tests. **Decision**: Remove the method entirely. `get_template_by_name()` is the correct lookup.

### US-005: templates_router refactoring
Add these public methods to `NotificationService`:

```python
def get_all_templates(self) -> list[TemplateDTO]: ...
def get_template_by_id(self, template_id: int) -> NotificationTemplate: ...
def create_template(self, **data) -> NotificationTemplate: ...
def update_template(self, template_id: int, **data) -> NotificationTemplate: ...
def delete_template(self, template_id: int) -> bool: ...
```

Each method delegates to `self._repo.<method>()`. This closes the encapsulation breach while keeping the repo calls behind the service boundary.

### US-007: commit() vs flush()
`AdminSettingsRepository` receives its session from the router's `get_session()` context manager. The context manager owns the transaction lifecycle. `commit()` in the repo can cause partial commits or leave the session in an inconsistent state if the outer context manager also tries to commit. **Decision**: Change `commit()` to `flush()`.

### US-008: FALLBACK_EMAIL via Pydantic settings
Add `fallback_email: str = "ibrahim.ahmd.net@gmail.com"` to `app/core/config.py` Settings class. Update `base_notification_service.py:15` to `from app.core.config import settings` and use `settings.fallback_email`.

### US-010: Protocol inheritance
Simply change:
```python
class GmailEmailDispatcher:  →  class GmailEmailDispatcher(IMessageDispatcher):
class TwilioWhatsAppDispatcher:  →  class TwilioWhatsAppDispatcher(IMessageDispatcher):
```

### US-006: US-006 and US-004 overlap
US-004 (dead code) includes "commented-out parent code" and US-006 says the same. These are the same 4 blocks. US-004 covers it; US-006 is a duplicate. Remove from US-006 to avoid double-counting.

### Cross-module caller update needed
`app/modules/enrollments/services/enrollment_service.py` calls `svc.enrollment.notify_enrollment_created()`. This PR moves helpers (`_get_student_name`, etc.) to `BaseNotificationService` — callers are unaffected since method signatures don't change. The method just resolves on a different class in the MRO now.
