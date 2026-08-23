# API Contract: Employee Lifecycle (Delete / Restore / Deleted-View)

**Feature**: 040-employee-soft-delete | **Date**: 2026-08-24
All routes live under `/api/v1/hr` and require `Authorization: Bearer <admin-jwt>`.
Envelope: `{success, data, message}` on success; `{success:false, error, message}` on failure
(error = typed exception class name per AGENTS.md).

---

## DELETE /employees/{employee_id}

Soft-deletes the employee. Never removes rows. Blocks the linked login account in the
same transaction when one exists.

**Responses**

| Status | When | Body |
|--------|------|------|
| 200 | Deleted (or already-deactivated account — idempotent block) | `{"success": true, "data": true, "message": "Employee deleted"}` |
| 401 | Missing/invalid credentials | `{"success": false, "error": "Unauthorized", "message": "..."}` |
| 403 | Authenticated non-admin | `{"success": false, "error": "HTTPError", "message": "Access denied..."}` |
| 404 | Unknown ID **or** already-deleted employee | `{"success": false, "error": "NotFoundError", "message": "Employee {id} not found"}` |

**Guarantees**: single transaction (block + stamp); historical references untouched;
`deleted_by` always the acting admin's local user id.

---

## POST /employees/{employee_id}/restore

Clears deletion markers. Does NOT reactivate a blocked login account.

**Responses**

| Status | When | Body |
|--------|------|------|
| 200 | Restored | `{"success": true, "data": {EmployeeRead}, "message": "Employee restored"}` — full record with `deleted_at`/`deleted_by` null again |
| 401 / 403 | As above | standard envelopes |
| 404 | Unknown ID | `NotFoundError` envelope |
| 409 | Employee is not deleted | `{"success": false, "error": "ConflictError", "message": "Employee {id} is not deleted"}` |
| 409 | Restore would collide with any LIVE employee's email/national_id/phone (possible after re-hire) | `{"success": false, "error": "ConflictError", "message": "email: already in use; phone: already in use"}` — ALL colliding fields named together |

---

## GET /employees?include_deleted=true

Existing list endpoint with a new optional flag (default `false` → unchanged behavior).

**Query params**: `page`, `page_size`, `include_deleted` (bool, default false).

**Responses**

| Status | When | Body |
|--------|------|------|
| 200 | Success | `{"success": true, "data": {"items": [EmployeeRead...], "total": N, "page": P, "page_size": S}}` — when flagged, deleted rows included with populated `deleted_at`/`deleted_by`; live rows carry them as `null` |
| 403 | Non-admin attempting the flag (or the endpoint at all) | standard rejection — flag never widens access |

**EmployeeRead additions** (both nullable, present for all consumers of this DTO):
`deleted_at: datetime | null`, `deleted_by: int | null`.

---

## Error-mapping notes

- No router-level try/except: typed exceptions flow to global handlers
  (`NotFoundError`→404, `ConflictError`→409, `BusinessRuleError`→409).
- IntegrityError translation layer unchanged: partial indexes reuse the original
  constraint names (`uq_employees_email`, `_national_id`, `_phone`), so concurrent
  duplicate inserts still map to field-named 409s exactly as in feature 039.
