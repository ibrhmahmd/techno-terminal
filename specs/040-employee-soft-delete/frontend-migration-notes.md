# HR Employees API — Soft Delete Contract (for Frontend)

Feature 040. All endpoints under `/api/v1`, all require
`Authorization: Bearer <token>` and the **admin** role.
Envelope is unchanged everywhere: `{ success, data, message }` /
`{ success: false, error, message }`.

## What changed (TL;DR)

1. **New** `DELETE /hr/employees/{id}` — soft-delete (record is hidden, not gone).
2. **New** `POST /hr/employees/{id}/restore` — bring it back.
3. **New** query flag on the list endpoint: `?include_deleted=true`.
4. Every employee read shape gains two always-present nullable fields:
   `deleted_at` / `deleted_by`.

No existing endpoint, path, or field was removed or renamed.

```ts
interface EmployeeMarkers {
  deleted_at: string | null; // ISO timestamp when soft-deleted
  deleted_by: number | null; // local user id of the deleting admin
}
```

---

## 1) Soft-delete an employee

```
DELETE /api/v1/hr/employees/{employee_id}
```

Response `200`:
```json
{ "success": true, "data": true, "message": "Employee deleted successfully." }
```

UI should immediately:
- remove them from every default list/lookup,
- treat any linked login as blocked (the account is deactivated server-side
  in the same step).

## 2) Restore a soft-deleted employee

```
POST /api/v1/hr/employees/{employee_id}/restore
```

Response `200` — the restored employee (`deleted_at`/`deleted_by` back to null):
```json
{ "success": true, "data": { "...employee fields...", "deleted_at": null, "deleted_by": null }, "message": "Employee restored successfully." }
```

Gotchas to surface in the UI:
- Restore does **not** unblock a linked login — that stays a separate admin action.
- If their identity was reused meanwhile (re-hire), restore is refused — see errors.

## 3) List with deleted rows (admin discovery view)

```
GET /api/v1/hr/employees?page=1&page_size=20            → live only (unchanged)
GET /api/v1/hr/employees?include_deleted=true           → live + deleted
```

Deleted rows come back fully populated plus markers:
```json
{ "id": 42, "full_name": "...", "deleted_at": "2026-08-24T10:15:00Z", "deleted_by": 3 }
```

Live rows always carry `"deleted_at": null, "deleted_by": null`.
Typical UI: an "include deleted" toggle + a "Restorable" badge/undo action on marked rows.

---

## Errors

| Scenario | Status | `error` | Message hint |
|---|---|---|---|
| Delete missing / already-deleted id | 404 | `NotFoundError` | "Employee {id} not found" |
| Restore unknown id | 404 | `NotFoundError` | "Employee {id} not found" |
| Restore an employee that isn't deleted | 409 | `ConflictError` | "{id} is not deleted" |
| Restore after identity re-use (re-hire) | 409 | `ConflictError` | names **every** colliding field, e.g. `national_id: already in use; phone: already in use` |
| Missing/invalid token | 401 | `Unauthorized` | standard envelope |

## Uniqueness semantics (why delete ≠ forever)

After deletion, the employee's `national_id`, `phone`, and `email` become
creatable again. Uniqueness among **live** employees is unchanged — creating a
duplicate of a live employee still returns a single aggregated `409` listing
all colliding fields at once.
