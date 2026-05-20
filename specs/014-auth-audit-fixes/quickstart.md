# Quickstart: Auth Module Bug Fixes & Audit Remediation

## Scope

This is a bug-fix and cleanup feature — no new endpoints, no migration steps, no configuration changes.

## What Changes

| File | Change | Risk |
|------|--------|------|
| `app/modules/auth/services/auth_service.py` | Remove `get_users_for_employee`; add Supabase orphan cleanup; add inactive check | Low (method has no callers; additions are guard code) |
| `app/modules/auth/repositories/auth_repository.py` | Remove `update_user`; change `create_user` param from `dict` → `UserCreate` | Low |
| `app/modules/auth/repositories/__init__.py` | Remove `update_user` export | None |
| `app/modules/auth/schemas/auth_schemas.py` | Remove `PasswordResetBody`, `UserRead`; add `ConfigDict` | None |
| `app/modules/auth/schemas/__init__.py` | Remove dead DTO exports | None |
| `app/modules/auth/models/auth_models.py` | Fix `is_admin` property to use enum values | None |
| `app/modules/auth/__init__.py` | Remove dead aliases/exports | Low |
| `app/api/routers/auth_router.py` | Fix import path; remove debug prints; fix logout error handling | Low |
| `app/api/dependencies.py` | Fix `AuthService` import path | Low |
| `tests/test_auth.py` | Add 5+ new test functions; fix 2 broken tests | None (test-only) |

## Verification

```bash
# Run all tests
pytest tests/ -v

# Run auth-specific tests
pytest tests/test_auth.py -v

# Verify no dead code remains
grep -r "get_users_for_employee\|update_user\|PasswordResetBody\|UserRead" app/modules/auth/ --include="*.py"

# Verify no dict types in repo
grep -r "-> dict" app/modules/auth/repositories/ --include="*.py"

# Verify no direct service imports
grep -r "from app.modules.auth.services" app/api/ --include="*.py"

# Start server to verify imports
python run_api.py

# Coverage
pytest tests/ -v --cov=app.modules.auth --cov-report=term-missing
```
