# Quickstart: Self-Service Auth Features

## What Changes

| File | Change |
|------|--------|
| `app/modules/auth/schemas/auth_schemas.py` | Add `ChangePasswordInput`, `ForgotPasswordInput`, `UpdateProfileInput` |
| `app/modules/auth/services/auth_service.py` | Add `change_password()`, `forgot_password()`, `update_profile()` |
| `app/api/schemas/auth.py` | Add `ChangePasswordRequest`, `ForgotPasswordRequest`, `UpdateProfileRequest` |
| `app/api/routers/auth_router.py` | Add 3 new endpoint functions |
| `tests/test_auth.py` | Add 3 new test classes covering success + error paths |

## New Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/change-password` | `get_current_user` | Change own password |
| POST | `/api/v1/auth/forgot-password` | None (public) | Trigger reset email |
| PATCH | `/api/v1/auth/me` | `get_current_user` | Update own profile |

## Verification

```bash
pytest tests/test_auth.py -v
python run_api.py
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "old", "new_password": "newstrongpwd123"}'
```
