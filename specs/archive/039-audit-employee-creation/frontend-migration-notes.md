# Frontend Migration Notes: Staff Onboarding Endpoint Changes

**Feature**: 039-audit-employee-creation | **Date**: 2026-08-23
**Audience**: Frontend developers consuming the HR staff endpoints.

No paths, methods, auth rules, or success-response shapes changed. What changed is
failure behavior, one input rule, and data completeness. Check your client code
against each item below.

---

## 1. Password minimum raised: 8 → 12 characters

`POST /api/v1/hr/employees/{id}/create-account`

```json
// Request body — password must now be >= 12 chars (was 8)
{ "email": "user@center.com", "password": "Str0ngPass!23", "role": "admin" }
```

- Shorter passwords now return **422** instead of being accepted.
- Update any client-side password strength meter / validation to require 12.
- Invalid email + short password are rejected **together in one 422** naming both fields.

```json
{
  "success": false,
  "error": "ValidationError",
  "message": "email: value is not a valid email address; password: String should have at least 12 characters"
}
```

## 2. Partial employee updates now allowed

`PUT /api/v1/hr/employees/{id}`

- Previously required the full create-style body; missing fields → 422.
- **Now accepts any subset of fields** — only provided keys are applied.
- Existing clients sending full bodies keep working unchanged.

```json
// Both are valid now:
{ "is_active": false }
{ "full_name": "New Name", "phone": "+201001234567" }
```

## 3. Error names in the envelope changed

Applies to ALL four staff endpoints. If your code switches on the `error` string,
update the values:

| Situation | Old `error` value | New `error` value |
|-----------|-------------------|-------------------|
| Duplicate/conflict | `"Conflict"` | `"ConflictError"` |
| Record not found | `"NotFound"` | `"NotFoundError"` |
| Validation | `"ValidationError"` | unchanged |
| Provisioning unavailable / midway failure | `"Conflict"` (misleading) | `"BusinessRuleError"` |

HTTP status codes are unchanged (404/409/422). Prefer branching on status code +
`error` class name as documented in AGENTS.md.

## 4. Failure messages are aggregated and field-named

Duplicate submissions report EVERY colliding field at once instead of one per attempt:

```json
{
  "success": false,
  "error": "ConflictError",
  "message": "national_id: already in use; phone: already in use"
}
```

You can surface `message` directly to admins — no more fix-one-retry-discover-next loops.

## 5. Provisioning failure semantics (important for retry UX)

`POST .../create-account` failures are now honest:

| Condition | Status | `error` | Message pattern |
|-----------|--------|---------|-----------------|
| Email already registered | 409 | `ConflictError` | `email: already registered` |
| Employee already has account | 409 | `ConflictError` | `Employee {id} already has an account` |
| Identity provider unreachable / other remote failure | 409 | `BusinessRuleError` | contains `nothing was created` + `retry` |
| Local-side failure after remote user created | 409 | `BusinessRuleError` | contains `nothing was created` + `safe to retry` |

Retry guidance for UIs: on `BusinessRuleError`, show a transient-error state with a
retry button — the system guarantees zero partial records, so retrying is always safe.

## 6. Staff accounts overview is complete

`GET /api/v1/hr/staff-accounts`

- Freshly provisioned accounts now **appear immediately** (a link bug previously
  hid them from the list).
- `email`, `job_title`, `created_at` now carry real values — remove any UI
  workarounds that assumed permanent blanks/nulls.
- Field names themselves are unchanged.

---

## Quick client checklist

- [ ] Password inputs enforce min 12 chars on the provisioning form
- [ ] No `error === "Conflict"` / `"NotFound"` string comparisons remain on HR calls
- [ ] PUT employee forms may send only changed fields (optional simplification)
- [ ] Duplicate-error rendering handles multiple `field: reason` pairs in one message
- [ ] Provisioning retry button treats `BusinessRuleError` as safe-to-retry
- [ ] Removed any placeholder handling for null email/job_title/created_at in accounts table

---

## Post-analysis additions (2026-08-23)

Hardening pass after the audit review — **no request/response shapes changed**.
Status codes and envelopes below are exactly as documented above.

### Faster, cleaner 404 on provisioning

`POST .../create-account` for an unknown employee ID now fails **before** contacting
the identity provider. Clients see the same `404` + `"NotFoundError"` envelope as
before — just immediately, with no window where a retry could hit a half-provisioned
state.

### Second-account refusal is guaranteed behavior

`Employee {id} already has an account` (`409 ConflictError`) is now locked by an
automated test proving the identity provider is never contacted on refusal. UIs can
reliably render it as a permanent state ("already provisioned"), not a transient error.

### Auth rejections are uniform

All HR endpoints return the standard `401 {"error": "Unauthorized"}` envelope for
missing or invalid credentials (verified endpoint-by-endpoint). Inactive accounts
get `403`. Nothing new to implement — this confirms existing assumptions.

### Internal-only changes (no client impact)

Repository-level typing refactors and the project constitution update (v1.1.2) do not
alter any endpoint, payload, status code, or error name.
