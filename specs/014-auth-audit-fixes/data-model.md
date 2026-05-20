# Data Model: Auth Module Bug Fixes & Audit Remediation

## Entity Changes

**No entity changes.** This feature does not modify any database models, add/remove columns, or change relationships.

The existing `User` model (`app/modules/auth/models/auth_models.py`) remains:

| Field | Type | Constraints | Change |
|-------|------|-------------|--------|
| `id` | `int` (PK, auto) | Primary key | None |
| `supabase_uid` | `str` | Unique, not null | None |
| `username` | `str` | Unique, not null | None |
| `role` | `str` | Validated via `ALL_ROLE_VALUES` | None |
| `is_active` | `bool` | Default `True` | None |
| `employee_id` | `int?` | FK → `employees.id` | None |
| `last_login` | `datetime?` | Nullable | None |
| `created_at` | `datetime?` | Nullable | None |

## Model-Level Changes

The only code change to `User` model is the `is_admin` property (no schema change):

```python
# Before:
@property
def is_admin(self) -> bool:
    return self.role in ("admin", "system_admin")

# After:
@property
def is_admin(self) -> bool:
    return self.role in (UserRole.ADMIN.value, UserRole.SYSTEM_ADMIN.value)
```

## Validation Rules (unchanged)

- `role` must be one of `ALL_ROLE_VALUES` = `{"admin", "system_admin"}` — enforced via `@field_validator`
- `username` must be unique — enforced at DB level
- Password: minimum 12 characters (`MIN_PASSWORD_LENGTH`) — enforced in service layer

## State Transitions (unchanged)

No state machine on `User` — the only relevant state is `is_active` toggle. The `force_reset_password` fix adds a guard check: if `is_active == False`, reject with `BusinessRuleError`.
