# Feature Specification: Self-Service Auth Features

**Feature Branch**: `015-self-service-auth`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: Change password, forgot password, and profile update endpoints for auth module

## User Scenarios & Testing

### User Story 1 — Change Own Password (Priority: P1)

As an authenticated user, I want to change my own password by providing my current password and a new password so that I can rotate my credentials without administrator involvement.

**Why this priority**: Self-service password change is the most requested auth feature and reduces admin burden.

**Independent Test**: Call `POST /api/v1/auth/change-password` with valid current + new password — expect 200.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they call `POST /api/v1/auth/change-password` with correct `current_password` and a valid `new_password` (≥12 chars), **Then** the password is updated in Supabase and the endpoint returns 200.

2. **Given** an authenticated user, **When** they call `POST /api/v1/auth/change-password` with an incorrect `current_password`, **Then** the endpoint returns 401.

3. **Given** an authenticated user, **When** they call `POST /api/v1/auth/change-password` with a `new_password` shorter than 12 characters, **Then** the endpoint returns 422 with a validation error.

4. **Given** a deactivated user, **When** they attempt to change their password, **Then** the endpoint returns 403.

---

### User Story 2 — Forgot Password / Reset Flow (Priority: P2)

As a user who has forgotten their password, I want to request a password reset email via Supabase's built-in flow so that I can regain access to my account without administrator help.

**Why this priority**: Reduces support tickets for password resets.

**Independent Test**: Call `POST /api/v1/auth/forgot-password` with a registered email — expect 200.

**Acceptance Scenarios**:

1. **Given** a registered user email, **When** `POST /api/v1/auth/forgot-password` is called with that email, **Then** Supabase's password reset email is triggered and the endpoint returns 200 with a success message.

2. **Given** an unregistered email, **When** `POST /api/v1/auth/forgot-password` is called, **Then** the endpoint returns 200 (no email sent, but no information leakage about which emails are registered).

3. **Given** a deactivated user's email, **When** `POST /api/v1/auth/forgot-password` is called, **Then** the endpoint returns 200 (same response as unregistered to prevent information leakage).

---

### User Story 3 — Update Own Profile (Priority: P2)

As an authenticated user, I want to update my own profile fields (username, display name) so that I can keep my account information current.

**Why this priority**: Users should manage their own profile without admin intervention.

**Independent Test**: Call `PATCH /api/v1/auth/me` with updated fields — expect 200 with updated `UserPublic`.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they call `PATCH /api/v1/auth/me` with a new `username`, **Then** the username is updated in the local database and the endpoint returns the updated `UserPublic`.

2. **Given** an authenticated user, **When** they call `PATCH /api/v1/auth/me` with a username that already exists, **Then** the endpoint returns 409 Conflict.

3. **Given** an deactivated user, **When** they attempt to update their profile, **Then** the endpoint returns 403.

---

### Edge Cases

- **Supabase password update succeeds but local `last_login` stamp fails**: Service returns 200 (password change is the critical operation).
- **Forgot password for email with no local `User` record**: Returns 200 to prevent email enumeration attacks. Supabase handles whether to send email based on its own records.
- **Username update conflicts with Supabase email identity**: Username may serve as the Supabase email (`username@system.local`). Changing username may require Supabase email update too, or the username change should be restricted to only the local `User` record.
- **Concurrent profile updates**: Last-write-wins for username changes (DB unique constraint catches duplicates).

## Requirements

### Functional Requirements

- **FR-001**: System MUST allow authenticated users to change their password via `POST /api/v1/auth/change-password` with `current_password` and `new_password` fields.
- **FR-002**: System MUST validate `new_password` against `MIN_PASSWORD_LENGTH` (12 chars).
- **FR-003**: System MUST verify `current_password` via Supabase `sign_in_with_password` before allowing the change.
- **FR-004**: System MUST allow users to request a password reset email via `POST /api/v1/auth/forgot-password` with an `email` field.
- **FR-005**: System MUST NOT reveal whether an email is registered — return 200 for both registered and unregistered emails.
- **FR-006**: System MUST allow authenticated users to update their username via `PATCH /api/v1/auth/me` with updatable fields.
- **FR-007**: System MUST reject duplicate usernames with 409 Conflict.
- **FR-008**: System MUST reject all self-service operations for deactivated (`is_active = False`) users with 403 Forbidden.

### Key Entities

- **User** (existing): Local DB mapping of Supabase identity. Fields relevant to this feature: `id`, `username` (updatable), `supabase_uid`, `is_active` (guard), `role`, `last_login`.
- **ChangePasswordRequest** (new): Input DTO with `current_password: str` and `new_password: str` (min_length=12).
- **ForgotPasswordRequest** (new): Input DTO with `email: str`.
- **UpdateProfileRequest** (new): Input DTO with optional `username: str`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can change their own password in under 3 API calls (login → change → verify with new password).
- **SC-002**: Password reset requests do not reveal email registration status — same response for registered, unregistered, and deactivated users.
- **SC-003**: Profile updates reflect immediately — subsequent `GET /api/v1/auth/me` returns the updated data.
- **SC-004**: All three endpoints have at least 90% test coverage for success and error paths.

## Assumptions

- Password reset email delivery is handled entirely by Supabase's built-in email service — no custom email template needed.
- `username` is the only updatable profile field in scope for this feature. `employee_id`, `role`, and `is_active` remain admin-only.
- Changing username does not require updating the Supabase email identity (username is a local concept; `email_binding` for Supabase is generated at creation).
- The existing `get_current_user` dependency is reused for authentication on all three endpoints.
- No rate limiting is applied to the forgot-password endpoint in this iteration.
