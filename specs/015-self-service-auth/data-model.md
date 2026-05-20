# Data Model: Self-Service Auth Features

## Entity Changes

**No entity or column changes.** The existing `User` model is sufficient for all three features.

## New DTOs

### Module-Level (`app/modules/auth/schemas/auth_schemas.py`)

**ChangePasswordInput**:
| Field | Type | Validation |
|-------|------|------------|
| `current_password` | `str` | Required |
| `new_password` | `str` | `min_length=MIN_PASSWORD_LENGTH` (12) |

**ForgotPasswordInput**:
| Field | Type | Validation |
|-------|------|------------|
| `email` | `str` | Required |

**UpdateProfileInput**:
| Field | Type | Validation |
|-------|------|------------|
| `username` | `Optional[str]` | At least one field required |

### API-Level (`app/api/schemas/auth.py`)

| DTO | Fields | Maps To |
|-----|--------|---------|
| `ChangePasswordRequest` | `current_password`, `new_password` | `ChangePasswordInput` |
| `ForgotPasswordRequest` | `email` | `ForgotPasswordInput` |
| `UpdateProfileRequest` | `username` | `UpdateProfileInput` |

## User State Transitions

No new state transitions. The `is_active` guard is enforced at the dependency level (`get_current_user`). Relevant states:

```
[Active] ──→ all self-service operations allowed
[Inactive] ──→ 403 Forbidden on all operations
```
