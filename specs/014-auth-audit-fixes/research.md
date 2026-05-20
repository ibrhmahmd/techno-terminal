# Phase 0 Research: Auth Module Bug Fixes & Audit Remediation

## 1. Orphaned Supabase Identity Cleanup

**Decision**: Wrap `link_employee_to_new_user` Supabase creation in try/except that calls `supabase.auth.admin.delete_user(supabase_uid)` on local DB failure.

**Rationale**: Supabase Admin API supports `delete_user` by UID. The local DB insert (`session.add` + `session.commit`) can fail due to constraint violations (duplicate username) or connectivity issues. The relatively short window between Supabase create and local commit makes this safe — if local fails, clean up Supabase.

**Alternatives considered**:
- Create local DB record first, then Supabase — rejected because Supabase validation (email format, duplicate check) runs first; if Supabase fails after local insert, we'd have an incomplete local record.
- Use a DB transaction to wrap both — not possible because Supabase is an external system.
- Use a background cleanup job — overkill; synchronous cleanup is simpler and sufficient.

## 2. Email Leakage in Login Endpoint

**Decision**: Remove both the `print(f"Login attempt: email={body.email}")` and the commented-out `print(f"Supabase URL: {settings.SUPABASE_URL}")`.

**Rationale**: The `print` is unreachable (after `raise`) and leaks PII. The commented line is noise. Both should be deleted.

## 3. Password Reset Inactive User Check

**Decision**: Add `if not user.is_active: raise BusinessRuleError(...)` to `force_reset_password` before the Supabase password update.

**Rationale**: The Supabase Admin API will happily reset any user's password regardless of local `is_active` status. The local check prevents accidental reactivation of deactivated accounts.

## 4. Typed DTO for Repository

**Decision**: Change `create_user(session, user_data: dict)` to `create_user(session, data: UserCreate)` — the existing `UserCreate` DTO from `app/modules/auth/schemas/auth_schemas.py` already has the correct shape.

**Rationale**: The DTO already exists and validates at input time. The repo was receiving `model_dump()` output — passing the DTO directly preserves type safety. Add `model_config = ConfigDict(from_attributes=True)` to `UserCreate` and `UserPublic`.

## 5. Direct Import Path Fix

**Decision**: Change `from app.modules.auth.services.auth_service import AuthService` → `from app.modules.auth import AuthService` in both `auth_router.py` and `dependencies.py`.

**Rationale**: Per constitution Article II — services must be imported from module root to maintain the import dependency chain. The `__init__.py` compatibility facade already exports `AuthService`.

## 6. Dead Code Deletion

**Decision**: Delete all 4 dead items:
- `get_users_for_employee` in service + `__init__.py` alias
- `update_user` in repository + `__init__.py` export
- `PasswordResetBody` in schemas
- `UserRead` in schemas

**Rationale**: Zero external callers confirmed via grep. Per constitution: "Delete dead code immediately — never migrate it."

## 7. Test Strategy

**Decision**: Use existing `override_auth` fixture for endpoint tests, mock Supabase via `unittest.mock.patch` for service-level tests.

**Rationale**:
- Auth endpoint tests don't need real Supabase — the `override_auth` fixture bypasses JWT validation.
- For `login` endpoint specifically, the test needs to mock `get_supabase_anon().auth.sign_in_with_password()` since login actually calls Supabase.
- For `create_login_user` endpoint, test needs to mock `get_supabase_admin().auth.admin.create_user()`.
- Existing test infrastructure (`TestClient`, `override_auth`, `mock_admin_headers`) is sufficient.

## 8. `User.is_admin` Property

**Decision**: Change string literals to `UserRole.ADMIN.value` and `UserRole.SYSTEM_ADMIN.value`.

**Rationale**: The enum is already imported in `auth_models.py` (via `ALL_ROLE_VALUES` from constants). Using `UserRole.ADMIN.value` keeps it in sync with the role definition.
