# Feature Specification: Advanced User & Auth Management

**Feature Branch**: `016-user-auth-management`
**Created**: 2026-05-20
**Status**: Draft
**Input**: Admin user management (CRUD), self-service enhancements, user registration/onboarding flows, session & security controls, audit & reporting.

## User Scenarios & Testing

### User Story 1 — Admin User Management (Priority: P1)

System administrators can list all users, view a single user by ID, update a user's role, toggle `is_active`, and soft-delete/deactivate accounts — all through the REST API.

**Why this priority**: Admins need the ability to manage users before any other auth feature has value. This is the foundation for all user lifecycle management.

**Independent Test**: `GET /api/v1/admin/users` returns paginated user list; `GET /api/v1/admin/users/{id}` returns user detail; `PATCH /api/v1/admin/users/{id}` modifies role/active status; `DELETE /api/v1/admin/users/{id}` deactivates or hard-deletes.

**Acceptance Scenarios**:

1. **Given** an authenticated system admin, **When** requesting `GET /api/v1/admin/users`, **Then** a paginated list of all users is returned with id, username, role, is_active, employee_id, last_login, created_at.

2. **Given** an authenticated system admin, **When** requesting `GET /api/v1/admin/users/{id}`, **Then** the full user record is returned.

3. **Given** an authenticated system admin, **When** requesting `PATCH /api/v1/admin/users/{id}` with `{"role": "admin"}` or `{"is_active": false}`, **Then** the user is updated and the new state is returned.

4. **Given** an authenticated system admin, **When** requesting `DELETE /api/v1/admin/users/{id}`, **Then** the user is soft-deleted (is_active=false) and the Supabase identity is removed. Returns 200.

5. **Given** an unauthenticated request, **When** hitting any admin user endpoint, **Then** 401 is returned.

6. **Given** a non-admin authenticated user, **When** hitting any admin user endpoint, **Then** 403 is returned.

7. **Given** that an admin tries to deactivate their own account, **When** sending `PATCH /api/v1/admin/users/self` with `{"is_active": false}`, **Then** the request is rejected with 409 (cannot deactivate yourself).

---

### User Story 2 — Self-Service Profile Enhancement (Priority: P2)

Authenticated users can change their own email (update Supabase email binding and local record) and view their session/activity history.

**Why this priority**: Allows users to self-manage their account after admin management is in place. Reduces support burden.

**Independent Test**: `PATCH /api/v1/auth/me` extended to support email changes; `GET /api/v1/auth/me/sessions` returns session history.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** requesting `PATCH /api/v1/auth/me` with `{"email": "new@example.com"}`, **Then** the Supabase email is updated via `admin.update_user_by_id` and the local email binding reference is updated.

2. **Given** an authenticated user, **When** requesting `GET /api/v1/auth/me/sessions`, **Then** a list of recent login sessions (timestamp, IP, user agent) is returned.

3. **Given** an authenticated user, **When** requesting `GET /api/v1/auth/me/activity`, **Then** a list of login activity events (login, logout, password change) is returned.

4. **Given** an unauthenticated request to any self-service endpoint, **Then** 401 is returned.

---

### User Story 3 — User Registration & Onboarding (Priority: P2)

Admins can invite new users via email invite flow. Prospective users can self-register with role selection (subject to admin approval if needed).

**Why this priority**: Streamlines the onboarding process for new employees and reduces manual account creation overhead.

**Independent Test**: `POST /api/v1/auth/invite` sends an invite email; user completes registration via invite link.

**Acceptance Scenarios**:

1. **Given** an authenticated admin, **When** requesting `POST /api/v1/auth/invite` with `{"email": "new@example.com", "role": "admin"}`, **Then** an invite email is sent with a one-time registration link. The user record is created with `is_active=false` and a temporary `invite_token`.

2. **Given** a prospective user with a valid invite token, **When** requesting `POST /api/v1/auth/register` with `{"token": "...", "username": "...", "password": "..."}`, **Then** the account is activated and the user can log in.

3. **Given** an expired or invalid invite token, **When** requesting registration, **Then** 401 is returned with "Invalid or expired invite token."

---

### User Story 4 — Session & Security Controls (Priority: P3)

Users can view their active sessions and force-logout all sessions. MFA setup is stubbed for future implementation.

**Why this priority**: Security features that enhance account protection, but are less critical than basic user management and onboarding.

**Independent Test**: `GET /api/v1/auth/me/sessions/active` returns active sessions; `POST /api/v1/auth/me/sessions/logout-all` invalidates all sessions.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** requesting `GET /api/v1/auth/me/sessions/active`, **Then** a list of active Supabase sessions is returned.

2. **Given** an authenticated user, **When** requesting `POST /api/v1/auth/me/sessions/logout-all`, **Then** all Supabase sessions for that user are revoked, requiring re-login.

3. **Given** an authenticated user, **When** requesting `GET /api/v1/auth/me/mfa/status`, **Then** the current MFA enrollment status is returned (enrolled/not-enrolled).

4. **Given** an authenticated user, **When** requesting `POST /api/v1/auth/me/mfa/enroll`, **Then** MFA enrollment is initiated (stubbed — returns "Feature coming soon" for v1).

---

### User Story 5 — Audit & Reporting (Priority: P3)

System logs for password changes, login history per user, and failed authentication attempts are visible to admins.

**Why this priority**: Compliance and security monitoring. Valuable but not blocking for user management or onboarding.

**Independent Test**: `GET /api/v1/admin/audit/logins` returns login history; `GET /api/v1/admin/audit/password-changes` returns password change log.

**Acceptance Scenarios**:

1. **Given** an authenticated admin, **When** requesting `GET /api/v1/admin/audit/logins?user_id={id}&from={date}&to={date}`, **Then** a paginated list of login events is returned with username, timestamp, IP, success/failure.

2. **Given** an authenticated admin, **When** requesting `GET /api/v1/admin/audit/password-changes?user_id={id}`, **Then** a list of password change events is returned with timestamp and changed-by info.

3. **Given** an authenticated admin, **When** requesting `GET /api/v1/admin/audit/failed-attempts?from={date}`, **Then** a list of failed login attempts is returned.

---

### Edge Cases

- What happens when an admin tries to delete a user that has active enrollments or linked records?
- How does the system handle deleting the last system_admin (prevent total lockout)?
- What happens when email change conflicts with an existing Supabase email?
- How does invite token expiry work? What is the TTL?
- What happens when self-registration username conflicts with an existing username?
- How are failed login attempts tracked — in memory or persistent storage?
- What happens to linked employee records when a user is deactivated?

## Requirements

### Functional Requirements

- **FR-001**: System MUST allow admins to list, read, update, and deactivate users via REST API.
- **FR-002**: System MUST prevent self-deactivation (admin cannot deactivate own account).
- **FR-003**: System MUST allow authenticated users to change their own email address.
- **FR-004**: System MUST log all successful and failed login attempts.
- **FR-005**: System MUST log all password changes with user identity and timestamp.
- **FR-006**: System MUST support an invite-based registration flow with one-time tokens.
- **FR-007**: System MUST allow users to view and revoke their active sessions.
- **FR-008**: System MUST prevent email enumeration in all user-facing endpoints.
- **FR-009**: System MUST require `system_admin` role for admin management endpoints.
- **FR-010**: System MUST soft-delete users (set is_active=false) rather than hard-delete by default, with Supabase identity cleanup.
- **FR-011**: System MUST provide paginated audit log endpoints for login history and password changes.
- **FR-012**: System MUST reject registration with expired or invalid invite tokens.

### Key Entities

- **User**: Extended to support `email` field (nullable, stored independently of Supabase binding). Add `deleted_at` timestamp for soft-delete tracking. Add `invite_token` and `invite_expires_at` for registration flow.
- **AuditLog**: New entity to track login events, password changes, failed attempts. Fields: `id`, `user_id` (nullable), `event_type` (login_success, login_failure, password_change, account_deactivated, etc.), `ip_address`, `user_agent`, `timestamp`, `details` (JSON).
- **UserSession**: New entity or view of Supabase sessions. Track `user_id`, `supabase_session_id`, `created_at`, `last_active_at`, `ip_address`, `user_agent`, `is_active`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Admin can complete full user lifecycle management (list, read, update, deactivate) in under 5 API calls.
- **SC-002**: User can change their own email address in under 3 API calls.
- **SC-003**: Audit log captures 100% of login attempts (success + failure).
- **SC-004**: Invite-based registration completes in under 30 seconds from email receipt.
- **SC-005**: All new endpoints have test coverage for success + error paths (min 3 tests per endpoint).

## Assumptions

- MFA will be stubbed in v1 — actual TOTP/SMS enrollment deferred to future iteration.
- Supabase sessions API (`list_sessions`, `sign_out_all_sessions`) is available for session management.
- Audit logging uses a new DB table (`audit_logs`) — existing notification logs are not reused for this purpose.
- Invite tokens are JWTs with a configurable TTL (default 24 hours).
- Email changes require Supabase admin API (`admin.update_user_by_id`) — the user's Supabase email identity is the source of truth.
- Hard-delete is never exposed via API; all deletes are soft-deletes (is_active=false). Supabase identity cleanup happens synchronously on deactivation.
- The `username` field remains the primary local identifier; `email` is an optional additional field for contact purposes (not the Supabase binding).
