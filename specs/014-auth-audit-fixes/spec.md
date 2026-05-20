# Feature Specification: Auth Module Bug Fixes & Audit Remediation

**Feature Branch**: `014-auth-audit-fixes`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: User description: "fixing the auth audit findings"

## User Scenarios & Testing

### User Story 1 — Fix Runtime Bugs in Auth Module (Priority: P1)

As a system administrator, I want the auth module's runtime bugs fixed so that user accounts are created reliably without orphaned Supabase identities, and no sensitive data leaks to server logs.

**Why this priority**: Runtime bugs directly impact system reliability and security. Orphaned Supabase identities and email leakage are the highest-severity findings.

**Independent Test**: Each bug fix can be verified independently through its specific acceptance scenario.

**Acceptance Scenarios**:

1. **Given** an employee does not yet have a login, **When** `link_employee_to_new_user` fails during local DB insert after Supabase user creation, **Then** the Supabase identity is cleaned up and no orphan remains.

2. **Given** a user attempts to log in, **When** credentials are invalid, **Then** no email address is printed to server stdout.

3. **Given** the login endpoint executes, **When** authentication succeeds, **Then** the response contains a valid `TokenResponse` with `UserPublic` data, and `last_login` is updated.

---

### User Story 2 — Secure Password Reset for Inactive Users (Priority: P2)

As a system administrator, I want password resets to respect account active status so that deactivated users cannot have their passwords reset, preventing accidental reactivation of access.

**Why this priority**: This is a security gap that could allow bypassing account deactivation.

**Independent Test**: Can be fully tested by calling the reset-password endpoint on a deactivated user and verifying it returns a business rule error.

**Acceptance Scenarios**:

1. **Given** a user has `is_active = False`, **When** an admin calls `POST /api/v1/auth/users/{id}/reset-password`, **Then** the system returns a `409 Conflict` with a `BusinessRuleError` message indicating the user is inactive.

2. **Given** a user has `is_active = True`, **When** an admin calls `POST /api/v1/auth/users/{id}/reset-password`, **Then** the password is successfully reset.

---

### User Story 3 — Remove Dead Code & Fix Architecture Violations (Priority: P2)

As a developer, I want the auth module's dead code removed and architecture violations fixed so that the codebase stays clean, maintainable, and compliant with project conventions.

**Why this priority**: Dead code creates confusion and maintenance burden. Architecture violations break import dependency chains.

**Independent Test**: Can be verified by grepping for removed symbols and checking that no `from app.api.schemas` or `-> dict` exist in the module, and that all imports use the module root.

**Acceptance Scenarios**:

1. **Given** the auth module, **When** searching for `get_users_for_employee`, `update_user`, `PasswordResetBody`, and `UserRead`, **Then** no definitions remain in module code.

2. **Given** the auth module, **When** checking for `-> dict` return types in `repositories/auth_repository.py`, **Then** `create_user` accepts a typed DTO instead of `dict`.

3. **Given** `auth_router.py` and `dependencies.py`, **When** checking imports for `AuthService`, **Then** they import from `app.modules.auth` (module root), not from `app.modules.auth.services.auth_service`.

4. **Given** all DTOs in `app/modules/auth/schemas/`, **When** checking for `model_config`, **Then** all DTOs used for ORM conversion have `ConfigDict(from_attributes=True)`.

---

### User Story 4 — Add Missing Auth Tests (Priority: P2)

As a developer, I want comprehensive test coverage for all auth endpoints so that regressions are caught automatically and the module's behavior is well-documented through tests.

**Why this priority**: Currently only `GET /api/v1/auth/me` and general auth-required endpoint tests exist. Login, create user, refresh, logout, and reset-password endpoints have zero coverage.

**Independent Test**: Each test file can be run independently via `pytest tests/test_auth.py -v`.

**Acceptance Scenarios**:

1. **Given** the test suite, **When** running auth tests, **Then** at least 90% of auth endpoint code paths are covered by tests.

2. **Given** a test for `POST /api/v1/auth/login`, **When** called with valid credentials, **Then** it returns 200 with access/refresh tokens and user data.

3. **Given** a test for `POST /api/v1/auth/login`, **When** called with invalid credentials, **Then** it returns 401.

4. **Given** a test for `POST /api/v1/auth/users`, **When** called by an admin with valid employee data, **Then** it returns 200 with user data.

5. **Given** a test for `POST /api/v1/auth/users/{id}/reset-password`, **When** called by an admin, **Then** it returns 200 on success.

6. **Given** the test in `tests/test_auth.py:104` (`test_hr_employees_requires_auth`), **When** executed, **Then** it actually asserts the response status code.

7. **Given** the test in `tests/test_auth.py:106` (`test_enrollments_requires_auth`), **When** executed, **Then** it uses the correct URL prefix (`/api/v1/enrollments`).

---

### User Story 5 — Fix `User.is_admin` Property (Priority: P3)

As a developer, I want the `is_admin` property on the `User` model to reference enum values instead of hardcoded strings so that it stays in sync with the role definitions.

**Why this priority**: Low risk since the string values match the enum, but violates DRY and could break silently if enum values are ever updated.

**Independent Test**: Can be verified by checking the property references `UserRole.ADMIN.value` and `UserRole.SYSTEM_ADMIN.value`.

**Acceptance Scenarios**:

1. **Given** the `User` model, **When** checking the `is_admin` property, **Then** it uses `UserRole.ADMIN.value` and `UserRole.SYSTEM_ADMIN.value` instead of string literals `"admin"` and `"system_admin"`.

---

### User Story 6 — Fix Logout Error Handling (Priority: P3)

As a system administrator, I want the logout endpoint to log errors instead of silently swallowing them so that operational issues with Supabase session invalidation can be diagnosed.

**Why this priority**: Silent `except: pass` hides real errors that could indicate connectivity or authentication issues.

**Independent Test**: Can be verified by inspecting the logout endpoint handler for proper error logging.

**Acceptance Scenarios**:

1. **Given** the logout endpoint, **When** Supabase `sign_out` raises an exception, **Then** the exception is logged via the application logger instead of silently swallowed.

---

### Edge Cases

- **Supabase identity creation succeeds but local DB insert fails**: The Supabase user is deleted to prevent orphaned identities.
- **Concurrent user creation for same employee**: Two simultaneous `link_employee_to_new_user` calls for the same employee — the second detects the duplicate after the first commits and raises `ConflictError`.
- **Password reset on deactivated user**: Returns `409 BusinessRuleError` instead of resetting the password.
- **Login with correct Supabase JWT but missing local `User` record**: Returns 401 "User authenticated but no local identity found".
- **Logout without a Bearer token**: Returns 200 with no-op behavior (no exception).
- **Empty/nil username used as Supabase email binding**: The `@system.local` suffix ensures a valid email format for Supabase.

## Requirements

### Functional Requirements

- **FR-001**: System MUST clean up Supabase identity when local DB user creation fails in `link_employee_to_new_user`.
- **FR-002**: System MUST NOT print user email addresses to stdout during login attempts.
- **FR-003**: System MUST reject password reset requests for deactivated (`is_active = False`) users with a business rule error.
- **FR-004**: System MUST ensure `create_user` repository function accepts a typed DTO instead of `dict`.
- **FR-005**: System MUST use `UserRole` enum values instead of hardcoded strings in `User.is_admin`.
- **FR-006**: System MUST log Supabase `sign_out` exceptions in the logout endpoint instead of silently swallowing them.
- **FR-007**: All auth module DTOs used for ORM conversion MUST include `model_config = ConfigDict(from_attributes=True)`.
- **FR-008**: `AuthService` MUST be imported from `app.modules.auth` (module root) in `auth_router.py` and `dependencies.py`.
- **FR-009**: Dead code (`get_users_for_employee`, `update_user`, `PasswordResetBody`, `UserRead`) MUST be removed.
- **FR-010**: Auth module MUST have tests covering `POST /api/v1/auth/login`, `POST /api/v1/auth/users`, `POST /api/v1/auth/users/{id}/reset-password`, `POST /api/v1/auth/refresh`, and `POST /api/v1/auth/logout`.
- **FR-011**: Tests that silently pass without assertions MUST be fixed (`test_hr_employees_requires_auth`, `test_enrollments_requires_auth`).

### Key Entities

- **User**: Local database mapping of a Supabase-authenticated identity. Key attributes: `id`, `supabase_uid` (unique), `username` (unique), `role` (admin/system_admin), `is_active`, `employee_id` (FK to employees), `last_login`.
- **Employee**: HR entity that a User can be linked to via `employee_id`. A User represents the login identity for an Employee.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 42 audit findings are resolved — zero remaining bugs, zero dead code items, zero constitution violations flagged for the auth module.
- **SC-002**: Auth endpoint test coverage increases from ~15% to >90% as measured by `pytest --cov=app.modules.auth`.
- **SC-003**: No user email addresses appear in server stdout during login flows.
- **SC-004**: Zero `-> dict` type annotations remain in `app/modules/auth/repositories/`.
- **SC-005**: Zero `from app.api.schemas` imports exist in `app/modules/auth/`.
- **SC-006**: All auth service method imports in routers/dependencies import from module root (`app.modules.auth`) — zero direct internal path imports.

## Assumptions

- The existing Supabase Auth integration (JWT validation via `get_supabase_anon()`) remains the authentication mechanism — no migration away from Supabase.
- DTO naming conventions follow the existing `{Operation}{Entity}Input` / `{Entity}{Qualifier}DTO` pattern per the architecture guide.
- Tests will use the existing `override_auth` fixture and mock JWT tokens to avoid depending on real Supabase.
- The `User` model's `employee_id` field will remain a non-unique FK (no DB-level unique constraint added) — the application-level check is considered sufficient for now.
- Minor DTO renames (`UserCreate -> UserCreateInput`, `UserPublic -> UserPublicDTO`) are included only if explicitly needed for constitution compliance; backward-compatible aliases are acceptable.
