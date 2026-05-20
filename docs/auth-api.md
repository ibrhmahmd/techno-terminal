# Authentication & User Management API

**Base URL**: `/api/v1`

All endpoints return a standard envelope:

```json
// Success (single)
{"success": true, "data": {...}, "message": "..."}
// Success (list)
{"success": true, "data": [...], "total": 42, "skip": 0, "limit": 50}
// Error
{"success": false, "error": "NotFoundError", "message": "User 12 not found"}
```

**Auth header**: `Authorization: Bearer <supabase_access_token>`

- Tokens issued by Supabase on login. Refresh via `POST /auth/refresh`.
- **HTTP 401** = missing/invalid/expired token. **403** = wrong role.

**Roles** (hierarchical): `system_admin` > `admin` > `instructor`

---

## 1. Authentication (public)

### `POST /auth/login`
Authenticate with Supabase. Returns JWT + user profile.

```json
// Request
{"email": "user@example.com", "password": "..."}
// Response 200
{"access_token": "...", "refresh_token": "...", "token_type": "bearer", "user": {...}}
// 401 = wrong credentials
```

### `POST /auth/refresh`
Exchange refresh token for new JWT.

```json
// Request
{"refresh_token": "..."}
// Response 200 — same shape as login
// Response 401 = expired/invalid refresh token
```

### `POST /auth/logout`
Revoke current Supabase session (Bearer token in header). No body. Returns 200.

### `POST /auth/register`
Complete invite registration with a one-time token.

```json
// Request
{"token": "uuid-here", "username": "chosen_name", "password": "min8chars"}
// Response 200 — returns user profile
// 400 = invalid/expired token
```

---

## 2. Self-Service (any authenticated user)

### `GET /auth/me`
Returns current user's public profile. No body.

```json
// Response 200
{"id": 1, "username": "...", "role": "admin", "is_active": true, "employee_id": null, "last_login": null, "created_at": "..."}
```

### `PATCH /auth/me`
Update username and/or email.

```json
// Request
{"username": "new_name", "email": "new@email.com"}  // both optional
// Response 200 — returns updated user profile
// 409 = username taken
```

### `GET /auth/me/sessions`
List active Supabase sessions for this user.

```json
// Response 200
[{"id": "...", "created_at": "...", "last_active_at": "...", "ip": "192.168.1.1", "user_agent": "..."}]
```

### `POST /auth/me/sessions/logout-all`
Revoke all Supabase sessions except current one. Returns 200.

### `GET /auth/me/activity`
Paginated audit trail for current user.

| Query | Default | Description |
|-------|---------|-------------|
| skip | 0 | Offset |
| limit | 50 | Page size (max 100) |

### `GET /auth/me/mfa/status`
Return `{"enrolled": false}` (stub — always false).

### `POST /auth/me/mfa/enroll`
Return 200 with message "coming soon" (stub).

---

## 3. Password Management

### `POST /auth/change-password`
Verify current password, then update in Supabase. **Requires auth.**

```json
// Request
{"current_password": "...", "new_password": "min8chars"}
// Response 200
// 401 = wrong current password
```

### `POST /auth/forgot-password`
Trigger Supabase password-reset email. Returns 200 regardless (don't leak existence).

```json
// Request
{"email": "user@example.com"}
```

### `POST /auth/users/{id}/reset-password`
Force-reset another user's password. **Requires `admin` role.**

```json
// Request
{"new_password": "min8chars"}
```

### `POST /auth/users`
Create a new local user + Supabase account. **Requires `admin` role.**

```json
// Request
{"employee_id": 5, "username": "...", "password": "...", "role": "instructor"}
// Response 200 — returns user profile
```

---

## 4. Admin User Management (requires `system_admin` role)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/users` | List users (see filters below) |
| GET | `/admin/users/{id}` | Get single user |
| PATCH | `/admin/users/{id}` | Update role / active status |
| DELETE | `/admin/users/{id}` | Soft-deactivate user |
| POST | `/admin/users/invite` | Send invite email |

### `GET /admin/users`

| Query | Type | Description |
|-------|------|-------------|
| skip | int | Offset (default 0) |
| limit | int | Page size (default 50, max 100) |
| is_active | bool | Filter by active/inactive |
| role | string | Filter by role |
| q | string | Search username |

### `PATCH /admin/users/{id}`
```json
// Request — both fields optional
{"role": "admin", "is_active": true}
// 409 = cannot deactivate self
```

### `DELETE /admin/users/{id}`
No body. Soft-deletes: sets `is_active=false`, clears `supabase_uid`. Cannot delete your own account.

### `POST /admin/users/invite`
Create a user with pending status and generates an invite token.

```json
// Request
{"email": "new@example.com", "role": "instructor", "employee_id": 5}
// Response 200
{"id": 10, "username": "", "role": "instructor", "is_active": false, "invite_expires_at": "2026-05-21T00:00:00"}
```

---

## 5. Audit Reports (requires `system_admin` role)

### `GET /admin/audit/logins`

| Query | Type | Description |
|-------|------|-------------|
| user_id | int | Filter by user (optional) |
| from | ISO date | Start (optional) |
| to | ISO date | End (optional) |
| skip | int | Offset |
| limit | int | Page size |

### `GET /admin/audit/password-changes`
Same parameters as logins.

### `GET /admin/audit/failed-attempts`

| Query | Type | Description |
|-------|------|-------------|
| from | ISO date | **Required** start date |
| to | ISO date | End (optional) |
| skip | int | Offset |
| limit | int | Page size |

Audit log entry shape:

```json
{"id": 1, "user_id": 5, "event_type": "login_success", "ip_address": null, "user_agent": null, "details": null, "created_at": "2026-05-20T12:00:00"}
```

**Event types**: `login_success`, `login_failure`, `password_change`, `account_deactivated`, `account_reactivated`, `user_created`, `user_invited`, `invite_completed`, `email_changed`, `role_changed`

---

## Error Reference

| HTTP Status | Error Type | Typical Cause |
|-------------|-----------|---------------|
| 401 | AuthError | Invalid/expired JWT or wrong password |
| 403 | — | Wrong role (calls `require_system_admin` as `admin`) |
| 404 | NotFoundError | User not found |
| 409 | ConflictError | Duplicate username |
| 409 | BusinessRuleError | Deactivating own account |
| 422 | ValidationError | Short password, missing fields |
