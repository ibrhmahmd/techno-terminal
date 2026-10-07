# Quickstart: Employee Soft Delete Verification

**Feature**: 040-employee-soft-delete

## Prerequisites

- Test DB reachable (`.env.test` auto-loaded under pytest via `config.py`)
- Schema current: `psql "$DATABASE_URL" -f db/schema.sql` (fresh) — or apply
  `db/migrations/079_employee_soft_delete.sql` to an existing DB
- Auth bypass fixtures: `override_auth` + `mock_admin_headers` (no real Supabase needed)

## Automated verification

```powershell
python -m pytest tests/test_hr_delete.py -v          # new lifecycle suite
python -m pytest tests/test_hr_audit_regressions.py -v  # incl. FR-007 probe-exclusion lock
python -m pytest tests/test_hr.py tests/test_hr_full.py tests/test_hr_audit_regressions.py tests/test_hr_delete.py -v  # full HR gate (SC-005)
```

Coverage map (FR → test):

| FR | Behavior | Where locked |
|----|----------|--------------|
| FR-001/005 | Delete stamps markers, preserves history, actor attributed | `test_delete_stamps_markers_and_preserves_history` |
| FR-002 | Hidden from lookup/lists/overview | `test_deleted_hidden_from_all_read_surfaces` |
| FR-003 | Linked login blocked same transaction | `test_deleting_provisioned_employee_blocks_login_row` |
| FR-004 | Double delete → 404 | `test_double_delete_returns_uniform_404` |
| FR-006/007 | Re-hire same identity triple succeeds; probes skip deleted | `test_rehire_with_deleted_identity_succeeds`, regression extension |
| FR-009/010 | Restore clears markers; live-restore 409; unknown 404; collision 409 names all fields | restore test class |
| FR-011 | Restore leaves account blocked | `test_restore_keeps_account_blocked` |
| FR-012 | Admin-only + uniform 401s | auth test class |
| FR-014 | include_deleted flag semantics + non-admin rejection | flag test class |

## Manual walk (optional)

1. Create employee A with identity triple X.
2. Provision account for A (`POST /{id}/create-account`) — optional path.
3. `DELETE /api/v1/hr/employees/{A}` → 200 `data:true`.
4. `GET /{A}` → 404 · list → absent · staff-accounts → absent.
5. `GET /api/v1/hr/employees?include_deleted=true` → A present with markers set.
6. Re-create employee B using triple X → 201 (re-hire works).
7. `POST /{A}/restore` → 409 naming every colliding field of triple X.
8. Delete B (or use fresh triple), then `POST /{A}/restore` → 200 with cleared markers;
   linked login (if any) still blocked until explicit `PUT {"is_active": true}`.

> Live Supabase credentials are not required for any step above except step 2's remote
> call; skip it and seed the link locally when running without credentials (same
> approach as feature 039's suite).

## CI note

GitHub workflow applies `db/schema.sql` fresh then runs finance+crm suites only. The
HR suites run locally/pre-merge; schema files are synced in the same change so a
future CI expansion inherits correct constraints.
