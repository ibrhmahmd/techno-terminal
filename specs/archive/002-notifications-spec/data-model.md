# Data Model: Notifications Module

## Entity Changes

### notification_logs (existing — add columns)

| Column | Type | Current | Change |
|--------|------|---------|--------|
| `retry_count` | `INT DEFAULT 0` | Missing | **ADD** |
| `next_retry_at` | `TIMESTAMP` | Missing | **ADD** |

Existing columns (keep as-is): `id` (PK), `template_id` (FK), `channel`, `recipient_type`, `recipient_id`, `recipient_contact`, `subject`, `body`, `status`, `error_message`, `sent_at`, `created_at`.

**Status values**: `PENDING` → `SENT` / `FAILED` / `RETRYING`

**Retry lifecycle**:
1. Initial send → `PENDING`
2. Send attempt → success: `SENT` | failure: `RETRYING` (if retries remain) or `FAILED` (if exhausted)
3. Manual retry from logs → re-sets to `PENDING`, dispatches, updates status

### notification_templates (existing — no changes)

Keep as-is: `id`, `name` (unique), `channel`, `subject`, `body`, `variables` (ARRAY), `is_standard`, `is_active`, `created_at`, `updated_at`.

### admin_notification_settings (existing — no changes)

Keep as-is: `admin_id`, `notification_type`, `is_enabled`, `channel`, `created_at`, `updated_at`.

Channel currently defaults to `EMAIL` for all types.

### notification_additional_recipients (existing — no changes)

Keep as-is: `id`, `admin_id`, `email`, `label`, `notification_types` (ARRAY), `is_active`, `created_at`, `updated_at`.

## DTO Additions/Refinements

### AdminSettingDTO (typed — replace list[dict])
```python
class AdminSettingDTO(BaseModel):
    notification_type: str
    is_enabled: bool
    channel: str  # "EMAIL" for now, extensible
    description: str | None = None
```

### AdditionalRecipientDTO (typed — exists, verify)
```python
class AdditionalRecipientDTO(BaseModel):
    id: int
    email: str
    label: str | None
    notification_types: list[str] | None
    is_active: bool
```

### NotificationLogDTO (add retry fields)
```python
class NotificationLogDTO(BaseModel):
    id: int
    template_id: int | None
    channel: str
    recipient_type: str
    recipient_id: int | None
    recipient_contact: str | None
    subject: str | None
    body: str | None
    status: str  # PENDING | SENT | FAILED | RETRYING
    error_message: str | None
    retry_count: int = 0
    next_retry_at: datetime | None
    sent_at: datetime | None
    created_at: datetime
```

### RetryRequest (new)
```python
class RetryRequest(BaseModel):
    log_id: int
```

### RetryResult (new)
```python
class RetryResult(BaseModel):
    log_id: int
    status: str
    message: str
```

## Validation Rules

| Entity | Rule | Source |
|--------|------|--------|
| notification_logs | `retry_count` ≤ 3 | FR-014 |
| notification_logs | `next_retry_at` must be in future when status is `RETRYING` | Implicit |
| notification_templates | Standard templates: name, variables, channel are immutable | FR-006 |
| notification_templates | Standard templates cannot be deleted | FR-007 |
| admin_notification_settings | `channel` must be valid (`EMAIL` currently, extensible) | FR-019 |
| notification_additional_recipients | `email` must be valid format | Repository validates |
