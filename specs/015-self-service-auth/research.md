# Phase 0 Research: Self-Service Auth Features

## 1. Change Password — Verify Current Password

**Decision**: Use Supabase `sign_in_with_password(email, password)` to verify the current password before updating.

**Rationale**: Supabase stores password hashes; we cannot verify locally. The `sign_in_with_password` call validates credentials against Supabase Auth. If it succeeds, the current password is correct. Then call `admin.update_user_by_id(uid, {"password": new_password})` to set the new password.

**Edge case — deactivated user**: The `get_current_user` dependency already rejects deactivated users (returns 403). The change-password endpoint reuses this, matching spec FR-008.

**Alternatives considered**:
- Store a password hash locally — violates security best practices and duplicates Supabase.
- Use Supabase RPC — not needed; the standard auth API suffices.

## 2. Forgot Password — Supabase Reset Email

**Decision**: Call `supabase.auth.reset_password_email(email)` to trigger Supabase's built-in email flow.

**Rationale**: Supabase handles email delivery, token generation, and the reset form. We just need to trigger it. Return 200 for all cases (registered, unregistered, deactivated) to prevent email enumeration (FR-005).

**Edge case — no local User record**: Still return 200. Supabase may or may not send the email based on its own records, but our endpoint doesn't leak the distinction.

**Edge case — deactivated user**: Return 200 with no email sent. The endpoint never checks local `is_active` status since it doesn't look up the user at all.

## 3. Update Profile — Username Change

**Decision**: Update the local `User.username` field directly via the existing `update_user` repository function.

**Rationale**: Username has a DB unique constraint — duplicate detection is automatic via `ConflictError` propagation. The username is a local concept; the Supabase email binding (`username@system.local` or the raw username if it contains `@`) is generated at account creation and does NOT need to change (per spec assumptions).

**Edge case — username contains `@`**: Already handled by existing logic — usernames with `@` pass through directly. The update preserves the original Supabase email identity unchanged.

## 4. DTO Placement

**Decision**: Module-level DTOs in `app/modules/auth/schemas/auth_schemas.py` for service layer. HTTP-only request DTOs in `app/api/schemas/auth.py`.

**Rationale**: Follows the Two-Layer Schema Rule. Service methods accept module DTOs, routers accept HTTP DTOs and translate.

**DTOs needed**:

Module schemas:
- `ChangePasswordInput(BaseModel)` — `current_password: str`, `new_password: str` (min_length=12)
- `ForgotPasswordInput(BaseModel)` — `email: str`
- `UpdateProfileInput(BaseModel)` — `username: Optional[str] = None`

API schemas:
- `ChangePasswordRequest` — proxies `ChangePasswordInput` or duplicates fields
- `ForgotPasswordRequest` — proxies `ForgotPasswordInput`
- `UpdateProfileRequest` — proxies `UpdateProfileInput`

## 5. Service Method Signatures

- `change_password(self, user: User, current_password: str, new_password: str) -> None` — Raises `AuthError` on incorrect current password, `ValidationError` on short password.
- `forgot_password(self, email: str) -> None` — Triggers Supabase email, always returns gracefully. Never raises.
- `update_profile(self, user: User, dto: UpdateProfileInput) -> User` — Updates `username`, raises `ConflictError` on duplicate.

All methods follow the stateless pattern: each opens `with get_session()` internally.
