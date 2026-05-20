# Auth API Contracts — Self-Service

## POST `/api/v1/auth/change-password`

**Auth**: Bearer token (any active user)  
**Request**:
```json
{
  "current_password": "currentpwd123",
  "new_password": "newstrongpwd456"
}
```
**Responses**:
| Status | Body |
|--------|------|
| 200 | `{"success": true, "data": null, "message": "Password changed successfully."}` |
| 401 | `{"success": false, "error": "AuthError", "message": "Current password is incorrect."}` |
| 403 | `{"success": false, "error": "Forbidden", "message": "Inactive user"}` |
| 422 | `{"success": false, "error": "ValidationError", "message": "..."}` (short password) |

## POST `/api/v1/auth/forgot-password`

**Auth**: None (public)  
**Request**:
```json
{
  "email": "user@example.com"
}
```
**Responses**:
| Status | Body |
|--------|------|
| 200 | `{"success": true, "data": null, "message": "If the email exists, a password reset link has been sent."}` |

> Always returns 200 regardless of whether the email exists. Prevents email enumeration.

## PATCH `/api/v1/auth/me`

**Auth**: Bearer token (any active user)  
**Request**:
```json
{
  "username": "new_username"
}
```
**Responses**:
| Status | Body |
|--------|------|
| 200 | `{"success": true, "data": {"id": 1, "username": "new_username", ...}, "message": "Profile updated."}` |
| 403 | `{"success": false, "error": "Forbidden", "message": "Inactive user"}` |
| 409 | `{"success": false, "error": "ConflictError", "message": "Username 'new_username' already exists."}` |
