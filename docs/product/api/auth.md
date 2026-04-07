# Authentication API Reference

Base path: `/api/v1/auth`

---

## 🔐 Global Authentication
Most API requests MUST include a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

---

## Schemas

### UserPublic
```json
{
  "id": 1,
  "employee_id": 1,
  "username": "admin_user",
  "email": "admin@techno.com",
  "role": "admin",
  "is_active": true,
  "last_login": "2026-04-03T10:30:00"
}
```

### LoginRequest
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

### TokenResponse
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "employee_id": 1,
    "username": "admin_user",
    "email": "admin@techno.com",
    "role": "admin",
    "is_active": true,
    "last_login": "2026-04-03T10:30:00"
  }
}
```

### RefreshRequest
```json
{
  "refresh_token": "string (required)"
}
```

### CreateUserRequest
```json
{
  "employee_id": "integer (required)",
  "username": "string (required)",
  "password": "string (required, min 8 chars)",
  "role": "string (required) - admin or system_admin"
}
```

### ResetPasswordRequest
```json
{
  "new_password": "string (required, min 8 chars)"
}
```

### ApiResponse (Envelope)
```json
{
  "success": true,
  "data": {},
  "message": null
}
```

---

## Endpoints

### 1. Login with Email and Password
**POST** `/api/v1/auth/login`

**Request Body:** `LoginRequest`

**Response (200):** `TokenResponse`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Validates credentials against Supabase Auth
- Returns JWT access token and refresh token
- Includes user profile in response

---

### 2. Refresh Supabase JWT
**POST** `/api/v1/auth/refresh`

**Request Body:** `RefreshRequest`

**Response (200):** `TokenResponse`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Uses refresh token to get new access token
- Returns updated tokens with extended expiry

---

### 3. Logout user
**POST** `/api/v1/auth/logout`

**Response (200):** `ApiResponse<None>`

**Notes:**
- Invalidates the current session/token
- Client should clear stored tokens

---

### 4. Get current authenticated user
**GET** `/api/v1/auth/me`

**Response (200):** `UserPublic`

**Notes:**
- Returns profile of currently authenticated user
- Requires valid Bearer token

---

### 5. Create a new login user
**POST** `/api/v1/auth/users`

**Request Body:** `CreateUserRequest`

**Response (200):** `ApiResponse<UserPublic>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Creates Supabase Auth user + local user record
- Links user to employee record via `employee_id`
- Requires admin role

---

### 6. Force reset a user's password
**POST** `/api/v1/auth/users/{user_id}/reset-password`

**Path Parameters:**
- `user_id` - integer (required)

**Request Body:** `ResetPasswordRequest`

**Response (200):** `ApiResponse<None>`

**Error Response (422):** `HTTPValidationError`

**Notes:**
- Admin-only endpoint
- Forces password reset via Supabase Admin API
- User must be notified of new password
