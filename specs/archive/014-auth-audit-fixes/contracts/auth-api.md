# Auth API Contracts

## Overview

This feature introduces no new API endpoints and breaks no existing contracts. The only behavioral change is an additional error response on the reset-password endpoint.

## Endpoint Changes

### POST `/api/v1/auth/users/{user_id}/reset-password`

**New error response**:

```json
{
  "success": false,
  "error": "BusinessRuleError",
  "message": "Cannot reset password for deactivated user."
}
```

**Scenario**: User with `is_active = False` — returns `409 Conflict` instead of proceeding with the password reset.

**No other endpoint contracts are modified.**
